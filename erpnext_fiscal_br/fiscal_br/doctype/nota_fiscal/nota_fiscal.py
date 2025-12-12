"""
Nota Fiscal Eletrônica (NFe/NFCe)
Gerencia a emissão, autorização e eventos de notas fiscais eletrônicas
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, getdate, flt
from datetime import datetime, timedelta


class NotaFiscal(Document):
    def validate(self):
        # Define ambiente da configuração fiscal se ainda não definido ou se for Rascunho
        if self.status in ["Rascunho", "Pendente"] or not self.ambiente:
            self.definir_ambiente()
        self.validar_destinatario()
        self.validar_itens()
        self.calcular_totais()
    
    def before_insert(self):
        # Sempre busca ambiente da configuração fiscal
        self.definir_ambiente()
        if not self.numero:
            self.obter_proximo_numero()
    
    def definir_ambiente(self):
        """Define o ambiente a partir da configuração fiscal da empresa"""
        if not self.empresa:
            return
        
        from erpnext_fiscal_br.fiscal_br.doctype.configuracao_fiscal.configuracao_fiscal import ConfiguracaoFiscal
        
        config = ConfiguracaoFiscal.get_config_for_company(self.empresa)
        if config and config.ambiente:
            self.ambiente = config.ambiente
    
    def validar_destinatario(self):
        """Valida os dados do destinatário"""
        from erpnext_fiscal_br.utils.cnpj_cpf import validar_cpf, validar_cnpj
        
        if self.cpf_cnpj_destinatario:
            doc = "".join(filter(str.isdigit, self.cpf_cnpj_destinatario))
            
            if len(doc) == 11:
                if not validar_cpf(doc):
                    frappe.throw(_("CPF do destinatário inválido"))
            elif len(doc) == 14:
                if not validar_cnpj(doc):
                    frappe.throw(_("CNPJ do destinatário inválido"))
            else:
                frappe.throw(_("CPF/CNPJ do destinatário deve ter 11 ou 14 dígitos"))
            
            self.cpf_cnpj_destinatario = doc
    
    def validar_itens(self):
        """Valida os itens da nota"""
        if not self.itens or len(self.itens) == 0:
            frappe.throw(_("A nota fiscal deve ter pelo menos um item"))
        
        for item in self.itens:
            if not item.ncm or len(item.ncm) != 8:
                frappe.throw(_("NCM do item {0} deve ter 8 dígitos").format(item.item_code))
            
            if not item.cfop or len(item.cfop) != 4:
                frappe.throw(_("CFOP do item {0} deve ter 4 dígitos").format(item.item_code))
    
    def calcular_totais(self):
        """Calcula os totais da nota fiscal"""
        self.valor_produtos = 0
        self.valor_icms = 0
        self.valor_icms_st = 0
        self.valor_ipi = 0
        self.valor_pis = 0
        self.valor_cofins = 0
        
        for item in self.itens:
            self.valor_produtos += flt(item.valor_total)
            self.valor_icms += flt(item.valor_icms)
            self.valor_icms_st += flt(item.valor_icms_st)
            self.valor_ipi += flt(item.valor_ipi)
            self.valor_pis += flt(item.valor_pis)
            self.valor_cofins += flt(item.valor_cofins)
        
        self.valor_total = (
            self.valor_produtos
            + flt(self.valor_frete)
            + flt(self.valor_seguro)
            + flt(self.valor_outras_despesas)
            + flt(self.valor_ipi)
            + flt(self.valor_icms_st)
            - flt(self.valor_desconto)
        )
    
    def obter_proximo_numero(self):
        """Obtém o próximo número da nota fiscal"""
        from erpnext_fiscal_br.fiscal_br.doctype.configuracao_fiscal.configuracao_fiscal import ConfiguracaoFiscal
        
        config = ConfiguracaoFiscal.get_config_for_company(self.empresa)
        if not config:
            frappe.throw(_("Configuração fiscal não encontrada para a empresa {0}").format(self.empresa))
        
        self.numero = config.get_proximo_numero(self.modelo)
        self.serie = config.get_serie(self.modelo)
        self.ambiente = config.ambiente
    
    def gerar_chave_acesso(self):
        """Gera a chave de acesso da NFe (44 dígitos)"""
        from erpnext_fiscal_br.fiscal_br.doctype.configuracao_fiscal.configuracao_fiscal import ConfiguracaoFiscal
        from erpnext_fiscal_br.utils.cnpj_cpf import calcular_dv_chave_nfe
        
        config = ConfiguracaoFiscal.get_config_for_company(self.empresa)
        if not config:
            frappe.throw(_("Configuração fiscal não encontrada"))
        
        # Formato da chave: cUF + AAMM + CNPJ + mod + serie + nNF + tpEmis + cNF + cDV
        data_emissao = getdate(now_datetime())
        
        chave = ""
        chave += config.codigo_uf.zfill(2)  # cUF (2)
        chave += data_emissao.strftime("%y%m")  # AAMM (4)
        chave += config.cnpj.zfill(14)  # CNPJ (14)
        chave += str(self.modelo).zfill(2)  # mod (2)
        chave += str(self.serie).zfill(3)  # serie (3)
        chave += str(self.numero).zfill(9)  # nNF (9)
        chave += "1"  # tpEmis (1) - Normal
        chave += str(self.numero).zfill(8)  # cNF (8) - Código numérico
        
        # Calcula dígito verificador
        dv = calcular_dv_chave_nfe(chave)
        chave += str(dv)
        
        self.chave_acesso = chave
        return chave
    
    def emitir(self):
        """Emite a nota fiscal para a SEFAZ"""
        from erpnext_fiscal_br.services.xml_builder import XMLBuilder
        from erpnext_fiscal_br.services.signer import XMLSigner
        from erpnext_fiscal_br.services.transmitter import SEFAZTransmitter
        
        try:
            self.status = "Processando"
            self.save(ignore_permissions=True)
            
            # Gera chave de acesso
            self.gerar_chave_acesso()
            
            # Monta XML
            builder = XMLBuilder(self)
            xml_nfe = builder.build()
            
            # Assina XML
            signer = XMLSigner(self.empresa)
            xml_assinado = signer.sign(xml_nfe)
            
            # Salva XML assinado
            self.salvar_xml(xml_assinado, "xml_nfe")
            
            # Transmite para SEFAZ
            transmitter = SEFAZTransmitter(self.empresa)
            resultado = transmitter.enviar_nfe(xml_assinado)
            
            # Processa resultado
            self.processar_retorno_sefaz(resultado)
            
        except Exception as e:
            self.status = "Rejeitada"
            self.motivo_rejeicao = str(e)
            self.save(ignore_permissions=True)
            frappe.log_error(f"Erro ao emitir NFe: {str(e)}", "Emissão NFe")
            raise
    
    def processar_retorno_sefaz(self, resultado):
        """Processa o retorno da SEFAZ"""
        self.codigo_status = resultado.get("cStat")
        self.mensagem_sefaz = resultado.get("xMotivo")
        
        # Códigos de sucesso: 100 (Autorizada), 150 (Autorizada fora prazo)
        if self.codigo_status in ["100", "150"]:
            self.status = "Autorizada"
            self.protocolo_autorizacao = resultado.get("nProt")
            self.data_autorizacao = resultado.get("dhRecbto")
            
            # Salva XML autorizado (procNFe)
            if resultado.get("xml_proc"):
                self.salvar_xml(resultado.get("xml_proc"), "xml_autorizado")
            
            # Gera DANFE
            self.gerar_danfe()
            
            # Atualiza Sales Invoice
            self.atualizar_sales_invoice()
            
        elif self.codigo_status in ["204", "205", "206"]:
            # Duplicidade - já autorizada
            self.status = "Autorizada"
            self.protocolo_autorizacao = resultado.get("nProt")
            
        else:
            self.status = "Rejeitada"
            self.motivo_rejeicao = f"[{self.codigo_status}] {self.mensagem_sefaz}"
        
        self.save(ignore_permissions=True)
    
    def salvar_xml(self, xml_content, field_name):
        """Salva o XML como anexo"""
        file_name = f"{self.chave_acesso}_{field_name}.xml"
        
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": file_name,
            "attached_to_doctype": self.doctype,
            "attached_to_name": self.name,
            "content": xml_content,
            "is_private": 1
        })
        file_doc.insert(ignore_permissions=True)
        
        self.set(field_name, file_doc.file_url)
    
    def gerar_danfe(self):
        """Gera o DANFE (PDF) da nota fiscal"""
        from erpnext_fiscal_br.services.danfe import DANFEGenerator
        
        try:
            generator = DANFEGenerator(self)
            pdf_content = generator.generate()
            
            file_name = f"DANFE_{self.chave_acesso}.pdf"
            
            file_doc = frappe.get_doc({
                "doctype": "File",
                "file_name": file_name,
                "attached_to_doctype": self.doctype,
                "attached_to_name": self.name,
                "content": pdf_content,
                "is_private": 0
            })
            file_doc.insert(ignore_permissions=True)
            
            self.danfe = file_doc.file_url
            
        except Exception as e:
            frappe.log_error(f"Erro ao gerar DANFE: {str(e)}", "DANFE")
    
    def atualizar_sales_invoice(self):
        """Atualiza a Sales Invoice com os dados da NFe"""
        if self.sales_invoice:
            frappe.db.set_value("Sales Invoice", self.sales_invoice, {
                "nota_fiscal": self.name,
                "chave_nfe": self.chave_acesso,
                "status_fiscal": self.status,
                "numero_nfe": self.numero,
                "serie_nfe": self.serie,
                "protocolo_autorizacao": self.protocolo_autorizacao,
                "data_autorizacao": self.data_autorizacao
            })
    
    def cancelar(self, justificativa):
        """Cancela a nota fiscal"""
        if self.status != "Autorizada":
            frappe.throw(_("Apenas notas autorizadas podem ser canceladas"))
        
        if len(justificativa) < 15:
            frappe.throw(_("Justificativa deve ter no mínimo 15 caracteres"))
        
        # Verifica prazo de cancelamento (24 horas)
        if self.data_autorizacao:
            data_limite = self.data_autorizacao + timedelta(hours=24)
            if now_datetime() > data_limite:
                frappe.throw(_("Prazo de cancelamento expirado (24 horas)"))
        
        from erpnext_fiscal_br.services.transmitter import SEFAZTransmitter
        
        transmitter = SEFAZTransmitter(self.empresa)
        resultado = transmitter.cancelar_nfe(self.chave_acesso, self.protocolo_autorizacao, justificativa)
        
        if resultado.get("cStat") in ["135", "155"]:
            self.status = "Cancelada"
            self.mensagem_sefaz = resultado.get("xMotivo")
            self.save(ignore_permissions=True)
            
            # Cria evento fiscal
            self.criar_evento("Cancelamento", justificativa, resultado)
            
            # Atualiza Sales Invoice
            if self.sales_invoice:
                frappe.db.set_value("Sales Invoice", self.sales_invoice, "status_fiscal", "Cancelada")
        else:
            frappe.throw(_("Erro ao cancelar: [{0}] {1}").format(
                resultado.get("cStat"),
                resultado.get("xMotivo")
            ))
    
    def carta_correcao(self, correcao):
        """Envia carta de correção (CCe)"""
        if self.status != "Autorizada":
            frappe.throw(_("Apenas notas autorizadas podem receber carta de correção"))
        
        if len(correcao) < 15:
            frappe.throw(_("Correção deve ter no mínimo 15 caracteres"))
        
        # Conta sequência de eventos
        seq_evento = frappe.db.count("Evento Fiscal", {
            "nota_fiscal": self.name,
            "tipo_evento": "Carta de Correção"
        }) + 1
        
        if seq_evento > 20:
            frappe.throw(_("Limite de 20 cartas de correção atingido"))
        
        from erpnext_fiscal_br.services.transmitter import SEFAZTransmitter
        
        transmitter = SEFAZTransmitter(self.empresa)
        resultado = transmitter.carta_correcao(self.chave_acesso, correcao, seq_evento)
        
        if resultado.get("cStat") in ["135", "155"]:
            self.criar_evento("Carta de Correção", correcao, resultado, seq_evento)
            return True
        else:
            frappe.throw(_("Erro ao enviar CCe: [{0}] {1}").format(
                resultado.get("cStat"),
                resultado.get("xMotivo")
            ))
    
    def criar_evento(self, tipo, descricao, resultado, sequencia=1):
        """Cria um registro de evento fiscal"""
        evento = frappe.new_doc("Evento Fiscal")
        evento.nota_fiscal = self.name
        evento.tipo_evento = tipo
        evento.sequencia = sequencia
        evento.descricao = descricao
        evento.protocolo = resultado.get("nProt")
        evento.data_evento = resultado.get("dhRegEvento")
        evento.codigo_status = resultado.get("cStat")
        evento.mensagem = resultado.get("xMotivo")
        evento.insert(ignore_permissions=True)
        
        return evento


@frappe.whitelist()
def emitir_nfe(nota_fiscal):
    """API para emitir NFe"""
    nf = frappe.get_doc("Nota Fiscal", nota_fiscal)
    nf.emitir()
    return {
        "success": nf.status == "Autorizada",
        "status": nf.status,
        "chave_acesso": nf.chave_acesso,
        "protocolo": nf.protocolo_autorizacao,
        "mensagem": nf.mensagem_sefaz
    }


@frappe.whitelist()
def cancelar_nfe(nota_fiscal, justificativa):
    """API para cancelar NFe"""
    nf = frappe.get_doc("Nota Fiscal", nota_fiscal)
    nf.cancelar(justificativa)
    return {
        "success": nf.status == "Cancelada",
        "status": nf.status,
        "mensagem": nf.mensagem_sefaz
    }


@frappe.whitelist()
def carta_correcao_nfe(nota_fiscal, correcao):
    """API para enviar carta de correção"""
    nf = frappe.get_doc("Nota Fiscal", nota_fiscal)
    nf.carta_correcao(correcao)
    return {
        "success": True,
        "mensagem": "Carta de correção enviada com sucesso"
    }


@frappe.whitelist()
def criar_nota_fiscal_from_invoice(sales_invoice, modelo="55"):
    """
    Cria uma Nota Fiscal a partir de uma Sales Invoice
    
    Args:
        sales_invoice: Nome da Sales Invoice
        modelo: "55" para NFe, "65" para NFCe
    
    Returns:
        dict: Dados da nota fiscal criada
    """
    from erpnext_fiscal_br.api.nfe import criar_nfe_from_sales_invoice
    
    return criar_nfe_from_sales_invoice(sales_invoice, modelo)


@frappe.whitelist()
def duplicar_nota_fiscal(nota_fiscal):
    """
    Duplica uma Nota Fiscal existente
    
    Args:
        nota_fiscal: Nome da Nota Fiscal a ser duplicada
    
    Returns:
        dict: Dados da nova nota fiscal
    """
    # Carrega nota original
    nf_original = frappe.get_doc("Nota Fiscal", nota_fiscal)
    
    # Cria nova nota
    nova_nf = frappe.new_doc("Nota Fiscal")
    
    # Copia campos principais
    campos_copiar = [
        'modelo', 'empresa', 'sales_invoice',
        'cliente', 'cliente_nome', 'cpf_cnpj_destinatario', 
        'ie_destinatario', 'contribuinte_icms', 'email_destinatario',
        'endereco_destinatario', 'logradouro', 'numero_endereco', 
        'complemento', 'bairro', 'cidade', 'uf', 'cep', 
        'codigo_municipio', 'codigo_pais',
        'natureza_operacao', 'finalidade', 'tipo_operacao',
        'modalidade_frete', 'transportadora',
        'valor_frete', 'valor_seguro', 'valor_desconto', 'valor_outras_despesas',
        'informacoes_adicionais', 'informacoes_fisco'
    ]
    
    for campo in campos_copiar:
        if hasattr(nf_original, campo) and getattr(nf_original, campo):
            setattr(nova_nf, campo, getattr(nf_original, campo))
    
    # Status inicial
    nova_nf.status = 'Rascunho'
    
    # Limpa campos que não devem ser copiados
    nova_nf.numero = None
    nova_nf.serie = None
    nova_nf.chave_acesso = None
    nova_nf.protocolo_autorizacao = None
    nova_nf.data_autorizacao = None
    nova_nf.mensagem_sefaz = None
    nova_nf.motivo_rejeicao = None
    nova_nf.xml_nfe = None
    nova_nf.xml_autorizado = None
    nova_nf.danfe = None
    nova_nf.qrcode_url = None
    
    # Copia itens
    for item_original in nf_original.itens:
        novo_item = nova_nf.append('itens', {})
        campos_item = [
            'item_code', 'descricao', 'item_name', 'ncm', 'cest', 'cfop', 
            'unidade', 'quantidade', 'valor_unitario', 'valor_total', 'valor_desconto',
            'origem', 'cst_icms', 'base_icms', 'aliquota_icms', 'valor_icms',
            'base_icms_st', 'aliquota_icms_st', 'valor_icms_st',
            'cst_ipi', 'base_ipi', 'aliquota_ipi', 'valor_ipi',
            'cst_pis', 'base_pis', 'aliquota_pis', 'valor_pis',
            'cst_cofins', 'base_cofins', 'aliquota_cofins', 'valor_cofins',
            'informacoes_adicionais'
        ]
        for campo in campos_item:
            if hasattr(item_original, campo) and getattr(item_original, campo) is not None:
                setattr(novo_item, campo, getattr(item_original, campo))
        
        # Garante que descrição tenha valor
        if not novo_item.descricao:
            novo_item.descricao = novo_item.item_name or novo_item.item_code or "Item"
    
    # Salva nova nota
    nova_nf.insert(ignore_permissions=True)
    
    return {
        "success": True,
        "nota_fiscal": nova_nf.name,
        "numero": nova_nf.numero,
        "serie": nova_nf.serie
    }
