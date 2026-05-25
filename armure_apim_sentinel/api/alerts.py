import frappe
from frappe import _


@frappe.whitelist(allow_guest=True, methods="GET")
def list_alerts(limit=50, status="all"):
	filters = {}
	if status == "unresolved":
		filters["resolved"] = 0
	elif status == "resolved":
		filters["resolved"] = 1

	alerts = frappe.get_all(
		"Alert Instance",
		filters=filters,
		fields=["name", "alert_message", "severity", "alert_type", "resolved", "rule", "timestamp", "details"],
		order_by="timestamp desc",
		limit_page_length=limit,
	)
	result = []
	for a in alerts:
		result.append({
			"name": a.name,
			"message": a.alert_message,
			"severity": a.severity,
			"type": a.alert_type,
			"rule_name": a.rule,
			"resolved": a.resolved,
			"timestamp": a.timestamp,
			"details": a.details,
		})
	return result


@frappe.whitelist(allow_guest=True, methods="POST")
def resolve_alert():
	data = frappe.local.form_dict
	if isinstance(data, str):
		data = frappe.parse_json(data)

	name = data.get("name") or data.get("alert_name")
	if not name:
		frappe.throw(_("Missing alert name"))

	doc = frappe.get_doc("Alert Instance", name)
	doc.resolved = 1
	doc.save(ignore_permissions=True)

	return {"status": "resolved", "name": name}


@frappe.whitelist(allow_guest=True, methods="POST")
def resolve_all_alerts():
	frappe.db.set_value("Alert Instance", {"resolved": 0}, "resolved", 1)
	return {"status": "ok"}


@frappe.whitelist(allow_guest=True, methods="POST")
def create_rule():
	data = frappe.local.form_dict
	if isinstance(data, str):
		data = frappe.parse_json(data)

	doc = frappe.new_doc("Security Alert Rule")
	doc.rule_name = data.get("rule_name")
	doc.metric = data.get("metric")
	doc.condition = data.get("condition", "gt")
	doc.threshold = data.get("threshold")
	doc.severity = data.get("severity", "warning")
	doc.is_active = 1

	filter_fields = [
		"filter_method", "filter_path_pattern", "filter_path_search_type",
		"filter_source", "filter_ip_range",
		"filter_user_agent_pattern", "filter_user_agent_search_type",
		"filter_min_payload", "filter_max_payload",
		"filter_status_min", "filter_status_max",
		"count_based", "evaluation_window", "min_trigger_count", "group_by",
	]
	for field in filter_fields:
		if field in data:
			doc.set(field, data.get(field))

	doc.insert(ignore_permissions=True)

	# Link notification channels to rule
	channels = data.get("notification_channels", [])
	if isinstance(channels, str):
		channels = frappe.parse_json(channels)
	for ch_name in channels:
		ch_doc = frappe.get_value("Notification Channel", {"channel_name": ch_name})
		if ch_doc:
			doc.append("notifications", {"channel": ch_doc, "enabled": 1})
	if channels:
		doc.save(ignore_permissions=True)

	return {"status": "created", "name": doc.name}


@frappe.whitelist(allow_guest=True, methods="POST")
def toggle_rule():
	data = frappe.local.form_dict
	if isinstance(data, str):
		data = frappe.parse_json(data)

	name = data.get("rule_name") or data.get("name")
	is_active = data.get("is_active", 0)
	doc = frappe.get_doc("Security Alert Rule", name)
	doc.is_active = 1 if is_active else 0
	doc.save(ignore_permissions=True)

	return {"status": "updated", "name": name, "is_active": doc.is_active}


