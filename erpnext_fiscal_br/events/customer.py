"""
Eventos para Customer
"""

import frappe
from frappe import _


def validate(doc, method):
    """
    Valida dados fiscais do cliente
    """
    try:
        from erpnext_fiscal_br.utils.cnpj_cpf import validar_cpf, validar_cnpj, limpar_documento
    except ImportError:
        return
    
    # Valida CPF/CNPJ
    if doc.get("cpf_cnpj"):
        documento = limpar_documento(doc.cpf_cnpj)
        
        if len(documento) == 11:
            if not validar_cpf(documento):
                frappe.throw(_("CPF inválido: {0}").format(doc.cpf_cnpj))
            doc.cpf_cnpj = documento
            
        elif len(documento) == 14:
            if not validar_cnpj(documento):
                frappe.throw(_("CNPJ inválido: {0}").format(doc.cpf_cnpj))
            doc.cpf_cnpj = documento
            
        else:
            frappe.throw(_("CPF deve ter 11 dígitos ou CNPJ deve ter 14 dígitos"))
    
    # Valida IE se for contribuinte
    if doc.get("contribuinte_icms") and "1" in doc.contribuinte_icms:
        if not doc.get("inscricao_estadual_cliente"):
            frappe.msgprint(
                _("Contribuinte ICMS deve ter Inscrição Estadual informada"),
                indicator="orange",
                alert=True
            )
