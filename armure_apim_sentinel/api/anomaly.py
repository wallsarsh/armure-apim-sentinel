import json
from datetime import datetime

import frappe
from frappe import _

from armure_apim_sentinel.opensearch_client import get_client, aggregate_dashboard
from armure_apim_sentinel.realtime import publish_alert, publish_scan_complete


@frappe.whitelist(allow_guest=True, methods="POST")
def trigger_anomaly_scan():
	client = get_client()
	now = datetime.utcnow()

	query = {
		"size": 85,
		"query": {
			"range": {"timestamp": {"gte": (now).isoformat()}}
		},
		"sort": [{"timestamp": {"order": "desc"}}],
	}

	try:
		response = client.search(index="api-telemetry-logs-*", body=query)
	except Exception:
		frappe.throw(_("OpenSearch query failed"))

	logs = [hit["_source"] for hit in response.get("hits", {}).get("hits", [])]
	logs_payload = json.dumps([
		{
			"id": log.get("id"),
			"method": log.get("method"),
			"path": log.get("path"),
			"status": log.get("status"),
			"latency": log.get("latency"),
			"source": log.get("source"),
			"ip": log.get("ip"),
		}
		for log in logs
	])

	frappe.enqueue(
		"armure_apim_sentinel.api.ai.run_ai_audit",
		queue="long",
		logs_json=logs_payload,
		now=frappe.conf.developer_mode or False,
	)

	return {"status": "scan_queued", "logs_count": len(logs)}


@frappe.whitelist(allow_guest=True, methods="GET")
def list_anomaly_reports(limit=10):
	reports = frappe.get_all(
		"AI Audit Assessment",
		fields=["name", "scan_time", "anomaly_score", "triggered_alerts_count", "generated_summary"],
		order_by="scan_time desc",
		limit_page_length=limit,
	)
	return reports
