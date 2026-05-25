import frappe


def before_uninstall():
	doctypes = [
		"Log Ingest Adapter",
		"Security Alert Rule",
		"Alert Instance",
		"AI Audit Assessment",
		"API Security App Settings",
	]
	for dt in doctypes:
		frappe.db.delete(dt, {"*": "*"})
