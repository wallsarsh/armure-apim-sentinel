import functools

import frappe


def whitelist(role=None, allow_guest=False, methods=("GET",)):
	def decorator(fn):
		@functools.wraps(fn)
		@frappe.whitelist(allow_guest=allow_guest, methods=methods)
		def wrapper(*args, **kwargs):
			if role and not frappe.has_permission(doctype=None, ptype="read"):
				if role not in frappe.get_roles(frappe.session.user):
					frappe.throw(
						frappe._("Insufficient permissions. {0} role required.").format(role),
						frappe.PermissionError,
					)
			return fn(*args, **kwargs)
		return wrapper
	return decorator


def validate_type(expected_type):
	def decorator(fn):
		@functools.wraps(fn)
		def wrapper(*args, **kwargs):
			for key, value in kwargs.items():
				if not isinstance(value, expected_type):
					try:
						kwargs[key] = expected_type(value)
					except (ValueError, TypeError):
						frappe.throw(
							frappe._("{0} must be of type {1}").format(key, expected_type.__name__),
						)
			return fn(*args, **kwargs)
		return wrapper
	return decorator
