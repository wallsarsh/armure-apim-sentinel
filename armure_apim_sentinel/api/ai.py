import json

import frappe
from frappe import _

from armure_apim_sentinel.realtime import publish_scan_complete


def run_ai_audit(logs_json):
	try:
		logs = frappe.parse_json(logs_json)
	except Exception:
		logs = []

	gemini_api_key = frappe.conf.get("gemini_api_key")
	if not gemini_api_key:
		report = frappe.new_doc("AI Audit Assessment")
		report.anomaly_score = 0
		report.triggered_alerts_count = 0
		report.generated_summary = "<p><em>Gemini AI audit unavailable: GEMINI_API_KEY not configured.</em></p>"
		report.insert(ignore_permissions=True)
		publish_scan_complete({"name": report.name, "score": 0, "summary": report.generated_summary})
		return

	try:
		from google import genai
		client = genai.Client(api_key=gemini_api_key)
		prompt = f"""You are an API security auditor. Analyze these {len(logs)} API log entries and provide:
1. An anomaly score (0-100)
2. Number of suspicious events detected
3. A brief markdown summary of findings

Logs: {json.dumps(logs, default=str)}
"""
		response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
		analysis = response.text
	except Exception as e:
		report = frappe.new_doc("AI Audit Assessment")
		report.anomaly_score = 0
		report.triggered_alerts_count = 0
		report.generated_summary = f"<p>AI audit failed: {str(e)}</p>"
		report.insert(ignore_permissions=True)
		publish_scan_complete({"name": report.name, "score": 0, "summary": report.generated_summary})
		return

	score = 0
	alerts_count = 0
	if "score" in analysis.lower():
		import re
		matches = re.findall(r"(\d+)(?:\s*\/\s*100)?", analysis)
		if matches:
			score = min(100, max(0, int(matches[0])))

	report = frappe.new_doc("AI Audit Assessment")
	report.anomaly_score = score
	report.triggered_alerts_count = alerts_count
	report.generated_summary = analysis
	report.insert(ignore_permissions=True)

	if score > 40:
		alert = frappe.new_doc("Alert Instance")
		alert.alert_message = f"AI anomaly scan detected suspicious activity (score: {score}/100)"
		alert.severity = "critical" if score > 70 else "warning"
		alert.alert_type = "AI"
		alert.details = json.dumps({"report": report.name, "score": score})
		alert.insert(ignore_permissions=True)
		publish_alert({
			"name": alert.name,
			"alert_message": alert.alert_message,
			"severity": alert.severity,
			"alert_type": "AI",
		})

	publish_scan_complete({"name": report.name, "score": score, "summary": analysis})