@frappe.whitelist(allow_guest=True, methods="POST")
def clone_rule():
	data = frappe.local.form_dict
	if isinstance(data, str):
		data = frappe.parse_json(data)

	src_name = data.get("rule_name") or data.get("name")
	src_fields = frappe.db.get_value("Security Alert Rule", src_name, [
		"rule_name", "metric", "condition", "threshold", "severity",
		"filter_method", "filter_path_pattern", "filter_path_search_type",
		"filter_source", "filter_ip_range",
		"filter_user_agent_pattern", "filter_user_agent_search_type",
		"filter_min_payload", "filter_max_payload",
		"filter_status_min", "filter_status_max",
		"count_based", "evaluation_window", "min_trigger_count", "group_by",
	], as_dict=True)
	if not src_fields:
		frappe.throw(_("Source rule not found"))

	doc = frappe.new_doc("Security Alert Rule")
	doc.rule_name = data.get("new_rule_name") or (src_fields.rule_name + " (Copy)")
	doc.metric = src_fields.metric
	doc.condition = src_fields.condition
	doc.threshold = src_fields.threshold
	doc.severity = src_fields.severity
	doc.is_active = 1

	for field in [
		"filter_method", "filter_path_pattern", "filter_path_search_type",
		"filter_source", "filter_ip_range",
		"filter_user_agent_pattern", "filter_user_agent_search_type",
		"filter_min_payload", "filter_max_payload",
		"filter_status_min", "filter_status_max",
		"count_based", "evaluation_window", "min_trigger_count", "group_by",
	]:
		doc.set(field, src_fields.get(field))

	doc.insert(ignore_permissions=True)

	# Clone notification channels
	notifs = frappe.get_all("Security Alert Rule Notification",
		filters={"parent": src_name, "parenttype": "Security Alert Rule", "parentfield": "notifications"},
		fields=["channel", "enabled"])
	for n in notifs:
		doc.append("notifications", {"channel": n.channel, "enabled": n.enabled})
	if notifs:
		doc.save(ignore_permissions=True)

	return {"status": "cloned", "name": doc.name, "source": src_name}


@frappe.whitelist(allow_guest=True, methods="POST")
def update_rule():
	data = frappe.local.form_dict
	if isinstance(data, str):
		data = frappe.parse_json(data)

	name = data.get("rule_name") or data.get("name")

	# Use db_set for each field to bypass permission checks
	updatable = [
		"rule_name", "metric", "condition", "threshold", "severity",
		"filter_method", "filter_path_pattern", "filter_path_search_type",
		"filter_source", "filter_ip_range",
		"filter_user_agent_pattern", "filter_user_agent_search_type",
		"filter_min_payload", "filter_max_payload",
		"filter_status_min", "filter_status_max",
		"count_based", "evaluation_window", "min_trigger_count", "group_by",
	]
	for field in updatable:
		if field in data:
			frappe.db.set_value("Security Alert Rule", name, field, data.get(field))
	frappe.db.commit()

	return {"status": "updated", "name": name}


@frappe.whitelist(allow_guest=True, methods="POST")
def delete_rule():
	data = frappe.local.form_dict
	if isinstance(data, str):
		data = frappe.parse_json(data)

	name = data.get("rule_name") or data.get("name")
	frappe.delete_doc("Security Alert Rule", name, ignore_permissions=True)

	return {"status": "deleted", "name": name}


@frappe.whitelist(allow_guest=True, methods="POST")
def link_rule_channels():
	data = frappe.local.form_dict
	if isinstance(data, str):
		data = frappe.parse_json(data)

	name = data.get("rule_name") or data.get("name")
	channels = data.get("notification_channels", [])
	if isinstance(channels, str):
		channels = frappe.parse_json(channels)

	doc = frappe.get_doc("Security Alert Rule", name)
	doc.set("notifications", [])
	for ch_name in channels:
		ch_doc = frappe.get_value("Notification Channel", {"channel_name": ch_name})
		if ch_doc:
			doc.append("notifications", {"channel": ch_doc, "enabled": 1})
	doc.save(ignore_permissions=True)

	return {"status": "linked", "name": name}


@frappe.whitelist(allow_guest=True, methods="GET")
def list_rules():
	rule_names = frappe.get_all(
		"Security Alert Rule",
		fields=[
			"name", "rule_name", "metric", "condition", "threshold", "severity", "is_active",
			"filter_method", "filter_path_pattern", "filter_path_search_type",
			"filter_source", "filter_ip_range",
			"filter_user_agent_pattern", "filter_user_agent_search_type",
			"filter_min_payload", "filter_max_payload",
			"filter_status_min", "filter_status_max",
			"count_based", "evaluation_window", "min_trigger_count", "group_by",
		],
		order_by="creation asc",
	)

	for rule in rule_names:
		rule["notification_channels"] = []
		notifs = frappe.get_all(
			"Security Alert Rule Notification",
			filters={"parent": rule["name"], "parenttype": "Security Alert Rule", "parentfield": "notifications"},
			fields=["channel", "enabled"],
		)
		for n in notifs:
			ch = frappe.get_value("Notification Channel", n.channel, "channel_name")
			if ch:
				rule["notification_channels"].append({"name": ch, "enabled": n.enabled})

	return rule_names
