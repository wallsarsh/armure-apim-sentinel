import frappe
from armure_apim_sentinel.notification.adapter_base import NotificationAdapter


class SlackAdapter(NotificationAdapter):
	def send(self, payload: dict, config: dict) -> dict:
		webhook_url = config.get("webhook_url")
		if not webhook_url:
			return {"success": False, "error": "Missing webhook_url"}

		color_map = {"info": "#36a64f", "warning": "#ffcc00", "critical": "#ff0000"}

		blocks = [
			{
				"type": "header",
				"text": {"type": "plain_text", "text": payload.get("title", "Armure APIM Alert")},
			},
			{
				"type": "section",
				"text": {"type": "mrkdwn", "text": payload.get("message", "")},
			},
			{
				"type": "section",
				"fields": [
					{"type": "mrkdwn", "text": f"*Severity:* {payload.get('severity', 'unknown')}"},
					{"type": "mrkdwn", "text": f"*Rule:* {payload.get('rule', 'N/A')}"},
				],
			},
			{"type": "context", "elements": [{"type": "mrkdwn", "text": f"Armure APIM Sentinel | {payload.get('timestamp', '')}"}]},
		]

		body = {
			"attachments": [{"color": color_map.get(payload.get("severity"), "#cccccc"), "blocks": blocks}]
		}

		try:
			import requests
			resp = requests.post(webhook_url, json=body, headers={"Content-Type": "application/json"}, timeout=15)
			resp.raise_for_status()
			return {"success": True, "response": resp.text}
		except Exception as e:
			return {"success": False, "error": str(e)}

	@classmethod
	def validate_config(cls, config: dict) -> list[str]:
		errors = []
		if not config.get("webhook_url"):
			errors.append("webhook_url is required")
		return errors
