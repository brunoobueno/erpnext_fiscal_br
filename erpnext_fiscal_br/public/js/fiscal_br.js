/**
 * ERPNext Fiscal BR - JavaScript principal
 */

// Namespace
frappe.provide("erpnext_fiscal_br");

erpnext_fiscal_br = {
    /**
     * Emite NFe a partir de uma Sales Invoice
     */
    emitir_nfe: function(sales_invoice, callback) {
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
                        frappe.show_alert({
                            message: __("NFe emitida com sucesso! Protocolo: {0}", [r.message.protocolo]),
                            indicator: "green"
                        });
                        
                        if (callback) callback(r.message);
                    } else {
                        frappe.msgprint({
                            title: __("Erro na emissão"),
                            message: r.message.errors ? r.message.errors.join("<br>") : r.message.mensagem,
                            indicator: "red"
                        });
                    }
                }
            }
        });
    },
    
    /**
     * Emite NFCe a partir de uma Sales Invoice
     */
    emitir_nfce: function(sales_invoice, callback) {
        frappe.call({
            method: "erpnext_fiscal_br.api.nfce.emitir_nfce_from_invoice",
            args: {
                sales_invoice: sales_invoice
            },
            freeze: true,
            freeze_message: __("Emitindo NFCe..."),
            callback: function(r) {
                if (r.message) {
                    if (r.message.success) {
                        frappe.show_alert({
                            message: __("NFCe emitida com sucesso!"),
                            indicator: "green"
                        });
                        
                        if (callback) callback(r.message);
                    } else {
                        frappe.msgprint({
                            title: __("Erro na emissão"),
                            message: r.message.errors ? r.message.errors.join("<br>") : r.message.mensagem,
                            indicator: "red"
                        });
                    }
                }
            }
        });
    },
    
    /**
     * Cancela uma NFe
     */
    cancelar_nfe: function(nota_fiscal, callback) {
        frappe.prompt({
            fieldname: "justificativa",
            label: __("Justificativa"),
            fieldtype: "Small Text",
            reqd: 1,
            description: __("Mínimo 15 caracteres")
        }, function(values) {
            if (values.justificativa.length < 15) {
                frappe.msgprint(__("Justificativa deve ter no mínimo 15 caracteres"));
                return;
            }
            
            frappe.call({
                method: "erpnext_fiscal_br.api.nfe.cancelar_nfe",
                args: {
                    nota_fiscal: nota_fiscal,
                    justificativa: values.justificativa
                },
                freeze: true,
                freeze_message: __("Cancelando NFe..."),
                callback: function(r) {
                    if (r.message) {
                        if (r.message.success) {
                            frappe.show_alert({
                                message: __("NFe cancelada com sucesso!"),
                                indicator: "green"
                            });
                            
                            if (callback) callback(r.message);
                        } else {
                            frappe.msgprint({
                                title: __("Erro no cancelamento"),
                                message: r.message.error || r.message.mensagem,
                                indicator: "red"
                            });
                        }
                    }
                }
            });
        }, __("Cancelar NFe"), __("Cancelar"));
    },
    
    /**
     * Envia carta de correção
     */
    carta_correcao: function(nota_fiscal, callback) {
        frappe.prompt({
            fieldname: "correcao",
            label: __("Correção"),
            fieldtype: "Small Text",
            reqd: 1,
            description: __("Mínimo 15 caracteres. Não é possível corrigir valores ou dados que alterem o cálculo do imposto.")
        }, function(values) {
            if (values.correcao.length < 15) {
                frappe.msgprint(__("Correção deve ter no mínimo 15 caracteres"));
                return;
            }
            
            frappe.call({
                method: "erpnext_fiscal_br.api.nfe.carta_correcao",
                args: {
                    nota_fiscal: nota_fiscal,
                    correcao: values.correcao
                },
                freeze: true,
                freeze_message: __("Enviando carta de correção..."),
                callback: function(r) {
                    if (r.message) {
                        if (r.message.success) {
                            frappe.show_alert({
                                message: __("Carta de correção enviada com sucesso!"),
                                indicator: "green"
                            });
                            
                            if (callback) callback(r.message);
                        } else {
                            frappe.msgprint({
                                title: __("Erro no envio"),
                                message: r.message.error,
                                indicator: "red"
                            });
                        }
                    }
                }
            });
        }, __("Carta de Correção"), __("Enviar"));
    },
    
    /**
     * Consulta status do serviço SEFAZ
     */
    consultar_status_sefaz: function(empresa, callback) {
        frappe.call({
            method: "erpnext_fiscal_br.api.sefaz.consultar_status",
            args: {
                empresa: empresa
            },
            callback: function(r) {
                if (r.message) {
                    if (r.message.success) {
                        frappe.show_alert({
                            message: __("SEFAZ Online: {0}", [r.message.mensagem]),
                            indicator: "green"
                        });
                    } else {
                        frappe.show_alert({
                            message: __("SEFAZ: {0}", [r.message.mensagem || r.message.error]),
                            indicator: "red"
                        });
                    }
                    
                    if (callback) callback(r.message);
                }
            }
        });
    },
    
    /**
     * Abre DANFE em nova aba
     */
    abrir_danfe: function(danfe_url) {
        if (danfe_url) {
            window.open(danfe_url, "_blank");
        } else {
            frappe.msgprint(__("DANFE não disponível"));
        }
    },
    
    /**
     * Download do XML
     */
    download_xml: function(xml_url, chave) {
        if (xml_url) {
            window.open(xml_url, "_blank");
        } else {
            frappe.msgprint(__("XML não disponível"));
        }
    },
    
    /**
     * Formata CNPJ
     */
    formatar_cnpj: function(cnpj) {
        if (!cnpj) return "";
        cnpj = cnpj.replace(/\D/g, "");
        if (cnpj.length !== 14) return cnpj;
        return cnpj.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, "$1.$2.$3/$4-$5");
    },
    
    /**
     * Formata CPF
     */
    formatar_cpf: function(cpf) {
        if (!cpf) return "";
        cpf = cpf.replace(/\D/g, "");
        if (cpf.length !== 11) return cpf;
        return cpf.replace(/^(\d{3})(\d{3})(\d{3})(\d{2})$/, "$1.$2.$3-$4");
    },
    
    /**
     * Formata chave de acesso
     */
    formatar_chave: function(chave) {
        if (!chave) return "";
        chave = chave.replace(/\D/g, "");
        // Divide em grupos de 4
        return chave.match(/.{1,4}/g).join(" ");
    }
};
