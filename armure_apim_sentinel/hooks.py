app_name = "armure_apim_sentinel"
app_title = "Armure APIM Sentinel"
app_publisher = "Armure Suite"
app_description = "Real-time API threat auditing with OpenSearch & WebSockets"
app_email = "development@armure.in"
app_license = "mit"

required_apps = []

add_to_apps_screen = [
	{
		"name": "armure_apim_sentinel",
		"logo": "/assets/armure_apim_sentinel/logo.png",
		"title": "Armure APIM Sentinel",
		"route": "/api-security-monitor",
		"has_permission": "armure_apim_sentinel.permissions.has_app_permission"
	}
]

website_route_rules = [
	{"from_route": "/api-security-monitor", "to_route": "api_security_monitor"},
	{"from_route": "/api-security-monitor/<path:app_path>", "to_route": "api_security_monitor"},
]

doctype_js = {
	"Security Alert Rule": "public/js/security_alert_rule.js"
}

scheduler_events = {
	"cron": {
		"*/1 * * * *": [
			"armure_apim_sentinel.tasks.generate_simulated_logs"
		]
	}
}

doc_events = {
	"Security Alert Rule": {
		"on_update": "armure_apim_sentinel.doc_events.invalidate_rules_cache",
	}
}

permission_query_conditions = {
	"Log Ingest Adapter": "armure_apim_sentinel.permissions.get_permission_query_conditions",
	"Security Alert Rule": "armure_apim_sentinel.permissions.get_permission_query_conditions",
	"Alert Instance": "armure_apim_sentinel.permissions.get_permission_query_conditions",
	"AI Audit Assessment": "armure_apim_sentinel.permissions.get_permission_query_conditions",
}

has_permission = {
	"Log Ingest Adapter": "armure_apim_sentinel.permissions.has_permission",
	"Security Alert Rule": "armure_apim_sentinel.permissions.has_permission",
	"Alert Instance": "armure_apim_sentinel.permissions.has_permission",
	"AI Audit Assessment": "armure_apim_sentinel.permissions.has_permission",
}

after_migrate = ["armure_apim_sentinel.install.after_migrate"]
