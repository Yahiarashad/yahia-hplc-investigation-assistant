/*
Yahia HPLC Investigation Assistant — Founding Beta Google Sheets webhook

Mobile-friendly setup (no Extensions menu required):
1) Open https://script.google.com in Chrome.
2) Create a New project.
3) Paste this file into Code.gs.
4) In Apps Script Project Settings -> Script properties, add:
   BETA_FEEDBACK_WEBHOOK_TOKEN = the same long secret used in Streamlit Secrets.
5) Deploy -> New deployment -> Web app.
   Execute as: Me
   Who has access: Anyone
6) Copy the /exec URL into Streamlit Secrets as BETA_FEEDBACK_WEBHOOK.

This script writes directly to the dedicated Founding Beta spreadsheet below.
It does not receive HPLC case text from the app.
*/

const SPREADSHEET_ID = '1HgmAMUl0ZveRdn1LN2gsxuJWyzDpfWHVCQFR4tWDzcg';

const EVENT_HEADERS = [
  'created_at', 'session_id', 'source', 'event', 'language', 'metadata_json'
];

const FEEDBACK_HEADERS = [
  'created_at', 'session_id', 'source', 'language', 'rating', 'outcome',
  'accuracy', 'most_useful', 'improvement', 'desired_feature', 'name',
  'contact', 'consent_research'
];

function doGet() {
  return _jsonResponse({
    ok: true,
    service: 'Yahia Founding Beta Sheets Webhook',
    message: 'POST JSON only'
  });
}

function doPost(e) {
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);

  try {
    const raw = e && e.postData ? e.postData.contents : '';
    if (!raw) return _jsonResponse({ok: false, error: 'empty_body'});

    const payload = JSON.parse(raw);
    const expectedToken = PropertiesService.getScriptProperties()
      .getProperty('BETA_FEEDBACK_WEBHOOK_TOKEN');

    if (!expectedToken) {
      return _jsonResponse({ok: false, error: 'server_token_not_configured'});
    }
    if (!payload.token || payload.token !== expectedToken) {
      return _jsonResponse({ok: false, error: 'unauthorized'});
    }

    const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    if (!ss) return _jsonResponse({ok: false, error: 'spreadsheet_not_found'});

    if (payload.type === 'event') {
      const sheet = _ensureSheet(ss, 'Events', EVENT_HEADERS);
      const row = [
        payload.created_at || new Date().toISOString(),
        payload.session_id || '',
        payload.source || '',
        payload.event || '',
        payload.language || '',
        JSON.stringify(payload.metadata || {})
      ];
      if (!_isDuplicate(sheet, row[0], row[1], row[3])) {
        sheet.appendRow(row);
      }
      return _jsonResponse({ok: true, stored: 'event'});
    }

    if (payload.type === 'feedback') {
      const sheet = _ensureSheet(ss, 'Feedback', FEEDBACK_HEADERS);
      const row = [
        payload.created_at || new Date().toISOString(),
        payload.session_id || '',
        payload.source || '',
        payload.language || '',
        payload.rating == null ? '' : payload.rating,
        payload.outcome || '',
        payload.accuracy || '',
        payload.most_useful || '',
        payload.improvement || '',
        payload.desired_feature || '',
        payload.name || '',
        payload.contact || '',
        payload.consent_research === true
      ];
      if (!_isDuplicate(sheet, row[0], row[1], 'feedback')) {
        sheet.appendRow(row);
      }
      return _jsonResponse({ok: true, stored: 'feedback'});
    }

    return _jsonResponse({ok: false, error: 'unknown_payload_type'});
  } catch (err) {
    return _jsonResponse({ok: false, error: String(err)});
  } finally {
    lock.releaseLock();
  }
}

function _ensureSheet(ss, name, headers) {
  let sheet = ss.getSheetByName(name);
  if (!sheet) sheet = ss.insertSheet(name);

  if (sheet.getLastRow() === 0) {
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    sheet.setFrozenRows(1);
    sheet.getRange(1, 1, 1, headers.length).setFontWeight('bold');
  }
  return sheet;
}

function _isDuplicate(sheet, createdAt, sessionId, eventKey) {
  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) return false;

  const scanStart = Math.max(2, lastRow - 100);
  const count = lastRow - scanStart + 1;
  const width = Math.min(sheet.getLastColumn(), 6);
  const values = sheet.getRange(scanStart, 1, count, width).getValues();

  return values.some(function(row) {
    const sameTime = String(row[0]) === String(createdAt);
    const sameSession = String(row[1]) === String(sessionId);
    const thirdKey = String(row[3] || '');
    return sameTime && sameSession && (eventKey === 'feedback' || thirdKey === String(eventKey));
  });
}

function _jsonResponse(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
