/**
 * Customizações para Sales Invoice
 * Adiciona botões de emissão de NFe/NFCe
 */

frappe.ui.form.on("Sales Invoice", {
    refresh: function(frm) {
        // Só mostra botões se a fatura estiver submetida
        if (frm.doc.docstatus !== 1) {
            return;
        }
        
        // Verifica se já tem NFe
        if (frm.doc.nota_fiscal) {
            // Mostra informações da NFe
            frm.add_custom_button(__("Ver NFe"), function() {
                frappe.set_route("Form", "Nota Fiscal", frm.doc.nota_fiscal);
            }, __("Nota Fiscal"));
            
            // Botão para DANFE
            if (frm.doc.status_fiscal === "Autorizada") {
                frm.add_custom_button(__("DANFE"), function() {
                    frappe.call({
                        method: "erpnext_fiscal_br.events.sales_invoice.get_fiscal_status",
                        args: { sales_invoice: frm.doc.name },
                        callback: function(r) {
                            if (r.message && r.message.danfe) {
                                erpnext_fiscal_br.abrir_danfe(r.message.danfe);
                            }
                        }
                    });
                }, __("Nota Fiscal"));
                
                // Botão para XML
                frm.add_custom_button(__("XML"), function() {
                    frappe.call({
                        method: "erpnext_fiscal_br.events.sales_invoice.get_fiscal_status",
                        args: { sales_invoice: frm.doc.name },
                        callback: function(r) {
                            if (r.message && r.message.xml) {
                                erpnext_fiscal_br.download_xml(r.message.xml, frm.doc.chave_nfe);
                            }
                        }
                    });
                }, __("Nota Fiscal"));
            }
            
            return;
        }
        
        // Adiciona botão de emissão de NFe
        frm.add_custom_button(__("Emitir NFe"), function() {
            // Verifica se pode emitir
            frappe.call({
                method: "erpnext_fiscal_br.events.sales_invoice.check_can_emit_nfe",
                args: { sales_invoice: frm.doc.name },
                callback: function(r) {
                    if (r.message) {
                        if (!r.message.valid) {
                            frappe.msgprint({
                                title: __("Não é possível emitir NFe"),
                                message: r.message.errors.join("<br>"),
                                indicator: "red"
                            });
                            return;
                        }
                        
                        // Mostra warnings se houver
                        if (r.message.warnings && r.message.warnings.length > 0) {
                            frappe.confirm(
                                __("Avisos:") + "<br>" + r.message.warnings.join("<br>") + 
                                "<br><br>" + __("Deseja continuar?"),
                                function() {
                                    emitir_nfe(frm);
                                }
                            );
                        } else {
                            emitir_nfe(frm);
                        }
                    }
                }
            });
        }, __("Nota Fiscal"));
        
        // Adiciona botão de emissão de NFCe
        frm.add_custom_button(__("Emitir NFCe"), function() {
            frappe.call({
                method: "erpnext_fiscal_br.events.sales_invoice.check_can_emit_nfe",
                args: { sales_invoice: frm.doc.name },
                callback: function(r) {
                    if (r.message) {
                        if (!r.message.valid) {
                            frappe.msgprint({
                                title: __("Não é possível emitir NFCe"),
                                message: r.message.errors.join("<br>"),
                                indicator: "red"
                            });
                            return;
                        }
                        
                        emitir_nfce(frm);
                    }
                }
            });
        }, __("Nota Fiscal"));
    },
    
    onload: function(frm) {
        // Atualiza indicador de status fiscal
        if (frm.doc.status_fiscal) {
            update_fiscal_indicator(frm);
        }
    }
});

function emitir_nfe(frm) {
    frappe.confirm(
        __("Confirma a emissão da NFe para esta fatura?"),
        function() {
            erpnext_fiscal_br.emitir_nfe(frm.doc.name, function(result) {
                frm.reload_doc();
            });
        }
    );
}

function emitir_nfce(frm) {
    frappe.confirm(
        __("Confirma a emissão da NFCe para esta fatura?"),
        function() {
            erpnext_fiscal_br.emitir_nfce(frm.doc.name, function(result) {
                frm.reload_doc();
            });
        }
    );
}

function update_fiscal_indicator(frm) {
    let indicator = "gray";
    let status = frm.doc.status_fiscal || "Sem NF";
    
    switch(status) {
        case "Autorizada":
            indicator = "green";
            break;
        case "Cancelada":
            indicator = "red";
            break;
        case "Rejeitada":
            indicator = "red";
            break;
        case "Pendente":
            indicator = "orange";
            break;
        default:
            indicator = "gray";
    }
    
    frm.page.set_indicator(status, indicator);
}
