"""
API para configuração e correção do módulo fiscal
"""

import frappe
from frappe import _


@frappe.whitelist()
def rebuild_workspace():
    """
    Reconstrói o workspace Fiscal BR
    Execute via console: frappe.call('erpnext_fiscal_br.api.setup.rebuild_workspace')
    """
    try:
        # Remove workspace existente
        if frappe.db.exists("Workspace", "Fiscal BR"):
            frappe.delete_doc("Workspace", "Fiscal BR", force=True)
            frappe.db.commit()
        
        # Cria novo workspace
        workspace = frappe.new_doc("Workspace")
        workspace.name = "Fiscal BR"
        workspace.label = "Fiscal BR"
        workspace.title = "Fiscal BR"
        workspace.icon = "file-text"
        workspace.module = "Fiscal BR"
        workspace.category = "Modules"
        workspace.public = 1
        workspace.is_standard = 0
        
        # Links
        workspace.append("links", {
            "type": "Link",
            "link_type": "DocType",
            "link_to": "Nota Fiscal",
            "label": "Notas Fiscais",
            "onboard": 1
        })
        workspace.append("links", {
            "type": "Link",
            "link_type": "DocType",
            "link_to": "Configuracao Fiscal",
            "label": "Configuração Fiscal",
            "onboard": 1
        })
        workspace.append("links", {
            "type": "Link",
            "link_type": "DocType",
            "link_to": "Certificado Digital",
            "label": "Certificados Digitais",
            "onboard": 1
        })
        workspace.append("links", {
            "type": "Link",
            "link_type": "DocType",
            "link_to": "Evento Fiscal",
            "label": "Eventos Fiscais"
        })
        
        # Shortcuts
        workspace.append("shortcuts", {
            "type": "DocType",
            "link_to": "Nota Fiscal",
            "label": "Nota Fiscal",
            "doc_view": "List",
            "color": "Blue"
        })
        workspace.append("shortcuts", {
            "type": "DocType",
            "link_to": "Configuracao Fiscal",
            "label": "Configuração Fiscal",
            "doc_view": "List",
            "color": "Green"
        })
        workspace.append("shortcuts", {
            "type": "DocType",
            "link_to": "Certificado Digital",
            "label": "Certificado Digital",
            "doc_view": "List",
            "color": "Orange"
        })
        
        workspace.flags.ignore_links = True
        workspace.insert(ignore_permissions=True, ignore_links=True)
        frappe.db.commit()
        
        return {"success": True, "message": "Workspace recriado com sucesso!"}
    except Exception as e:
        frappe.log_error(f"Erro ao recriar workspace: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def check_module_status():
    """
    Verifica o status do módulo fiscal
    """
    status = {
        "doctypes": {},
        "workspace": False,
        "roles": {},
        "custom_fields": 0
    }
    
    # Verifica DocTypes
    doctypes = ["Nota Fiscal", "Configuracao Fiscal", "Certificado Digital", "Evento Fiscal"]
    for dt in doctypes:
        status["doctypes"][dt] = frappe.db.exists("DocType", dt) is not None
    
    # Verifica Workspace
    status["workspace"] = frappe.db.exists("Workspace", "Fiscal BR") is not None
    
    # Verifica Roles
    roles = ["Fiscal Manager", "Fiscal User"]
    for role in roles:
        status["roles"][role] = frappe.db.exists("Role", role) is not None
    
    # Conta Custom Fields
    status["custom_fields"] = frappe.db.count("Custom Field", {"module": "Fiscal BR"})
    
    return status
