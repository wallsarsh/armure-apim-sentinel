import frappe
from armure_apim_sentinel.notification.adapter_base import NotificationAdapter


class WhatsAppAdapter(NotificationAdapter):
	def send(self, payload: dict, config: dict) -> dict:
		frappe.logger().warning("WhatsAppAdapter not yet implemented — notification skipped")
		return {"success": False, "error": "Not implemented"}

	@classmethod
	def validate_config(cls, config: dict) -> list[str]:
		return ["WhatsApp adapter is not yet implemented"]
