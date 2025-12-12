"""
Instalação e migração do módulo ERPNext Fiscal BR
"""

import frappe
from frappe import _


def after_install():
    """Executado após a instalação do app"""
    try:
        create_roles()
        create_custom_fields()
        create_workspace()
        frappe.db.commit()
        print("ERPNext Fiscal BR instalado com sucesso!")
    except Exception as e:
        frappe.log_error(f"Erro na instalação do ERPNext Fiscal BR: {str(e)}")
        print(f"Aviso: Alguns componentes podem não ter sido instalados: {str(e)}")


def after_migrate():
    """Executado após cada migração"""
    try:
        create_custom_fields()
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Erro na migração do ERPNext Fiscal BR: {str(e)}")


def create_roles():
    """Cria roles específicas para o módulo fiscal"""
    roles = [
        {
            "role_name": "Fiscal Manager",
            "desk_access": 1,
            "is_custom": 1,
        },
        {
            "role_name": "Fiscal User",
            "desk_access": 1,
            "is_custom": 1,
        },
    ]
    
    for role_data in roles:
        if not frappe.db.exists("Role", role_data["role_name"]):
            role = frappe.new_doc("Role")
            role.update(role_data)
            role.insert(ignore_permissions=True)
            print(f"Role '{role_data['role_name']}' criada")


def create_custom_fields():
    """Cria campos customizados nos DocTypes do ERPNext"""
    custom_fields = get_custom_fields()
    
    for doctype, fields in custom_fields.items():
        for field in fields:
            field_name = f"{doctype}-{field['fieldname']}"
            if not frappe.db.exists("Custom Field", field_name):
                custom_field = frappe.new_doc("Custom Field")
                custom_field.dt = doctype
                custom_field.module = "Fiscal BR"
                custom_field.update(field)
                custom_field.insert(ignore_permissions=True)
                print(f"Campo '{field['fieldname']}' criado em '{doctype}'")


