import os
import pytest
import tempfile
from app import create_app
from app.models import get_logs, get_settings
from app.mailer import render_template, build_email_message, send_smtp_mail

@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    app = create_app({"TESTING": True, "DATABASE": db_path})

    with app.test_client() as client:
        yield client

    os.close(db_fd)
    os.unlink(db_path)

def test_index_route(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"CleanMail" in res.data

def test_template_rendering():
    template = "Hello {{name}}, your account at {{service}} is ready."
    context = {"name": "Alice", "service": "CleanMail"}
    rendered = render_template(template, context)
    assert rendered == "Hello Alice, your account at CleanMail is ready."

def test_build_email_message():
    msg = build_email_message(
        sender_name="Tester",
        sender_email="test@example.com",
        recipient="dest@example.com",
        subject="Unit Test Subject",
        body_text="Hello test body",
        body_html="<p>Hello test body</p>",
        attachments=[("note.txt", b"sample attachment content")]
    )
    raw_str = msg.as_string()
    assert "Subject: Unit Test Subject" in raw_str
    assert "To: dest@example.com" in raw_str
    assert "note.txt" in raw_str

def test_single_send_dry_run(client):
    data = {
        "recipient": "user@domain.com",
        "subject": "Test Subject",
        "body_text": "This is a dry run test."
    }
    res = client.post("/api/send", data=data)
    assert res.status_code == 200
    json_resp = res.get_json()
    assert json_resp["status"] == "success"

    # Verify log in outbox
    logs_res = client.get("/api/logs")
    logs = logs_res.get_json()
    assert len(logs) >= 1
    assert logs[0]["recipient"] == "user@domain.com"
    assert logs[0]["status"] == "SUCCESS"

def test_batch_send_endpoint(client):
    payload = {
        "recipients": [
            {"email": "dev1@example.com", "name": "Dev One"},
            {"email": "dev2@example.com", "name": "Dev Two"}
        ],
        "subject": "Notice for {{name}}",
        "body": "Welcome {{name}}!"
    }
    res = client.post("/api/batch", json=payload)
    assert res.status_code == 200
    json_resp = res.get_json()
    assert len(json_resp["results"]) == 2
    assert json_resp["results"][0]["success"] is True

def test_settings_update(client):
    update_data = {
        "host": "smtp.custommail.org",
        "port": 465,
        "sender_name": "Custom Sender",
        "sender_email": "custom@custommail.org",
        "dry_run": True,
        "use_ssl": True
    }
    res = client.post("/api/settings", json=update_data)
    assert res.status_code == 200

    get_res = client.get("/api/settings")
    settings = get_res.get_json()
    assert settings["host"] == "smtp.custommail.org"
    assert settings["port"] == 465
    assert settings["use_ssl"] == 1
