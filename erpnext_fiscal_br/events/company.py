"""
Eventos para Company
"""

import frappe
from frappe import _


def validate(doc, method):
    """
    Valida dados fiscais da empresa
    """
    try:
        from erpnext_fiscal_br.utils.cnpj_cpf import validar_cnpj, limpar_documento
    except ImportError:
        return
    
    # Valida CNPJ
    if doc.get("cnpj"):
        cnpj = limpar_documento(doc.cnpj)
        
        if len(cnpj) != 14:
            frappe.throw(_("CNPJ deve ter 14 dígitos"))
        
        if not validar_cnpj(cnpj):
            frappe.throw(_("CNPJ inválido: {0}").format(doc.cnpj))
        
        doc.cnpj = cnpj
