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

	return ""


def has_permission(doctype=None, ptype="read", user=None, doc=None, **kwargs):
	if not user:
		user = frappe.session.user

	dt = doctype
	if not dt and doc:
		dt = doc.doctype
	if not dt:
		return False

	if dt not in VALID_DOCTYPES:
		return False

	if "System Manager" in frappe.get_roles(user):
		return True

	return False


def has_app_permission():
	return "System Manager" in frappe.get_roles(frappe.session.user)
