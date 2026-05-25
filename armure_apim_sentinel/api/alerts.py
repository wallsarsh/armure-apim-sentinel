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
	doc.insert(ignore_permissions=True)

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
def delete_rule():
	data = frappe.local.form_dict
	if isinstance(data, str):
		data = frappe.parse_json(data)

	name = data.get("rule_name") or data.get("name")
	frappe.delete_doc("Security Alert Rule", name, ignore_permissions=True)

	return {"status": "deleted", "name": name}


@frappe.whitelist(allow_guest=True, methods="GET")
def list_rules():
	rules = frappe.get_all(
		"Security Alert Rule",
		fields=["name", "rule_name", "metric", "condition", "threshold", "severity", "is_active"],
		order_by="creation asc",
	)
	return rules
