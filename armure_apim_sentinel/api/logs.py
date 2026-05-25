import frappe
from frappe import _

from armure_apim_sentinel.opensearch_client import search_logs, index_log, get_client


@frappe.whitelist(allow_guest=True, methods="GET")
def query_logs(
	search=None,
	source=None,
	status=None,
	method=None,
	min_latency=None,
	max_latency=None,
	start=None,
	end=None,
	page=1,
	page_size=50,
):
	result = search_logs(
		search=search,
		source=source,
		status=status,
		method=method,
		min_latency=min_latency,
		max_latency=max_latency,
		start=start,
		end=end,
		page=page,
		page_size=page_size,
	)
	result["logs"] = [_map_log_fields(log) for log in result.get("logs", [])]
	return result


@frappe.whitelist(allow_guest=True, methods="POST")
def ingest_logs():
	data = frappe.local.form_dict
	if isinstance(data, str):
		data = frappe.parse_json(data)

	logs = data.get("logs") or (data if isinstance(data, list) else [data])

	token = frappe.get_request_header("X-Ingest-Token")
	source_name = None

	if token:
		source_name = frappe.db.get_value("Log Ingest Adapter", {"secret_token": token}, "channel_name")
		if not source_name:
			frappe.throw(_("Invalid ingest token"), frappe.AuthenticationError)
	else:
		source_name = logs[0].get("source") if isinstance(logs, list) and logs else None
		if not source_name:
			source_name = frappe.db.get_value("Log Ingest Adapter", {}, "channel_name")
		if not source_name:
			frappe.throw(_("No source specified and no ingest token provided"), frappe.AuthenticationError)

	client = get_client()
	for log in logs:
		log["source"] = source_name
		index_log(client, log)

	frappe.enqueue(
		"armure_apim_sentinel.utils.evaluate_rules_for_log",
		queue="short",
		log_payload=logs[-1] if logs else {},
	)

	return {"status": "ok", "ingested": len(logs)}


_FIELD_MAP = {
	"user_agent": "userAgent",
	"payload_size": "payloadSize",
	"user_id": "userId",
	"rate_limit_remaining": "rateLimitRemaining",
	"rate_limit_limit": "rateLimitLimit",
	"response_body": "responseBody",
}


def _map_log_fields(log):
	if not isinstance(log, dict):
		return log
	mapped = {}
	for k, v in log.items():
		mapped[_FIELD_MAP.get(k, k)] = v
	return mapped
