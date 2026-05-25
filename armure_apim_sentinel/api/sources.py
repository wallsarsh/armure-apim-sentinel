import secrets
import frappe
from frappe import _

STATUS_MAP = {"Active": "active", "Inactive": "inactive"}


def _docname_by_channel(name):
	docname = frappe.db.get_value("Log Ingest Adapter", {"channel_name": name})
	if not docname:
		docname = frappe.db.get_value("Log Ingest Adapter", name)
	return docname or name


@frappe.whitelist(allow_guest=True, methods="POST")
def add_source():
	data = frappe.local.form_dict
	if isinstance(data, str):
		data = frappe.parse_json(data)

	doc = frappe.new_doc("Log Ingest Adapter")
	doc.channel_name = data.get("name") or data.get("channel_name")
	doc.protocol_type = data.get("type") or data.get("protocol_type", "Gateway")
	doc.status = "Active"
	token = secrets.token_urlsafe(24)
	doc.secret_token = token
	doc.insert(ignore_permissions=True)

	return {"name": doc.channel_name, "secret_token": token}


create_source = add_source


@frappe.whitelist(allow_guest=True, methods="POST")
def toggle_source_status():
	data = frappe.local.form_dict
	if isinstance(data, str):
		data = frappe.parse_json(data)

	source_name = data.get("source_name") or data.get("name")
	if not source_name:
		frappe.throw(_("Missing source name"))
	new_status = data.get("status", "active")
	status_str = "Active" if new_status == "active" else "Inactive"
	doc = frappe.get_doc("Log Ingest Adapter", _docname_by_channel(source_name))
	doc.status = status_str
	doc.save(ignore_permissions=True)
	return {"name": doc.channel_name, "status": new_status}


toggle_source = toggle_source_status


@frappe.whitelist(allow_guest=True, methods="POST")
def remove_source():
	data = frappe.local.form_dict
	if isinstance(data, str):
		data = frappe.parse_json(data)

	source_name = data.get("source_name") or data.get("name")
	if not source_name:
		frappe.throw(_("Missing source name"))
	frappe.delete_doc("Log Ingest Adapter", _docname_by_channel(source_name), ignore_permissions=True)
	return {"status": "deleted", "name": source_name}


delete_source = remove_source


@frappe.whitelist(allow_guest=True, methods="GET")
def list_sources():
	sources = frappe.get_all(
		"Log Ingest Adapter",
		fields=["name", "channel_name", "protocol_type", "status", "secret_token", "total_logs_received", "creation"],
	)
	result = []
	for s in sources:
		result.append({
			"name": s.channel_name,
			"channel_name": s.channel_name,
			"type": s.protocol_type,
			"status": STATUS_MAP.get(s.status, s.status.lower()),
			"apiKeySnippet": _token_snippet(s.secret_token),
			"totalLogsReceived": s.total_logs_received or 0,
			"created": s.creation,
		})
	return result


@frappe.whitelist(allow_guest=True, methods="POST")
def toggle_simulation():
	data = frappe.local.form_dict
	if isinstance(data, str):
		data = frappe.parse_json(data)

	settings = frappe.get_single("API Security App Settings")
	settings.enable_live_simulation = 1 if data.get("active") else 0
	settings.save(ignore_permissions=True)

	return {"active": bool(settings.enable_live_simulation)}


@frappe.whitelist(allow_guest=True, methods="POST")
def set_simulation_speed():
	data = frappe.local.form_dict
	if isinstance(data, str):
		data = frappe.parse_json(data)

	settings = frappe.get_single("API Security App Settings")
	settings.simulation_interval_ms = int(data.get("speed", 3000))
	settings.save(ignore_permissions=True)

	return {"speed": settings.simulation_interval_ms}


def _token_snippet(token):
	if not token:
		return "none"
	if len(token) <= 8:
		return token
	return token[:8] + "..."
