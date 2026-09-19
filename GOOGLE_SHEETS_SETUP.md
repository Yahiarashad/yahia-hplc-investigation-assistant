# Founding Beta — Durable Google Sheets Analytics

The app already stores beta activity locally and can mirror every anonymous event and optional feedback submission to Google Sheets through a secure Apps Script webhook.

## What is sent

### Events
- UTC timestamp
- anonymous session/tester ID
- source (`qc_gap`, `hplc_assistant`, etc.)
- event (`assessment_started`, `assessment_completed`, `investigation_started`, etc.)
- language
- non-case metadata

### Feedback
- UTC timestamp
- anonymous session/tester ID
- source and language
- rating
- helpfulness/outcome
- perceived accuracy
- most useful part
- requested improvement
- desired feature
- optional name
- optional LinkedIn/email
- anonymized-research consent

**HPLC case text is not mirrored by the beta analytics system.**

## Setup — about 5 minutes

### 1. Create the Sheet
Create a blank Google Sheet named, for example:

`Yahia HPLC Founding Beta — Analytics`

You do not need to create tabs manually. The webhook creates `Events` and `Feedback` on first use.

### 2. Open Apps Script
Inside the Sheet:

`Extensions -> Apps Script`

Delete the default code and paste the full contents of `google_sheets_webhook.gs` from this repository.

### 3. Add the shared webhook token
In Apps Script:

`Project Settings -> Script properties -> Add script property`

Use:

- Property: `BETA_FEEDBACK_WEBHOOK_TOKEN`
- Value: a long private random string that you will also put in Streamlit Secrets

Do not commit this token to GitHub.

### 4. Deploy as a Web App
In Apps Script:

`Deploy -> New deployment -> Web app`

Choose:

- Execute as: **Me**
- Who has access: **Anyone**

Authorize the script, deploy it, and copy the URL ending in `/exec`.

### 5. Add two Streamlit Secrets
Open Streamlit Community Cloud -> your app -> Settings -> Secrets and add:

```toml
BETA_FEEDBACK_WEBHOOK = "https://script.google.com/macros/s/...../exec"
BETA_FEEDBACK_WEBHOOK_TOKEN = "the-same-long-private-token"
```

Keep your existing secrets, including `OPENAI_API_KEY` and `BETA_DASHBOARD_PIN`.

### 6. Verify
Open `Founding Beta Dashboard` and enter your PIN.

When the external mirror is configured, the dashboard will show the durable-storage status. Use the connection test button to send a harmless `storage_test` event.

Then open the Google Sheet. The `Events` tab should contain the new test row.

## Security notes

- The Web App URL may be reachable publicly, but writes are accepted only when the JSON payload contains the matching private token.
- Keep the Apps Script token and Streamlit token private.
- Do not collect confidential company/product/method data through the feedback form.
- The current design intentionally keeps HPLC problem text outside the beta analytics mirror.
