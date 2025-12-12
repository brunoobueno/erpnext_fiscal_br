"""
Validação e formatação de CPF e CNPJ
"""

import re


def validar_cpf(cpf):
    """
    Valida um CPF
    
    Args:
        cpf: CPF com ou sem formatação
    
    Returns:
        bool: True se válido, False caso contrário
    """
    # Remove caracteres não numéricos
    cpf = re.sub(r'[^0-9]', '', str(cpf))
    
    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        return False
    
    # Verifica se todos os dígitos são iguais
    if cpf == cpf[0] * 11:
        return False
    
    # Calcula primeiro dígito verificador
    soma = 0
    for i in range(9):
        soma += int(cpf[i]) * (10 - i)
    resto = soma % 11
    dv1 = 0 if resto < 2 else 11 - resto
    
    # Verifica primeiro dígito
    if int(cpf[9]) != dv1:
        return False
    
    # Calcula segundo dígito verificador
    soma = 0
    for i in range(10):
        soma += int(cpf[i]) * (11 - i)
    resto = soma % 11
    dv2 = 0 if resto < 2 else 11 - resto
    
    # Verifica segundo dígito
    if int(cpf[10]) != dv2:
        return False
    
    return True


def validar_cnpj(cnpj):
    """
    Valida um CNPJ
    
    Args:
        cnpj: CNPJ com ou sem formatação
    
    Returns:
        bool: True se válido, False caso contrário
    """
    # Remove caracteres não numéricos
    cnpj = re.sub(r'[^0-9]', '', str(cnpj))
    
    # Verifica se tem 14 dígitos
    if len(cnpj) != 14:
        return False
    
    # Verifica se todos os dígitos são iguais
    if cnpj == cnpj[0] * 14:
        return False
    
    # Pesos para cálculo
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    
    # Calcula primeiro dígito verificador
    soma = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
    resto = soma % 11
    dv1 = 0 if resto < 2 else 11 - resto
    
    # Verifica primeiro dígito
    if int(cnpj[12]) != dv1:
        return False
    
    # Calcula segundo dígito verificador
    soma = sum(int(cnpj[i]) * pesos2[i] for i in range(13))
    resto = soma % 11
    dv2 = 0 if resto < 2 else 11 - resto
    
    # Verifica segundo dígito
    if int(cnpj[13]) != dv2:
        return False
    
    return True


def formatar_cpf(cpf):
    """
    Formata um CPF
    
    Args:
        cpf: CPF apenas com números
    
    Returns:
        str: CPF formatado (XXX.XXX.XXX-XX)
    """
    cpf = re.sub(r'[^0-9]', '', str(cpf))
    if len(cpf) != 11:
        return cpf
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def formatar_cnpj(cnpj):
    """
    Formata um CNPJ
    
    Args:
        cnpj: CNPJ apenas com números
    
    Returns:
        str: CNPJ formatado (XX.XXX.XXX/XXXX-XX)
    """
    cnpj = re.sub(r'[^0-9]', '', str(cnpj))
    if len(cnpj) != 14:
        return cnpj
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"


def limpar_documento(documento):
    """
    Remove formatação de um documento (CPF ou CNPJ)
    
    Args:
        documento: CPF ou CNPJ com ou sem formatação
    
    Returns:
        str: Documento apenas com números
    """
    return re.sub(r'[^0-9]', '', str(documento))


def identificar_documento(documento):
    """
    Identifica se é CPF ou CNPJ
    
    Args:
        documento: Documento com ou sem formatação
    
    Returns:
        str: "CPF", "CNPJ" ou "INVALIDO"
    """
    doc = limpar_documento(documento)
    
    if len(doc) == 11:
        return "CPF" if validar_cpf(doc) else "INVALIDO"
    elif len(doc) == 14:
        return "CNPJ" if validar_cnpj(doc) else "INVALIDO"
    else:
        return "INVALIDO"


def calcular_dv_chave_nfe(chave):
    """
    Calcula o dígito verificador da chave de acesso da NFe
    
    Args:
        chave: Primeiros 43 dígitos da chave
    
    Returns:
        int: Dígito verificador
    """
    if len(chave) != 43:
        raise ValueError("Chave deve ter 43 dígitos para cálculo do DV")
    
    # Pesos de 2 a 9, repetindo
    pesos = [2, 3, 4, 5, 6, 7, 8, 9]
    
    # Soma ponderada da direita para esquerda
    soma = 0
    for i, digito in enumerate(reversed(chave)):
        soma += int(digito) * pesos[i % 8]
    
    # Calcula DV
    resto = soma % 11
    dv = 0 if resto < 2 else 11 - resto
    
    return dv


def validar_chave_nfe(chave):
    """
    Valida uma chave de acesso de NFe
    
    Args:
        chave: Chave de acesso com 44 dígitos
    
    Returns:
        bool: True se válida, False caso contrário
    """
    chave = re.sub(r'[^0-9]', '', str(chave))
    
    if len(chave) != 44:
        return False
    
    # Calcula DV esperado
    dv_calculado = calcular_dv_chave_nfe(chave[:43])
    dv_informado = int(chave[43])
    
    return dv_calculado == dv_informado


def validar_ncm(ncm):
    """
    Valida um código NCM
    
    Args:
        ncm: Código NCM
    
    Returns:
        bool: True se válido (8 dígitos numéricos)
    """
    ncm = re.sub(r'[^0-9]', '', str(ncm))
    return len(ncm) == 8


def validar_cest(cest):
    """
    Valida um código CEST
    
    Args:
        cest: Código CEST
    
    Returns:
        bool: True se válido (7 dígitos numéricos)
    """
    if not cest:
        return True  # CEST é opcional
    cest = re.sub(r'[^0-9]', '', str(cest))
    return len(cest) == 7


def validar_inscricao_estadual(ie, uf):
    """
    Valida uma Inscrição Estadual (validação básica)
    
    Args:
        ie: Inscrição Estadual
        uf: Sigla do estado
    
    Returns:
        bool: True se válida (validação básica de tamanho)
    """
    if not ie or ie.upper() == "ISENTO":
        return True
    
    ie = re.sub(r'[^0-9]', '', str(ie))
    
    # Tamanhos válidos por UF (aproximado)
    tamanhos = {
        "AC": [13], "AL": [9], "AP": [9], "AM": [9], "BA": [8, 9],
        "CE": [9], "DF": [13], "ES": [9], "GO": [9], "MA": [9],
        "MT": [11], "MS": [9], "MG": [13], "PA": [9], "PB": [9],
        "PR": [10], "PE": [9, 14], "PI": [9], "RJ": [8], "RN": [9, 10],
        "RS": [10], "RO": [14], "RR": [9], "SC": [9], "SP": [12],
        "SE": [9], "TO": [11]
    }
    
    uf = uf.upper()
    if uf in tamanhos:
        return len(ie) in tamanhos[uf]
    
    return len(ie) >= 8 and len(ie) <= 14
