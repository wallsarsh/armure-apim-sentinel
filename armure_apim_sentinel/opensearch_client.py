import uuid
import json
from datetime import datetime, timedelta, timezone

import frappe
from opensearchpy import OpenSearch


def get_settings():
	return frappe.get_single("API Security App Settings")


def get_client():
	settings = get_settings()
	client = OpenSearch(
		hosts=[{"host": settings.opensearch_host, "port": settings.opensearch_port}],
		http_auth=(settings.opensearch_user, settings.opensearch_password or ""),
		use_ssl=False,
		verify_certs=False,
	)
	return client


INDEX_PREFIX = "api-telemetry-logs"
INDEX_TEMPLATE = f"{INDEX_PREFIX}-{{date}}"

INDEX_MAPPING = {
	"settings": {
		"number_of_shards": 1,
		"number_of_replicas": 0,
		"refresh_interval": "5s",
	},
	"mappings": {
		"properties": {
			"id": {"type": "keyword"},
			"timestamp": {"type": "date"},
			"method": {"type": "keyword"},
			"path": {"type": "keyword"},
			"status": {"type": "integer"},
			"latency": {"type": "integer"},
			"source": {"type": "keyword"},
			"ip": {"type": "ip"},
			"user_agent": {"type": "text"},
			"payload_size": {"type": "integer"},
			"user_id": {"type": "keyword"},
			"rate_limit_remaining": {"type": "integer"},
			"rate_limit_limit": {"type": "integer"},
			"response_body": {"type": "text"},
		}
	},
}


def _daily_index(date=None):
	date = date or datetime.utcnow()
	return INDEX_TEMPLATE.format(date=date.strftime("%Y.%m.%d"))


def ensure_index(client=None, index=None):
	client = client or get_client()
	index = index or _daily_index()
	if not client.indices.exists(index=index):
		client.indices.create(index=index, body=INDEX_MAPPING)
	return index


def _ensure_timestamp(val):
	if val:
		return val
	return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + datetime.now(timezone.utc).strftime("%f")[:3] + "Z"

def index_log(client, log_data, index=None):
	index = index or ensure_index(client)
	now = datetime.now(timezone.utc)
	log_id = log_data.get("id") or str(uuid.uuid4())
	doc = {
		"id": log_id,
		"timestamp": _ensure_timestamp(log_data.get("timestamp")),
		"method": log_data.get("method"),
		"path": log_data.get("path"),
		"status": log_data.get("status"),
		"latency": log_data.get("latency"),
		"source": log_data.get("source"),
		"ip": log_data.get("ip"),
		"user_agent": log_data.get("userAgent"),
		"payload_size": log_data.get("payloadSize"),
		"user_id": log_data.get("userId"),
		"rate_limit_remaining": log_data.get("rateLimitRemaining"),
		"rate_limit_limit": log_data.get("rateLimitLimit"),
		"response_body": json.dumps(log_data.get("responseBody", "")),
	}
	client.index(index=index, id=log_id, body=doc)


def bulk_index(client, logs, index=None):
	index = index or ensure_index(client)
	bulk_body = []
	for log in logs:
		log_id = log.get("id") or str(uuid.uuid4())
		bulk_body.append({"index": {"_index": index, "_id": log_id}})
		bulk_body.append({
			"id": log_id,
			"timestamp": _ensure_timestamp(log.get("timestamp")),
			"method": log.get("method"),
			"path": log.get("path"),
			"status": log.get("status"),
			"latency": log.get("latency"),
			"source": log.get("source"),
			"ip": log.get("ip"),
			"user_agent": log.get("userAgent"),
			"payload_size": log.get("payloadSize"),
			"user_id": log.get("userId"),
			"rate_limit_remaining": log.get("rateLimitRemaining"),
			"rate_limit_limit": log.get("rateLimitLimit"),
			"response_body": json.dumps(log.get("responseBody", "")),
		})
	if bulk_body:
		client.bulk(body=bulk_body)


def search_logs(
	search=None,
	source=None,
	status=None,
	method=None,
	min_latency=None,
	max_latency=None,
	start=None,
	end=None,
	page=1,
	page_size=50,
):
	client = get_client()
	must = []

	if search:
		must.append({"query_string": {"query": search, "fields": ["path", "ip", "user_agent", "response_body"]}})
	if source:
		must.append({"term": {"source": source}})
	if status:
		must.append({"term": {"status": int(status)}})
	if method:
		must.append({"term": {"method": method.upper()}})
	if min_latency:
		must.append({"range": {"latency": {"gte": int(min_latency)}}})
	if max_latency:
		must.append({"range": {"latency": {"lte": int(max_latency)}}})

	time_range = {}
	if start:
		time_range["gte"] = start
	if end:
		time_range["lte"] = end
	if time_range:
		must.append({"range": {"timestamp": time_range}})

	query = {"query": {"bool": {"must": must}}} if must else {"query": {"match_all": {}}}

	from_size = (int(page) - 1) * int(page_size)
	query["size"] = int(page_size)
	query["from"] = from_size
	query["sort"] = [{"timestamp": {"order": "desc"}}]

	indices = ",".join([_daily_index(datetime.utcnow() - timedelta(days=i)) for i in range(7)])
	try:
		response = client.search(index=indices, body=query, ignore_unavailable=True, allow_no_indices=True)
	except Exception:
		return {"total": 0, "logs": [], "page": int(page), "page_size": int(page_size)}

	hits = response.get("hits", {})
	total = hits.get("total", {}).get("value", 0)
	logs = []
	for hit in hits.get("hits", []):
		src = hit["_source"]
		logs.append(src)

	return {"total": total, "logs": logs, "page": int(page), "page_size": int(page_size)}


