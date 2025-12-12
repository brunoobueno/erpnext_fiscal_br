"""
API para emissão de NFCe
"""

import frappe
from frappe import _

from erpnext_fiscal_br.api.nfe import criar_nfe_from_sales_invoice, emitir_nfe


@frappe.whitelist()
def criar_nfce_from_sales_invoice(sales_invoice):
    """
    Cria uma NFCe a partir de uma Sales Invoice
    
    Args:
        sales_invoice: Nome da Sales Invoice
    
    Returns:
        dict: Dados da nota fiscal criada
    """
    return criar_nfe_from_sales_invoice(sales_invoice, modelo="65")


@frappe.whitelist()
def emitir_nfce(nota_fiscal):
    """
    Emite uma NFCe para a SEFAZ
    
    Args:
        nota_fiscal: Nome da Nota Fiscal
    
    Returns:
        dict: Resultado da emissão
    """
    return emitir_nfe(nota_fiscal)


@frappe.whitelist()
def emitir_nfce_from_invoice(sales_invoice):
    """
    Cria e emite NFCe a partir de uma Sales Invoice em uma única operação
    
    Args:
        sales_invoice: Nome da Sales Invoice
    
    Returns:
        dict: Resultado da emissão
    """
    from erpnext_fiscal_br.api.nfe import emitir_nfe_from_invoice
    return emitir_nfe_from_invoice(sales_invoice, modelo="65")


@frappe.whitelist()
def get_nfce_config(empresa):
    """
    Retorna configuração de NFCe para uma empresa
    
    Args:
        empresa: Nome da empresa
    
    Returns:
        dict: Configuração de NFCe
    """
    from erpnext_fiscal_br.fiscal_br.doctype.configuracao_fiscal.configuracao_fiscal import ConfiguracaoFiscal
    
    config = ConfiguracaoFiscal.get_config_for_company(empresa)
    
    if not config:
        return {
            "success": False,
            "error": _("Configuração fiscal não encontrada")
        }
    
    # Verifica se tem CSC configurado
    has_csc = bool(config.csc_nfce and config.id_token_csc)
    
    return {
        "success": True,
        "serie": config.serie_nfce,
        "proximo_numero": config.proximo_numero_nfce,
        "ambiente": config.ambiente,
        "has_csc": has_csc,
        "warning": None if has_csc else _("CSC não configurado para NFCe")
    }
