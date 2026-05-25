import json

import frappe
from armure_apim_sentinel.notification.adapter_base import NotificationAdapter


class HTTPAdapter(NotificationAdapter):
	def send(self, payload: dict, config: dict) -> dict:
		url = config.get("url")
		if not url:
			return {"success": False, "error": "Missing URL"}

		method = config.get("method", "POST").upper()
		headers = config.get("headers", {})
		template = config.get("template", "")

		if template:
			body_str = self._render_template(template, payload)
			try:
				body = json.loads(body_str)
			except (json.JSONDecodeError, TypeError):
				body = body_str
		else:
			body = payload

		try:
			import requests
			if method == "GET":
				resp = requests.get(url, headers=headers, params=body, timeout=15)
			else:
				resp = requests.post(url, json=body, headers=headers, timeout=15)
			resp.raise_for_status()
			return {"success": True, "response": resp.text}
		except Exception as e:
			return {"success": False, "error": str(e)}

	@classmethod
	def validate_config(cls, config: dict) -> list[str]:
		errors = []
		if not config.get("url"):
			errors.append("url is required")
		return errors

	def _render_template(self, template: str, payload: dict) -> str:
		result = template
		for key, value in payload.items():
			placeholder = "{" + key + "}"
			if placeholder in result:
				result = result.replace(placeholder, str(value))
		return result
