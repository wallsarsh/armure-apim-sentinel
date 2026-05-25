from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AuditResult:
	anomaly_score: int
	report: str
	alerts_count: int


class AIProvider(ABC):
	@abstractmethod
	def audit_logs(self, logs: list[dict]) -> AuditResult:
		pass

	@abstractmethod
	def explain_error(self, log: dict) -> str:
		pass
