import json
import re

from openai import OpenAI

from armure_apim_sentinel.ai.base_provider import AIProvider, AuditResult
from armure_apim_sentinel.ai.prompts import AUDIT_PROMPT, EXPLAIN_ERROR_PROMPT


class OpenAICompatibleProvider(AIProvider):
	def __init__(self, api_base: str, api_key: str, model: str):
		self.client = OpenAI(base_url=api_base, api_key=api_key)
		self.model = model

	def _parse_score(self, text: str) -> int:
		matches = re.findall(r"(\d+)(?:\s*\/\s*100)?", text)
		if matches:
			return min(100, max(0, int(matches[0])))
		return 0

	def _chat(self, prompt: str) -> str:
		response = self.client.chat.completions.create(
			model=self.model,
			messages=[{"role": "user", "content": prompt}],
		)
		return response.choices[0].message.content or ""

	def audit_logs(self, logs: list[dict]) -> AuditResult:
		prompt = AUDIT_PROMPT.format(
			log_count=len(logs),
			logs_json=json.dumps(logs, default=str),
		)
		analysis = self._chat(prompt)

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
		return self._chat(prompt)
