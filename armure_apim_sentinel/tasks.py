import json
import random
import secrets
from datetime import datetime

import frappe

from armure_apim_sentinel.opensearch_client import get_client, ensure_index, index_log
from armure_apim_sentinel.utils import evaluate_rules_for_log
from armure_apim_sentinel.realtime import publish_alert
from armure_apim_sentinel.notification import dispatch_notification


API_PATHS = [
	{"path": "/api/v1/users/login", "method": "POST", "source": "Auth Service"},
	{"path": "/api/v1/users/profile", "method": "GET", "source": "Auth Service"},
	{"path": "/api/v1/billing/checkout", "method": "POST", "source": "Billing Gateway"},
	{"path": "/api/v1/billing/invoices", "method": "GET", "source": "Billing Gateway"},
	{"path": "/api/v1/products/list", "method": "GET", "source": "Catalog Engine"},
	{"path": "/api/v1/products/detail", "method": "GET", "source": "Catalog Engine"},
	{"path": "/api/v1/analytics/stream", "method": "POST", "source": "Data Collector"},
	{"path": "/api/v1/webhooks/stripe", "method": "POST", "source": "Billing Gateway"},
]

IPS = [
	"192.168.1.50", "203.0.113.88", "198.51.100.12", "185.228.168.10",
	"34.120.45.99", "8.8.8.8", "172.56.21.90", "192.168.1.112", "45.12.33.20",
]

USER_AGENTS = [
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
	"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15",
	"PostmanRuntime/7.35.0",
	"curl/8.4.0",
	"Mozilla/5.0 (Linux; Android 10; K) Chrome/120.0.0.0 Mobile Safari/537.36",
	"Go-http-client/1.1",
]


def _random_uuid():
	return "log_" + secrets.token_hex(8)


def _generate_single_log():
	template = random.choice(API_PATHS)

	latency = random.randint(10, 90)
	status = 200

	roll = random.random()
	if roll < 0.05:
		status = random.choice([500, 429])
		latency = random.randint(400, 2200) if status == 500 else random.randint(5, 30)
	elif roll < 0.10:
		status = 401
	elif roll < 0.12:
		status = 404

	source_doc = frappe.db.get_value("Log Ingest Adapter", {"channel_name": template["source"], "status": "Active"}, "channel_name")
	if not source_doc:
		return None

	rate_limit_remaining = 0 if status == 429 else random.randint(5, 100)

	log = {
		"id": _random_uuid(),
		"timestamp": datetime.utcnow().isoformat(),
		"method": template["method"],
		"path": template["path"],
		"status": status,
		"latency": latency,
		"source": template["source"],
		"ip": random.choice(IPS),
		"userAgent": random.choice(USER_AGENTS),
		"payloadSize": random.randint(100, 2100) if template["method"] == "POST" else random.randint(20, 320),
		"rateLimitRemaining": rate_limit_remaining,
		"rateLimitLimit": 100,
	}

	frappe.db.set_value("Log Ingest Adapter", source_doc, "total_logs_received", frappe.db.get_value("Log Ingest Adapter", source_doc, "total_logs_received") + 1)

	return log


def generate_simulated_logs():
	settings = frappe.get_single("API Security App Settings")
	if not settings.enable_live_simulation:
		return

	client = get_client()
	ensure_index(client)

	for _ in range(random.randint(1, 3)):
		log = _generate_single_log()
		if not log:
			continue

		index_log(client, log)
		alerts = evaluate_rules_for_log(log)
		for alert_data in alerts:
			doc = frappe.new_doc("Alert Instance")
			doc.update(alert_data)
			doc.insert(ignore_permissions=True)
			publish_alert(alert_data)
			dispatch_notification(doc, alert_data.get("rule"))
