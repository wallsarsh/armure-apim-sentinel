AUDIT_PROMPT = """You are an AI Security and Systems SRE Bot.
We will give you the latest {log_count} API log summaries in JSON format.
Your task is to:
1. Scan for anomalies: Is there an unusual spike of status codes (e.g., 429, 401, 500)? Are clients from a single IP sending brute-force payloads? Is there a latency regression or database timeout?
2. Quantify an Overall Anomaly Score on a scale from 0 to 100 (where 0 means pristine operations, and 100 means systemic global platform failure).
3. If structural failures are identified, suggest automated alert rule sets that can catch this.
4. Output your analysis in a structured, professional markdown report.

API logs to analyze:
```json
{logs_json}
```

First, return your response in the structure:
ANOMALY_SCORE: <number between 0 and 100>
REPORT:
<Your markdown content starting here. Explain precisely what IPs or Services look anomalous and how to lock down governance. Ensure formatting is visual and clear.>
"""

EXPLAIN_ERROR_PROMPT = """You are a Principal Backend Engineer & API Architect.
Analyze the following raw API Log trace that encountered an issue, status code, or warning. Explain:
1. What the standard status code {status} means for this API.
2. The most probable root cause of this specific failure given the latency of {latency}ms, route "{method} {path}", source "{source}", and client IP "{ip}".
3. Three highly practical, clean, and actionable troubleshooting steps or architectural corrections to resolve this in production.

Raw Log Context:
```json
{log_json}
```

Write the response in structured, beautifully formatted markdown, keeping it clear, helpful, and highly technical. Avoid flowery corporate speak.
"""
