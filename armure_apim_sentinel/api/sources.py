import secrets

import frappe
from frappe import _


@frappe.whitelist(allow_guest=True, methods="POST")
def create_source():
	data = frappe.local.form_dict
	if isinstance(data, str):
		data = frappe.parse_json(data)

	doc = frappe.new_doc("Log Ingest Adapter")
	doc.channel_name = data.get("channel_name")
	doc.protocol_type = data.get("protocol_type", "Gateway")
	doc.status = "Active"
	token = secrets.token_urlsafe(24)
	doc.secret_token = token
	doc.insert(ignore_permissions=True)

	return {"name": doc.name, "secret_token": token}


@frappe.whitelist(allow_guest=True, methods="POST")
def toggle_source():
	data = frappe.local.form_dict
	if isinstance(data, str):
		data = frappe.parse_json(data)

	name = data.get("name")
	doc = frappe.get_doc("Log Ingest Adapter", name)
	doc.status = "Inactive" if doc.status == "Active" else "Active"
	doc.save(ignore_permissions=True)

	return {"name": doc.name, "status": doc.status}


@frappe.whitelist(allow_guest=True, methods="POST")
def delete_source():
	data = frappe.local.form_dict
	if isinstance(data, str):
		data = frappe.parse_json(data)

	name = data.get("name")
	frappe.delete_doc("Log Ingest Adapter", name, ignore_permissions=True)

	return {"status": "deleted", "name": name}


@frappe.whitelist(allow_guest=True, methods="GET")
def list_sources():
	sources = frappe.get_all(
		"Log Ingest Adapter",
		fields=["name", "channel_name", "protocol_type", "status", "total_logs_received", "creation"],
	)
	return sources
