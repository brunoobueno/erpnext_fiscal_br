"""
Tabelas de impostos e alíquotas
"""

# Alíquotas internas de ICMS por UF (2024)
ALIQUOTAS_ICMS_INTERNAS = {
    "AC": 19.0, "AL": 19.0, "AP": 18.0, "AM": 20.0, "BA": 20.5,
    "CE": 20.0, "DF": 20.0, "ES": 17.0, "GO": 19.0, "MA": 22.0,
    "MT": 17.0, "MS": 17.0, "MG": 18.0, "PA": 19.0, "PB": 20.0,
    "PR": 19.5, "PE": 20.5, "PI": 21.0, "RJ": 22.0, "RN": 20.0,
    "RS": 17.0, "RO": 19.5, "RR": 20.0, "SC": 17.0, "SP": 18.0,
    "SE": 19.0, "TO": 20.0
}

# Alíquotas interestaduais de ICMS
# Origem -> Destino
ALIQUOTAS_ICMS_INTERESTADUAIS = {
    # Sul e Sudeste (exceto ES) para Norte, Nordeste, Centro-Oeste e ES
    ("SP", "AC"): 7.0, ("SP", "AL"): 7.0, ("SP", "AP"): 7.0, ("SP", "AM"): 7.0,
    ("SP", "BA"): 7.0, ("SP", "CE"): 7.0, ("SP", "DF"): 7.0, ("SP", "ES"): 7.0,
    ("SP", "GO"): 7.0, ("SP", "MA"): 7.0, ("SP", "MT"): 7.0, ("SP", "MS"): 7.0,
    ("SP", "PA"): 7.0, ("SP", "PB"): 7.0, ("SP", "PE"): 7.0, ("SP", "PI"): 7.0,
    ("SP", "RN"): 7.0, ("SP", "RO"): 7.0, ("SP", "RR"): 7.0, ("SP", "SE"): 7.0,
    ("SP", "TO"): 7.0,
    # Sul e Sudeste (exceto ES) entre si
    ("SP", "RJ"): 12.0, ("SP", "MG"): 12.0, ("SP", "PR"): 12.0,
    ("SP", "SC"): 12.0, ("SP", "RS"): 12.0,
    # Demais estados para Sul e Sudeste (exceto ES)
    ("BA", "SP"): 12.0, ("BA", "RJ"): 12.0, ("BA", "MG"): 12.0,
    ("BA", "PR"): 12.0, ("BA", "SC"): 12.0, ("BA", "RS"): 12.0,
}

# CST ICMS para Regime Normal
CST_ICMS = {
    "00": "Tributada integralmente",
    "10": "Tributada com cobrança de ICMS por ST",
    "20": "Com redução de base de cálculo",
    "30": "Isenta ou não tributada com cobrança de ICMS por ST",
    "40": "Isenta",
    "41": "Não tributada",
    "50": "Suspensão",
    "51": "Diferimento",
    "60": "ICMS cobrado anteriormente por ST",
    "70": "Com redução de base de cálculo e cobrança de ICMS por ST",
    "90": "Outros",
}

# CSOSN para Simples Nacional
CSOSN = {
    "101": "Tributada com permissão de crédito",
    "102": "Tributada sem permissão de crédito",
    "103": "Isenção do ICMS para faixa de receita bruta",
    "201": "Tributada com permissão de crédito e cobrança de ICMS por ST",
    "202": "Tributada sem permissão de crédito e cobrança de ICMS por ST",
    "203": "Isenção do ICMS para faixa de receita bruta e cobrança de ICMS por ST",
    "300": "Imune",
    "400": "Não tributada",
    "500": "ICMS cobrado anteriormente por ST ou por antecipação",
    "900": "Outros",
}

