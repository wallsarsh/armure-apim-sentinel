import frappe


def after_migrate():
	"""Idempotent seed function. Only seeds data if the DocTypes exist."""
	if frappe.db.exists("DocType", "Log Ingest Adapter"):
		seed_default_sources()
	if frappe.db.exists("DocType", "Security Alert Rule"):
		seed_default_rules()
	if frappe.db.exists("DocType", "API Security App Settings"):
		seed_app_settings()


def seed_default_sources():
	defaults = [
		{"channel_name": "Auth Service", "protocol_type": "Gateway"},
		{"channel_name": "Billing Gateway", "protocol_type": "Webhook"},
		{"channel_name": "Catalog Engine", "protocol_type": "Gateway"},
		{"channel_name": "Data Collector", "protocol_type": "Agent"},
	]
	for source in defaults:
		if not frappe.db.exists("Log Ingest Adapter", {"channel_name": source["channel_name"]}):
			doc = frappe.new_doc("Log Ingest Adapter")
			doc.update(source)
			doc.insert()


def seed_default_rules():
	defaults = [
		{
			"rule_name": "Critical Response Latency Spike",
			"metric": "latency",
			"condition": "gt",
			"threshold": 800,
			"severity": "critical",
			"is_active": 1,
		},
		{
			"rule_name": "High HTTP Error Count",
			"metric": "status_code",
			"condition": "gt",
			"threshold": 499,
			"severity": "warning",
			"is_active": 1,
		},
		{
			"rule_name": "Rate Limit Exhaustion Trigger",
			"metric": "rate_limit",
			"condition": "lt",
			"threshold": 5,
			"severity": "info",
			"is_active": 1,
		},
		{
			"rule_name": "Repeated 5xx Burst Detection",
			"metric": "status_code",
			"condition": "gt",
			"threshold": 499,
			"severity": "critical",
			"is_active": 1,
			"count_based": 1,
			"evaluation_window": 5,
			"min_trigger_count": 3,
			"filter_status_min": 500,
			"group_by": "path",
		},
	]
	for rule in defaults:
		if not frappe.db.exists("Security Alert Rule", {"rule_name": rule["rule_name"]}):
			doc = frappe.new_doc("Security Alert Rule")
			doc.update(rule)
			doc.insert()


def seed_app_settings():
	if frappe.db.exists("API Security App Settings", "API Security App Settings"):
		return
	settings = frappe.new_doc("API Security App Settings")
	settings.opensearch_host = "opensearch"
	settings.opensearch_port = 9200
	settings.opensearch_user = "admin"
	settings.enable_live_simulation = 1
	settings.simulation_interval_ms = 4000
	settings.insert()
