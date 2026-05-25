import json

import frappe
from frappe import _

from armure_apim_sentinel.ai.provider_factory import get_ai_provider
from armure_apim_sentinel.opensearch_client import get_client
from armure_apim_sentinel.realtime import publish_alert, publish_scan_complete


def run_ai_audit(logs_json):
	try:
		logs = frappe.parse_json(logs_json)
	except Exception:
		logs = []

	provider = get_ai_provider()

	try:
		result = provider.audit_logs(logs)
	except Exception as e:
		report = frappe.new_doc("AI Audit Assessment")
		report.anomaly_score = 0
		report.triggered_alerts_count = 0
		report.generated_summary = f"<p>AI audit failed: {str(e)}</p>"
		report.insert(ignore_permissions=True)
		publish_scan_complete({"name": report.name, "score": 0, "summary": report.generated_summary})
		return

	report = frappe.new_doc("AI Audit Assessment")
	report.anomaly_score = result.anomaly_score
	report.triggered_alerts_count = result.alerts_count
	report.generated_summary = result.report
	report.insert(ignore_permissions=True)

	if result.anomaly_score > 40:
		alert = frappe.new_doc("Alert Instance")
		alert.alert_message = f"AI anomaly scan detected suspicious activity (score: {result.anomaly_score}/100)"
		alert.severity = "critical" if result.anomaly_score > 70 else "warning"
		alert.alert_type = "AI"
		alert.details = json.dumps({"report": report.name, "score": result.anomaly_score})
		alert.insert(ignore_permissions=True)
		publish_alert({
			"name": alert.name,
			"alert_message": alert.alert_message,
			"severity": alert.severity,
			"alert_type": "AI",
		})

	publish_scan_complete({"name": report.name, "score": result.anomaly_score, "summary": result.report})


@frappe.whitelist(allow_guest=True, methods="POST")
def explain_error(logId):
	client = get_client()
	try:
		response = client.search(
			index="api-telemetry-logs-*",
			body={
				"query": {"term": {"id": logId}},
				"size": 1,
			},
			ignore_unavailable=True,
			allow_no_indices=True,
		)
		hits = response.get("hits", {}).get("hits", [])
		if not hits:
			return {"explanation": _("Log not found in OpenSearch.")}
		log = hits[0]["_source"]
	except Exception as e:
		return {"explanation": _("Failed to fetch log: {0}").format(str(e))}

	provider = get_ai_provider()
	try:
		explanation = provider.explain_error(log)
	except Exception as e:
		explanation = _("Failed to get AI explanation: {0}").format(str(e))

	return {"explanation": explanation}
