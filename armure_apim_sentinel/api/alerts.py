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
	return alerts


@frappe.whitelist(allow_guest=True, methods="POST")
def resolve_alert():
	data = frappe.local.form_dict
	if isinstance(data, str):
		data = frappe.parse_json(data)

	name = data.get("name")
	doc = frappe.get_doc("Alert Instance", name)
	doc.resolved = 1
	doc.save(ignore_permissions=True)

	return {"status": "resolved", "name": name}


@frappe.whitelist(allow_guest=True, methods="POST")
def bulk_resolve_alerts():
	data = frappe.local.form_dict
	if isinstance(data, str):
		data = frappe.parse_json(data)

	names = data.get("names", [])
	for name in names:
		doc = frappe.get_doc("Alert Instance", name)
		doc.resolved = 1
		doc.save(ignore_permissions=True)

	return {"status": "ok", "resolved": len(names)}
