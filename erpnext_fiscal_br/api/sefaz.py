"""
API para comunicação com a SEFAZ
"""

import frappe
from frappe import _


@frappe.whitelist()
def consultar_status(empresa):
    """
    Consulta status do serviço da SEFAZ
    
    Args:
        empresa: Nome da empresa
    
    Returns:
        dict: Status do serviço
    """
    from erpnext_fiscal_br.services.transmitter import SEFAZTransmitter
    
    try:
        transmitter = SEFAZTransmitter(empresa)
        resultado = transmitter.consultar_status_servico()
        
        return {
            "success": resultado.get("cStat") == "107",
            "codigo": resultado.get("cStat"),
            "mensagem": resultado.get("xMotivo"),
            "uf": resultado.get("cUF"),
            "ambiente": resultado.get("tpAmb")
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def consultar_nfe(empresa, chave_acesso):
    """
    Consulta uma NFe pela chave de acesso
    
    Args:
        empresa: Nome da empresa
        chave_acesso: Chave de acesso da NFe (44 dígitos)
    
    Returns:
        dict: Dados da NFe
    """
    from erpnext_fiscal_br.services.transmitter import SEFAZTransmitter
    from erpnext_fiscal_br.utils.cnpj_cpf import validar_chave_nfe
    
    # Valida chave
    if not validar_chave_nfe(chave_acesso):
        return {
            "success": False,
            "error": _("Chave de acesso inválida")
        }
    
    try:
        transmitter = SEFAZTransmitter(empresa)
        resultado = transmitter.consultar_nfe(chave_acesso)
        
        return {
            "success": resultado.get("cStat") in ["100", "101", "110"],
            "codigo": resultado.get("cStat"),
            "mensagem": resultado.get("xMotivo"),
            "protocolo": resultado.get("nProt"),
            "data_autorizacao": resultado.get("dhRecbto"),
            "chave": resultado.get("chNFe")
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def consultar_cadastro(empresa, uf, documento):
    """
    Consulta cadastro de contribuinte na SEFAZ
    
    Args:
        empresa: Nome da empresa (para usar o certificado)
        uf: UF do contribuinte
        documento: CNPJ ou IE do contribuinte
    
    Returns:
        dict: Dados cadastrais
    """
    # Implementação futura
    return {
        "success": False,
        "error": _("Funcionalidade não implementada")
    }


@frappe.whitelist()
def download_nfe(empresa, chave_acesso):
    """
    Faz download de uma NFe pela chave de acesso
    
    Args:
        empresa: Nome da empresa
        chave_acesso: Chave de acesso da NFe
    
    Returns:
        dict: XML da NFe
    """
    # Implementação futura - requer manifestação do destinatário
    return {
        "success": False,
        "error": _("Funcionalidade não implementada")
    }


@frappe.whitelist()
def get_ambiente_info(empresa):
    """
    Retorna informações do ambiente configurado
    
    Args:
        empresa: Nome da empresa
    
    Returns:
        dict: Informações do ambiente
    """
    from erpnext_fiscal_br.fiscal_br.doctype.configuracao_fiscal.configuracao_fiscal import ConfiguracaoFiscal
    from erpnext_fiscal_br.fiscal_br.doctype.certificado_digital.certificado_digital import CertificadoDigital
    
    config = ConfiguracaoFiscal.get_config_for_company(empresa)
    cert = CertificadoDigital.get_valid_certificate(empresa)
    
    if not config:
        return {
            "success": False,
            "error": _("Configuração fiscal não encontrada")
        }
    
    return {
        "success": True,
        "empresa": empresa,
        "cnpj": config.cnpj,
        "inscricao_estadual": config.inscricao_estadual,
        "regime_tributario": config.regime_tributario,
        "ambiente": config.ambiente,
        "uf_emissao": config.uf_emissao,
        "serie_nfe": config.serie_nfe,
        "proximo_numero_nfe": config.proximo_numero_nfe,
        "serie_nfce": config.serie_nfce,
        "proximo_numero_nfce": config.proximo_numero_nfce,
        "certificado": {
            "status": cert.status if cert else "Não encontrado",
            "validade": str(cert.validade_fim) if cert else None,
            "dias_para_expirar": cert.dias_para_expirar if cert else None
        } if cert else None
    }
