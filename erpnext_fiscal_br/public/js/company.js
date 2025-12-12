/**
 * Customizações para Company
 */

frappe.ui.form.on("Company", {
    cnpj: function(frm) {
        // Formata CNPJ
        let cnpj = frm.doc.cnpj;
        if (!cnpj) return;
        
        cnpj = cnpj.replace(/\D/g, "");
        
        if (cnpj.length !== 14) {
            frappe.show_alert({
                message: __("CNPJ deve ter 14 dígitos"),
                indicator: "orange"
            });
            return;
        }
        
        frm.set_value("cnpj", erpnext_fiscal_br.formatar_cnpj(cnpj));
    },
    
    refresh: function(frm) {
        if (!frm.is_new()) {
            // Adiciona botão para criar configuração fiscal
            frm.add_custom_button(__("Configuração Fiscal"), function() {
                frappe.call({
                    method: "frappe.client.get_value",
                    args: {
                        doctype: "Configuracao Fiscal",
                        filters: { empresa: frm.doc.name },
                        fieldname: "name"
                    },
                    callback: function(r) {
                        if (r.message && r.message.name) {
                            frappe.set_route("Form", "Configuracao Fiscal", r.message.name);
                        } else {
                            frappe.new_doc("Configuracao Fiscal", {
                                empresa: frm.doc.name,
                                cnpj: frm.doc.cnpj
                            });
                        }
                    }
                });
            }, __("Fiscal BR"));
            
            // Adiciona botão para certificado digital
            frm.add_custom_button(__("Certificado Digital"), function() {
                frappe.call({
                    method: "frappe.client.get_value",
                    args: {
                        doctype: "Certificado Digital",
                        filters: { empresa: frm.doc.name },
                        fieldname: "name"
                    },
                    callback: function(r) {
                        if (r.message && r.message.name) {
                            frappe.set_route("Form", "Certificado Digital", r.message.name);
                        } else {
                            frappe.new_doc("Certificado Digital", {
                                empresa: frm.doc.name
                            });
                        }
                    }
                });
            }, __("Fiscal BR"));
            
            // Botão para testar conexão SEFAZ
            frm.add_custom_button(__("Testar SEFAZ"), function() {
                erpnext_fiscal_br.consultar_status_sefaz(frm.doc.name);
            }, __("Fiscal BR"));
        }
    }
});
