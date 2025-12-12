"""
Relatório de Notas Fiscais Emitidas
"""

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    summary = get_summary(data)
    
    return columns, data, None, chart, summary


def get_columns():
    return [
        {
            "fieldname": "name",
            "label": _("Nota Fiscal"),
            "fieldtype": "Link",
            "options": "Nota Fiscal",
            "width": 150
        },
        {
            "fieldname": "modelo",
            "label": _("Modelo"),
            "fieldtype": "Data",
            "width": 70
        },
        {
            "fieldname": "serie",
            "label": _("Série"),
            "fieldtype": "Int",
            "width": 60
        },
        {
            "fieldname": "numero",
            "label": _("Número"),
            "fieldtype": "Int",
            "width": 80
        },
        {
            "fieldname": "empresa",
            "label": _("Empresa"),
            "fieldtype": "Link",
            "options": "Company",
            "width": 150
        },
        {
            "fieldname": "cliente_nome",
            "label": _("Cliente"),
            "fieldtype": "Data",
            "width": 200
        },
        {
            "fieldname": "valor_total",
            "label": _("Valor Total"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "status",
            "label": _("Status"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "data_autorizacao",
            "label": _("Data Autorização"),
            "fieldtype": "Datetime",
            "width": 150
        },
        {
            "fieldname": "chave_acesso",
            "label": _("Chave de Acesso"),
            "fieldtype": "Data",
            "width": 350
        }
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    
    data = frappe.db.sql("""
        SELECT
            name,
            modelo,
            serie,
            numero,
            empresa,
            cliente_nome,
            valor_total,
            status,
            data_autorizacao,
            chave_acesso
        FROM
            `tabNota Fiscal`
        WHERE
            1=1 {conditions}
        ORDER BY
            creation DESC
    """.format(conditions=conditions), filters, as_dict=1)
    
    return data


def get_conditions(filters):
    conditions = ""
    
    if filters.get("empresa"):
        conditions += " AND empresa = %(empresa)s"
    
    if filters.get("modelo"):
        conditions += " AND modelo = %(modelo)s"
    
    if filters.get("status"):
        conditions += " AND status = %(status)s"
    
    if filters.get("from_date"):
        conditions += " AND DATE(creation) >= %(from_date)s"
    
    if filters.get("to_date"):
        conditions += " AND DATE(creation) <= %(to_date)s"
    
    return conditions


def get_chart(data):
    if not data:
        return None
    
    # Agrupa por status
    status_count = {}
    for row in data:
        status = row.get("status", "Outros")
        status_count[status] = status_count.get(status, 0) + 1
    
    return {
        "data": {
            "labels": list(status_count.keys()),
            "datasets": [
                {
                    "name": _("Quantidade"),
                    "values": list(status_count.values())
                }
            ]
        },
        "type": "pie",
        "colors": ["#28a745", "#dc3545", "#ffc107", "#17a2b8"]
    }


def get_summary(data):
    if not data:
        return []
    
    total_notas = len(data)
    total_valor = sum(flt(row.get("valor_total", 0)) for row in data)
    autorizadas = len([row for row in data if row.get("status") == "Autorizada"])
    canceladas = len([row for row in data if row.get("status") == "Cancelada"])
    
    return [
        {
            "value": total_notas,
            "label": _("Total de Notas"),
            "datatype": "Int"
        },
        {
            "value": total_valor,
            "label": _("Valor Total"),
            "datatype": "Currency"
        },
        {
            "value": autorizadas,
            "label": _("Autorizadas"),
            "datatype": "Int",
            "indicator": "green"
        },
        {
            "value": canceladas,
            "label": _("Canceladas"),
            "datatype": "Int",
            "indicator": "red"
        }
    ]