def get_custom_fields():
    """Retorna definição dos campos customizados"""
    return {
        # Campos na Company
        "Company": [
            {
                "fieldname": "fiscal_br_section",
                "label": "Dados Fiscais Brasil",
                "fieldtype": "Section Break",
                "insert_after": "default_currency",
                "collapsible": 1,
            },
            {
                "fieldname": "cnpj",
                "label": "CNPJ",
                "fieldtype": "Data",
                "insert_after": "fiscal_br_section",
                "description": "CNPJ da empresa (apenas números)",
            },
            {
                "fieldname": "inscricao_estadual",
                "label": "Inscrição Estadual",
                "fieldtype": "Data",
                "insert_after": "cnpj",
            },
            {
                "fieldname": "inscricao_municipal",
                "label": "Inscrição Municipal",
                "fieldtype": "Data",
                "insert_after": "inscricao_estadual",
            },
            {
                "fieldname": "cnae",
                "label": "CNAE",
                "fieldtype": "Data",
                "insert_after": "inscricao_municipal",
                "description": "Código Nacional de Atividade Econômica",
            },
            {
                "fieldname": "regime_tributario",
                "label": "Regime Tributário",
                "fieldtype": "Select",
                "options": "\nSimples Nacional\nLucro Presumido\nLucro Real",
                "insert_after": "cnae",
            },
            {
                "fieldname": "column_break_fiscal",
                "fieldtype": "Column Break",
                "insert_after": "regime_tributario",
            },
            {
                "fieldname": "codigo_uf",
                "label": "Código UF (IBGE)",
                "fieldtype": "Data",
                "insert_after": "column_break_fiscal",
                "description": "Código IBGE do estado",
            },
            {
                "fieldname": "codigo_municipio",
                "label": "Código Município (IBGE)",
                "fieldtype": "Data",
                "insert_after": "codigo_uf",
                "description": "Código IBGE do município",
            },
            {
                "fieldname": "suframa",
                "label": "SUFRAMA",
                "fieldtype": "Data",
                "insert_after": "codigo_municipio",
                "description": "Inscrição SUFRAMA (se aplicável)",
            },
        ],
        
        # Campos no Customer
        "Customer": [
            {
                "fieldname": "fiscal_br_section",
                "label": "Dados Fiscais Brasil",
                "fieldtype": "Section Break",
                "insert_after": "customer_type",
                "collapsible": 1,
            },
            {
                "fieldname": "cpf_cnpj",
                "label": "CPF/CNPJ",
                "fieldtype": "Data",
                "insert_after": "fiscal_br_section",
                "description": "CPF (pessoa física) ou CNPJ (pessoa jurídica)",
            },
            {
                "fieldname": "inscricao_estadual_cliente",
                "label": "Inscrição Estadual",
                "fieldtype": "Data",
                "insert_after": "cpf_cnpj",
            },
            {
                "fieldname": "contribuinte_icms",
                "label": "Contribuinte ICMS",
                "fieldtype": "Select",
                "options": "\n1 - Contribuinte ICMS\n2 - Contribuinte isento\n9 - Não Contribuinte",
                "insert_after": "inscricao_estadual_cliente",
                "default": "9 - Não Contribuinte",
            },
            {
                "fieldname": "column_break_fiscal_customer",
                "fieldtype": "Column Break",
                "insert_after": "contribuinte_icms",
            },
            {
                "fieldname": "inscricao_municipal_cliente",
                "label": "Inscrição Municipal",
                "fieldtype": "Data",
                "insert_after": "column_break_fiscal_customer",
            },
            {
                "fieldname": "suframa_cliente",
                "label": "SUFRAMA",
                "fieldtype": "Data",
                "insert_after": "inscricao_municipal_cliente",
            },
            {
                "fieldname": "email_nfe",
                "label": "Email para NFe",
                "fieldtype": "Data",
                "insert_after": "suframa_cliente",
                "description": "Email para envio automático da NFe",
            },
        ],
        
        # Campos no Item
        "Item": [
            {
                "fieldname": "fiscal_br_section",
                "label": "Dados Fiscais Brasil",
                "fieldtype": "Section Break",
                "insert_after": "item_group",
                "collapsible": 1,
            },
            {
                "fieldname": "ncm",
                "label": "NCM",
                "fieldtype": "Data",
                "insert_after": "fiscal_br_section",
                "description": "Nomenclatura Comum do Mercosul (8 dígitos)",
            },
            {
                "fieldname": "cest",
                "label": "CEST",
                "fieldtype": "Data",
                "insert_after": "ncm",
                "description": "Código Especificador da Substituição Tributária",
            },
            {
                "fieldname": "origem",
                "label": "Origem",
                "fieldtype": "Select",
                "options": "0 - Nacional\n1 - Estrangeira - Importação direta\n2 - Estrangeira - Adquirida no mercado interno\n3 - Nacional - Conteúdo de importação > 40%\n4 - Nacional - Processos produtivos básicos\n5 - Nacional - Conteúdo de importação <= 40%\n6 - Estrangeira - Importação direta, sem similar nacional\n7 - Estrangeira - Adquirida no mercado interno, sem similar nacional\n8 - Nacional - Conteúdo de importação > 70%",
                "insert_after": "cest",
                "default": "0 - Nacional",
            },
            {
                "fieldname": "column_break_fiscal_item",
                "fieldtype": "Column Break",
                "insert_after": "origem",
            },
            {
                "fieldname": "cfop_venda_interna",
                "label": "CFOP Venda Interna",
                "fieldtype": "Data",
                "insert_after": "column_break_fiscal_item",
                "default": "5102",
                "description": "CFOP para vendas dentro do estado",
            },
            {
                "fieldname": "cfop_venda_interestadual",
                "label": "CFOP Venda Interestadual",
                "fieldtype": "Data",
                "insert_after": "cfop_venda_interna",
                "default": "6102",
                "description": "CFOP para vendas fora do estado",
            },
            {
                "fieldname": "unidade_tributavel",
                "label": "Unidade Tributável",
                "fieldtype": "Data",
                "insert_after": "cfop_venda_interestadual",
                "default": "UN",
                "description": "Unidade de medida tributável (UN, KG, etc.)",
            },
            {
                "fieldname": "extipi",
                "label": "EX TIPI",
                "fieldtype": "Data",
                "insert_after": "unidade_tributavel",
                "description": "Código de exceção da TIPI",
            },
            {
                "fieldname": "genero",
                "label": "Gênero",
                "fieldtype": "Data",
                "insert_after": "extipi",
                "description": "Gênero do item (2 primeiros dígitos do NCM)",
            },
        ],
        
        # Campos na Sales Invoice
        "Sales Invoice": [
            {
                "fieldname": "fiscal_br_section",
                "label": "Nota Fiscal Eletrônica",
                "fieldtype": "Section Break",
                "insert_after": "amended_from",
                "collapsible": 1,
            },
            {
                "fieldname": "nota_fiscal",
                "label": "Nota Fiscal",
                "fieldtype": "Link",
                "options": "Nota Fiscal",
                "insert_after": "fiscal_br_section",
                "read_only": 1,
            },
            {
                "fieldname": "chave_nfe",
                "label": "Chave NFe",
                "fieldtype": "Data",
                "insert_after": "nota_fiscal",
                "read_only": 1,
                "description": "Chave de acesso da NFe (44 dígitos)",
            },
            {
                "fieldname": "status_fiscal",
                "label": "Status Fiscal",
                "fieldtype": "Select",
                "options": "\nSem NF\nPendente\nAutorizada\nCancelada\nRejeitada",
                "insert_after": "chave_nfe",
                "read_only": 1,
                "default": "Sem NF",
            },
            {
                "fieldname": "column_break_fiscal_invoice",
                "fieldtype": "Column Break",
                "insert_after": "status_fiscal",
            },
            {
                "fieldname": "numero_nfe",
                "label": "Número NFe",
                "fieldtype": "Int",
                "insert_after": "column_break_fiscal_invoice",
                "read_only": 1,
            },
            {
                "fieldname": "serie_nfe",
                "label": "Série NFe",
                "fieldtype": "Int",
                "insert_after": "numero_nfe",
                "read_only": 1,
            },
            {
                "fieldname": "protocolo_autorizacao",
                "label": "Protocolo Autorização",
                "fieldtype": "Data",
                "insert_after": "serie_nfe",
                "read_only": 1,
            },
            {
                "fieldname": "data_autorizacao",
                "label": "Data Autorização",
                "fieldtype": "Datetime",
                "insert_after": "protocolo_autorizacao",
                "read_only": 1,
            },
        ],
        
        # Campos no Sales Invoice Item
        "Sales Invoice Item": [
            {
                "fieldname": "ncm_item",
                "label": "NCM",
                "fieldtype": "Data",
                "insert_after": "item_code",
                "fetch_from": "item_code.ncm",
            },
            {
                "fieldname": "cfop_item",
                "label": "CFOP",
                "fieldtype": "Data",
                "insert_after": "ncm_item",
            },
            {
                "fieldname": "cst_icms",
                "label": "CST ICMS",
                "fieldtype": "Data",
                "insert_after": "cfop_item",
            },
            {
                "fieldname": "cst_pis",
                "label": "CST PIS",
                "fieldtype": "Data",
                "insert_after": "cst_icms",
            },
            {
                "fieldname": "cst_cofins",
                "label": "CST COFINS",
                "fieldtype": "Data",
                "insert_after": "cst_pis",
            },
        ],
        
        # Campos no Address
        "Address": [
            {
                "fieldname": "codigo_municipio_ibge",
                "label": "Código Município (IBGE)",
                "fieldtype": "Data",
                "insert_after": "city",
                "description": "Código IBGE do município",
            },
            {
                "fieldname": "codigo_uf_ibge",
                "label": "Código UF (IBGE)",
                "fieldtype": "Data",
                "insert_after": "state",
                "description": "Código IBGE do estado",
            },
            {
                "fieldname": "numero_endereco",
                "label": "Número",
                "fieldtype": "Data",
                "insert_after": "address_line1",
                "description": "Número do endereço",
            },
            {
                "fieldname": "complemento",
                "label": "Complemento",
                "fieldtype": "Data",
                "insert_after": "numero_endereco",
            },
            {
                "fieldname": "bairro",
                "label": "Bairro",
                "fieldtype": "Data",
                "insert_after": "complemento",
            },
        ],
    }


