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

        // Botão Duplicar - para notas rejeitadas ou qualquer status
        if (frm.doc.name && !frm.is_new()) {
            frm.add_custom_button(__('Duplicar Nota'), function() {
                frappe.call({
                    method: 'erpnext_fiscal_br.fiscal_br.doctype.nota_fiscal.nota_fiscal.duplicar_nota_fiscal',
                    args: {
                        nota_fiscal: frm.doc.name
                    },
                    freeze: true,
                    freeze_message: __('Duplicando nota fiscal...'),
                    callback: function(r) {
                        if (r.message && r.message.success) {
                            frappe.set_route('Form', 'Nota Fiscal', r.message.nota_fiscal);
                            frappe.show_alert({
                                message: __('Nota fiscal duplicada com sucesso'),
                                indicator: 'green'
                            });
                        }
                    }
                });
            }, __('Ações'));
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
                        let modelo = frm.doc.modelo || '55';
                        if (modelo === '65') {
                            frm.set_value('serie', r.message.serie_nfce);
                            frm.set_value('numero', r.message.proximo_numero_nfce);
                        } else {
                            frm.set_value('serie', r.message.serie_nfe);
                            frm.set_value('numero', r.message.proximo_numero_nfe);
                        }
                    } else {
                        frappe.msgprint({
                            title: __('Configuração Fiscal'),
                            indicator: 'orange',
                            message: __('Configuração fiscal não encontrada para a empresa {0}. Por favor, cadastre a configuração fiscal antes de emitir notas.', [frm.doc.empresa])
                        });
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
    },

    sales_invoice: function(frm) {
        // Carrega dados da Sales Invoice automaticamente
        if (frm.doc.sales_invoice) {
            frappe.call({
                method: 'erpnext_fiscal_br.api.nfe.get_dados_from_sales_invoice',
                args: {
                    sales_invoice: frm.doc.sales_invoice
                },
                freeze: true,
                freeze_message: __('Carregando dados da fatura...'),
                callback: function(r) {
                    if (r.message) {
                        let dados = r.message;
                        
                        // Dados da empresa e configuração fiscal
                        frm.set_value('empresa', dados.empresa);
                        if (dados.ambiente) {
                            frm.set_value('ambiente', dados.ambiente);
                        }
                        if (dados.serie) {
                            frm.set_value('serie', dados.serie);
                        }
                        
                        // Dados do cliente/destinatário
                        frm.set_value('cliente', dados.cliente);
                        frm.set_value('cliente_nome', dados.cliente_nome);
                        frm.set_value('cpf_cnpj_destinatario', dados.cpf_cnpj);
                        frm.set_value('ie_destinatario', dados.ie_destinatario || '');
                        frm.set_value('contribuinte_icms', dados.contribuinte_icms || '9');
                        frm.set_value('email_destinatario', dados.email || '');
                        
                        // Endereço do destinatário
                        if (dados.endereco) {
                            frm.set_value('logradouro', dados.endereco.logradouro || '');
                            frm.set_value('numero_endereco', dados.endereco.numero || 'S/N');
                            frm.set_value('complemento', dados.endereco.complemento || '');
                            frm.set_value('bairro', dados.endereco.bairro || '');
                            frm.set_value('cidade', dados.endereco.cidade || '');
                            frm.set_value('uf', dados.endereco.uf || '');
                            frm.set_value('cep', dados.endereco.cep || '');
                            frm.set_value('codigo_municipio', dados.endereco.codigo_municipio || '');
                            frm.set_value('codigo_pais', dados.endereco.codigo_pais || '1058');
                        }
                        
                        // Dados da operação
                        frm.set_value('natureza_operacao', dados.natureza_operacao || 'Venda de mercadoria');
                        frm.set_value('finalidade', dados.finalidade || '1');
                        frm.set_value('tipo_operacao', dados.tipo_operacao || '1');
                        
                        // Valores totais
                        frm.set_value('valor_produtos', dados.valor_produtos || 0);
                        frm.set_value('valor_frete', dados.valor_frete || 0);
                        frm.set_value('valor_seguro', dados.valor_seguro || 0);
                        frm.set_value('valor_desconto', dados.valor_desconto || 0);
                        frm.set_value('valor_outras_despesas', dados.valor_outras_despesas || 0);
                        frm.set_value('valor_total', dados.valor_total || 0);
                        
                        // Informações adicionais
                        if (dados.informacoes_adicionais) {
                            frm.set_value('informacoes_adicionais', dados.informacoes_adicionais);
                        }
                        
                        // Limpa itens existentes e adiciona novos
                        frm.clear_table('itens');
                        if (dados.itens && dados.itens.length > 0) {
                            dados.itens.forEach(function(item) {
                                let row = frm.add_child('itens');
                                row.item_code = item.item_code;
                                row.descricao = item.descricao;
                                row.ncm = item.ncm;
                                row.cfop = item.cfop;
                                row.unidade = item.unidade;
                                row.quantidade = item.quantidade;
                                row.valor_unitario = item.valor_unitario;
                                row.valor_total = item.valor_total;
                                row.origem = item.origem || '0';
                                row.cst_icms = item.cst_icms || '00';
                                row.aliquota_icms = item.aliquota_icms || 0;
                                row.valor_icms = item.valor_icms || 0;
                                row.base_icms = item.valor_total || 0;
                                row.cst_pis = item.cst_pis || '07';
                                row.cst_cofins = item.cst_cofins || '07';
                            });
                            frm.refresh_field('itens');
                        }
                        
                        frappe.show_alert({
                            message: __('Todos os dados carregados da fatura'),
                            indicator: 'green'
                        });
                    }
                }
            });
        }
    }
});
