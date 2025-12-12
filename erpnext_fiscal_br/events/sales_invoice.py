"""
Eventos para Sales Invoice
"""

import frappe
from frappe import _


def on_submit(doc, method):
    """
    Executado quando uma Sales Invoice é submetida
    Pode ser usado para emissão automática de NFe
    """
    # Verifica se a empresa tem configuração fiscal
    from erpnext_fiscal_br.fiscal_br.doctype.configuracao_fiscal.configuracao_fiscal import ConfiguracaoFiscal
    
    config = ConfiguracaoFiscal.get_config_for_company(doc.company)
    
    if not config:
        return
    
    # Por enquanto, apenas marca como "Sem NF"
    # A emissão será feita manualmente pelo botão
    if not doc.get("status_fiscal"):
        frappe.db.set_value("Sales Invoice", doc.name, "status_fiscal", "Sem NF")


def on_cancel(doc, method):
    """
    Executado quando uma Sales Invoice é cancelada
    Verifica se há NFe vinculada
    """
    if doc.get("nota_fiscal"):
        nf = frappe.get_doc("Nota Fiscal", doc.nota_fiscal)
        
        if nf.status == "Autorizada":
            frappe.throw(
                _("Esta fatura possui uma NFe autorizada ({0}). "
                  "Cancele a NFe antes de cancelar a fatura.").format(nf.name)
            )


def validate(doc, method):
    """
    Validação adicional na Sales Invoice
    """
    pass


@frappe.whitelist()
def get_fiscal_status(sales_invoice):
    """
    Retorna o status fiscal de uma Sales Invoice
    
    Args:
        sales_invoice: Nome da Sales Invoice
    
    Returns:
        dict: Status fiscal
    """
    invoice = frappe.get_doc("Sales Invoice", sales_invoice)
    
    result = {
        "status_fiscal": invoice.get("status_fiscal", "Sem NF"),
        "nota_fiscal": invoice.get("nota_fiscal"),
        "chave_nfe": invoice.get("chave_nfe"),
        "numero_nfe": invoice.get("numero_nfe"),
        "serie_nfe": invoice.get("serie_nfe"),
        "protocolo": invoice.get("protocolo_autorizacao"),
    }
    
    if invoice.get("nota_fiscal"):
        nf = frappe.get_doc("Nota Fiscal", invoice.nota_fiscal)
        result["danfe"] = nf.danfe
        result["xml"] = nf.xml_autorizado
    
    return result


@frappe.whitelist()
def check_can_emit_nfe(sales_invoice):
    """
    Verifica se uma Sales Invoice pode emitir NFe
    
    Args:
        sales_invoice: Nome da Sales Invoice
    
    Returns:
        dict: Resultado da verificação
    """
    from erpnext_fiscal_br.services.validators import validate_sales_invoice_for_nfe
    
    return validate_sales_invoice_for_nfe(sales_invoice)