def create_workspace():
    """Cria o workspace do módulo fiscal"""
    if frappe.db.exists("Workspace", "Fiscal BR"):
        return
    
    workspace = frappe.new_doc("Workspace")
    workspace.name = "Fiscal BR"
    workspace.label = "Fiscal BR"
    workspace.title = "Fiscal BR"
    workspace.icon = "file-text"
    workspace.module = "Fiscal BR"
    workspace.category = "Modules"
    workspace.is_standard = 0
    
    # Shortcuts
    workspace.append("shortcuts", {
        "type": "Doctype",
        "label": "Notas Fiscais",
        "link_to": "Nota Fiscal",
        "color": "#3498db",
        "icon": "file-text",
    })
    workspace.append("shortcuts", {
        "type": "Doctype",
        "label": "Configuração Fiscal",
        "link_to": "Configuracao Fiscal",
        "color": "#2ecc71",
        "icon": "settings",
    })
    workspace.append("shortcuts", {
        "type": "Doctype",
        "label": "Certificados",
        "link_to": "Certificado Digital",
        "color": "#e74c3c",
        "icon": "lock",
    })
    
    # Links
    workspace.append("links", {
        "type": "Doctype",
        "label": "Nota Fiscal",
        "link_to": "Nota Fiscal",
        "link_type": "DocType",
    })
    workspace.append("links", {
        "type": "Doctype",
        "label": "Evento Fiscal",
        "link_to": "Evento Fiscal",
        "link_type": "DocType",
    })
    workspace.append("links", {
        "type": "Doctype",
        "label": "Configuração Fiscal",
        "link_to": "Configuracao Fiscal",
        "link_type": "DocType",
    })
    workspace.append("links", {
        "type": "Doctype",
        "label": "Certificado Digital",
        "link_to": "Certificado Digital",
        "link_type": "DocType",
    })
    
    workspace.insert(ignore_permissions=True)
    print("Workspace 'Fiscal BR' criado")
