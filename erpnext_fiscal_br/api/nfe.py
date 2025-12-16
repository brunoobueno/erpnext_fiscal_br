"""
API para emissão de NFe
"""

import frappe
from frappe import _
from frappe.utils import flt, now_datetime

from erpnext_fiscal_br.utils.tax_tables import get_cfop, get_cst_icms, get_cst_pis_cofins, get_aliquotas_pis_cofins
from erpnext_fiscal_br.utils.ibge import get_codigo_uf, get_codigo_municipio


@frappe.whitelist()
def get_invoices_from_sales_order(sales_order):
    """
    Retorna as faturas vinculadas a um pedido de venda
    Esta função é whitelisted para evitar problemas de permissão no frontend
    """
    invoices = frappe.db.sql("""
        SELECT DISTINCT si.name, si.nota_fiscal, si.status_fiscal
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        WHERE sii.sales_order = %s AND si.docstatus = 1
    """, sales_order, as_dict=True)
    
    return invoices


@frappe.whitelist()
def criar_nfe_from_sales_invoice(sales_invoice, modelo="55"):
    """
    Cria uma Nota Fiscal a partir de uma Sales Invoice
    
    Args:
        sales_invoice: Nome da Sales Invoice
        modelo: "55" para NFe, "65" para NFCe
    
    Returns:
        dict: Dados da nota fiscal criada
    """
    # Valida
    from erpnext_fiscal_br.services.validators import validate_sales_invoice_for_nfe
    validation = validate_sales_invoice_for_nfe(sales_invoice)
    
    if not validation["valid"]:
        return {
            "success": False,
            "errors": validation["errors"]
        }
    
    # Carrega documentos
    invoice = frappe.get_doc("Sales Invoice", sales_invoice)
    customer = frappe.get_doc("Customer", invoice.customer)
    
    # Obtém configuração fiscal
    from erpnext_fiscal_br.fiscal_br.doctype.configuracao_fiscal.configuracao_fiscal import ConfiguracaoFiscal
    config = ConfiguracaoFiscal.get_config_for_company(invoice.company)
    
    # Obtém endereço do cliente
    endereco = _get_customer_address(invoice)
    
    # Cria nota fiscal
    nf = frappe.new_doc("Nota Fiscal")
    nf.modelo = modelo
    nf.empresa = invoice.company
    nf.sales_invoice = invoice.name
    
    # Dados do destinatário
    nf.cliente = invoice.customer
    nf.cliente_nome = customer.customer_name
    nf.cpf_cnpj_destinatario = customer.get("cpf_cnpj", "")
    nf.ie_destinatario = customer.get("inscricao_estadual_cliente", "")
    nf.contribuinte_icms = customer.get("contribuinte_icms", "9 - Não Contribuinte")
    nf.email_destinatario = customer.get("email_nfe", "")
    
    # Endereço
    if endereco:
        nf.endereco_destinatario = endereco.name
        nf.logradouro = endereco.address_line1 or ""
        nf.numero_endereco = endereco.get("numero_endereco", "S/N")
        nf.complemento = endereco.get("complemento", "")
        nf.bairro = endereco.get("bairro", endereco.city or "")
        nf.cidade = endereco.city or ""
        nf.uf = endereco.state or ""
        nf.cep = (endereco.pincode or "").replace("-", "")
        nf.codigo_municipio = endereco.get("codigo_municipio_ibge", "")
        
        # Se não tem código IBGE, tenta buscar
        if not nf.codigo_municipio and nf.cidade and nf.uf:
            nf.codigo_municipio = get_codigo_municipio(nf.cidade, nf.uf) or ""
    
    # Valores
    nf.valor_produtos = invoice.total
    nf.valor_desconto = invoice.discount_amount or 0
    nf.valor_frete = 0
    nf.valor_seguro = 0
    nf.valor_outras_despesas = 0
    nf.valor_total = invoice.grand_total
    
    # Natureza da operação
    nf.natureza_operacao = "Venda de mercadoria"
    nf.finalidade = "1 - NF-e normal"
    nf.tipo_operacao = "1 - Saída"
    
    # Itens
    regime = config.get_regime_codigo() if config else "1"
    uf_emit = config.uf_emissao if config else "SP"
    uf_dest = nf.uf or uf_emit
    
    for item in invoice.items:
        item_doc = frappe.get_doc("Item", item.item_code)
        
        nf_item = nf.append("itens", {})
        nf_item.item_code = item.item_code
        nf_item.item_name = item.item_name or item_doc.item_name
        nf_item.ncm = item_doc.get("ncm", "00000000")
        nf_item.cest = item_doc.get("cest", "")
        nf_item.origem = (item_doc.get("origem", "0 - Nacional") or "0").split(" - ")[0]
        
        # CFOP
        cfop_interno = item_doc.get("cfop_venda_interna", "5102")
        cfop_interestadual = item_doc.get("cfop_venda_interestadual", "6102")
        nf_item.cfop = cfop_interno if uf_emit == uf_dest else cfop_interestadual
        
        nf_item.unidade = item_doc.get("unidade_tributavel", item.uom or "UN")
        nf_item.quantidade = item.qty
        nf_item.valor_unitario = item.rate
        nf_item.valor_total = item.amount
        nf_item.valor_desconto = item.discount_amount or 0
        
        # Impostos
        _calcular_impostos_item(nf_item, regime, uf_emit, uf_dest)
    
    # Calcula totais de impostos
    nf.calcular_totais()
    
    # Salva
    nf.insert(ignore_permissions=True)
    
    return {
        "success": True,
        "nota_fiscal": nf.name,
        "numero": nf.numero,
        "serie": nf.serie,
        "warnings": validation.get("warnings", [])
    }


