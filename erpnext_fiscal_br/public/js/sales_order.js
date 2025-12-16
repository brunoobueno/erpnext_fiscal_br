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

        // Usa API whitelisted para evitar problemas de permissão
        frappe.call({
            method: "erpnext_fiscal_br.api.nfe.get_invoices_from_sales_order",
            args: {
                sales_order: frm.doc.name
            },
            callback: function(r) {
                let invoices = r.message || [];

                // Botão principal - Gerar Nota Fiscal
                frm.add_custom_button(__("Gerar Nota Fiscal"), function() {
                    if (invoices.length > 0) {
                        // Tem fatura - verifica se já tem NF
                        let invoices_sem_nf = invoices.filter(i => !i.nota_fiscal);
                        
                        if (invoices_sem_nf.length === 0) {
                            frappe.msgprint(__("Todas as faturas deste pedido já possuem NFe emitida."));
                            return;
                        }
                        
                        if (invoices_sem_nf.length === 1) {
                            emitir_nfe_from_invoice(invoices_sem_nf[0].name);
                        } else {
                            // Múltiplas faturas - deixa escolher
                            frappe.prompt({
                                fieldname: "invoice",
                                label: __("Selecione a Fatura"),
                                fieldtype: "Select",
                                options: invoices_sem_nf.map(i => i.name).join("\n"),
                                reqd: 1
                            }, function(values) {
                                emitir_nfe_from_invoice(values.invoice);
                            }, __("Emitir NFe"), __("Emitir"));
                        }
                    } else {
                        // Não tem fatura - cria uma
                        frappe.confirm(
                            __("Este pedido não possui fatura. Deseja criar uma Fatura primeiro?"),
                            function() {
                                criar_fatura_e_emitir_nfe(frm);
                            }
                        );
                    }
                }, __("Fiscal BR"));
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
