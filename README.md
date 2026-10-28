# CleanMail - Modern Python Email Dispatcher

A streamlined, production-grade Email Sender application with a responsive web dashboard. Features instant single dispatch, batch templated campaigns, rich HTML email assembly, attachment support, history logging, and a built-in Dry-Run / Simulation mode for testing without active SMTP credentials.

## Features

- **Modern Responsive Dashboard**: Clean UI built with Tailwind CSS for single sending, bulk campaigns, and settings.
- **Direct & Bulk Sending**: Supports recipient personalization with template tags (e.g. `{{name}}`, `{{company}}`).
- **Rich Formats & Attachments**: Send standard text, rich HTML, and binary attachments.
- **Dry-Run / Simulation Mode**: Test templates, campaign delivery logic, and logs safely without credentials.
- **SMTP Protocol Support**: Seamless STARTTLS (Port 587) and SSL (Port 465) configurations.
- **Outbox & Delivery Logs**: Local SQLite log storage tracking timestamps, statuses, recipients, and error traces.

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   python main.py
   ```
   Open `http://127.0.0.1:5000` in your browser.

3. **Run Automated Tests**:
   ```bash
   pytest
   ```

## Configuration

Default settings run in **Dry-Run Mode** (emails are rendered, validated, and logged to the SQLite database without connecting to external SMTP servers). To send live emails, navigate to the **SMTP Settings** tab in the UI or set environment variables:

- `SMTP_HOST`: SMTP server address (e.g., `smtp.gmail.com`)
- `SMTP_PORT`: Port (e.g., `587` or `465`)
- `SMTP_USER`: Login username/email
- `SMTP_PASS`: App password or SMTP password
- `SMTP_USE_TLS`: `true` or `false`
- `SMTP_USE_SSL`: `true` or `false`
