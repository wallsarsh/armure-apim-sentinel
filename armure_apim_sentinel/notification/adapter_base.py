from abc import ABC, abstractmethod


class NotificationAdapter(ABC):
	@abstractmethod
	def send(self, payload: dict, config: dict) -> dict:
		pass

	@classmethod
	@abstractmethod
	def validate_config(cls, config: dict) -> list[str]:
		pass
