"""
Eventos para Item
"""

import frappe
from frappe import _


def validate(doc, method):
    """
    Valida dados fiscais do item
    """
    try:
        from erpnext_fiscal_br.utils.cnpj_cpf import validar_ncm, validar_cest
    except ImportError:
        return
    
    # Valida NCM
    if doc.get("ncm"):
        ncm = str(doc.ncm).replace(".", "").replace("-", "")
        
        if not validar_ncm(ncm):
            frappe.throw(_("NCM deve ter 8 dígitos: {0}").format(doc.ncm))
        
        doc.ncm = ncm
        
        # Preenche gênero automaticamente
        if not doc.get("genero"):
            doc.genero = ncm[:2]
    
    # Valida CEST
    if doc.get("cest"):
        cest = str(doc.cest).replace(".", "").replace("-", "")
        
        if not validar_cest(cest):
            frappe.throw(_("CEST deve ter 7 dígitos: {0}").format(doc.cest))
        
        doc.cest = cest
    
    # Valida CFOP
    if doc.get("cfop_venda_interna"):
        cfop = str(doc.cfop_venda_interna).replace(".", "")
        if len(cfop) != 4:
            frappe.throw(_("CFOP de venda interna deve ter 4 dígitos"))
        doc.cfop_venda_interna = cfop
    
    if doc.get("cfop_venda_interestadual"):
        cfop = str(doc.cfop_venda_interestadual).replace(".", "")
        if len(cfop) != 4:
            frappe.throw(_("CFOP de venda interestadual deve ter 4 dígitos"))
        doc.cfop_venda_interestadual = cfop
