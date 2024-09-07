import frappe
from frappe.core.doctype.server_script.server_script_utils import get_server_script_map


def get_permission_query_conditions(self) -> str:
    conditions = []
    hooks = frappe.get_hooks("permission_query_conditions", {})
    condition_methods = hooks.get(self.doctype, []) + hooks.get("*", [])
    for method in condition_methods:
        if c := frappe.call(frappe.get_attr(method), self.user, doctype=self.doctype):
            conditions.append(c)

    if permission_script_name := get_server_script_map().get("permission_query", {}).get(self.doctype):
        script = frappe.get_doc("Server Script", permission_script_name)
        if condition := script.get_permission_query_conditions(self.user):
            conditions.append(condition)
    
    # Patch - DocType Permission
    if doctype_permission_names := get_doctype_permission_map().get(self.doctype):
        for name in doctype_permission_names:
            dt_perm = frappe.get_doc("DocType Permission", name)
            if not to_apply_doctype_permission(dt_perm, self.user):
                continue          
            if condition := dt_perm.get_doctype_permission_conditions(self.user):
                conditions.append(condition)
    # --
    return " and ".join(conditions) if conditions else ""


def to_apply_doctype_permission(dt_perm, user):
    if dt_perm.apply_mode == "Restrict All":
        return True
    user_roles = frappe.get_roles(user)
    perm_roles = [r.role for r in dt_perm.roles]
    has_role = set(user_roles).intersection(set(perm_roles))
    if dt_perm.apply_mode == "Restrict Roles" and has_role:
        return True
    if dt_perm.apply_mode == "Restrict All Except Roles" and not has_role:
        return True
    perm_users = [u.user for u in dt_perm.users]
    has_user = user in perm_users
    if dt_perm.apply_mode == "Restrict Users" and has_user:
        return True
    if dt_perm.apply_mode == "Restrict All Except Users" and not has_user:
        return True
    return False


def get_doctype_permission_map():
	# fetch doctype_permission_map
	# {
	# 	'DocType': ['[doctype_permission]', '[doctype_permission 2]']
	# }
    if frappe.flags.in_patch and not frappe.db.table_exists("DocType Permission"):
         return {}
    
    permission_map = frappe.cache.get_value("doctype_permission_map")

    if permission_map is None:
        permission_map = {}
        permissions = frappe.get_all(
			"DocType Permission",
			fields=("name", "restrict_doctype"),
			or_filters=[
                ["testing", "=", 1],
                ["docstatus", "=", 1],
            ],
		)
        for script in permissions:
            if not permission_map.get(script.restrict_doctype):
                permission_map[script.restrict_doctype] = []
            permission_map[script.restrict_doctype] += [script.name]
        frappe.cache.set_value("doctype_permission_map", permission_map)

    return permission_map
