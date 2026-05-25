import frappe
from frappe import _

from armure_apim_sentinel.decorators import whitelist
from armure_apim_sentinel.opensearch_client import aggregate_dashboard


@frappe.whitelist(allow_guest=True, methods="GET")
def get_summary(period=24):
	return aggregate_dashboard(period=period).get("summary", {})


@frappe.whitelist(allow_guest=True, methods="GET")
def get_charts(period=24):
	return aggregate_dashboard(period=period).get("charts", {})


@frappe.whitelist(allow_guest=True, methods="GET")
def get_breakdown(period=24):
	return aggregate_dashboard(period=period).get("breakdown", {})
