import frappe

from armure_apim_sentinel.ai.base_provider import AIProvider
from armure_apim_sentinel.ai.providers.gemini import GeminiProvider
from armure_apim_sentinel.ai.providers.openai_compatible import OpenAICompatibleProvider


def get_ai_provider() -> AIProvider:
	settings = frappe.get_single("API Security App Settings")
	provider_type = settings.ai_provider or "Gemini"

	if provider_type == "OpenAI Compatible":
		return OpenAICompatibleProvider(
			api_base=settings.ai_api_base or "http://ollama:11434/v1",
			api_key=settings.get_password("ai_api_key") or "",
			model=settings.ai_model or "llama3.2",
		)

	return GeminiProvider(
		api_key=frappe.conf.get("gemini_api_key") or "",
		model=settings.ai_model or "gemini-2.0-flash",
	)
