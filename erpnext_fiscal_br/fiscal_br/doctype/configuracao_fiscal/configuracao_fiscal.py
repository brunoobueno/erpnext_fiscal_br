"""
Configuração Fiscal por Empresa
Gerencia as configurações fiscais para emissão de NFe/NFCe
"""

import frappe
from frappe import _
from frappe.model.document import Document

from erpnext_fiscal_br.utils.cnpj_cpf import validar_cnpj, formatar_cnpj


class ConfiguracaoFiscal(Document):
    def validate(self):
        self.validar_cnpj()
        self.validar_inscricao_estadual()
        self.validar_codigos_ibge()
        self.validar_numeracao()
        self.calcular_aliquota_simples()
    
    def validar_cnpj(self):
        """Valida o CNPJ da empresa"""
        if self.cnpj:
            # Remove formatação
            cnpj_limpo = "".join(filter(str.isdigit, self.cnpj))
            
            if not validar_cnpj(cnpj_limpo):
                frappe.throw(_("CNPJ inválido: {0}").format(self.cnpj))
            
            # Armazena apenas números
            self.cnpj = cnpj_limpo
    
    def validar_inscricao_estadual(self):
        """Valida a Inscrição Estadual"""
        if self.inscricao_estadual:
            # Remove formatação
            ie_limpa = "".join(filter(str.isdigit, self.inscricao_estadual))
            self.inscricao_estadual = ie_limpa
    
    def validar_codigos_ibge(self):
        """Valida os códigos IBGE"""
        if self.codigo_uf:
            if len(self.codigo_uf) != 2:
                frappe.throw(_("Código UF deve ter 2 dígitos"))
        
        if self.codigo_municipio:
            if len(self.codigo_municipio) != 7:
                frappe.throw(_("Código do município deve ter 7 dígitos"))
    
    def validar_numeracao(self):
        """Valida a numeração das notas"""
        if self.proximo_numero_nfe and self.proximo_numero_nfe < 1:
            frappe.throw(_("Próximo número NFe deve ser maior que zero"))
        
        if self.proximo_numero_nfce and self.proximo_numero_nfce < 1:
            frappe.throw(_("Próximo número NFCe deve ser maior que zero"))
    
    def calcular_aliquota_simples(self):
        """Calcula a alíquota efetiva do Simples Nacional"""
        if not self.regime_tributario or "Simples Nacional" not in self.regime_tributario:
            return
        
        if not self.anexo_simples or not self.faixa_simples or not self.rbt12:
            return
        
        # Tabela de alíquotas do Simples Nacional (LC 123/2006)
        # Formato: {anexo: {faixa: (aliquota_nominal, parcela_deduzir)}}
        tabela_simples = {
            "Anexo I - Comércio": {
                "1ª Faixa": (4.0, 0),
                "2ª Faixa": (7.3, 5940),
                "3ª Faixa": (9.5, 13860),
                "4ª Faixa": (10.7, 22500),
                "5ª Faixa": (14.3, 87300),
                "6ª Faixa": (19.0, 378000),
            },
            "Anexo II - Indústria": {
                "1ª Faixa": (4.5, 0),
                "2ª Faixa": (7.8, 5940),
                "3ª Faixa": (10.0, 13860),
                "4ª Faixa": (11.2, 22500),
                "5ª Faixa": (14.7, 85500),
                "6ª Faixa": (30.0, 720000),
            },
            "Anexo III - Serviços": {
                "1ª Faixa": (6.0, 0),
                "2ª Faixa": (11.2, 9360),
                "3ª Faixa": (13.5, 17640),
                "4ª Faixa": (16.0, 35640),
                "5ª Faixa": (21.0, 125640),
                "6ª Faixa": (33.0, 648000),
            },
            "Anexo IV - Serviços": {
                "1ª Faixa": (4.5, 0),
                "2ª Faixa": (9.0, 8100),
                "3ª Faixa": (10.2, 12420),
                "4ª Faixa": (14.0, 39780),
                "5ª Faixa": (22.0, 183780),
                "6ª Faixa": (33.0, 828000),
            },
            "Anexo V - Serviços": {
                "1ª Faixa": (15.5, 0),
                "2ª Faixa": (18.0, 4500),
                "3ª Faixa": (19.5, 9900),
                "4ª Faixa": (20.5, 17100),
                "5ª Faixa": (23.0, 62100),
                "6ª Faixa": (30.5, 540000),
            },
        }
        
        anexo = self.anexo_simples
        faixa = self.faixa_simples.split(" - ")[0] if self.faixa_simples else None
        
        if anexo in tabela_simples and faixa in tabela_simples[anexo]:
            aliq_nominal, parcela_deduzir = tabela_simples[anexo][faixa]
            rbt12 = float(self.rbt12 or 0)
            
            if rbt12 > 0:
                # Fórmula: [(RBT12 × Aliq) - PD] / RBT12
                aliquota_efetiva = ((rbt12 * aliq_nominal / 100) - parcela_deduzir) / rbt12 * 100
                self.aliquota_simples = max(0, aliquota_efetiva)
            else:
                self.aliquota_simples = aliq_nominal
    
    def get_crt_codigo(self):
        """Retorna o código CRT (Código de Regime Tributário) para NFe"""
        if not self.regime_tributario:
            return "1"
        
        regime = self.regime_tributario.split(" - ")[0]
        # CRT: 1=Simples Nacional, 2=Simples Nacional Excesso, 3=Regime Normal
        if regime == "1":
            return "1"  # Simples Nacional
        elif regime == "2":
            return "2"  # Simples Nacional - Excesso de sublimite
        else:
            return "3"  # Regime Normal (Lucro Real, Presumido, Arbitrado)
    
    def get_proximo_numero(self, modelo="55"):
        """
        Retorna e incrementa o próximo número da nota
        
        Args:
            modelo: "55" para NFe, "65" para NFCe
        
        Returns:
            int: Próximo número disponível
        """
        if modelo == "55":
            numero = self.proximo_numero_nfe
            self.proximo_numero_nfe += 1
        else:
            numero = self.proximo_numero_nfce
            self.proximo_numero_nfce += 1
        
        self.save(ignore_permissions=True)
        return numero
    
    def get_serie(self, modelo="55"):
        """
        Retorna a série para o modelo especificado
        
        Args:
            modelo: "55" para NFe, "65" para NFCe
        
        Returns:
            int: Série da nota
        """
        if modelo == "55":
            return self.serie_nfe
        return self.serie_nfce
    
    def get_ambiente_codigo(self):
        """Retorna o código do ambiente (1=Produção, 2=Homologação)"""
        if self.ambiente:
            return self.ambiente.split(" - ")[0]
        return "2"
    
    def get_regime_codigo(self):
        """Retorna o código do regime tributário"""
        if self.regime_tributario:
            return self.regime_tributario.split(" - ")[0]
        return "1"
    
    @staticmethod
    def get_config_for_company(company):
        """
        Retorna a configuração fiscal para uma empresa
        
        Args:
            company: Nome da empresa
        
        Returns:
            ConfiguracaoFiscal: Documento de configuração ou None
        """
        config_name = frappe.db.get_value(
            "Configuracao Fiscal",
            {"empresa": company},
            "name"
        )
        
        if config_name:
            return frappe.get_doc("Configuracao Fiscal", config_name)
        
        return None


@frappe.whitelist()
def get_configuracao_fiscal(empresa):
    """
    API para obter configuração fiscal de uma empresa
    
    Args:
        empresa: Nome da empresa
    
    Returns:
        dict: Dados da configuração fiscal ou None se não encontrada
    """
    config = ConfiguracaoFiscal.get_config_for_company(empresa)
    
    if not config:
        return None
    
    return {
        "cnpj": config.cnpj,
        "inscricao_estadual": config.inscricao_estadual,
        "regime_tributario": config.regime_tributario,
        "ambiente": config.ambiente,
        "uf_emissao": config.uf_emissao,
        "serie_nfe": config.serie_nfe,
        "serie_nfce": config.serie_nfce,
        "proximo_numero_nfe": config.proximo_numero_nfe,
        "proximo_numero_nfce": config.proximo_numero_nfce,
    }
