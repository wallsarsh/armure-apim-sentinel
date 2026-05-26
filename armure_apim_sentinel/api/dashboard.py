import frappe
from frappe import _

from armure_apim_sentinel.decorators import whitelist
from armure_apim_sentinel.opensearch_client import aggregate_dashboard


@frappe.whitelist(allow_guest=True, methods="GET")
def get_summary(period=24, from_=None, to=None):
	return aggregate_dashboard(period=period, from_timestamp=from_, to_timestamp=to).get("summary", {})


@frappe.whitelist(allow_guest=True, methods="GET")
def get_charts(period=24, from_=None, to=None):
	return aggregate_dashboard(period=period, from_timestamp=from_, to_timestamp=to).get("charts", {})


@frappe.whitelist(allow_guest=True, methods="GET")
def get_breakdown(period=24, from_=None, to=None):
	return aggregate_dashboard(period=period, from_timestamp=from_, to_timestamp=to).get("breakdown", {})