# CST PIS/COFINS
CST_PIS_COFINS = {
    "01": "Operação Tributável com Alíquota Básica",
    "02": "Operação Tributável com Alíquota Diferenciada",
    "03": "Operação Tributável com Alíquota por Unidade de Medida",
    "04": "Operação Tributável Monofásica - Revenda a Alíquota Zero",
    "05": "Operação Tributável por ST",
    "06": "Operação Tributável a Alíquota Zero",
    "07": "Operação Isenta da Contribuição",
    "08": "Operação sem Incidência da Contribuição",
    "09": "Operação com Suspensão da Contribuição",
    "49": "Outras Operações de Saída",
    "99": "Outras Operações",
}

# CST IPI
CST_IPI = {
    "00": "Entrada com Recuperação de Crédito",
    "01": "Entrada Tributável com Alíquota Zero",
    "02": "Entrada Isenta",
    "03": "Entrada Não Tributada",
    "04": "Entrada Imune",
    "05": "Entrada com Suspensão",
    "49": "Outras Entradas",
    "50": "Saída Tributada",
    "51": "Saída Tributável com Alíquota Zero",
    "52": "Saída Isenta",
    "53": "Saída Não Tributada",
    "54": "Saída Imune",
    "55": "Saída com Suspensão",
    "99": "Outras Saídas",
}

# CFOPs mais comuns
CFOP = {
    # Vendas dentro do estado
    "5101": "Venda de produção do estabelecimento",
    "5102": "Venda de mercadoria adquirida ou recebida de terceiros",
    "5103": "Venda de produção do estabelecimento efetuada fora do estabelecimento",
    "5104": "Venda de mercadoria adquirida ou recebida de terceiros, efetuada fora do estabelecimento",
    "5405": "Venda de mercadoria adquirida ou recebida de terceiros em operação com mercadoria sujeita ao regime de ST",
    "5910": "Remessa em bonificação, doação ou brinde",
    "5911": "Remessa de amostra grátis",
    "5949": "Outra saída de mercadoria ou prestação de serviço não especificado",
    # Vendas fora do estado
    "6101": "Venda de produção do estabelecimento",
    "6102": "Venda de mercadoria adquirida ou recebida de terceiros",
    "6103": "Venda de produção do estabelecimento efetuada fora do estabelecimento",
    "6104": "Venda de mercadoria adquirida ou recebida de terceiros, efetuada fora do estabelecimento",
    "6108": "Venda de mercadoria adquirida ou recebida de terceiros, destinada a não contribuinte",
    "6405": "Venda de mercadoria adquirida ou recebida de terceiros em operação com mercadoria sujeita ao regime de ST",
    "6910": "Remessa em bonificação, doação ou brinde",
    "6911": "Remessa de amostra grátis",
    "6949": "Outra saída de mercadoria ou prestação de serviço não especificado",
    # Devoluções dentro do estado
    "5201": "Devolução de compra para industrialização ou produção rural",
    "5202": "Devolução de compra para comercialização",
    "5411": "Devolução de compra para comercialização em operação com mercadoria sujeita ao regime de ST",
    # Devoluções fora do estado
    "6201": "Devolução de compra para industrialização ou produção rural",
    "6202": "Devolução de compra para comercialização",
    "6411": "Devolução de compra para comercialização em operação com mercadoria sujeita ao regime de ST",
    # Exportação
    "7101": "Venda de produção do estabelecimento",
    "7102": "Venda de mercadoria adquirida ou recebida de terceiros",
}


