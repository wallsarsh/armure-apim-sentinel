import csv
import json
from io import StringIO

import frappe
from frappe import _

from armure_apim_sentinel.opensearch_client import search_logs


@frappe.whitelist(allow_guest=True, methods="GET")
def export_logs(format="json", search=None, source=None, status=None, method=None, start=None, end=None):
	result = search_logs(
		search=search,
		source=source,
		status=status,
		method=method,
		start=start,
		end=end,
		page=1,
		page_size=5000,
	)
	logs = result.get("logs", [])

	if format == "csv":
		output = StringIO()
		writer = csv.writer(output)
		if logs:
			writer.writerow(logs[0].keys())
			for log in logs:
				writer.writerow(log.values())
		frappe.response["content_type"] = "text/csv"
		frappe.response["filename"] = "api-logs-export.csv"
		return output.getvalue()

	return logs
