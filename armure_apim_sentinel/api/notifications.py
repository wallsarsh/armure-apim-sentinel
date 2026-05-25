import json

import frappe
from frappe import _

from armure_apim_sentinel.notification import get_adapter
from armure_apim_sentinel.notification.queue import send_queued_notification


@frappe.whitelist(allow_guest=True, methods="GET")
def list_channels():
	channels = frappe.get_all(
		"Notification Channel",
		fields=["name", "channel_name", "channel_type", "is_active", "rate_limit_per_minute", "config_json"],
		order_by="creation asc",
	)
	for ch in channels:
		ch["config_preview"] = _mask_config(ch["channel_type"], ch["config_json"])
	return channels


def _mask_config(channel_type, config_json):
	try:
		config = json.loads(config_json or "{}")
	except (json.JSONDecodeError, TypeError):
		return {}
	masked = {}
	for k, v in config.items():
		if any(secret in k.lower() for secret in ["password", "token", "secret", "key", "auth"]):
			masked[k] = "********"
		else:
			masked[k] = v
	return masked


@frappe.whitelist(allow_guest=True, methods="POST")
def create_channel():
	data = frappe.local.form_dict
	if isinstance(data, str):
		data = frappe.parse_json(data)

	channel_type = data.get("channel_type")
	config = data.get("config_json", {})

	if isinstance(config, str):
		try:
			config = json.loads(config)
		except (json.JSONDecodeError, TypeError):
			config = {}

	adapter = get_adapter(channel_type)
	errors = adapter.validate_config(config)
	if errors:
		return {"status": "error", "errors": errors}

	doc = frappe.new_doc("Notification Channel")
	doc.channel_name = data.get("channel_name")
	doc.channel_type = channel_type
	doc.is_active = 1
	doc.rate_limit_per_minute = data.get("rate_limit_per_minute", 60)
	doc.config_json = json.dumps(config)
	doc.insert(ignore_permissions=True)

	return {"status": "created", "name": doc.name}


@frappe.whitelist(allow_guest=True, methods="POST")
def toggle_channel():
	data = frappe.local.form_dict
	if isinstance(data, str):
		data = frappe.parse_json(data)

	name = data.get("name") or data.get("channel_name")
	is_active = data.get("is_active", 0)
	doc = frappe.get_doc("Notification Channel", name)
	doc.is_active = 1 if is_active else 0
	doc.save(ignore_permissions=True)

	return {"status": "updated", "name": name, "is_active": doc.is_active}


@frappe.whitelist(allow_guest=True, methods="POST")
def delete_channel():
	data = frappe.local.form_dict
	if isinstance(data, str):
		data = frappe.parse_json(data)

	name = data.get("name") or data.get("channel_name")
	frappe.delete_doc("Notification Channel", name, ignore_permissions=True)

	return {"status": "deleted", "name": name}


@frappe.whitelist(allow_guest=True, methods="POST")
def test_channel():
	data = frappe.local.form_dict
	if isinstance(data, str):
		data = frappe.parse_json(data)

	name = data.get("name") or data.get("channel_name")
	channel = frappe.get_doc("Notification Channel", name)

	config = {}
	try:
		config = json.loads(channel.config_json or "{}")
	except (json.JSONDecodeError, TypeError):
		pass

	test_payload = {
		"title": "[TEST] Armure APIM Sentinel - Channel Test",
		"message": "This is a test notification from Armure APIM Sentinel.",
		"severity": "info",
		"rule": "N/A (Test)",
		"timestamp": str(frappe.utils.now_datetime()),
		"channel": name,
		"alert_details": {"test": True},
	}

	try:
		adapter = get_adapter(channel.channel_type)
		result = adapter.send(test_payload, config)
		return {"status": "success" if result.get("success") else "failed", "result": result}
	except Exception as e:
		return {"status": "error", "error": str(e)}


@frappe.whitelist(allow_guest=True, methods="GET")
def list_queue(status=None, limit=50):
	filters = {}
	if status and status != "all":
		filters["status"] = status

	items = frappe.get_all(
		"Notification Queue Item",
		filters=filters,
		fields=["name", "title", "severity", "status", "retry_count", "channel", "rule", "last_error", "next_retry_at", "sent_at", "created_at"],
		order_by="created_at desc",
		limit_page_length=limit,
	)
	return items


