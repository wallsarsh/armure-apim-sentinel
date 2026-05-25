import frappe
from armure_apim_sentinel.notification.adapter_base import NotificationAdapter


class TeamsAdapter(NotificationAdapter):
	def send(self, payload: dict, config: dict) -> dict:
		frappe.logger().warning("TeamsAdapter not yet implemented — notification skipped")
		return {"success": False, "error": "Not implemented"}

	@classmethod
	def validate_config(cls, config: dict) -> list[str]:
		return ["Teams adapter is not yet implemented"]
