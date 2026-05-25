import json

import frappe
from armure_apim_sentinel.notification.adapter_base import NotificationAdapter


class DiscordAdapter(NotificationAdapter):
	def send(self, payload: dict, config: dict) -> dict:
		webhook_url = config.get("webhook_url")
		if not webhook_url:
			return {"success": False, "error": "Missing webhook_url"}

		embed = {
			"title": payload.get("title", "Armure APIM Alert"),
			"description": payload.get("message", ""),
			"color": {"info": 3447003, "warning": 15105570, "critical": 15548997}.get(
				payload.get("severity"), 10070709
			),
			"fields": [
				{"name": "Severity", "value": payload.get("severity", "unknown"), "inline": True},
				{"name": "Rule", "value": payload.get("rule", "N/A"), "inline": True},
				{"name": "Timestamp", "value": payload.get("timestamp", ""), "inline": False},
			],
			"footer": {"text": "Armure APIM Sentinel"},
		}

		try:
			import requests
			resp = requests.post(
				webhook_url,
				json={"embeds": [embed]},
				headers={"Content-Type": "application/json"},
				timeout=15,
			)
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
