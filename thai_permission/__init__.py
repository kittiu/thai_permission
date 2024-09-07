__version__ = "0.0.1"

from frappe.model.db_query import DatabaseQuery
from thai_permission.custom.db_query import get_permission_query_conditions
DatabaseQuery.get_permission_query_conditions = get_permission_query_conditions