@frappe.whitelist()
def emitir_nfe(nota_fiscal):
    """
    Emite uma NFe para a SEFAZ
    
    Args:
        nota_fiscal: Nome da Nota Fiscal
    
    Returns:
        dict: Resultado da emissão
    """
    nf = frappe.get_doc("Nota Fiscal", nota_fiscal)
    
    # Valida
    from erpnext_fiscal_br.services.validators import NFValidator
    validator = NFValidator(nf)
    is_valid, errors, warnings = validator.validate()
    
    if not is_valid:
        return {
            "success": False,
            "errors": errors
        }
    
    try:
        nf.emitir()
        
        return {
            "success": nf.status == "Autorizada",
            "status": nf.status,
            "chave_acesso": nf.chave_acesso,
            "protocolo": nf.protocolo_autorizacao,
            "mensagem": nf.mensagem_sefaz,
            "danfe": nf.danfe,
            "warnings": warnings
        }
    except Exception as e:
        frappe.log_error(f"Erro ao emitir NFe: {str(e)}")
        return {
            "success": False,
            "errors": [str(e)]
        }


@frappe.whitelist()
def emitir_nfe_from_invoice(sales_invoice, modelo="55"):
    """
    Cria e emite NFe a partir de uma Sales Invoice em uma única operação
    
    Args:
        sales_invoice: Nome da Sales Invoice
        modelo: "55" para NFe, "65" para NFCe
    
    Returns:
        dict: Resultado da emissão
    """
    # Cria a nota
    result = criar_nfe_from_sales_invoice(sales_invoice, modelo)
    
    if not result.get("success"):
        return result
    
    # Emite
    return emitir_nfe(result["nota_fiscal"])


def _get_customer_address(invoice):
    """Obtém endereço do cliente da fatura"""
    # Tenta endereço da fatura
    if invoice.customer_address:
        return frappe.get_doc("Address", invoice.customer_address)
    
    # Tenta endereço de cobrança
    if invoice.get("billing_address"):
        return frappe.get_doc("Address", invoice.billing_address)
    
    # Busca endereço padrão do cliente
    addresses = frappe.get_all(
        "Dynamic Link",
        filters={
            "link_doctype": "Customer",
            "link_name": invoice.customer,
            "parenttype": "Address"
        },
        fields=["parent"]
    )
    
    if addresses:
        return frappe.get_doc("Address", addresses[0].parent)
    
    return None


