frappe.query_reports["Notas Emitidas"] = {
    "filters": [
        {
            "fieldname": "empresa",
            "label": __("Empresa"),
            "fieldtype": "Link",
            "options": "Company",
            "default": frappe.defaults.get_user_default("Company")
        },
        {
            "fieldname": "modelo",
            "label": __("Modelo"),
            "fieldtype": "Select",
            "options": "\n55\n65"
        },
        {
            "fieldname": "status",
            "label": __("Status"),
            "fieldtype": "Select",
            "options": "\nRascunho\nAutorizada\nCancelada\nRejeitada\nInutilizada"
        },
        {
            "fieldname": "from_date",
            "label": __("De"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1)
        },
        {
            "fieldname": "to_date",
            "label": __("Até"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today()
        }
    ],
    
    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        if (column.fieldname === "status") {
            if (data.status === "Autorizada") {
                value = `<span class="indicator-pill green">${value}</span>`;
            } else if (data.status === "Cancelada") {
                value = `<span class="indicator-pill red">${value}</span>`;
            } else if (data.status === "Rejeitada") {
                value = `<span class="indicator-pill red">${value}</span>`;
            } else if (data.status === "Pendente") {
                value = `<span class="indicator-pill orange">${value}</span>`;
            }
        }
        
        return value;
    }
};
