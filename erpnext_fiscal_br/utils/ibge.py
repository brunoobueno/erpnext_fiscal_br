"""
Códigos IBGE de UF e Municípios
"""

# Códigos IBGE das UFs
UF_CODES = {
    "AC": "12", "AL": "27", "AP": "16", "AM": "13", "BA": "29",
    "CE": "23", "DF": "53", "ES": "32", "GO": "52", "MA": "21",
    "MT": "51", "MS": "50", "MG": "31", "PA": "15", "PB": "25",
    "PR": "41", "PE": "26", "PI": "22", "RJ": "33", "RN": "24",
    "RS": "43", "RO": "11", "RR": "14", "SC": "42", "SP": "35",
    "SE": "28", "TO": "17"
}

# Códigos IBGE reverso (código -> sigla)
CODE_TO_UF = {v: k for k, v in UF_CODES.items()}

# Nomes das UFs
UF_NAMES = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas",
    "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo",
    "GO": "Goiás", "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba", "PR": "Paraná",
    "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina",
    "SP": "São Paulo", "SE": "Sergipe", "TO": "Tocantins"
}

# Principais municípios (código IBGE -> nome)
# Lista parcial - em produção usar tabela completa
MUNICIPIOS = {
    # São Paulo
    "3550308": "São Paulo",
    "3509502": "Campinas",
    "3518800": "Guarulhos",
    "3547809": "Santo André",
    "3548708": "São Bernardo do Campo",
    "3548807": "São Caetano do Sul",
    "3534401": "Osasco",
    "3543402": "Ribeirão Preto",
    "3552205": "Sorocaba",
    "3549805": "Santos",
    # Rio de Janeiro
    "3304557": "Rio de Janeiro",
    "3302403": "Niterói",
    "3301702": "Duque de Caxias",
    "3303500": "Nova Iguaçu",
    "3304904": "São Gonçalo",
    # Minas Gerais
    "3106200": "Belo Horizonte",
    "3170206": "Uberlândia",
    "3118601": "Contagem",
    "3136702": "Juiz de Fora",
    "3106705": "Betim",
    # Outros estados - capitais
    "5300108": "Brasília",
    "2927408": "Salvador",
    "4106902": "Curitiba",
    "4314902": "Porto Alegre",
    "2611606": "Recife",
    "2304400": "Fortaleza",
    "1302603": "Manaus",
    "1501402": "Belém",
    "5208707": "Goiânia",
    "3205309": "Vitória",
    "2111300": "São Luís",
    "5103403": "Cuiabá",
    "5002704": "Campo Grande",
    "2408102": "Natal",
    "2507507": "João Pessoa",
    "2211001": "Teresina",
    "2800308": "Aracaju",
    "1100205": "Porto Velho",
    "1200401": "Rio Branco",
    "1600303": "Macapá",
    "1400100": "Boa Vista",
    "1721000": "Palmas",
    "2704302": "Maceió",
    "4205407": "Florianópolis",
}


def get_codigo_uf(sigla):
    """
    Retorna o código IBGE de uma UF
    
    Args:
        sigla: Sigla da UF (ex: "SP")
    
    Returns:
        str: Código IBGE (ex: "35")
    """
    return UF_CODES.get(sigla.upper(), "")


def get_sigla_uf(codigo):
    """
    Retorna a sigla da UF a partir do código IBGE
    
    Args:
        codigo: Código IBGE (ex: "35")
    
    Returns:
        str: Sigla da UF (ex: "SP")
    """
    return CODE_TO_UF.get(str(codigo), "")


def get_nome_uf(sigla):
    """
    Retorna o nome completo de uma UF
    
    Args:
        sigla: Sigla da UF (ex: "SP")
    
    Returns:
        str: Nome da UF (ex: "São Paulo")
    """
    return UF_NAMES.get(sigla.upper(), "")


def get_codigo_municipio(nome_municipio, uf):
    """
    Retorna o código IBGE de um município
    
    Args:
        nome_municipio: Nome do município
        uf: Sigla da UF
    
    Returns:
        str: Código IBGE do município ou None
    """
    nome_upper = nome_municipio.upper().strip()
    
    for codigo, nome in MUNICIPIOS.items():
        if nome.upper() == nome_upper:
            # Verifica se pertence à UF correta
            codigo_uf = codigo[:2]
            if get_sigla_uf(codigo_uf) == uf.upper():
                return codigo
    
    return None


def get_nome_municipio(codigo):
    """
    Retorna o nome de um município a partir do código IBGE
    
    Args:
        codigo: Código IBGE do município
    
    Returns:
        str: Nome do município ou None
    """
    return MUNICIPIOS.get(str(codigo))


def get_uf_from_codigo_municipio(codigo_municipio):
    """
    Extrai a UF do código do município
    
    Args:
        codigo_municipio: Código IBGE do município (7 dígitos)
    
    Returns:
        str: Sigla da UF
    """
    if len(str(codigo_municipio)) >= 2:
        codigo_uf = str(codigo_municipio)[:2]
        return get_sigla_uf(codigo_uf)
    return ""


def validar_codigo_municipio(codigo):
    """
    Valida um código IBGE de município
    
    Args:
        codigo: Código do município
    
    Returns:
        bool: True se válido (7 dígitos e UF válida)
    """
    codigo = str(codigo).strip()
    
    if len(codigo) != 7:
        return False
    
    if not codigo.isdigit():
        return False
    
    # Verifica se a UF é válida
    codigo_uf = codigo[:2]
    return codigo_uf in CODE_TO_UF


def get_codigo_pais(nome_pais="Brasil"):
    """
    Retorna o código do país
    
    Args:
        nome_pais: Nome do país
    
    Returns:
        str: Código do país (1058 para Brasil)
    """
    paises = {
        "Brasil": "1058",
        "Argentina": "0639",
        "Paraguai": "5860",
        "Uruguai": "8451",
        "Chile": "1589",
        "Estados Unidos": "2496",
        "China": "1600",
    }
    return paises.get(nome_pais, "1058")


def get_todas_ufs():
    """
    Retorna lista de todas as UFs
    
    Returns:
        list: Lista de dicionários com sigla, codigo e nome
    """
    return [
        {"sigla": sigla, "codigo": codigo, "nome": UF_NAMES.get(sigla, "")}
        for sigla, codigo in UF_CODES.items()
    ]