def _calcular_impostos_item(item, regime, uf_origem, uf_destino):
    """Calcula impostos do item baseado no regime tributário"""
    from erpnext_fiscal_br.utils.tax_tables import get_aliquota_icms
    
    # CST/CSOSN ICMS
    item.cst_icms = get_cst_icms(regime)
    
    # Base e alíquota ICMS
    if regime in ["1", "simples"]:
        # Simples Nacional - não destaca ICMS
        item.base_icms = 0
        item.aliquota_icms = 0
        item.valor_icms = 0
    else:
        # Regime Normal
        item.base_icms = flt(item.valor_total)
        item.aliquota_icms = get_aliquota_icms(uf_origem, uf_destino)
        item.valor_icms = flt(item.base_icms) * flt(item.aliquota_icms) / 100
    
    # ICMS ST (simplificado - sem ST)
    item.base_icms_st = 0
    item.aliquota_icms_st = 0
    item.valor_icms_st = 0
    
    # IPI (simplificado - sem IPI para comércio)
    item.cst_ipi = "53"  # Saída não tributada
    item.base_ipi = 0
    item.aliquota_ipi = 0
    item.valor_ipi = 0
    
    # PIS/COFINS
    item.cst_pis = get_cst_pis_cofins(regime)
    item.cst_cofins = get_cst_pis_cofins(regime)
    
    aliq_pis, aliq_cofins = get_aliquotas_pis_cofins(regime)
    
    if regime in ["1", "simples"]:
        # Simples não destaca PIS/COFINS
        item.base_pis = 0
        item.aliquota_pis = 0
        item.valor_pis = 0
        item.base_cofins = 0
        item.aliquota_cofins = 0
        item.valor_cofins = 0
    else:
        item.base_pis = flt(item.valor_total)
        item.aliquota_pis = aliq_pis
        item.valor_pis = flt(item.base_pis) * aliq_pis / 100
        
        item.base_cofins = flt(item.valor_total)
        item.aliquota_cofins = aliq_cofins
        item.valor_cofins = flt(item.base_cofins) * aliq_cofins / 100


@frappe.whitelist()
def get_dados_from_sales_invoice(sales_invoice):
    """
    Retorna dados da Sales Invoice para preencher a Nota Fiscal
    
    Args:
        sales_invoice: Nome da Sales Invoice
    
    Returns:
        dict: Dados para preencher a nota fiscal
    """
    invoice = frappe.get_doc("Sales Invoice", sales_invoice)
    customer = frappe.get_doc("Customer", invoice.customer)
    
    # Obtém configuração fiscal
    from erpnext_fiscal_br.fiscal_br.doctype.configuracao_fiscal.configuracao_fiscal import ConfiguracaoFiscal
    config = ConfiguracaoFiscal.get_config_for_company(invoice.company)
    
    # Dados básicos
    dados = {
        "empresa": invoice.company,
        "cliente": invoice.customer,
        "cliente_nome": customer.customer_name,
        "cpf_cnpj": customer.get("tax_id") or customer.get("cpf_cnpj") or "",
        "ie_destinatario": customer.get("inscricao_estadual_cliente") or "",
        "contribuinte_icms": customer.get("contribuinte_icms") or "9",
        "email": customer.get("email_id") or "",
        "natureza_operacao": "Venda de mercadoria",
        "finalidade": "1 - NF-e normal",
        "tipo_operacao": "1 - Saída",
        "data_emissao": str(invoice.posting_date),
        "data_saida": str(invoice.posting_date),
        "valor_produtos": flt(invoice.total),
        "valor_frete": flt(invoice.get("shipping_amount") or 0),
        "valor_seguro": 0,
        "valor_desconto": flt(invoice.discount_amount or 0),
        "valor_outras_despesas": 0,
        "valor_total": flt(invoice.grand_total),
        "informacoes_adicionais": invoice.get("terms") or "",
        "informacoes_fisco": ""
    }
    
    # Dados da configuração fiscal
    if config:
        dados["ambiente"] = config.ambiente
        dados["serie"] = config.serie_nfe
    
    # Endereço
    endereco = _get_customer_address(invoice)
    if endereco:
        dados["endereco"] = {
            "logradouro": endereco.address_line1 or "",
            "numero": endereco.get("numero_endereco") or endereco.address_line2 or "S/N",
            "complemento": endereco.get("complemento") or "",
            "bairro": endereco.get("bairro") or endereco.city or "",
            "cidade": endereco.city or "",
            "uf": endereco.state or "",
            "cep": (endereco.pincode or "").replace("-", "").replace(".", ""),
            "codigo_municipio": endereco.get("codigo_municipio_ibge") or "",
            "codigo_pais": "1058"
        }
        
        # Se não tem código IBGE, tenta buscar
        if not dados["endereco"]["codigo_municipio"] and dados["endereco"]["cidade"] and dados["endereco"]["uf"]:
            dados["endereco"]["codigo_municipio"] = get_codigo_municipio(dados["endereco"]["cidade"], dados["endereco"]["uf"]) or ""
    
    # Itens
    regime = config.get_regime_codigo() if config else "1"
    uf_emit = config.uf_emissao if config else "SP"
    uf_dest = dados.get("endereco", {}).get("uf") or uf_emit
    
    dados["itens"] = []
    for item in invoice.items:
        item_doc = frappe.get_doc("Item", item.item_code)
        
        # CFOP
        cfop_interno = item_doc.get("cfop_venda_interna") or "5102"
        cfop_interestadual = item_doc.get("cfop_venda_interestadual") or "6102"
        cfop = cfop_interno if uf_emit == uf_dest else cfop_interestadual
        
        # CST ICMS
        cst_icms = get_cst_icms(regime)
        
        # Alíquota ICMS
        if regime in ["1", "simples"]:
            aliquota_icms = 0
            valor_icms = 0
        else:
            from erpnext_fiscal_br.utils.tax_tables import get_aliquota_icms
            aliquota_icms = get_aliquota_icms(uf_emit, uf_dest)
            valor_icms = flt(item.amount) * flt(aliquota_icms) / 100
        
        dados["itens"].append({
            "item_code": item.item_code,
            "descricao": item.item_name or item_doc.item_name,
            "ncm": item_doc.get("ncm") or "00000000",
            "cfop": cfop,
            "unidade": item_doc.get("unidade_tributavel") or item.uom or "UN",
            "quantidade": item.qty,
            "valor_unitario": item.rate,
            "valor_total": item.amount,
            "origem": (item_doc.get("origem") or "0").split(" - ")[0] if item_doc.get("origem") else "0",
            "cst_icms": cst_icms,
            "aliquota_icms": aliquota_icms,
            "valor_icms": valor_icms,
            "cst_pis": get_cst_pis_cofins(regime),
            "cst_cofins": get_cst_pis_cofins(regime)
        })
    
    return dados


