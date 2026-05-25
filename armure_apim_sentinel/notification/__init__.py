import json

import frappe

from armure_apim_sentinel.notification.adapters.discord import DiscordAdapter
from armure_apim_sentinel.notification.adapters.slack import SlackAdapter
from armure_apim_sentinel.notification.adapters.email import EmailAdapter
from armure_apim_sentinel.notification.adapters.http import HTTPAdapter
from armure_apim_sentinel.notification.adapters.teams import TeamsAdapter
from armure_apim_sentinel.notification.adapters.telegram import TelegramAdapter
from armure_apim_sentinel.notification.adapters.whatsapp import WhatsAppAdapter
from armure_apim_sentinel.notification.adapters.sms import SMSAdapter


_ADAPTER_MAP = {
	"discord": DiscordAdapter(),
	"slack": SlackAdapter(),
	"email": EmailAdapter(),
	"http": HTTPAdapter(),
	"teams": TeamsAdapter(),
	"telegram": TelegramAdapter(),
	"whatsapp": WhatsAppAdapter(),
	"sms": SMSAdapter(),
}


def get_adapter(channel_type: str):
	adapter = _ADAPTER_MAP.get(channel_type)
	if not adapter:
		raise ValueError(f"Unknown channel type: {channel_type}")
	return adapter


def _build_payload(alert_doc, channel_name: str) -> dict:
	details = {}
	try:
		details = json.loads(alert_doc.details or "{}")
	except (json.JSONDecodeError, TypeError):
		pass

	return {
		"title": f"[{alert_doc.severity.upper()}] Security Alert - {alert_doc.alert_type}",
		"message": alert_doc.alert_message or "No message",
		"severity": alert_doc.severity or "info",
		"rule": alert_doc.rule or "N/A",
		"rule_url": "",
		"timestamp": str(alert_doc.timestamp or ""),
		"channel": channel_name,
		"alert_details": details,
	}


def dispatch_notification(alert_doc, rule_name: str = None):
	rule = alert_doc.rule or rule_name
	if not rule:
		return

	rule_doc = frappe.get_doc("Security Alert Rule", rule)
	notifications = rule_doc.get("notifications", [])
	if not notifications:
		return

	for row in notifications:
		if not row.get("enabled"):
			continue

		channel_name = row.get("channel")
		if not channel_name:
			continue

		channel_doc = frappe.get_value(
			"Notification Channel",
			channel_name,
			["channel_type", "config_json", "rate_limit_per_minute", "name"],
			as_dict=True,
		)
		if not channel_doc or not channel_doc.channel_type:
			continue

		channel_config = {}
		try:
			channel_config = json.loads(channel_doc.config_json or "{}")
		except (json.JSONDecodeError, TypeError):
			pass

		payload = _build_payload(alert_doc, channel_name)

		queue_item = frappe.new_doc("Notification Queue Item")
		queue_item.title = payload.get("title", "Alert")
		queue_item.severity = alert_doc.severity or "info"
		queue_item.status = "pending"
		queue_item.channel = channel_name
		queue_item.alert_instance = alert_doc.name
		queue_item.rule = rule
		queue_item.payload = json.dumps(payload)
		queue_item.insert(ignore_permissions=True)

		frappe.enqueue(
			"armure_apim_sentinel.notification.queue.send_queued_notification",
			queue_item_name=queue_item.name,
			queue="long",
			timeout=300,
		)
