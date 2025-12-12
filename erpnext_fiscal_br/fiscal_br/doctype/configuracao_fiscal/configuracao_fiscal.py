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
