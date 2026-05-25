import csv
import json
from io import StringIO

import frappe
from frappe import _

from armure_apim_sentinel.opensearch_client import get_settings


@frappe.whitelist(allow_guest=True, methods="GET")
def get_settings_data():
	settings = get_settings()
	return {
		"opensearch_host": settings.opensearch_host,
		"opensearch_port": settings.opensearch_port,
		"enable_live_simulation": settings.enable_live_simulation,
		"simulation_interval_ms": settings.simulation_interval_ms,
	}


@frappe.whitelist(allow_guest=True, methods="POST")
def update_settings():
	data = frappe.local.form_dict
	if isinstance(data, str):
		data = frappe.parse_json(data)

	settings = frappe.get_single("API Security App Settings")
	if "opensearch_host" in data:
		settings.opensearch_host = data["opensearch_host"]
	if "opensearch_port" in data:
		settings.opensearch_port = int(data["opensearch_port"])
	if "opensearch_user" in data:
		settings.opensearch_user = data["opensearch_user"]
	if "opensearch_password" in data:
		settings.opensearch_password = data["opensearch_password"]
	if "enable_live_simulation" in data:
		settings.enable_live_simulation = 1 if data["enable_live_simulation"] else 0
	if "simulation_interval_ms" in data:
		settings.simulation_interval_ms = int(data["simulation_interval_ms"])
	settings.save(ignore_permissions=True)

	return {"status": "updated"}
