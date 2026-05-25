import fnmatch
import json
import re

import frappe
from frappe.utils import cint


if not hasattr(frappe, "_rule_cache_imported"):
	import ipaddress
	frappe._rule_cache_imported = True


def get_cached_rules():
	rules = frappe.cache().get_value("security_alert_rules")
	if rules:
		return rules
	rules = frappe.get_all(
		"Security Alert Rule",
		filters={"is_active": 1},
		fields=[
			"name", "rule_name", "metric", "condition", "threshold", "severity", "duration",
			"filter_method", "filter_path_pattern", "filter_path_search_type",
			"filter_source", "filter_ip_range",
			"filter_user_agent_pattern", "filter_user_agent_search_type",
			"filter_min_payload", "filter_max_payload",
			"filter_status_min", "filter_status_max",
			"count_based", "evaluation_window", "min_trigger_count", "group_by",
		],
	)
	frappe.cache().set_value("security_alert_rules", rules, expires_in_sec=300)
	return rules


def invalidate_rules_cache():
	frappe.cache().delete_value("security_alert_rules")


def _matches_filters(log, rule):
	if rule.get("filter_method") and rule["filter_method"] != "Any":
		if log.get("method", "").upper() != rule["filter_method"].upper():
			return False

	if rule.get("filter_path_pattern"):
		if not _match_pattern(
			log.get("path", ""),
			rule["filter_path_pattern"],
			rule.get("filter_path_search_type", "glob"),
		):
			return False

	if rule.get("filter_source"):
		if log.get("source", "") != rule["filter_source"]:
			return False

	if rule.get("filter_ip_range"):
		if not _match_ip_range(log.get("ip", ""), rule["filter_ip_range"]):
			return False

	if rule.get("filter_user_agent_pattern"):
		if not _match_pattern(
			log.get("userAgent", "") or log.get("user_agent", ""),
			rule["filter_user_agent_pattern"],
			rule.get("filter_user_agent_search_type", "glob"),
		):
			return False

	min_pl = cint(rule.get("filter_min_payload", 0))
	if min_pl > 0:
		payload = log.get("payloadSize") or log.get("payload_size") or 0
		if payload < min_pl:
			return False

	max_pl = cint(rule.get("filter_max_payload", 0))
	if max_pl > 0:
		payload = log.get("payloadSize") or log.get("payload_size") or 0
		if payload > max_pl:
			return False

	min_st = cint(rule.get("filter_status_min", 0))
	if min_st > 0:
		if cint(log.get("status", 200)) < min_st:
			return False

	max_st = cint(rule.get("filter_status_max", 0))
	if max_st > 0:
		if cint(log.get("status", 200)) > max_st:
			return False

	return True


def _match_pattern(value, pattern, search_type="glob"):
	if not pattern:
		return True
	if search_type == "regex" or pattern.startswith("re:"):
		pat = pattern[3:] if pattern.startswith("re:") else pattern
		try:
			return bool(re.search(pat, value))
		except re.error:
			return False
	return fnmatch.fnmatch(value, pattern)


def _match_ip_range(ip_str, ranges_str):
	if not ip_str or not ranges_str:
		return True
	try:
		addr = ipaddress.ip_address(ip_str)
	except ValueError:
		return False
	parts = [p.strip() for p in ranges_str.split(",") if p.strip()]
	for part in parts:
		try:
			if "/" in part:
				if addr in ipaddress.ip_network(part, strict=False):
					return True
			else:
				if addr == ipaddress.ip_address(part):
					return True
		except ValueError:
			continue
	return False


def _build_group_by_value(rule, log):
	group_by = rule.get("group_by", "none")
	if group_by == "source":
		return log.get("source", "unknown")
	if group_by == "ip":
		return log.get("ip", "unknown")
	if group_by == "path":
		return log.get("path", "unknown")
	if group_by == "method":
		return log.get("method", "unknown")
	return "global"


def _check_count_based_rule(rule, log):
	group_val = _build_group_by_value(rule, log)
	cache = frappe.cache()

	count_key = f"rule_count:{rule['name']}:{group_val}"
	alerted_key = f"rule_alerted:{rule['name']}:{group_val}"
	window_sec = cint(rule.get("evaluation_window", 5)) * 60

	count = cache.get_value(count_key) or 0
	count += 1
	cache.set_value(count_key, count, expires_in_sec=window_sec)

	min_count = cint(rule.get("min_trigger_count", 1))
	if count >= min_count:
		already_alerted = cache.get_value(alerted_key) or False
		if not already_alerted:
			cache.set_value(alerted_key, True, expires_in_sec=window_sec)
			return True, count, group_val

	return False, count, group_val


def _check_metric_condition(log, rule):
	metric = rule.get("metric")
	condition = rule.get("condition")
	threshold = cint(rule.get("threshold"))

	if metric == "latency" and condition == "gt":
		return cint(log.get("latency", 0)) > threshold

	if metric == "latency" and condition == "lt":
		return cint(log.get("latency", 0)) < threshold

	if metric == "latency" and condition == "eq":
		return cint(log.get("latency", 0)) == threshold

	if metric == "status_code" and condition == "gt":
		return cint(log.get("status", 200)) > threshold

	if metric == "status_code" and condition == "lt":
		return cint(log.get("status", 200)) < threshold

	if metric == "status_code" and condition == "eq":
		return cint(log.get("status", 200)) == threshold

	if metric == "rate_limit":
		remaining = log.get("rateLimitRemaining")
		if remaining is None:
			remaining = log.get("rate_limit_remaining")
		if remaining is None:
			return False
		if condition == "lt":
			return cint(remaining) < threshold
		if condition == "gt":
			return cint(remaining) > threshold
		if condition == "eq":
			return cint(remaining) == threshold

	return False


def _build_alert_message(rule, log, trigger_type="metric", count=None, group_val=None):
	if trigger_type == "count":
		return (
			f"Count-based rule '{rule.get('rule_name')}' triggered: "
			f"{count} matching logs in {rule.get('evaluation_window', 5)} min window "
			f"({group_val or 'global'}). "
			f"Latest: [{log.get('method')}] {log.get('path')} "
			f"from {log.get('source')} ({log.get('ip')})."
		)

	metric = rule.get("metric")
	if metric == "latency":
		return (
			f"High response latency detected on [{log.get('method')}] {log.get('path')}. "
			f"Reached {log.get('latency')}ms (threshold: {rule.get('threshold')}ms)."
		)
	if metric == "status_code":
		return (
			f"HTTP {log.get('status')} Error on [{log.get('method')}] {log.get('path')} "
			f"for source \"{log.get('source')}\"."
		)
	if metric == "rate_limit":
		remaining = log.get("rateLimitRemaining") or log.get("rate_limit_remaining") or 0
		return (
			f"IP {log.get('ip')} is close to exceeding rate limit on gateway! "
			f"Only {remaining} requests remaining."
		)
	return f"Rule '{rule.get('rule_name')}' triggered by log."


def evaluate_rules_for_log(log_payload):
	rules = get_cached_rules()
	triggered_alerts = []

	for rule in rules:
		if not _matches_filters(log_payload, rule):
			continue

		count_based = cint(rule.get("count_based", 0))
		trigger = False
		message = ""
		details = {}

		if count_based:
			triggered, count, group_val = _check_count_based_rule(rule, log_payload)
			if triggered:
				trigger = True
				message = _build_alert_message(rule, log_payload, trigger_type="count", count=count, group_val=group_val)
		else:
			if _check_metric_condition(log_payload, rule):
				trigger = True
				message = _build_alert_message(rule, log_payload)

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
