import frappe

from armure_apim_sentinel.utils import invalidate_rules_cache as _invalidate_rules_cache


def clear_rules_cache(controller, method):
	_invalidate_rules_cache()
