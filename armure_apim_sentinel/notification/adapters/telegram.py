import frappe
from armure_apim_sentinel.notification.adapter_base import NotificationAdapter


class TelegramAdapter(NotificationAdapter):
	def send(self, payload: dict, config: dict) -> dict:
		frappe.logger().warning("TelegramAdapter not yet implemented — notification skipped")
		return {"success": False, "error": "Not implemented"}

	@classmethod
	def validate_config(cls, config: dict) -> list[str]:
		return ["Telegram adapter is not yet implemented"]
