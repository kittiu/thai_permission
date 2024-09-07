# Copyright (c) 2024, Kitti U. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.safe_exec import safe_exec


class DocTypePermission(Document):

	def validate(self):
		if self.docstatus in (1, 2):
			self.testing = 0

	def clear_cache(self):
		frappe.cache.delete_value("doctype_permission_map")
		return super().clear_cache()

	def on_trash(self):
		frappe.cache.delete_value("doctype_permission_map")

	def get_doctype_permission_conditions(self, user: str) -> list[str]:
		locals = {"user": user, "conditions": ""}
		safe_exec(self.script, None, locals, script_filename=self.name)
		if locals["conditions"]:
			return locals["conditions"]