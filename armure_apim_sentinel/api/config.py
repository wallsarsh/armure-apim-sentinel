import csv
import json
from io import StringIO

import frappe
from frappe import _

from armure_apim_sentinel.opensearch_client import get_settings


@frappe.whitelist(allow_guest=True, methods="GET")
def get_settings_data():
	settings = get_settings()
	ai_provider = settings.ai_provider or "Gemini"
	if ai_provider == "Gemini":
		gemini_key = frappe.conf.get("gemini_api_key")
		ai_configured = bool(gemini_key) and bool(settings.ai_model)
	else:
		ai_configured = bool(settings.ai_api_key) and bool(settings.ai_api_base) and bool(settings.ai_model)
	return {
		"opensearch_host": settings.opensearch_host,
		"opensearch_port": settings.opensearch_port,
		"enable_live_simulation": settings.enable_live_simulation,
		"simulation_interval_ms": settings.simulation_interval_ms,
		"ai_provider": ai_provider,
		"ai_api_base": settings.ai_api_base or "",
		"ai_model": settings.ai_model or "",
		"ai_configured": ai_configured,
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
	if "ai_provider" in data:
		settings.ai_provider = data["ai_provider"]
	if "ai_api_base" in data:
		settings.ai_api_base = data["ai_api_base"]
	if "ai_model" in data:
		settings.ai_model = data["ai_model"]
	if "ai_api_key" in data:
		settings.ai_api_key = data["ai_api_key"]
	settings.save(ignore_permissions=True)

	return {"status": "updated"}