@frappe.whitelist()
def cancelar_nfe(nota_fiscal, justificativa):
    """
    Cancela uma NFe
    
    Args:
        nota_fiscal: Nome da Nota Fiscal
        justificativa: Justificativa do cancelamento
    
    Returns:
        dict: Resultado do cancelamento
    """
    nf = frappe.get_doc("Nota Fiscal", nota_fiscal)
    
    try:
        nf.cancelar(justificativa)
        return {
            "success": nf.status == "Cancelada",
            "status": nf.status,
            "mensagem": nf.mensagem_sefaz
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def carta_correcao(nota_fiscal, correcao):
    """
    Envia carta de correção para uma NFe
    
    Args:
        nota_fiscal: Nome da Nota Fiscal
        correcao: Texto da correção
    
    Returns:
        dict: Resultado do envio
    """
    nf = frappe.get_doc("Nota Fiscal", nota_fiscal)
    
    try:
        nf.carta_correcao(correcao)
        return {
            "success": True,
            "mensagem": "Carta de correção enviada com sucesso"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def inutilizar_numeracao(empresa, serie, numero_inicial, numero_final, justificativa, modelo="55"):
    """
    Inutiliza uma faixa de numeração
    
    Args:
        empresa: Nome da empresa
        serie: Série
        numero_inicial: Número inicial
        numero_final: Número final
        justificativa: Justificativa
        modelo: "55" ou "65"
    
    Returns:
        dict: Resultado da inutilização
    """
    from erpnext_fiscal_br.services.transmitter import SEFAZTransmitter
    
    try:
        transmitter = SEFAZTransmitter(empresa)
        resultado = transmitter.inutilizar_numeracao(
            serie, numero_inicial, numero_final, justificativa, modelo
        )
        
        # Cria evento de inutilização
        if resultado.get("cStat") in ["102"]:
            for num in range(int(numero_inicial), int(numero_final) + 1):
                nf = frappe.new_doc("Nota Fiscal")
                nf.modelo = modelo
                nf.serie = serie
                nf.numero = num
                nf.empresa = empresa
                nf.status = "Inutilizada"
                nf.cliente_nome = "INUTILIZADA"
                nf.cpf_cnpj_destinatario = "00000000000"
                nf.logradouro = "N/A"
                nf.numero_endereco = "0"
                nf.bairro = "N/A"
                nf.cidade = "N/A"
                nf.uf = "SP"
                nf.cep = "00000000"
                nf.codigo_municipio = "0000000"
                nf.mensagem_sefaz = justificativa
                nf.insert(ignore_permissions=True)
        
        return {
            "success": resultado.get("cStat") in ["102"],
            "codigo": resultado.get("cStat"),
            "mensagem": resultado.get("xMotivo")
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
