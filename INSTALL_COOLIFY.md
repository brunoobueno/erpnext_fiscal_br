# Instalação no Coolify

## Pré-requisitos

- ERPNext v15 rodando no Coolify
- Acesso ao repositório do app

## Opção 1: Via apps.json (Recomendado)

### 1. Atualize o `apps.json`

Adicione o app ao seu arquivo `apps.json`:

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

### 2. Gere o APPS_JSON_BASE64

```bash
export APPS_JSON_BASE64=$(base64 -w 0 apps.json)
```

### 3. Rebuild da imagem

No Coolify, faça o rebuild do serviço backend com a nova variável de ambiente.

### 4. Instale o app no site

```bash
docker exec -it <container_backend> bench --site <seu-site> install-app erpnext_fiscal_br
docker exec -it <container_backend> bench --site <seu-site> migrate
docker exec -it <container_backend> bench build
```

## Opção 2: Instalação manual no container

### 1. Acesse o container

```bash
docker exec -it <container_backend> bash
```

### 2. Instale o app

```bash
cd /home/frappe/frappe-bench
bench get-app https://github.com/brunoobueno/erpnext_fiscal_br --branch main
bench --site <seu-site> install-app erpnext_fiscal_br
bench --site <seu-site> migrate
bench build
```

### 3. Reinicie os workers

```bash
bench restart
```

## Dependências do Sistema

O app requer algumas bibliotecas do sistema para funcionar corretamente. Adicione ao Dockerfile:

```dockerfile
RUN apt-get update && apt-get install -y \
    libxmlsec1-dev \
    libxmlsec1-openssl \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*
```

## Configuração Pós-Instalação

### 1. Configuração Fiscal

Acesse: **Fiscal BR > Configuração Fiscal**

- Selecione a empresa
- Preencha CNPJ, IE, Regime Tributário
- Configure séries de NFe/NFCe
- Defina ambiente (Homologação para testes)

### 2. Certificado Digital

Acesse: **Fiscal BR > Certificado Digital**

- Faça upload do arquivo .pfx (certificado A1)
- Informe a senha
- O sistema validará automaticamente

### 3. Dados dos Clientes

Configure nos clientes:
- CPF/CNPJ
- Inscrição Estadual (se PJ contribuinte)
- Indicador de contribuinte ICMS

### 4. Dados dos Itens

Configure nos itens:
- NCM (8 dígitos)
- CFOP de venda interna e interestadual
- Origem da mercadoria

## Teste de Funcionamento

### 1. Teste conexão SEFAZ

Na empresa, clique em **Fiscal BR > Testar SEFAZ**

### 2. Emita uma NFe de teste

1. Crie uma Sales Invoice
2. Submeta a fatura
3. Clique em **Nota Fiscal > Emitir NFe**
4. Confirme a emissão

Em ambiente de homologação, a nota será processada mas não terá valor fiscal.

## Troubleshooting

### Erro de certificado SSL

```
SSLError: certificate verify failed
```

Verifique se o certificado digital está válido e a senha está correta.

### Erro de timeout

```
Timeout na comunicação com a SEFAZ
```

Aumente o timeout em **Configuração Fiscal > Timeout SEFAZ**.

### Erro de assinatura

```
Erro ao assinar XML
```

Verifique se as bibliotecas `xmlsec` e `cryptography` estão instaladas corretamente.

## Suporte

- Issues: https://github.com/brunoobueno/erpnext_fiscal_br/issues
- Email: contato@alquimiaindustria.com.br
