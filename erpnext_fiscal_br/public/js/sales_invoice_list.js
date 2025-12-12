/**
 * Customizações para lista de Sales Invoice
 */

frappe.listview_settings["Sales Invoice"] = frappe.listview_settings["Sales Invoice"] || {};

// Adiciona indicador de status fiscal
const original_get_indicator = frappe.listview_settings["Sales Invoice"].get_indicator;

frappe.listview_settings["Sales Invoice"].get_indicator = function(doc) {
    // Chama indicador original se existir
    let indicator = original_get_indicator ? original_get_indicator(doc) : null;
    
    // Se tiver status fiscal, mostra
    if (doc.status_fiscal === "Autorizada") {
        return [__("NFe OK"), "green", "status_fiscal,=,Autorizada"];
    } else if (doc.status_fiscal === "Cancelada") {
        return [__("NFe Cancelada"), "red", "status_fiscal,=,Cancelada"];
    } else if (doc.status_fiscal === "Rejeitada") {
        return [__("NFe Rejeitada"), "red", "status_fiscal,=,Rejeitada"];
    }
    
    return indicator;
};

// Adiciona coluna de status fiscal
frappe.listview_settings["Sales Invoice"].add_fields = frappe.listview_settings["Sales Invoice"].add_fields || [];
if (!frappe.listview_settings["Sales Invoice"].add_fields.includes("status_fiscal")) {
    frappe.listview_settings["Sales Invoice"].add_fields.push("status_fiscal");
}
if (!frappe.listview_settings["Sales Invoice"].add_fields.includes("nota_fiscal")) {
    frappe.listview_settings["Sales Invoice"].add_fields.push("nota_fiscal");
}
