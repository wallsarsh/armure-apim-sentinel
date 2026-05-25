import frappe


def publish_alert(alert_data):
	frappe.publish_realtime(
		event="security_anomaly_triggered",
		message=alert_data,
		after_commit=True,
	)


def publish_scan_complete(report_data):
	frappe.publish_realtime(
		event="security_scan_complete",
		message=report_data,
		after_commit=True,
	)