def aggregate_dashboard(period=24):
	client = get_client()
	now = datetime.utcnow()
	start_time = (now - timedelta(hours=int(period))).isoformat()

	indices = ",".join([_daily_index(now - timedelta(days=i)) for i in range(max(1, int(period) // 24 + 1))])

	STATUS_DESCRIPTIONS = {
		"200": "OK", "201": "Created", "204": "No Content", "301": "Moved",
		"304": "Not Modified", "400": "Bad Request", "401": "Unauthorized",
		"403": "Forbidden", "404": "Not Found", "405": "Method Not Allowed",
		"408": "Timeout", "409": "Conflict", "422": "Unprocessable",
		"429": "Rate Limited", "500": "Server Error", "502": "Bad Gateway",
		"503": "Service Unavailable",
	}

	query = {
		"size": 0,
		"query": {"range": {"timestamp": {"gte": start_time}}},
		"aggs": {
			"total_requests": {"value_count": {"field": "id"}},
			"avg_latency": {"avg": {"field": "latency"}},
			"error_count": {"filter": {"range": {"status": {"gte": 400}}}},
			"rate_limit_count": {"filter": {"term": {"status": 429}}},
			"status_breakdown": {"terms": {"field": "status", "size": 20}},
			"source_breakdown": {"terms": {"field": "source", "size": 20}},
			"path_breakdown": {
				"terms": {"field": "path", "size": 20},
				"aggs": {
					"avg_latency": {"avg": {"field": "latency"}},
					"error_count": {"filter": {"range": {"status": {"gte": 400}}}},
					"top_method": {"top_hits": {"size": 1, "_source": {"includes": ["method"]}}},
				},
			},
			"timeline": {
				"date_histogram": {
					"field": "timestamp",
					"fixed_interval": "1h",
					"min_doc_count": 0,
					"extended_bounds": {"min": start_time, "max": now.isoformat()},
				},
				"aggs": {
					"avg_latency": {"avg": {"field": "latency"}},
					"error_count": {"filter": {"range": {"status": {"gte": 400}}}},
				},
			},
		},
	}

	try:
		response = client.search(index=indices, body=query, ignore_unavailable=True, allow_no_indices=True)
	except Exception:
		return _empty_dashboard()

	aggs = response.get("aggregations", {})
	summary = {
		"totalRequests": aggs.get("total_requests", {}).get("value", 0),
		"avgLatency": round(aggs.get("avg_latency", {}).get("value", 0), 1),
		"successRate": _calc_success_rate(aggs),
		"errorCount": aggs.get("error_count", {}).get("doc_count", 0),
		"rateLimitCount": aggs.get("rate_limit_count", {}).get("doc_count", 0),
		"activeAlerts": frappe.db.count("Alert Instance", filters={"resolved": 0}),
	}

	charts = {
		"timeline": [
			{
				"timestamp": bucket.get("key_as_string"),
				"count": bucket.get("doc_count"),
				"success": bucket.get("doc_count") - bucket.get("error_count", {}).get("doc_count", 0),
				"errors": bucket.get("error_count", {}).get("doc_count", 0),
				"avgLatency": round(bucket.get("avg_latency", {}).get("value") or 0, 1),
				"timeLabel": _format_timeline_label(bucket.get("key_as_string")),
			}
			for bucket in aggs.get("timeline", {}).get("buckets", [])
		]
	}

	statuses = [
		{
			"code": int(b["key"]),
			"count": b["doc_count"],
			"description": STATUS_DESCRIPTIONS.get(str(b["key"]), "Unknown"),
		}
		for b in aggs.get("status_breakdown", {}).get("buckets", [])
	]

	endpoints = []
	for b in aggs.get("path_breakdown", {}).get("buckets", []):
		path = b["key"]
		hits = b["doc_count"]
		avg_latency = (b.get("avg_latency", {}).get("value") or 0)
		errors = b.get("error_count", {}).get("doc_count", 0)
		error_rate = round((errors / hits * 100) if hits else 0, 1)
		method = "GET"
		try:
			th = b.get("top_method", {}).get("hits", {}).get("hits", [])
			if th:
				method = th[0].get("_source", {}).get("method", "GET")
		except Exception:
			pass
		endpoints.append({
			"method": method,
			"path": path,
			"hits": hits,
			"avgLatency": round(avg_latency, 1),
			"errorRate": error_rate,
		})

	breakdown = {
		"bySource": {b["key"]: b["doc_count"] for b in aggs.get("source_breakdown", {}).get("buckets", [])},
		"statuses": statuses,
		"endpoints": endpoints,
		"byStatus": {str(b["key"]): b["doc_count"] for b in aggs.get("status_breakdown", {}).get("buckets", [])},
		"byPath": {b["key"]: b["doc_count"] for b in aggs.get("path_breakdown", {}).get("buckets", [])},
	}

	return {"summary": summary, "charts": charts, "breakdown": breakdown}


def _format_timeline_label(ts_str):
	if not ts_str:
		return ""
	try:
		dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
		return dt.strftime("%H:%M")
	except Exception:
		return ts_str


def _calc_success_rate(aggs):
	total = aggs.get("total_requests", {}).get("value", 0)
	errors = aggs.get("error_count", {}).get("doc_count", 0)
	if total == 0:
		return 100.0
	return round((1 - errors / total) * 100, 1)


def _empty_dashboard():
	return {
		"summary": {"totalRequests": 0, "avgLatency": 0, "successRate": 100, "errorCount": 0, "rateLimitCount": 0, "activeAlerts": 0},
		"charts": {"timeline": []},
		"breakdown": {"bySource": {}, "byStatus": {}, "byPath": {}, "statuses": [], "endpoints": []},
	}
