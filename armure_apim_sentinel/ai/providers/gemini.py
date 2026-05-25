import json
import re

from armure_apim_sentinel.ai.base_provider import AIProvider, AuditResult
from armure_apim_sentinel.ai.prompts import AUDIT_PROMPT, EXPLAIN_ERROR_PROMPT


class GeminiProvider(AIProvider):
	def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
		self.api_key = api_key
		self.model = model

	def _get_client(self):
		from google import genai
		return genai.Client(api_key=self.api_key)

	def _parse_score(self, text: str) -> int:
		matches = re.findall(r"(\d+)(?:\s*\/\s*100)?", text)
		if matches:
			return min(100, max(0, int(matches[0])))
		return 0

	def audit_logs(self, logs: list[dict]) -> AuditResult:
		prompt = AUDIT_PROMPT.format(
			log_count=len(logs),
			logs_json=json.dumps(logs, default=str),
		)
		client = self._get_client()
		response = client.models.generate_content(model=self.model, contents=prompt)
		analysis = response.text

		score = self._parse_score(analysis)

		alerts_count = 0
		if score > 40:
			alerts_count = 1

		return AuditResult(anomaly_score=score, report=analysis, alerts_count=alerts_count)

	def explain_error(self, log: dict) -> str:
		prompt = EXPLAIN_ERROR_PROMPT.format(
			status=log.get("status", "unknown"),
			latency=log.get("latency", "unknown"),
			method=log.get("method", "unknown"),
			path=log.get("path", "unknown"),
			source=log.get("source", "unknown"),
			ip=log.get("ip", "unknown"),
			log_json=json.dumps(log, default=str, indent=2),
		)
		client = self._get_client()
		response = client.models.generate_content(model=self.model, contents=prompt)
		return response.text
