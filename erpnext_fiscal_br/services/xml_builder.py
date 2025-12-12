"""
XML Builder para NFe/NFCe
Gera o XML da nota fiscal conforme layout da SEFAZ
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, getdate, flt
from datetime import datetime
from lxml import etree

# Namespace da NFe
NAMESPACE_NFE = "http://www.portalfiscal.inf.br/nfe"
NAMESPACE_DS = "http://www.w3.org/2000/09/xmldsig#"

NSMAP = {
    None: NAMESPACE_NFE,
}


class XMLBuilder:
    """Construtor de XML para NFe/NFCe"""
    
    def __init__(self, nota_fiscal):
        """
        Inicializa o builder
        
        Args:
            nota_fiscal: Documento Nota Fiscal
        """
        self.nf = nota_fiscal
        self.config = self._get_config()
        
    def _get_config(self):
        """Obtém a configuração fiscal da empresa"""
        from erpnext_fiscal_br.fiscal_br.doctype.configuracao_fiscal.configuracao_fiscal import ConfiguracaoFiscal
        
        config = ConfiguracaoFiscal.get_config_for_company(self.nf.empresa)
        if not config:
            frappe.throw(_("Configuração fiscal não encontrada para a empresa"))
        return config
    
    def build(self):
        """
        Constrói o XML completo da NFe
        
        Returns:
            str: XML da NFe
        """
        # Elemento raiz
        nfe = etree.Element("{%s}NFe" % NAMESPACE_NFE, nsmap=NSMAP)
        
        # infNFe - Informações da NFe
        inf_nfe = etree.SubElement(nfe, "infNFe")
        inf_nfe.set("versao", "4.00")
        inf_nfe.set("Id", f"NFe{self.nf.chave_acesso}")
        
        # Adiciona grupos
        self._add_ide(inf_nfe)
        self._add_emit(inf_nfe)
        self._add_dest(inf_nfe)
        self._add_det(inf_nfe)
        self._add_total(inf_nfe)
        self._add_transp(inf_nfe)
        self._add_pag(inf_nfe)
        self._add_inf_adic(inf_nfe)
        
        # Para NFCe, adiciona infNFeSupl (depois da assinatura, não aqui)
        # O infNFeSupl será adicionado após a assinatura do XML
        
        # Converte para string
        xml_str = etree.tostring(nfe, encoding="unicode", pretty_print=True)
        
        # Adiciona declaração XML
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>' + xml_str
        
        return xml_str
    
    def _add_ide(self, parent):
        """Adiciona grupo de identificação da NFe"""
        ide = etree.SubElement(parent, "ide")
        
        # Código UF
        self._add_element(ide, "cUF", self.config.codigo_uf)
        
        # Código numérico
        self._add_element(ide, "cNF", str(self.nf.numero).zfill(8))
        
        # Natureza da operação
        self._add_element(ide, "natOp", self.nf.natureza_operacao or "Venda de mercadoria")
        
        # Modelo (55=NFe, 65=NFCe)
        self._add_element(ide, "mod", self.nf.modelo)
        
        # Série
        self._add_element(ide, "serie", str(self.nf.serie))
        
        # Número
        self._add_element(ide, "nNF", str(self.nf.numero))
        
        # Data de emissão
        data_emissao = now_datetime()
        self._add_element(ide, "dhEmi", data_emissao.strftime("%Y-%m-%dT%H:%M:%S-03:00"))
        
        # Data de saída (apenas NFe)
        if self.nf.modelo == "55":
            self._add_element(ide, "dhSaiEnt", data_emissao.strftime("%Y-%m-%dT%H:%M:%S-03:00"))
        
        # Tipo de operação (0=Entrada, 1=Saída)
        tipo_op = self.nf.tipo_operacao.split(" - ")[0] if self.nf.tipo_operacao else "1"
        self._add_element(ide, "tpNF", tipo_op)
        
        # Identificador de destino (1=Interna, 2=Interestadual, 3=Exterior)
        id_dest = self._get_id_destino()
        self._add_element(ide, "idDest", id_dest)
        
        # Código do município
        self._add_element(ide, "cMunFG", self.config.codigo_municipio)
        
        # Formato de impressão (0=Sem DANFE, 1=Retrato, 2=Paisagem, 4=NFCe, 5=NFCe msg eletrônica)
        if self.nf.modelo == "65":
            self._add_element(ide, "tpImp", "4")
        else:
            self._add_element(ide, "tpImp", "1")
        
        # Tipo de emissão (1=Normal)
        self._add_element(ide, "tpEmis", "1")
        
        # Dígito verificador
        self._add_element(ide, "cDV", self.nf.chave_acesso[-1])
        
        # Ambiente (1=Produção, 2=Homologação)
        ambiente = self.config.get_ambiente_codigo()
        self._add_element(ide, "tpAmb", ambiente)
        
        # Finalidade (1=Normal, 2=Complementar, 3=Ajuste, 4=Devolução)
        finalidade = self.nf.finalidade.split(" - ")[0] if self.nf.finalidade else "1"
        self._add_element(ide, "finNFe", finalidade)
        
        # Indicador de consumidor final (0=Normal, 1=Consumidor final)
        ind_final = "1" if self.nf.modelo == "65" else "0"
        self._add_element(ide, "indFinal", ind_final)
        
        # Indicador de presença (0=Não se aplica, 1=Presencial, 2=Internet, etc)
        ind_pres = "1" if self.nf.modelo == "65" else "0"
        self._add_element(ide, "indPres", ind_pres)
        
        # Processo de emissão (0=Aplicativo do contribuinte)
        self._add_element(ide, "procEmi", "0")
        
        # Versão do aplicativo
        self._add_element(ide, "verProc", "ERPNextFiscalBR-1.0")
    
    def _add_emit(self, parent):
        """Adiciona grupo do emitente"""
        emit = etree.SubElement(parent, "emit")
        
        # CNPJ
        self._add_element(emit, "CNPJ", self.config.cnpj)
        
        # Razão Social
        company = frappe.get_doc("Company", self.nf.empresa)
        self._add_element(emit, "xNome", company.company_name[:60])
        
        # Nome Fantasia
        if company.abbr:
            self._add_element(emit, "xFant", company.abbr[:60])
        
        # Endereço
        self._add_endereco_emit(emit)
        
        # Inscrição Estadual
        self._add_element(emit, "IE", self.config.inscricao_estadual)
        
        # CRT - Código de Regime Tributário
        crt = self.config.get_regime_codigo()
        self._add_element(emit, "CRT", crt)
    
    def _add_endereco_emit(self, parent):
        """Adiciona endereço do emitente"""
        ender = etree.SubElement(parent, "enderEmit")
        
        company = frappe.get_doc("Company", self.nf.empresa)
        
        # Tenta obter endereço da empresa
        address = None
        if company.get("company_address"):
            address = frappe.get_doc("Address", company.company_address)
        
        if address:
            self._add_element(ender, "xLgr", (address.address_line1 or "")[:60])
            self._add_element(ender, "nro", address.get("numero_endereco") or "S/N")
            if address.get("complemento"):
                self._add_element(ender, "xCpl", address.complemento[:60])
            self._add_element(ender, "xBairro", (address.get("bairro") or address.city or "")[:60])
            self._add_element(ender, "cMun", self.config.codigo_municipio)
            self._add_element(ender, "xMun", (address.city or "")[:60])
            self._add_element(ender, "UF", self.config.uf_emissao)
            self._add_element(ender, "CEP", (address.pincode or "").replace("-", "").replace(".", ""))
            self._add_element(ender, "cPais", "1058")
            self._add_element(ender, "xPais", "Brasil")
            if address.phone:
                self._add_element(ender, "fone", address.phone.replace("-", "").replace(" ", "").replace("(", "").replace(")", "")[:14])
        else:
            # Dados mínimos
            self._add_element(ender, "xLgr", "Endereço não informado")
            self._add_element(ender, "nro", "S/N")
            self._add_element(ender, "xBairro", "Centro")
            self._add_element(ender, "cMun", self.config.codigo_municipio)
            self._add_element(ender, "xMun", "Município")
            self._add_element(ender, "UF", self.config.uf_emissao)
            self._add_element(ender, "CEP", "00000000")
            self._add_element(ender, "cPais", "1058")
            self._add_element(ender, "xPais", "Brasil")
    
    def _add_dest(self, parent):
        """Adiciona grupo do destinatário"""
        dest = etree.SubElement(parent, "dest")
        
        # CPF ou CNPJ
        doc = self.nf.cpf_cnpj_destinatario
        if len(doc) == 11:
            self._add_element(dest, "CPF", doc)
        else:
            self._add_element(dest, "CNPJ", doc)
        
        # Nome/Razão Social
        # Em homologação, usar nome padrão
        ambiente = self.config.get_ambiente_codigo()
        if ambiente == "2":
            self._add_element(dest, "xNome", "NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL")
        else:
            self._add_element(dest, "xNome", self.nf.cliente_nome[:60])
        
        # Endereço
        self._add_endereco_dest(dest)
        
        # Indicador de IE
        ind_ie = self.nf.contribuinte_icms.split(" - ")[0] if self.nf.contribuinte_icms else "9"
        self._add_element(dest, "indIEDest", ind_ie)
        
        # IE do destinatário (se contribuinte)
        if ind_ie == "1" and self.nf.ie_destinatario:
            self._add_element(dest, "IE", self.nf.ie_destinatario)
        
        # Email
        if self.nf.email_destinatario:
            self._add_element(dest, "email", self.nf.email_destinatario[:60])
    
    def _add_endereco_dest(self, parent):
        """Adiciona endereço do destinatário"""
        ender = etree.SubElement(parent, "enderDest")
        
        self._add_element(ender, "xLgr", (self.nf.logradouro or "")[:60])
        self._add_element(ender, "nro", self.nf.numero_endereco or "S/N")
        if self.nf.complemento:
            self._add_element(ender, "xCpl", self.nf.complemento[:60])
        self._add_element(ender, "xBairro", (self.nf.bairro or "")[:60])
        self._add_element(ender, "cMun", self.nf.codigo_municipio)
        self._add_element(ender, "xMun", (self.nf.cidade or "")[:60])
        self._add_element(ender, "UF", self.nf.uf)
        self._add_element(ender, "CEP", (self.nf.cep or "").replace("-", "").replace(".", ""))
        self._add_element(ender, "cPais", self.nf.codigo_pais or "1058")
        self._add_element(ender, "xPais", "Brasil")
    
    def _add_det(self, parent):
        """Adiciona grupo de detalhes (itens)"""
        for idx, item in enumerate(self.nf.itens, start=1):
            det = etree.SubElement(parent, "det")
            det.set("nItem", str(idx))
            
            # Produto
            self._add_prod(det, item)
            
            # Impostos
            self._add_imposto(det, item)
            
            # Informações adicionais do item
            if hasattr(item, 'informacoes_adicionais') and item.informacoes_adicionais:
                self._add_element(det, "infAdProd", item.informacoes_adicionais[:500])
    
    def _add_prod(self, parent, item):
        """Adiciona dados do produto"""
        prod = etree.SubElement(parent, "prod")
        
        # Código do produto
        self._add_element(prod, "cProd", (item.item_code or str(item.idx))[:60])
        
        # Código de barras (GTIN)
        self._add_element(prod, "cEAN", "SEM GTIN")
        
        # Descrição
        self._add_element(prod, "xProd", item.item_name[:120])
        
        # NCM
        self._add_element(prod, "NCM", item.ncm)
        
        # CEST (se houver)
        if item.cest:
            self._add_element(prod, "CEST", item.cest)
        
        # CFOP
        self._add_element(prod, "CFOP", item.cfop)
        
        # Unidade comercial
        self._add_element(prod, "uCom", item.unidade or "UN")
        
        # Quantidade comercial
        self._add_element(prod, "qCom", self._format_decimal(item.quantidade, 4))
        
        # Valor unitário comercial
        self._add_element(prod, "vUnCom", self._format_decimal(item.valor_unitario, 10))
        
        # Valor total bruto
        self._add_element(prod, "vProd", self._format_decimal(item.valor_total, 2))
        
        # Código de barras tributável
        self._add_element(prod, "cEANTrib", "SEM GTIN")
        
        # Unidade tributável
        self._add_element(prod, "uTrib", item.unidade or "UN")
        
        # Quantidade tributável
        self._add_element(prod, "qTrib", self._format_decimal(item.quantidade, 4))
        
        # Valor unitário tributável
        self._add_element(prod, "vUnTrib", self._format_decimal(item.valor_unitario, 10))
        
        # Valor do desconto
        if flt(item.valor_desconto) > 0:
            self._add_element(prod, "vDesc", self._format_decimal(item.valor_desconto, 2))
        
        # Indica se compõe valor total (0=Não, 1=Sim)
        self._add_element(prod, "indTot", "1")
    
    def _add_imposto(self, parent, item):
        """Adiciona grupo de impostos"""
        imposto = etree.SubElement(parent, "imposto")
        
        # Valor aproximado dos tributos (Lei da Transparência)
        valor_tributos = flt(item.valor_icms) + flt(item.valor_pis) + flt(item.valor_cofins) + flt(item.valor_ipi)
        if valor_tributos > 0:
            self._add_element(imposto, "vTotTrib", self._format_decimal(valor_tributos, 2))
        
        # ICMS
        self._add_icms(imposto, item)
        
        # IPI (apenas para NFe)
        if self.nf.modelo == "55":
            self._add_ipi(imposto, item)
        
        # PIS
        self._add_pis(imposto, item)
        
        # COFINS
        self._add_cofins(imposto, item)
    
    def _add_icms(self, parent, item):
        """Adiciona grupo ICMS"""
        icms = etree.SubElement(parent, "ICMS")
        
        # Verifica regime tributário
        regime = self.config.get_regime_codigo()
        
        if regime == "1":
            # Simples Nacional - ICMSSN
            self._add_icms_simples(icms, item)
        else:
            # Regime Normal
            self._add_icms_normal(icms, item)
    
    def _add_icms_simples(self, parent, item):
        """Adiciona ICMS para Simples Nacional"""
        csosn = item.cst_icms or "102"
        
        if csosn in ["101"]:
            icms = etree.SubElement(parent, "ICMSSN101")
            self._add_element(icms, "orig", item.origem or "0")
            self._add_element(icms, "CSOSN", csosn)
            self._add_element(icms, "pCredSN", self._format_decimal(item.aliquota_icms, 4))
            self._add_element(icms, "vCredICMSSN", self._format_decimal(item.valor_icms, 2))
        
        elif csosn in ["102", "103", "300", "400"]:
            icms = etree.SubElement(parent, "ICMSSN102")
            self._add_element(icms, "orig", item.origem or "0")
            self._add_element(icms, "CSOSN", csosn)
        
        elif csosn in ["201"]:
            icms = etree.SubElement(parent, "ICMSSN201")
            self._add_element(icms, "orig", item.origem or "0")
            self._add_element(icms, "CSOSN", csosn)
            self._add_element(icms, "modBCST", "4")
            self._add_element(icms, "pMVAST", "0.00")
            self._add_element(icms, "vBCST", self._format_decimal(item.base_icms_st, 2))
            self._add_element(icms, "pICMSST", self._format_decimal(item.aliquota_icms_st, 4))
            self._add_element(icms, "vICMSST", self._format_decimal(item.valor_icms_st, 2))
            self._add_element(icms, "pCredSN", self._format_decimal(item.aliquota_icms, 4))
            self._add_element(icms, "vCredICMSSN", self._format_decimal(item.valor_icms, 2))
        
        elif csosn in ["202", "203"]:
            icms = etree.SubElement(parent, "ICMSSN202")
            self._add_element(icms, "orig", item.origem or "0")
            self._add_element(icms, "CSOSN", csosn)
            self._add_element(icms, "modBCST", "4")
            self._add_element(icms, "vBCST", self._format_decimal(item.base_icms_st, 2))
            self._add_element(icms, "pICMSST", self._format_decimal(item.aliquota_icms_st, 4))
            self._add_element(icms, "vICMSST", self._format_decimal(item.valor_icms_st, 2))
        
        elif csosn in ["500"]:
            icms = etree.SubElement(parent, "ICMSSN500")
            self._add_element(icms, "orig", item.origem or "0")
            self._add_element(icms, "CSOSN", csosn)
        
        else:
            # CSOSN 900 - Outros
            icms = etree.SubElement(parent, "ICMSSN900")
            self._add_element(icms, "orig", item.origem or "0")
            self._add_element(icms, "CSOSN", "900")
            self._add_element(icms, "modBC", "3")
            self._add_element(icms, "vBC", self._format_decimal(item.base_icms, 2))
            self._add_element(icms, "pICMS", self._format_decimal(item.aliquota_icms, 4))
            self._add_element(icms, "vICMS", self._format_decimal(item.valor_icms, 2))
    
    def _add_icms_normal(self, parent, item):
        """Adiciona ICMS para Regime Normal"""
        cst = item.cst_icms or "00"
        
        if cst == "00":
            icms = etree.SubElement(parent, "ICMS00")
            self._add_element(icms, "orig", item.origem or "0")
            self._add_element(icms, "CST", cst)
            self._add_element(icms, "modBC", "3")
            self._add_element(icms, "vBC", self._format_decimal(item.base_icms, 2))
            self._add_element(icms, "pICMS", self._format_decimal(item.aliquota_icms, 4))
            self._add_element(icms, "vICMS", self._format_decimal(item.valor_icms, 2))
        
        elif cst in ["10", "30", "70", "90"]:
            icms = etree.SubElement(parent, f"ICMS{cst}")
            self._add_element(icms, "orig", item.origem or "0")
            self._add_element(icms, "CST", cst)
            self._add_element(icms, "modBC", "3")
            self._add_element(icms, "vBC", self._format_decimal(item.base_icms, 2))
            self._add_element(icms, "pICMS", self._format_decimal(item.aliquota_icms, 4))
            self._add_element(icms, "vICMS", self._format_decimal(item.valor_icms, 2))
            self._add_element(icms, "modBCST", "4")
            self._add_element(icms, "vBCST", self._format_decimal(item.base_icms_st, 2))
            self._add_element(icms, "pICMSST", self._format_decimal(item.aliquota_icms_st, 4))
            self._add_element(icms, "vICMSST", self._format_decimal(item.valor_icms_st, 2))
        
        elif cst == "20":
            icms = etree.SubElement(parent, "ICMS20")
            self._add_element(icms, "orig", item.origem or "0")
            self._add_element(icms, "CST", cst)
            self._add_element(icms, "modBC", "3")
            self._add_element(icms, "pRedBC", "0.00")
            self._add_element(icms, "vBC", self._format_decimal(item.base_icms, 2))
            self._add_element(icms, "pICMS", self._format_decimal(item.aliquota_icms, 4))
            self._add_element(icms, "vICMS", self._format_decimal(item.valor_icms, 2))
        
        elif cst in ["40", "41", "50"]:
            icms = etree.SubElement(parent, "ICMS40")
            self._add_element(icms, "orig", item.origem or "0")
            self._add_element(icms, "CST", cst)
        
        elif cst == "51":
            icms = etree.SubElement(parent, "ICMS51")
            self._add_element(icms, "orig", item.origem or "0")
            self._add_element(icms, "CST", cst)
            self._add_element(icms, "modBC", "3")
            self._add_element(icms, "vBC", self._format_decimal(item.base_icms, 2))
            self._add_element(icms, "pICMS", self._format_decimal(item.aliquota_icms, 4))
            self._add_element(icms, "vICMS", self._format_decimal(item.valor_icms, 2))
        
        elif cst == "60":
            icms = etree.SubElement(parent, "ICMS60")
            self._add_element(icms, "orig", item.origem or "0")
            self._add_element(icms, "CST", cst)
        
        else:
            # CST genérico
            icms = etree.SubElement(parent, "ICMS00")
            self._add_element(icms, "orig", item.origem or "0")
            self._add_element(icms, "CST", "00")
            self._add_element(icms, "modBC", "3")
            self._add_element(icms, "vBC", self._format_decimal(item.base_icms, 2))
            self._add_element(icms, "pICMS", self._format_decimal(item.aliquota_icms, 4))
            self._add_element(icms, "vICMS", self._format_decimal(item.valor_icms, 2))
    
    def _add_ipi(self, parent, item):
        """Adiciona grupo IPI"""
        ipi = etree.SubElement(parent, "IPI")
        
        # Código de enquadramento
        cEnq = getattr(item, 'codigo_enquadramento_ipi', None) or "999"
        self._add_element(ipi, "cEnq", cEnq)
        
        cst = getattr(item, 'cst_ipi', None) or "53"
        
        if cst in ["00", "49", "50", "99"]:
            ipi_trib = etree.SubElement(ipi, "IPITrib")
            self._add_element(ipi_trib, "CST", cst)
            self._add_element(ipi_trib, "vBC", self._format_decimal(item.base_ipi, 2))
            self._add_element(ipi_trib, "pIPI", self._format_decimal(item.aliquota_ipi, 4))
            self._add_element(ipi_trib, "vIPI", self._format_decimal(item.valor_ipi, 2))
        else:
            ipi_nt = etree.SubElement(ipi, "IPINT")
            self._add_element(ipi_nt, "CST", cst)
    
    def _add_pis(self, parent, item):
        """Adiciona grupo PIS"""
        pis = etree.SubElement(parent, "PIS")
        
        cst = item.cst_pis or "07"
        
        if cst in ["01", "02"]:
            pis_aliq = etree.SubElement(pis, "PISAliq")
            self._add_element(pis_aliq, "CST", cst)
            self._add_element(pis_aliq, "vBC", self._format_decimal(item.base_pis, 2))
            self._add_element(pis_aliq, "pPIS", self._format_decimal(item.aliquota_pis, 4))
            self._add_element(pis_aliq, "vPIS", self._format_decimal(item.valor_pis, 2))
        
        elif cst in ["03"]:
            pis_qtde = etree.SubElement(pis, "PISQtde")
            self._add_element(pis_qtde, "CST", cst)
            self._add_element(pis_qtde, "qBCProd", self._format_decimal(item.quantidade, 4))
            self._add_element(pis_qtde, "vAliqProd", self._format_decimal(item.aliquota_pis, 4))
            self._add_element(pis_qtde, "vPIS", self._format_decimal(item.valor_pis, 2))
        
        elif cst in ["04", "05", "06", "07", "08", "09"]:
            pis_nt = etree.SubElement(pis, "PISNT")
            self._add_element(pis_nt, "CST", cst)
        
        else:
            pis_outr = etree.SubElement(pis, "PISOutr")
            self._add_element(pis_outr, "CST", cst)
            self._add_element(pis_outr, "vBC", self._format_decimal(item.base_pis, 2))
            self._add_element(pis_outr, "pPIS", self._format_decimal(item.aliquota_pis, 4))
            self._add_element(pis_outr, "vPIS", self._format_decimal(item.valor_pis, 2))
    
    def _add_cofins(self, parent, item):
        """Adiciona grupo COFINS"""
        cofins = etree.SubElement(parent, "COFINS")
        
        cst = item.cst_cofins or "07"
        
        if cst in ["01", "02"]:
            cofins_aliq = etree.SubElement(cofins, "COFINSAliq")
            self._add_element(cofins_aliq, "CST", cst)
            self._add_element(cofins_aliq, "vBC", self._format_decimal(item.base_cofins, 2))
            self._add_element(cofins_aliq, "pCOFINS", self._format_decimal(item.aliquota_cofins, 4))
            self._add_element(cofins_aliq, "vCOFINS", self._format_decimal(item.valor_cofins, 2))
        
        elif cst in ["03"]:
            cofins_qtde = etree.SubElement(cofins, "COFINSQtde")
            self._add_element(cofins_qtde, "CST", cst)
            self._add_element(cofins_qtde, "qBCProd", self._format_decimal(item.quantidade, 4))
            self._add_element(cofins_qtde, "vAliqProd", self._format_decimal(item.aliquota_cofins, 4))
            self._add_element(cofins_qtde, "vCOFINS", self._format_decimal(item.valor_cofins, 2))
        
        elif cst in ["04", "05", "06", "07", "08", "09"]:
            cofins_nt = etree.SubElement(cofins, "COFINSNT")
            self._add_element(cofins_nt, "CST", cst)
        
        else:
            cofins_outr = etree.SubElement(cofins, "COFINSOutr")
            self._add_element(cofins_outr, "CST", cst)
            self._add_element(cofins_outr, "vBC", self._format_decimal(item.base_cofins, 2))
            self._add_element(cofins_outr, "pCOFINS", self._format_decimal(item.aliquota_cofins, 4))
            self._add_element(cofins_outr, "vCOFINS", self._format_decimal(item.valor_cofins, 2))
    
    def _add_total(self, parent):
        """Adiciona grupo de totais"""
        total = etree.SubElement(parent, "total")
        icms_tot = etree.SubElement(total, "ICMSTot")
        
        self._add_element(icms_tot, "vBC", self._format_decimal(self._sum_items("base_icms"), 2))
        self._add_element(icms_tot, "vICMS", self._format_decimal(self.nf.valor_icms, 2))
        self._add_element(icms_tot, "vICMSDeson", "0.00")
        self._add_element(icms_tot, "vFCPUFDest", "0.00")
        self._add_element(icms_tot, "vICMSUFDest", "0.00")
        self._add_element(icms_tot, "vICMSUFRemet", "0.00")
        self._add_element(icms_tot, "vFCP", "0.00")
        self._add_element(icms_tot, "vBCST", self._format_decimal(self._sum_items("base_icms_st"), 2))
        self._add_element(icms_tot, "vST", self._format_decimal(self.nf.valor_icms_st, 2))
        self._add_element(icms_tot, "vFCPST", "0.00")
        self._add_element(icms_tot, "vFCPSTRet", "0.00")
        self._add_element(icms_tot, "vProd", self._format_decimal(self.nf.valor_produtos, 2))
        self._add_element(icms_tot, "vFrete", self._format_decimal(self.nf.valor_frete, 2))
        self._add_element(icms_tot, "vSeg", self._format_decimal(self.nf.valor_seguro, 2))
        self._add_element(icms_tot, "vDesc", self._format_decimal(self.nf.valor_desconto, 2))
        self._add_element(icms_tot, "vII", "0.00")
        self._add_element(icms_tot, "vIPI", self._format_decimal(self.nf.valor_ipi, 2))
        self._add_element(icms_tot, "vIPIDevol", "0.00")
        self._add_element(icms_tot, "vPIS", self._format_decimal(self.nf.valor_pis, 2))
        self._add_element(icms_tot, "vCOFINS", self._format_decimal(self.nf.valor_cofins, 2))
        self._add_element(icms_tot, "vOutro", self._format_decimal(self.nf.valor_outras_despesas, 2))
        self._add_element(icms_tot, "vNF", self._format_decimal(self.nf.valor_total, 2))
        
        # Valor aproximado dos tributos
        valor_tributos = flt(self.nf.valor_icms) + flt(self.nf.valor_pis) + flt(self.nf.valor_cofins) + flt(self.nf.valor_ipi)
        self._add_element(icms_tot, "vTotTrib", self._format_decimal(valor_tributos, 2))
    
    def _add_transp(self, parent):
        """Adiciona grupo de transporte"""
        transp = etree.SubElement(parent, "transp")
        
        # Modalidade do frete
        mod_frete = self.nf.modalidade_frete.split(" - ")[0] if self.nf.modalidade_frete else "9"
        self._add_element(transp, "modFrete", mod_frete)
    
    def _add_pag(self, parent):
        """Adiciona grupo de pagamento"""
        pag = etree.SubElement(parent, "pag")
        det_pag = etree.SubElement(pag, "detPag")
        
        # Indicador de forma de pagamento
        self._add_element(det_pag, "indPag", "0")  # 0=À vista
        
        # Meio de pagamento
        self._add_element(det_pag, "tPag", "01")  # 01=Dinheiro
        
        # Valor do pagamento
        self._add_element(det_pag, "vPag", self._format_decimal(self.nf.valor_total, 2))
    
    def _add_inf_adic(self, parent):
        """Adiciona informações adicionais"""
        if self.nf.informacoes_complementares or self.nf.informacoes_fisco:
            inf_adic = etree.SubElement(parent, "infAdic")
            
            if self.nf.informacoes_fisco:
                self._add_element(inf_adic, "infAdFisco", self.nf.informacoes_fisco[:2000])
            
            if self.nf.informacoes_complementares:
                self._add_element(inf_adic, "infCpl", self.nf.informacoes_complementares[:5000])
    
    def _add_inf_nfe_supl(self, parent):
        """Adiciona informações suplementares para NFCe"""
        inf_supl = etree.SubElement(parent, "infNFeSupl")
        
        # URL do QR Code
        qrcode_url = self._generate_qrcode_url()
        self._add_element(inf_supl, "qrCode", f"<![CDATA[{qrcode_url}]]>")
        
        # URL de consulta
        url_consulta = self._get_url_consulta_nfce()
        self._add_element(inf_supl, "urlChave", url_consulta)
        
        self.nf.qrcode_url = qrcode_url
    
    def _generate_qrcode_url(self):
        """Gera URL do QR Code para NFCe"""
        # Formato: URL?chNFe=CHAVE&nVersao=100&tpAmb=X&cDest=CPF&dhEmi=HEX&vNF=VALOR&vICMS=VALOR&digVal=HEX&cIdToken=ID&cHashQRCode=HASH
        
        ambiente = self.config.get_ambiente_codigo()
        
        # URL base por UF
        urls_qrcode = {
            "SP": {
                "1": "https://www.nfce.fazenda.sp.gov.br/NFCeConsultaPublica/Paginas/ConsultaQRCode.aspx",
                "2": "https://www.homologacao.nfce.fazenda.sp.gov.br/NFCeConsultaPublica/Paginas/ConsultaQRCode.aspx"
            }
        }
        
        uf = self.config.uf_emissao
        url_base = urls_qrcode.get(uf, urls_qrcode["SP"]).get(ambiente)
        
        # Monta parâmetros
        params = f"?chNFe={self.nf.chave_acesso}"
        params += f"&nVersao=100"
        params += f"&tpAmb={ambiente}"
        
        return url_base + params
    
    def _get_url_consulta_nfce(self):
        """Retorna URL de consulta da NFCe"""
        ambiente = self.config.get_ambiente_codigo()
        
        urls = {
            "SP": {
                "1": "https://www.nfce.fazenda.sp.gov.br/NFCeConsultaPublica",
                "2": "https://www.homologacao.nfce.fazenda.sp.gov.br/NFCeConsultaPublica"
            }
        }
        
        uf = self.config.uf_emissao
        return urls.get(uf, urls["SP"]).get(ambiente)
    
    def _get_id_destino(self):
        """Determina o identificador de destino da operação"""
        uf_emit = self.config.uf_emissao
        uf_dest = self.nf.uf
        
        if not uf_dest:
            return "1"  # Interna
        
        if uf_emit == uf_dest:
            return "1"  # Operação interna
        elif uf_dest == "EX":
            return "3"  # Operação com exterior
        else:
            return "2"  # Operação interestadual
    
    def _sum_items(self, field):
        """Soma um campo de todos os itens"""
        return sum(flt(getattr(item, field, 0)) for item in self.nf.itens)
    
    def _add_element(self, parent, tag, text):
        """Adiciona um elemento ao XML"""
        elem = etree.SubElement(parent, tag)
        elem.text = str(text) if text is not None else ""
        return elem
    
    def _format_decimal(self, value, decimals=2):
        """Formata um valor decimal"""
        return f"{flt(value):.{decimals}f}"
