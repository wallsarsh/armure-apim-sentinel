import frappe

from armure_apim_sentinel.utils import invalidate_rules_cache


def invalidate_rules_cache(controller, method):
	"""Called via doc_events on Security Alert Rule on_update."""
	invalidate_rules_cache()
