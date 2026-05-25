import frappe

VALID_DOCTYPES = [
	"Log Ingest Adapter",
	"Security Alert Rule",
	"Alert Instance",
	"AI Audit Assessment",
]


def get_permission_query_conditions(user=None):
	if not user:
		user = frappe.session.user

	if "System Manager" in frappe.get_roles(user):
		return ""

	return f"""(`tab{user}`.`owner` = {frappe.db.escape(user)})"""


def has_permission(doctype, ptype="read", user=None):
	if not user:
		user = frappe.session.user

	if doctype not in VALID_DOCTYPES:
		return False

	if "System Manager" in frappe.get_roles(user):
		return True

	return False


def has_app_permission():
	return "System Manager" in frappe.get_roles(frappe.session.user)
