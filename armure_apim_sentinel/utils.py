import json

import frappe
from frappe.utils import cint


def get_cached_rules():
	rules = frappe.cache().get_value("security_alert_rules")
	if rules:
		return rules
	rules = frappe.get_all(
		"Security Alert Rule",
		filters={"is_active": 1},
		fields=["name", "rule_name", "metric", "condition", "threshold", "severity", "duration"],
	)
	frappe.cache().set_value("security_alert_rules", rules, expires_in_sec=300)
	return rules


def invalidate_rules_cache():
	frappe.cache().delete_value("security_alert_rules")


def evaluate_rules_for_log(log_payload):
	rules = get_cached_rules()
	triggered_alerts = []

	for rule in rules:
		trigger = False
		message = ""
		details = {}

		metric = rule.get("metric")
		condition = rule.get("condition")
		threshold = cint(rule.get("threshold"))

		if metric == "latency" and condition == "gt" and log_payload.get("latency", 0) > threshold:
			trigger = True
			message = f"High response latency detected on [{log_payload.get('method')}] {log_payload.get('path')}. Reached {log_payload.get('latency')}ms (threshold: {threshold}ms)."

		elif metric == "status_code" and condition == "gt" and log_payload.get("status", 0) > threshold:
			trigger = True
			message = f"HTTP {log_payload.get('status')} Error on [{log_payload.get('method')}] {log_payload.get('path')} for source \"{log_payload.get('source')}\"."

		elif metric == "rate_limit" and condition == "lt":
			remaining = log_payload.get("rateLimitRemaining")
			if remaining is not None and remaining < threshold:
				trigger = True
				message = f"IP {log_payload.get('ip')} is close to exceeding rate limit on gateway! Only {remaining} requests remaining."

		if trigger:
			alert_data = {
				"rule": rule.get("name"),
				"alert_message": message,
				"severity": rule.get("severity"),
				"alert_type": "System",
				"resolved": 0,
				"details": json.dumps(log_payload, default=str),
			}
			triggered_alerts.append(alert_data)

	return triggered_alerts


def get_cached(key):
	return frappe.cache().get_value(key)


def set_cached(key, value, ttl=300):
	frappe.cache().set_value(key, value, expires_in_sec=ttl)


def invalidate(prefix):
	keys = frappe.cache().get_keys(prefix)
	for key in keys:
		frappe.cache().delete_value(key)


def get_severity_theme(severity):
	themes = {
		"info": "blue",
		"warning": "orange",
		"critical": "red",
	}
	return themes.get(severity, "gray")


def format_latency(ms):
	if ms < 1000:
		return f"{ms}ms"
	return f"{ms / 1000:.1f}s"
