import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import frappe
from armure_apim_sentinel.notification.adapter_base import NotificationAdapter


class EmailAdapter(NotificationAdapter):
	def send(self, payload: dict, config: dict) -> dict:
		smtp_host = config.get("smtp_host")
		if not smtp_host:
			return {"success": False, "error": "SMTP not configured, use Frappe's built-in email"}

		to_emails = config.get("to_emails", [])
		if not to_emails:
			return {"success": False, "error": "No recipient emails configured"}

		from_email = config.get("from_email", "armure@localhost")
		smtp_port = int(config.get("smtp_port", 587))
		smtp_user = config.get("smtp_user", "")
		smtp_password = config.get("smtp_password", "")
		use_tls = bool(config.get("use_tls", True))

		msg = MIMEMultipart()
		msg["From"] = from_email
		msg["To"] = ", ".join(to_emails)
		msg["Subject"] = payload.get("title", "Armure APIM Alert")

		body = payload.get("message", "")
		body += f"\n\n---\nSeverity: {payload.get('severity', 'N/A')}\n"
		body += f"Rule: {payload.get('rule', 'N/A')}\n"
		body += f"Timestamp: {payload.get('timestamp', 'N/A')}"
		msg.attach(MIMEText(body, "plain"))

		try:
			context = ssl.create_default_context()
			with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
				if use_tls:
					server.starttls(context=context)
				if smtp_user:
					server.login(smtp_user, smtp_password)
				server.sendmail(from_email, to_emails, msg.as_string())
			return {"success": True, "response": f"Email sent to {len(to_emails)} recipients"}
		except Exception as e:
			return {"success": False, "error": str(e)}

	@classmethod
	def validate_config(cls, config: dict) -> list[str]:
		errors = []
		if not config.get("smtp_host"):
			errors.append("smtp_host is required")
		if not config.get("to_emails"):
			errors.append("At least one recipient email (to_emails) is required")
		return errors
