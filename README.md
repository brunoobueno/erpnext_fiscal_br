# ERPNext Fiscal BR

Módulo Fiscal Brasileiro para ERPNext v15 - Emissão de NFe e NFCe

## Funcionalidades

- ✅ Emissão de NFe (Nota Fiscal Eletrônica)
- ✅ Emissão de NFCe (Nota Fiscal de Consumidor Eletrônica)
- ✅ Cancelamento de notas fiscais
- ✅ Carta de Correção (CCe)
- ✅ Inutilização de numeração
- ✅ Geração de DANFE (PDF)
- ✅ Suporte a múltiplas empresas
- ✅ Suporte a diferentes regimes tributários (Simples Nacional, Lucro Presumido, Lucro Real)
- ✅ Integração completa com Sales Invoice do ERPNext

## Requisitos

- ERPNext v15.x
- Frappe v15.x
- Python 3.10+
- Certificado Digital A1 (.pfx)

## Instalação

### Via Bench

```bash
cd frappe-bench
bench get-app https://github.com/brunoobueno/erpnext_fiscal_br
bench --site seu-site install-app erpnext_fiscal_br
bench migrate
bench build
bench restart
```

### Via Docker (Coolify)

Adicione ao seu `docker-compose.yml`:

```yaml
services:
  backend:
    build:
      context: .
      args:
        - APPS_JSON_BASE64=${APPS_JSON_BASE64}
```

E no `apps.json`:

```json
[
  {
    "url": "https://github.com/frappe/erpnext",
    "branch": "version-15"
  },
  {
    "url": "https://github.com/brunoobueno/erpnext_fiscal_br",
    "branch": "main"
  }
]
```

## Configuração

### 1. Configuração Fiscal

Acesse: **Fiscal BR > Configuração Fiscal**

- Selecione a empresa
- Configure CNPJ, Inscrição Estadual
- Defina o regime tributário
- Configure séries de NFe e NFCe
- Defina ambiente (Homologação/Produção)

### 2. Certificado Digital

Acesse: **Fiscal BR > Certificado Digital**

- Faça upload do arquivo .pfx
- Informe a senha do certificado
- O sistema validará automaticamente

### 3. Dados do Cliente

Configure nos clientes:
- CPF/CNPJ
- Inscrição Estadual (se PJ)
- Indicador de contribuinte ICMS

### 4. Dados dos Itens

Configure nos itens:
- NCM (8 dígitos)
- CEST (se aplicável)
- Origem da mercadoria
- CFOP padrão

## Uso

### Emitir NFe/NFCe

1. Crie e submeta uma **Sales Invoice**
2. Clique no botão **Emitir NFe** ou **Emitir NFCe**
3. Confirme os dados no modal
4. Aguarde a autorização da SEFAZ
5. Baixe o DANFE (PDF)

### Cancelar Nota Fiscal

1. Acesse a nota fiscal autorizada
2. Clique em **Cancelar**
3. Informe a justificativa (mín. 15 caracteres)
4. Confirme o cancelamento

### Carta de Correção

1. Acesse a nota fiscal autorizada
2. Clique em **Carta de Correção**
3. Informe a correção (mín. 15 caracteres)
4. Confirme o envio

## Estrutura de Diretórios

```
erpnext_fiscal_br/
├── erpnext_fiscal_br/
│   ├── fiscal_br/
│   │   ├── doctype/
│   │   │   ├── configuracao_fiscal/
│   │   │   ├── certificado_digital/
│   │   │   ├── nota_fiscal/
│   │   │   └── evento_fiscal/
│   │   └── report/
│   ├── api/
│   ├── services/
│   ├── utils/
│   ├── fixtures/
│   └── public/
├── setup.py
├── requirements.txt
└── README.md
```

## Suporte

- Issues: https://github.com/brunoobueno/erpnext_fiscal_br/issues
- Email: contato@alquimiaindustria.com.br

## Licença

MIT License - veja [license.txt](license.txt)
