app_name = "erpnext_fiscal_br"
app_title = "ERPNext Fiscal BR"
app_publisher = "Alquimia Industria"
app_description = "Módulo Fiscal Brasileiro para ERPNext - NFe/NFCe"
app_email = "contato@alquimiaindustria.com.br"
app_license = "MIT"
app_version = "0.0.1"

required_apps = ["frappe", "erpnext"]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/erpnext_fiscal_br/css/fiscal_br.css"
app_include_js = "/assets/erpnext_fiscal_br/js/fiscal_br.js"

# include js, css files in header of web template
# web_include_css = "/assets/erpnext_fiscal_br/css/erpnext_fiscal_br.css"
# web_include_js = "/assets/erpnext_fiscal_br/js/erpnext_fiscal_br.js"

# include custom scss in every website theme (without signing in)
# website_theme_scss = "erpnext_fiscal_br/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Sales Invoice": "public/js/sales_invoice.js",
    "Customer": "public/js/customer.js",
    "Item": "public/js/item.js",
    "Company": "public/js/company.js",
}

doctype_list_js = {
    "Sales Invoice": "public/js/sales_invoice_list.js"
}

# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "erpnext_fiscal_br/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "erpnext_fiscal_br.utils.jinja_methods",
#	"filters": "erpnext_fiscal_br.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "erpnext_fiscal_br.install.before_install"
after_install = "erpnext_fiscal_br.install.after_install"
after_migrate = "erpnext_fiscal_br.install.after_migrate"

# Uninstallation
# ------------

# before_uninstall = "erpnext_fiscal_br.uninstall.before_uninstall"
# after_uninstall = "erpnext_fiscal_br.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "erpnext_fiscal_br.utils.before_app_install"
# after_app_install = "erpnext_fiscal_br.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "erpnext_fiscal_br.utils.before_app_uninstall"
# after_app_uninstall = "erpnext_fiscal_br.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "erpnext_fiscal_br.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Sales Invoice": {
        "on_submit": "erpnext_fiscal_br.events.sales_invoice.on_submit",
        "on_cancel": "erpnext_fiscal_br.events.sales_invoice.on_cancel",
    },
    "Company": {
        "validate": "erpnext_fiscal_br.events.company.validate",
    },
    "Customer": {
        "validate": "erpnext_fiscal_br.events.customer.validate",
    },
    "Item": {
        "validate": "erpnext_fiscal_br.events.item.validate",
    },
}

# Scheduled Tasks
# ---------------

scheduler_events = {
    "daily": [
        "erpnext_fiscal_br.tasks.check_certificate_expiry",
    ],
    "hourly": [
        "erpnext_fiscal_br.tasks.retry_pending_notes",
    ],
    "cron": {
        "0 6 * * *": [
            "erpnext_fiscal_br.tasks.daily_fiscal_report",
        ],
    },
}

# Testing
# -------

# before_tests = "erpnext_fiscal_br.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "erpnext_fiscal_br.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "erpnext_fiscal_br.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["erpnext_fiscal_br.utils.before_request"]
# after_request = ["erpnext_fiscal_br.utils.after_request"]

# Job Events
# ----------
# before_job = ["erpnext_fiscal_br.utils.before_job"]
# after_job = ["erpnext_fiscal_br.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
#	{
#		"doctype": "{doctype_1}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_2}",
#		"filter_by": "{filter_by}",
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_3}",
#		"strict": False,
#	},
#	{
#		"doctype": "{doctype_4}"
#	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"erpnext_fiscal_br.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# Fixtures
# --------
fixtures = [
    {
        "doctype": "Custom Field",
        "filters": [["module", "=", "Fiscal BR"]]
    },
    {
        "doctype": "Property Setter",
        "filters": [["module", "=", "Fiscal BR"]]
    },
    {
        "doctype": "Role",
        "filters": [["name", "in", ["Fiscal Manager", "Fiscal User"]]]
    },
]

# Default print formats
# ---------------------
# default_print_format = "Standard"

# Website Route Rules
# -------------------
# website_route_rules = [
# 	{"from_route": "/fiscal/<path:app_path>", "to_route": "fiscal"},
# ]

# Desk Workspace
# --------------
# workspace_config = {
#     "Fiscal BR": {
#         "label": "Fiscal BR",
#         "icon": "file-text",
#         "color": "#3498db"
#     }
# }
