from flask import Blueprint, render_template, request, jsonify, current_app
from app.models import get_settings, update_settings, record_log, get_logs
from app.mailer import send_smtp_mail, render_template as format_email_body
import json

bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    return render_template("index.html")

@bp.route("/api/settings", methods=["GET", "POST"])
def handle_settings():
    db_path = current_app.config["DATABASE"]
    if request.method == "POST":
        payload = request.get_json(force=True)
        update_settings(db_path, payload)
        return jsonify({"status": "success", "message": "Settings updated successfully"})
    
    settings = get_settings(db_path)
    if settings:
        settings["password_set"] = bool(settings.get("password"))
        settings["password"] = ""  # Mask password
    return jsonify(settings)

@bp.route("/api/send", methods=["POST"])
def send_single():
    db_path = current_app.config["DATABASE"]
    settings = get_settings(db_path)
    
    recipient = request.form.get("recipient", "").strip()
    subject = request.form.get("subject", "").strip()
    body_text = request.form.get("body_text", "")
    body_html = request.form.get("body_html", None)

    if not recipient or not subject:
        return jsonify({"status": "error", "message": "Recipient and Subject are required."}), 400

    attachments = []
    for file in request.files.getlist("attachments"):
        if file and file.filename:
            attachments.append((file.filename, file.read()))

    success, error = send_smtp_mail(
        settings=settings,
        recipient=recipient,
        subject=subject,
        body_text=body_text,
        body_html=body_html if body_html else None,
        attachments=attachments
    )

    status_code = "SUCCESS" if success else "FAILED"
    record_log(
        db_path=db_path,
        recipient=recipient,
        subject=subject,
        body_preview=body_text or (body_html or ""),
        status=status_code,
        error=error if not success else None,
        is_dry_run=bool(settings.get("dry_run", 1))
    )

    if not success:
        return jsonify({"status": "error", "message": error}), 500
    return jsonify({"status": "success", "message": error or "Email dispatched successfully!"})

@bp.route("/api/batch", methods=["POST"])
def send_batch():
    db_path = current_app.config["DATABASE"]
    settings = get_settings(db_path)
    payload = request.get_json(force=True)

    recipients = payload.get("recipients", [])
    raw_subject = payload.get("subject", "")
    raw_body = payload.get("body", "")
    raw_html = payload.get("html_body", "")

    if not recipients or not isinstance(recipients, list):
        return jsonify({"status": "error", "message": "Recipients list is required."}), 400

    results = []
    for item in recipients:
        rec_email = item.get("email", "").strip()
        if not rec_email:
            continue

        subj = format_email_body(raw_subject, item)
        body_txt = format_email_body(raw_body, item)
        body_h = format_email_body(raw_html, item) if raw_html else None

        ok, err = send_smtp_mail(settings, rec_email, subj, body_txt, body_h)
        status_code = "SUCCESS" if ok else "FAILED"
        record_log(db_path, rec_email, subj, body_txt, status_code, err, bool(settings.get("dry_run", 1)))
        results.append({"email": rec_email, "success": ok, "error": err})

    return jsonify({"status": "success", "results": results})

@bp.route("/api/logs", methods=["GET"])
def fetch_logs():
    db_path = current_app.config["DATABASE"]
    limit = request.args.get("limit", 50, type=int)
    logs = get_logs(db_path, limit)
    return jsonify(logs)
