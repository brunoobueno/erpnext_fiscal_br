/**
 * Customizações para Sales Order
 * Adiciona botões de emissão de NFe/NFCe
 */

frappe.ui.form.on("Sales Order", {
    refresh: function(frm) {
        // Só mostra botões se o pedido estiver submetido
        if (frm.doc.docstatus !== 1) {
            return;
        }

        // Verifica se tem Sales Invoice vinculada através dos itens
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Sales Invoice Item",
                filters: {
                    "sales_order": frm.doc.name,
                    "docstatus": 1
                },
                fields: ["parent"],
                limit_page_length: 100
            },
            callback: function(r) {
                // Extrai faturas únicas
                let invoices_set = new Set();
                if (r.message) {
                    r.message.forEach(item => invoices_set.add(item.parent));
                }
                let invoice_names = Array.from(invoices_set);

                if (invoice_names.length > 0) {
                    // Tem fatura - mostra botão para emitir NF da fatura
                    frm.add_custom_button(__("Emitir NFe da Fatura"), function() {
                        // Busca detalhes das faturas
                        frappe.call({
                            method: "frappe.client.get_list",
                            args: {
                                doctype: "Sales Invoice",
                                filters: {
                                    "name": ["in", invoice_names],
                                    "docstatus": 1
                                },
                                fields: ["name", "nota_fiscal", "status_fiscal"],
                                limit_page_length: 100
                            },
                            callback: function(inv) {
                                if (inv.message && inv.message.length > 0) {
                                    let invoices = inv.message;
                                    
                                    if (invoices.length === 1) {
                                        // Uma fatura - emite direto
                                        let invoice = invoices[0];
                                        if (invoice.nota_fiscal) {
                                            frappe.msgprint(__("Esta fatura já possui NFe: {0}", [invoice.nota_fiscal]));
                                            return;
                                        }
                                        emitir_nfe_from_invoice(invoice.name);
                                    } else {
                                        // Múltiplas faturas - deixa escolher
                                        let options = invoices.filter(i => !i.nota_fiscal).map(i => ({
                                            label: i.name + (i.status_fiscal ? ` (${i.status_fiscal})` : ''),
                                            value: i.name
                                        }));
                                        
                                        if (options.length === 0) {
                                            frappe.msgprint(__("Todas as faturas já possuem NFe"));
                                            return;
                                        }
                                        
                                        frappe.prompt({
                                            fieldname: "invoice",
                                            label: __("Selecione a Fatura"),
                                            fieldtype: "Select",
                                            options: options.map(o => o.value).join("\n"),
                                            reqd: 1
                                        }, function(values) {
                                            emitir_nfe_from_invoice(values.invoice);
                                        }, __("Emitir NFe"), __("Emitir"));
                                    }
                                }
                            }
                        });
                    }, __("Nota Fiscal"));
                } else {
                    // Não tem fatura - mostra opção de criar fatura e emitir
                    frm.add_custom_button(__("Criar Fatura e Emitir NFe"), function() {
                        frappe.confirm(
                            __("Deseja criar uma Fatura (Sales Invoice) e emitir a NFe para este pedido?"),
                            function() {
                                criar_fatura_e_emitir_nfe(frm);
                            }
                        );
                    }, __("Nota Fiscal"));
                }
            }
        });
    }
});

function emitir_nfe_from_invoice(sales_invoice) {
    frappe.confirm(
        __("Confirma a emissão da NFe para a fatura {0}?", [sales_invoice]),
        function() {
            frappe.call({
                method: "erpnext_fiscal_br.api.nfe.emitir_nfe_from_invoice",
                args: {
                    sales_invoice: sales_invoice,
                    modelo: "55"
                },
                freeze: true,
                freeze_message: __("Emitindo NFe..."),
                callback: function(r) {
                    if (r.message) {
                        if (r.message.success) {
                            frappe.msgprint({
                                title: __("NFe Emitida"),
                                indicator: "green",
                                message: __("Chave de Acesso: {0}<br>Protocolo: {1}", 
                                    [r.message.chave_acesso, r.message.protocolo])
                            });
                        } else {
                            frappe.msgprint({
                                title: __("Erro na Emissão"),
                                indicator: "red",
                                message: r.message.errors ? r.message.errors.join("<br>") : r.message.mensagem
                            });
                        }
                    }
                }
            });
        }
    );
}

function criar_fatura_e_emitir_nfe(frm) {
    frappe.call({
        method: "erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice",
        args: {
            source_name: frm.doc.name
        },
        freeze: true,
        freeze_message: __("Criando Fatura..."),
        callback: function(r) {
            if (r.message) {
                // Abre a fatura para o usuário submeter
                frappe.model.sync(r.message);
                frappe.set_route("Form", r.message.doctype, r.message.name);
                
                frappe.show_alert({
                    message: __("Fatura criada. Submeta a fatura e depois emita a NFe."),
                    indicator: "blue"
                });
            }
        }
    });
}
