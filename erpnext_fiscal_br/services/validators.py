"""
Validators - Validações de dados fiscais
"""

import frappe
from frappe import _
from frappe.utils import flt

from erpnext_fiscal_br.utils.cnpj_cpf import (
    validar_cpf, validar_cnpj, validar_ncm, validar_cest,
    validar_chave_nfe, validar_inscricao_estadual
)


class NFValidator:
    """Validador de Nota Fiscal"""
    
    def __init__(self, nota_fiscal):
        """
        Inicializa o validador
        
        Args:
            nota_fiscal: Documento Nota Fiscal
        """
        self.nf = nota_fiscal
        self.errors = []
        self.warnings = []
    
    def validate(self):
        """
        Executa todas as validações
        
        Returns:
            tuple: (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        self._validate_empresa()
        self._validate_destinatario()
        self._validate_endereco()
        self._validate_itens()
        self._validate_totais()
        self._validate_impostos()
        
        return len(self.errors) == 0, self.errors, self.warnings
    
    def _validate_empresa(self):
        """Valida dados da empresa emitente"""
        from erpnext_fiscal_br.fiscal_br.doctype.configuracao_fiscal.configuracao_fiscal import ConfiguracaoFiscal
        from erpnext_fiscal_br.fiscal_br.doctype.certificado_digital.certificado_digital import CertificadoDigital
        
        # Configuração fiscal
        config = ConfiguracaoFiscal.get_config_for_company(self.nf.empresa)
        if not config:
            self.errors.append(_("Configuração fiscal não encontrada para a empresa"))
            return
        
        # CNPJ
        if not config.cnpj:
            self.errors.append(_("CNPJ da empresa não configurado"))
        elif not validar_cnpj(config.cnpj):
            self.errors.append(_("CNPJ da empresa inválido"))
        
        # IE
        if not config.inscricao_estadual:
            self.errors.append(_("Inscrição Estadual da empresa não configurada"))
        
        # Códigos IBGE
        if not config.codigo_uf or len(config.codigo_uf) != 2:
            self.errors.append(_("Código UF da empresa inválido"))
        
        if not config.codigo_municipio or len(config.codigo_municipio) != 7:
            self.errors.append(_("Código do município da empresa inválido"))
        
        # Certificado digital
        cert = CertificadoDigital.get_valid_certificate(self.nf.empresa)
        if not cert:
            self.errors.append(_("Certificado digital válido não encontrado"))
        elif cert.status == "Expirando":
            self.warnings.append(_("Certificado digital expirando em {0} dias").format(cert.dias_para_expirar))
    
    def _validate_destinatario(self):
        """Valida dados do destinatário"""
        # Nome
        if not self.nf.cliente_nome:
            self.errors.append(_("Nome do destinatário é obrigatório"))
        elif len(self.nf.cliente_nome) < 2:
            self.errors.append(_("Nome do destinatário muito curto"))
        
        # CPF/CNPJ
        if not self.nf.cpf_cnpj_destinatario:
            # Para NFCe, CPF é opcional
            if self.nf.modelo == "55":
                self.errors.append(_("CPF/CNPJ do destinatário é obrigatório para NFe"))
        else:
            doc = self.nf.cpf_cnpj_destinatario.replace(".", "").replace("-", "").replace("/", "")
            
            if len(doc) == 11:
                if not validar_cpf(doc):
                    self.errors.append(_("CPF do destinatário inválido"))
            elif len(doc) == 14:
                if not validar_cnpj(doc):
                    self.errors.append(_("CNPJ do destinatário inválido"))
            else:
                self.errors.append(_("CPF/CNPJ do destinatário deve ter 11 ou 14 dígitos"))
        
        # IE do destinatário
        if self.nf.contribuinte_icms and "1" in self.nf.contribuinte_icms:
            if not self.nf.ie_destinatario:
                self.errors.append(_("IE do destinatário é obrigatória para contribuinte ICMS"))
            elif self.nf.uf and not validar_inscricao_estadual(self.nf.ie_destinatario, self.nf.uf):
                self.warnings.append(_("IE do destinatário pode estar inválida"))
    
    def _validate_endereco(self):
        """Valida endereço do destinatário"""
        # Campos obrigatórios
        campos_obrigatorios = [
            ("logradouro", "Logradouro"),
            ("numero_endereco", "Número"),
            ("bairro", "Bairro"),
            ("cidade", "Cidade"),
            ("uf", "UF"),
            ("cep", "CEP"),
            ("codigo_municipio", "Código do município"),
        ]
        
        for campo, label in campos_obrigatorios:
            if not getattr(self.nf, campo, None):
                self.errors.append(_("{0} do destinatário é obrigatório").format(label))
        
        # CEP
        if self.nf.cep:
            cep = self.nf.cep.replace("-", "").replace(".", "")
            if len(cep) != 8:
                self.errors.append(_("CEP deve ter 8 dígitos"))
        
        # Código do município
        if self.nf.codigo_municipio:
            if len(self.nf.codigo_municipio) != 7:
                self.errors.append(_("Código do município deve ter 7 dígitos"))
        
        # UF
        ufs_validas = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
                       "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
                       "RS", "RO", "RR", "SC", "SP", "SE", "TO"]
        if self.nf.uf and self.nf.uf.upper() not in ufs_validas:
            self.errors.append(_("UF inválida: {0}").format(self.nf.uf))
    
    def _validate_itens(self):
        """Valida itens da nota"""
        if not self.nf.itens or len(self.nf.itens) == 0:
            self.errors.append(_("A nota deve ter pelo menos um item"))
            return
        
        if len(self.nf.itens) > 990:
            self.errors.append(_("Máximo de 990 itens por nota"))
        
        for idx, item in enumerate(self.nf.itens, 1):
            prefix = f"Item {idx}: "
            
            # Descrição
            if not item.item_name:
                self.errors.append(prefix + _("Descrição é obrigatória"))
            elif len(item.item_name) < 1:
                self.errors.append(prefix + _("Descrição muito curta"))
            
            # NCM
            if not item.ncm:
                self.errors.append(prefix + _("NCM é obrigatório"))
            elif not validar_ncm(item.ncm):
                self.errors.append(prefix + _("NCM deve ter 8 dígitos"))
            
            # CEST
            if item.cest and not validar_cest(item.cest):
                self.errors.append(prefix + _("CEST deve ter 7 dígitos"))
            
            # CFOP
            if not item.cfop:
                self.errors.append(prefix + _("CFOP é obrigatório"))
            elif len(str(item.cfop)) != 4:
                self.errors.append(prefix + _("CFOP deve ter 4 dígitos"))
            
            # Quantidade
            if not item.quantidade or flt(item.quantidade) <= 0:
                self.errors.append(prefix + _("Quantidade deve ser maior que zero"))
            
            # Valor unitário
            if flt(item.valor_unitario) < 0:
                self.errors.append(prefix + _("Valor unitário não pode ser negativo"))
            
            # Valor total
            if flt(item.valor_total) <= 0:
                self.errors.append(prefix + _("Valor total deve ser maior que zero"))
            
            # Verifica consistência do valor total
            valor_calculado = flt(item.quantidade) * flt(item.valor_unitario)
            if abs(valor_calculado - flt(item.valor_total)) > 0.01:
                self.warnings.append(prefix + _("Valor total difere do calculado (qtd x valor unit)"))
            
            # CST/CSOSN ICMS
            if not item.cst_icms:
                self.errors.append(prefix + _("CST/CSOSN ICMS é obrigatório"))
    
    def _validate_totais(self):
        """Valida totais da nota"""
        # Valor total
        if flt(self.nf.valor_total) <= 0:
            self.errors.append(_("Valor total da nota deve ser maior que zero"))
        
        # Soma dos itens
        soma_itens = sum(flt(item.valor_total) for item in self.nf.itens)
        if abs(soma_itens - flt(self.nf.valor_produtos)) > 0.01:
            self.warnings.append(_("Soma dos itens difere do valor de produtos"))
        
        # Valor total calculado
        valor_calculado = (
            flt(self.nf.valor_produtos)
            + flt(self.nf.valor_frete)
            + flt(self.nf.valor_seguro)
            + flt(self.nf.valor_outras_despesas)
            + flt(self.nf.valor_ipi)
            + flt(self.nf.valor_icms_st)
            - flt(self.nf.valor_desconto)
        )
        
        if abs(valor_calculado - flt(self.nf.valor_total)) > 0.01:
            self.warnings.append(_("Valor total difere do calculado"))
    
    def _validate_impostos(self):
        """Valida impostos"""
        for idx, item in enumerate(self.nf.itens, 1):
            prefix = f"Item {idx}: "
            
            # ICMS
            if flt(item.aliquota_icms) > 0 and flt(item.base_icms) <= 0:
                self.warnings.append(prefix + _("Alíquota ICMS informada mas base é zero"))
            
            if flt(item.valor_icms) > 0:
                valor_calculado = flt(item.base_icms) * flt(item.aliquota_icms) / 100
                if abs(valor_calculado - flt(item.valor_icms)) > 0.01:
                    self.warnings.append(prefix + _("Valor ICMS difere do calculado"))
            
            # PIS
            if flt(item.aliquota_pis) > 0 and flt(item.base_pis) <= 0:
                self.warnings.append(prefix + _("Alíquota PIS informada mas base é zero"))
            
            # COFINS
            if flt(item.aliquota_cofins) > 0 and flt(item.base_cofins) <= 0:
                self.warnings.append(prefix + _("Alíquota COFINS informada mas base é zero"))


def validar_nota_fiscal(nota_fiscal_name):
    """
    Valida uma nota fiscal
    
    Args:
        nota_fiscal_name: Nome do documento Nota Fiscal
    
    Returns:
        dict: Resultado da validação
    """
    nf = frappe.get_doc("Nota Fiscal", nota_fiscal_name)
    validator = NFValidator(nf)
    is_valid, errors, warnings = validator.validate()
    
    return {
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings
    }


@frappe.whitelist()
def validate_sales_invoice_for_nfe(sales_invoice):
    """
    Valida se uma Sales Invoice pode gerar NFe
    
    Args:
        sales_invoice: Nome da Sales Invoice
    
    Returns:
        dict: Resultado da validação
    """
    errors = []
    warnings = []
    
    invoice = frappe.get_doc("Sales Invoice", sales_invoice)
    
    # Verifica se já tem NFe
    if invoice.get("nota_fiscal"):
        errors.append(_("Esta fatura já possui uma Nota Fiscal vinculada"))
    
    # Verifica status
    if invoice.docstatus != 1:
        errors.append(_("A fatura deve estar submetida"))
    
    # Verifica empresa
    if not invoice.company:
        errors.append(_("Empresa não informada"))
    else:
        from erpnext_fiscal_br.fiscal_br.doctype.configuracao_fiscal.configuracao_fiscal import ConfiguracaoFiscal
        config = ConfiguracaoFiscal.get_config_for_company(invoice.company)
        if not config:
            errors.append(_("Configuração fiscal não encontrada para a empresa"))
    
    # Verifica cliente
    if not invoice.customer:
        errors.append(_("Cliente não informado"))
    else:
        customer = frappe.get_doc("Customer", invoice.customer)
        if not customer.get("cpf_cnpj"):
            warnings.append(_("CPF/CNPJ do cliente não informado"))
    
    # Verifica itens
    for item in invoice.items:
        item_doc = frappe.get_doc("Item", item.item_code)
        if not item_doc.get("ncm"):
            errors.append(_("Item {0} não possui NCM configurado").format(item.item_code))
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }
