"""
Evento Fiscal
Registra eventos de notas fiscais (cancelamento, CCe, inutilização, etc.)
"""

import frappe
from frappe import _
from frappe.model.document import Document


class EventoFiscal(Document):
    def validate(self):
        self.validar_descricao()
    
    def validar_descricao(self):
        """Valida a descrição/justificativa do evento"""
        if self.descricao and len(self.descricao) < 15:
            frappe.throw(_("Descrição/Justificativa deve ter no mínimo 15 caracteres"))
        
        if self.descricao and len(self.descricao) > 1000:
            frappe.throw(_("Descrição/Justificativa deve ter no máximo 1000 caracteres"))


@frappe.whitelist()
def get_eventos_nota(nota_fiscal):
    """
    Retorna todos os eventos de uma nota fiscal
    
    Args:
        nota_fiscal: Nome da nota fiscal
    
    Returns:
        list: Lista de eventos
    """
    eventos = frappe.get_all(
        "Evento Fiscal",
        filters={"nota_fiscal": nota_fiscal},
        fields=["name", "tipo_evento", "sequencia", "data_evento", "protocolo", "codigo_status", "mensagem"],
        order_by="sequencia desc"
    )
    
    return eventos
