/*
Yahia QC Instrument Lifecycle & Investigation Intelligence — Durable storage webhook

One-time setup:
1) Open https://script.google.com and create a New project.
2) Paste this file into Code.gs.
3) In Project Settings -> Script properties add:
   INSTRUMENT_LIFECYCLE_TOKEN = a long private random string
4) Deploy -> New deployment -> Web app.
   Execute as: Me
   Who has access: Anyone
5) Copy the /exec URL into Streamlit Secrets as:
   INSTRUMENT_LIFECYCLE_WEBHOOK = "https://script.google.com/macros/s/.../exec"
   INSTRUMENT_LIFECYCLE_TOKEN = "the same private token"

Spreadsheet used by this MVP:
Yahia QC Instrument Lifecycle Data
*/

const SPREADSHEET_ID = '1wUTfnkCTZhsNC7waR9p1q5KLLqC1KTDbg6ZZ9ustr18';

const INSTRUMENT_HEADERS = [
  'instrument_id','instrument_name','instrument_type','manufacturer','model',
  'serial_number','location','status','owner','qualification_due','pm_due',
  'calibration_due','created_at'
];

const EVENT_HEADERS = [
  'event_id','instrument_id','event_date','event_type','severity','subsystem',
  'status','observed_facts','immediate_action','root_cause_status','root_cause',
  'reference','created_at'
];

function doGet() {
  return _json({
    ok: true,
    service: 'Yahia QC Instrument Lifecycle Durable Storage',
    message: 'POST JSON only'
  });
}

function doPost(e) {
  const lock = LockService.getScriptLock();
  lock.waitLock(15000);
  try {
    const raw = e && e.postData ? e.postData.contents : '';
    if (!raw) return _json({ok:false, error:'empty_body'});

    const payload = JSON.parse(raw);
    const expectedToken = PropertiesService.getScriptProperties()
      .getProperty('INSTRUMENT_LIFECYCLE_TOKEN');

    if (!expectedToken) return _json({ok:false, error:'server_token_not_configured'});
    if (!payload.token || payload.token !== expectedToken) {
      return _json({ok:false, error:'unauthorized'});
    }

    const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    const action = String(payload.action || '');

    if (action === 'load') {
      const instruments = _readTable(_ensureSheet(ss, 'Instruments'), INSTRUMENT_HEADERS);
      const events = _readTable(_ensureSheet(ss, 'Events'), EVENT_HEADERS);
      const state = _readState(_ensureSheet(ss, 'State'));
      return _json({
        ok: true,
        instruments: instruments,
        events: events,
        last_brief: state.last_brief || '',
        last_result: _safeJsonParse(state.last_result_json || '{}')
      });
    }

    if (action === 'save') {
      const instruments = Array.isArray(payload.instruments) ? payload.instruments : [];
      const events = Array.isArray(payload.events) ? payload.events : [];
      const lastBrief = typeof payload.last_brief === 'string' ? payload.last_brief : '';
      const lastResult = payload.last_result && typeof payload.last_result === 'object'
        ? JSON.stringify(payload.last_result)
        : '{}';

      _writeTable(_ensureSheet(ss, 'Instruments'), INSTRUMENT_HEADERS, instruments);
      _writeTable(_ensureSheet(ss, 'Events'), EVENT_HEADERS, events);
      _writeState(_ensureSheet(ss, 'State'), {
        last_brief: lastBrief,
        last_result_json: lastResult,
        updated_at: new Date().toISOString()
      });
      _appendAudit(_ensureSheet(ss, 'Audit'), instruments.length, events.length);

      return _json({ok:true, saved:true, instruments:instruments.length, events:events.length});
    }

    return _json({ok:false, error:'unknown_action'});
  } catch (err) {
    return _json({ok:false, error:String(err)});
  } finally {
    lock.releaseLock();
  }
}

function _ensureSheet(ss, name) {
  let sheet = ss.getSheetByName(name);
  if (!sheet) sheet = ss.insertSheet(name);
  return sheet;
}

function _writeTable(sheet, headers, records) {
  sheet.clearContents();
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  sheet.setFrozenRows(1);
  sheet.getRange(1, 1, 1, headers.length).setFontWeight('bold');

  if (!records.length) return;
  const rows = records.map(function(record) {
    return headers.map(function(header) {
      const value = record && record[header] != null ? record[header] : '';
      return String(value);
    });
  });
  sheet.getRange(2, 1, rows.length, headers.length).setValues(rows);
}

function _readTable(sheet, headers) {
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return [];
  const values = sheet.getRange(2, 1, lastRow - 1, headers.length).getValues();
  return values.map(function(row) {
    const obj = {};
    headers.forEach(function(header, index) {
      obj[header] = row[index] == null ? '' : String(row[index]);
    });
    return obj;
  }).filter(function(obj) {
    return headers.some(function(header) { return String(obj[header] || '').trim() !== ''; });
  });
}

function _writeState(sheet, state) {
  const rows = [['state_key','state_value']];
  Object.keys(state).forEach(function(key) {
    rows.push([key, String(state[key] == null ? '' : state[key])]);
  });
  sheet.clearContents();
  sheet.getRange(1, 1, rows.length, 2).setValues(rows);
  sheet.setFrozenRows(1);
  sheet.getRange(1, 1, 1, 2).setFontWeight('bold');
}

function _readState(sheet) {
  const lastRow = sheet.getLastRow();
  const state = {};
  if (lastRow < 2) return state;
  const values = sheet.getRange(2, 1, lastRow - 1, 2).getValues();
  values.forEach(function(row) {
    const key = String(row[0] || '').trim();
    if (key) state[key] = row[1] == null ? '' : String(row[1]);
  });
  return state;
}

function _appendAudit(sheet, instrumentCount, eventCount) {
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(['created_at','action','instrument_count','event_count']);
    sheet.setFrozenRows(1);
    sheet.getRange(1, 1, 1, 4).setFontWeight('bold');
  }
  sheet.appendRow([new Date().toISOString(), 'sync_state', instrumentCount, eventCount]);
}

function _safeJsonParse(raw) {
  try {
    const value = JSON.parse(raw || '{}');
    return value && typeof value === 'object' ? value : {};
  } catch (err) {
    return {};
  }
}

function _json(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