def get_aliquota_icms(uf_origem, uf_destino):
    """
    Retorna a alíquota de ICMS para uma operação
    
    Args:
        uf_origem: UF de origem
        uf_destino: UF de destino
    
    Returns:
        float: Alíquota de ICMS
    """
    uf_origem = uf_origem.upper()
    uf_destino = uf_destino.upper()
    
    # Operação interna
    if uf_origem == uf_destino:
        return ALIQUOTAS_ICMS_INTERNAS.get(uf_origem, 18.0)
    
    # Operação interestadual
    chave = (uf_origem, uf_destino)
    if chave in ALIQUOTAS_ICMS_INTERESTADUAIS:
        return ALIQUOTAS_ICMS_INTERESTADUAIS[chave]
    
    # Regra geral interestadual
    # Sul e Sudeste (exceto ES) para Norte, Nordeste, Centro-Oeste e ES = 7%
    sul_sudeste = ["SP", "RJ", "MG", "PR", "SC", "RS"]
    norte_nordeste_co = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", 
                         "MA", "MT", "MS", "PA", "PB", "PE", "PI", "RN", "RO", 
                         "RR", "SE", "TO"]
    
    if uf_origem in sul_sudeste and uf_destino in norte_nordeste_co:
        return 7.0
    
    # Demais casos = 12%
    return 12.0


def get_cfop(tipo_operacao, uf_origem, uf_destino, tipo_produto="mercadoria"):
    """
    Retorna o CFOP sugerido para uma operação
    
    Args:
        tipo_operacao: "venda", "devolucao", "remessa"
        uf_origem: UF de origem
        uf_destino: UF de destino
        tipo_produto: "producao" ou "mercadoria"
    
    Returns:
        str: CFOP sugerido
    """
    uf_origem = uf_origem.upper()
    uf_destino = uf_destino.upper()
    
    # Determina se é operação interna ou interestadual
    interno = uf_origem == uf_destino
    
    if tipo_operacao == "venda":
        if tipo_produto == "producao":
            return "5101" if interno else "6101"
        else:
            return "5102" if interno else "6102"
    
    elif tipo_operacao == "devolucao":
        return "5202" if interno else "6202"
    
    elif tipo_operacao == "remessa":
        return "5949" if interno else "6949"
    
    # Padrão: venda de mercadoria
    return "5102" if interno else "6102"


def get_cst_icms(regime_tributario, tipo_operacao="venda"):
    """
    Retorna o CST/CSOSN de ICMS sugerido
    
    Args:
        regime_tributario: "simples", "presumido", "real"
        tipo_operacao: "venda", "isento", "st"
    
    Returns:
        str: CST ou CSOSN
    """
    if regime_tributario.lower() in ["simples", "simples nacional", "1"]:
        # Simples Nacional - CSOSN
        if tipo_operacao == "venda":
            return "102"  # Tributada sem permissão de crédito
        elif tipo_operacao == "st":
            return "500"  # ICMS cobrado anteriormente por ST
        elif tipo_operacao == "isento":
            return "400"  # Não tributada
        return "102"
    else:
        # Regime Normal - CST
        if tipo_operacao == "venda":
            return "00"  # Tributada integralmente
        elif tipo_operacao == "st":
            return "60"  # ICMS cobrado anteriormente por ST
        elif tipo_operacao == "isento":
            return "40"  # Isenta
        return "00"


def get_cst_pis_cofins(regime_tributario):
    """
    Retorna o CST de PIS/COFINS sugerido
    
    Args:
        regime_tributario: "simples", "presumido", "real"
    
    Returns:
        str: CST PIS/COFINS
    """
    if regime_tributario.lower() in ["simples", "simples nacional", "1"]:
        return "99"  # Outras operações (Simples não destaca PIS/COFINS)
    else:
        return "01"  # Operação tributável com alíquota básica


def get_aliquotas_pis_cofins(regime_tributario):
    """
    Retorna as alíquotas de PIS e COFINS
    
    Args:
        regime_tributario: "simples", "presumido", "real"
    
    Returns:
        tuple: (aliquota_pis, aliquota_cofins)
    """
    if regime_tributario.lower() in ["simples", "simples nacional", "1"]:
        return (0.0, 0.0)  # Simples não destaca
    elif regime_tributario.lower() in ["presumido", "lucro presumido", "2"]:
        return (0.65, 3.0)  # Regime cumulativo
    else:
        return (1.65, 7.6)  # Regime não-cumulativo (Lucro Real)