@frappe.whitelist(allow_guest=True, methods="POST")
def retry_queue_item():
	data = frappe.local.form_dict
	if isinstance(data, str):
		data = frappe.parse_json(data)

	name = data.get("name") or data.get("queue_item_name")
	if not name:
		frappe.throw(_("Missing queue item name"))

	item = frappe.get_doc("Notification Queue Item", name)
	if item.status in ("sent", "sending"):
		return {"status": "error", "message": "Item already sent or in progress"}

	send_queued_notification(name)
	return {"status": "retrying", "name": name}


@frappe.whitelist(allow_guest=True, methods="GET")
def get_channel_rules(channel_name=None, channel_docname=None):
	"""Get all alert rules linked to a given notification channel."""
	channel_field = frappe.get_value("Notification Channel", channel_docname or {"channel_name": channel_name})
	if not channel_field:
		return []

	links = frappe.get_all(
		"Security Alert Rule Notification",
		filters={"channel": channel_field},
		fields=["parent", "enabled"],
	)
	rules = []
	for link in links:
		rule = frappe.get_value(
			"Security Alert Rule",
			link.parent,
			["rule_name", "metric", "severity", "is_active"],
			as_dict=True,
		)
		if rule:
			rules.append({
				"name": link.parent,
				"rule_name": rule.rule_name,
				"metric": rule.metric,
				"severity": rule.severity,
				"is_active": rule.is_active,
				"enabled": link.enabled,
			})
	return rules


@frappe.whitelist(allow_guest=True, methods="POST")
def link_rule_to_channel():
	"""Link a notification channel to an alert rule."""
	data = frappe.local.form_dict
	if isinstance(data, str):
		data = frappe.parse_json(data)

	rule_name = data.get("rule_name") or data.get("name")
	channel_name = data.get("channel_name")

	ch_doc = frappe.get_value("Notification Channel", {"channel_name": channel_name})
	if not ch_doc:
		return {"status": "error", "message": f"Channel '{channel_name}' not found"}

	# Check if link already exists
	existing = frappe.get_all("Security Alert Rule Notification",
		filters={"parent": rule_name, "parenttype": "Security Alert Rule", "parentfield": "notifications", "channel": ch_doc})
	if existing:
		return {"status": "exists", "message": "Already linked"}

	# Direct insert into child table
	doc = frappe.new_doc("Security Alert Rule Notification")
	doc.parent = rule_name
	doc.parenttype = "Security Alert Rule"
	doc.parentfield = "notifications"
	doc.channel = ch_doc
	doc.enabled = 1
	doc.insert(ignore_permissions=True)

	return {"status": "linked", "rule": rule_name, "channel": channel_name}


@frappe.whitelist(allow_guest=True, methods="POST")
def unlink_rule_from_channel():
	"""Remove a notification channel from an alert rule."""
	data = frappe.local.form_dict
	if isinstance(data, str):
		data = frappe.parse_json(data)

	rule_name = data.get("rule_name") or data.get("name")
	channel_name = data.get("channel_name")

	ch_doc = frappe.get_value("Notification Channel", {"channel_name": channel_name})
	if not ch_doc:
		return {"status": "error", "message": f"Channel '{channel_name}' not found"}

	existing = frappe.get_all("Security Alert Rule Notification",
		filters={"parent": rule_name, "parenttype": "Security Alert Rule", "parentfield": "notifications", "channel": ch_doc},
		limit=1)
	if not existing:
		return {"status": "error", "message": "Link not found"}

	frappe.delete_doc("Security Alert Rule Notification", existing[0].name, ignore_permissions=True)

	return {"status": "unlinked", "rule": rule_name, "channel": channel_name}


@frappe.whitelist(allow_guest=True, methods="GET")
def list_notification_logs(limit=50, status=None, channel=None):
	filters = {}
	if status and status != "all":
		filters["status"] = status
	if channel:
		filters["channel"] = channel

	logs = frappe.get_all(
		"Notification Log",
		filters=filters,
		fields=["name", "title", "channel", "channel_type", "severity", "rule", "status", "response", "error_message", "attempts", "sent_at", "created_at"],
		order_by="created_at desc",
		limit_page_length=limit,
	)
	return logs
