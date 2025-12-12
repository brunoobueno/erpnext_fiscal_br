// Copyright (c) 2024, Bruno Bueno and contributors
// For license information, please see license.txt

frappe.ui.form.on('Nota Fiscal', {
    refresh: function(frm) {
        // Botão Emitir NFe - apenas para notas em Rascunho ou Pendente
        if (frm.doc.docstatus === 0 && ['Rascunho', 'Pendente'].includes(frm.doc.status)) {
            frm.add_custom_button(__('Emitir NFe'), function() {
                frappe.confirm(
                    __('Deseja emitir esta Nota Fiscal para a SEFAZ?'),
                    function() {
                        frm.call({
                            method: 'erpnext_fiscal_br.fiscal_br.doctype.nota_fiscal.nota_fiscal.emitir_nfe',
                            args: {
                                nota_fiscal: frm.doc.name
                            },
                            freeze: true,
                            freeze_message: __('Emitindo NFe...'),
                            callback: function(r) {
                                if (r.message) {
                                    if (r.message.success) {
                                        frappe.msgprint({
                                            title: __('NFe Autorizada'),
                                            indicator: 'green',
                                            message: __('Chave de Acesso: {0}<br>Protocolo: {1}', 
                                                [r.message.chave_acesso, r.message.protocolo])
                                        });
                                    } else {
                                        frappe.msgprint({
                                            title: __('Erro na Emissão'),
                                            indicator: 'red',
                                            message: r.message.mensagem || __('Erro desconhecido')
                                        });
                                    }
                                    frm.reload_doc();
                                }
                            }
                        });
                    }
                );
            }, __('Ações'));
        }

        // Botão Cancelar - apenas para notas Autorizadas
        if (frm.doc.status === 'Autorizada') {
            frm.add_custom_button(__('Cancelar NFe'), function() {
                frappe.prompt({
                    label: __('Justificativa'),
                    fieldname: 'justificativa',
                    fieldtype: 'Small Text',
                    reqd: 1,
                    description: __('Mínimo 15 caracteres')
                }, function(values) {
                    if (values.justificativa.length < 15) {
                        frappe.msgprint(__('Justificativa deve ter no mínimo 15 caracteres'));
                        return;
                    }
                    frm.call({
                        method: 'erpnext_fiscal_br.fiscal_br.doctype.nota_fiscal.nota_fiscal.cancelar_nfe',
                        args: {
                            nota_fiscal: frm.doc.name,
                            justificativa: values.justificativa
                        },
                        freeze: true,
                        freeze_message: __('Cancelando NFe...'),
                        callback: function(r) {
                            if (r.message) {
                                if (r.message.success) {
                                    frappe.msgprint({
                                        title: __('NFe Cancelada'),
                                        indicator: 'green',
                                        message: r.message.mensagem
                                    });
                                } else {
                                    frappe.msgprint({
                                        title: __('Erro no Cancelamento'),
                                        indicator: 'red',
                                        message: r.message.mensagem
                                    });
                                }
                                frm.reload_doc();
                            }
                        }
                    });
                }, __('Cancelar NFe'), __('Confirmar'));
            }, __('Ações'));

            // Botão Carta de Correção
            frm.add_custom_button(__('Carta de Correção'), function() {
                frappe.prompt({
                    label: __('Correção'),
                    fieldname: 'correcao',
                    fieldtype: 'Small Text',
                    reqd: 1,
                    description: __('Mínimo 15 caracteres. Máximo 20 cartas por nota.')
                }, function(values) {
                    if (values.correcao.length < 15) {
                        frappe.msgprint(__('Correção deve ter no mínimo 15 caracteres'));
                        return;
                    }
                    frm.call({
                        method: 'erpnext_fiscal_br.fiscal_br.doctype.nota_fiscal.nota_fiscal.carta_correcao_nfe',
                        args: {
                            nota_fiscal: frm.doc.name,
                            correcao: values.correcao
                        },
                        freeze: true,
                        freeze_message: __('Enviando Carta de Correção...'),
                        callback: function(r) {
                            if (r.message) {
                                frappe.msgprint({
                                    title: __('Carta de Correção'),
                                    indicator: r.message.success ? 'green' : 'red',
                                    message: r.message.mensagem
                                });
                                frm.reload_doc();
                            }
                        }
                    });
                }, __('Carta de Correção'), __('Enviar'));
            }, __('Ações'));

            // Botão Download DANFE
            if (frm.doc.danfe) {
                frm.add_custom_button(__('Download DANFE'), function() {
                    window.open(frm.doc.danfe);
                }, __('Ações'));
            }

            // Botão Download XML
            if (frm.doc.xml_autorizado) {
                frm.add_custom_button(__('Download XML'), function() {
                    window.open(frm.doc.xml_autorizado);
                }, __('Ações'));
            }
        }

        // Indicador de status
        if (frm.doc.status) {
            let indicator = {
                'Rascunho': 'grey',
                'Pendente': 'orange',
                'Processando': 'blue',
                'Autorizada': 'green',
                'Cancelada': 'red',
                'Rejeitada': 'red',
                'Denegada': 'darkgrey',
                'Inutilizada': 'darkgrey'
            }[frm.doc.status] || 'grey';
            
            frm.page.set_indicator(frm.doc.status, indicator);
        }

        // Mostra ambiente de forma destacada
        if (frm.doc.ambiente) {
            let ambiente_label = frm.doc.ambiente.includes('2') ? 'HOMOLOGAÇÃO' : 'PRODUÇÃO';
            let ambiente_color = frm.doc.ambiente.includes('2') ? 'orange' : 'red';
            frm.dashboard.add_indicator(__('Ambiente: {0}', [ambiente_label]), ambiente_color);
        }
    },

    empresa: function(frm) {
        // Quando selecionar empresa, busca configuração fiscal
        if (frm.doc.empresa) {
            frappe.call({
                method: 'erpnext_fiscal_br.fiscal_br.doctype.configuracao_fiscal.configuracao_fiscal.get_configuracao_fiscal',
                args: {
                    empresa: frm.doc.empresa
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('ambiente', r.message.ambiente);
                        frm.set_value('serie', frm.doc.modelo === '65' ? r.message.serie_nfce : r.message.serie_nfe);
                    }
                }
            });
        }
    },

    modelo: function(frm) {
        // Atualiza série quando mudar modelo
        if (frm.doc.empresa) {
            frm.trigger('empresa');
        }
    },

    cliente: function(frm) {
        // Preenche dados do cliente
        if (frm.doc.cliente) {
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Customer',
                    name: frm.doc.cliente
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('cliente_nome', r.message.customer_name);
                        frm.set_value('cpf_cnpj_destinatario', r.message.tax_id || '');
                        
                        // Busca endereço principal
                        frappe.call({
                            method: 'frappe.client.get_list',
                            args: {
                                doctype: 'Address',
                                filters: {
                                    link_doctype: 'Customer',
                                    link_name: frm.doc.cliente
                                },
                                fields: ['name'],
                                limit_page_length: 1
                            },
                            callback: function(addr) {
                                if (addr.message && addr.message.length > 0) {
                                    frm.set_value('endereco_destinatario', addr.message[0].name);
                                    frm.trigger('endereco_destinatario');
                                }
                            }
                        });
                    }
                }
            });
        }
    },

    endereco_destinatario: function(frm) {
        // Preenche dados do endereço
        if (frm.doc.endereco_destinatario) {
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Address',
                    name: frm.doc.endereco_destinatario
                },
                callback: function(r) {
                    if (r.message) {
                        let addr = r.message;
                        frm.set_value('logradouro', addr.address_line1 || '');
                        frm.set_value('numero_endereco', addr.address_line2 || 'S/N');
                        frm.set_value('complemento', addr.address_line3 || '');
                        frm.set_value('bairro', addr.city || '');
                        frm.set_value('cidade', addr.city || '');
                        frm.set_value('uf', addr.state || '');
                        frm.set_value('cep', (addr.pincode || '').replace(/\D/g, ''));
                    }
                }
            });
        }
    }
});
