import json
from datetime import datetime, timedelta

import frappe
from armure_apim_sentinel.notification import get_adapter


def send_queued_notification(queue_item_name: str):
	queue_item = frappe.get_doc("Notification Queue Item", queue_item_name)
	if not queue_item:
		return

	queue_item.db_set("status", "sending")
	frappe.db.commit()

	channel_name = queue_item.channel
	channel_doc = frappe.get_value(
		"Notification Channel",
		channel_name,
		["channel_type", "config_json", "rate_limit_per_minute", "name"],
		as_dict=True,
	)
	if not channel_doc:
		queue_item.db_set("status", "failed")
		queue_item.db_set("last_error", "Channel not found")
		return

	rate_limit = int(channel_doc.rate_limit_per_minute or 60)
	if not _enforce_rate_limit(channel_name, rate_limit):
		queue_item.db_set("status", "retrying")
		queue_item.db_set("last_error", "Rate limit exceeded, will retry")
		queue_item.db_set("next_retry_at", datetime.utcnow() + timedelta(minutes=1))
		return

	channel_config = {}
	try:
		channel_config = json.loads(channel_doc.config_json or "{}")
	except (json.JSONDecodeError, TypeError):
		pass

	payload = {}
	try:
		payload = json.loads(queue_item.payload or "{}")
	except (json.JSONDecodeError, TypeError):
		payload = {"message": queue_item.title}

	try:
		adapter = get_adapter(channel_doc.channel_type)
		result = adapter.send(payload, channel_config)
	except Exception as e:
		result = {"success": False, "error": str(e)}

	_handle_result(queue_item, channel_doc, result)


def _handle_result(queue_item, channel_doc, result):
	now = datetime.utcnow()
	if result.get("success"):
		queue_item.db_set("status", "sent")
		queue_item.db_set("sent_at", now)
		queue_item.db_set("last_error", None)

		log = frappe.new_doc("Notification Log")
		log.title = queue_item.title
		log.channel = channel_doc.name
		log.channel_type = channel_doc.channel_type
		log.severity = queue_item.severity
		log.rule = queue_item.rule
		log.alert_instance = queue_item.alert_instance
		log.queue_item = queue_item.name
		log.status = "sent"
		log.response = json.dumps(result.get("response", ""), default=str)
		log.attempts = queue_item.retry_count + 1
		log.sent_at = now
		log.insert(ignore_permissions=True)
	else:
		retry_count = (queue_item.retry_count or 0) + 1
		error_msg = str(result.get("error", "Unknown error"))

		if retry_count >= 3:
			queue_item.db_set("status", "failed")
			queue_item.db_set("last_error", error_msg)

			log = frappe.new_doc("Notification Log")
			log.title = queue_item.title
			log.channel = channel_doc.name
			log.channel_type = channel_doc.channel_type
			log.severity = queue_item.severity
			log.rule = queue_item.rule
			log.alert_instance = queue_item.alert_instance
			log.queue_item = queue_item.name
			log.status = "failed"
			log.error_message = error_msg
			log.attempts = retry_count
			log.insert(ignore_permissions=True)
		else:
			queue_item.db_set("status", "retrying")
			queue_item.db_set("retry_count", retry_count)
			queue_item.db_set("last_error", error_msg)
			queue_item.db_set("next_retry_at", now + timedelta(minutes=retry_count * 2))

			log = frappe.new_doc("Notification Log")
			log.title = queue_item.title
			log.channel = channel_doc.name
			log.channel_type = channel_doc.channel_type
			log.severity = queue_item.severity
			log.rule = queue_item.rule
			log.alert_instance = queue_item.alert_instance
			log.queue_item = queue_item.name
			log.status = "retried"
			log.error_message = error_msg
			log.attempts = retry_count
			log.insert(ignore_permissions=True)


def retry_failed_notifications():
	items = frappe.get_all(
		"Notification Queue Item",
		filters={
			"status": "retrying",
			"retry_count": ["<", 3],
			"next_retry_at": ["<=", datetime.utcnow()],
		},
		limit_page_length=50,
	)

	for item in items:
		frappe.enqueue(
			"armure_apim_sentinel.notification.queue.send_queued_notification",
			queue_item_name=item.name,
			queue="long",
			timeout=300,
		)


def _enforce_rate_limit(channel: str, max_per_minute: int) -> bool:
	import time

	now = time.time()
	key = f"rate_limit:{channel}"
	redis = frappe.cache().redis

	pipe = redis.pipeline()
	pipe.zremrangebyscore(key, 0, now - 60)
	pipe.zcard(key)
	pipe.zadd(key, {str(now): now})
	pipe.expire(key, 60)
	results = pipe.execute()

	count = results[1]
	return count <= max_per_minute
