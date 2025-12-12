"""
SEFAZ Transmitter - Comunicação com a SEFAZ
Envia documentos fiscais e recebe retornos
"""

import frappe
from frappe import _
from frappe.utils import now_datetime
from lxml import etree
import requests
import ssl
import tempfile
import os

# URLs dos Web Services da SEFAZ por UF e ambiente
SEFAZ_URLS = {
    "SP": {
        "1": {  # Produção
            "NfeAutorizacao": "https://nfe.fazenda.sp.gov.br/ws/nfeautorizacao4.asmx",
            "NfeRetAutorizacao": "https://nfe.fazenda.sp.gov.br/ws/nferetautorizacao4.asmx",
            "NfeConsultaProtocolo": "https://nfe.fazenda.sp.gov.br/ws/nfeconsultaprotocolo4.asmx",
            "NfeStatusServico": "https://nfe.fazenda.sp.gov.br/ws/nfestatusservico4.asmx",
            "RecepcaoEvento": "https://nfe.fazenda.sp.gov.br/ws/nferecepcaoevento4.asmx",
            "NfeInutilizacao": "https://nfe.fazenda.sp.gov.br/ws/nfeinutilizacao4.asmx",
            "NfceAutorizacao": "https://nfce.fazenda.sp.gov.br/ws/NFeAutorizacao4.asmx",
            "NfceRetAutorizacao": "https://nfce.fazenda.sp.gov.br/ws/NFeRetAutorizacao4.asmx",
        },
        "2": {  # Homologação
            "NfeAutorizacao": "https://homologacao.nfe.fazenda.sp.gov.br/ws/nfeautorizacao4.asmx",
            "NfeRetAutorizacao": "https://homologacao.nfe.fazenda.sp.gov.br/ws/nferetautorizacao4.asmx",
            "NfeConsultaProtocolo": "https://homologacao.nfe.fazenda.sp.gov.br/ws/nfeconsultaprotocolo4.asmx",
            "NfeStatusServico": "https://homologacao.nfe.fazenda.sp.gov.br/ws/nfestatusservico4.asmx",
            "RecepcaoEvento": "https://homologacao.nfe.fazenda.sp.gov.br/ws/nferecepcaoevento4.asmx",
            "NfeInutilizacao": "https://homologacao.nfe.fazenda.sp.gov.br/ws/nfeinutilizacao4.asmx",
            "NfceAutorizacao": "https://homologacao.nfce.fazenda.sp.gov.br/ws/NFeAutorizacao4.asmx",
            "NfceRetAutorizacao": "https://homologacao.nfce.fazenda.sp.gov.br/ws/NFeRetAutorizacao4.asmx",
        }
    },
    # SVRS - Sefaz Virtual Rio Grande do Sul (usado por vários estados)
    "SVRS": {
        "1": {
            "NfeAutorizacao": "https://nfe.svrs.rs.gov.br/ws/NfeAutorizacao/NFeAutorizacao4.asmx",
            "NfeRetAutorizacao": "https://nfe.svrs.rs.gov.br/ws/NfeRetAutorizacao/NFeRetAutorizacao4.asmx",
            "NfeConsultaProtocolo": "https://nfe.svrs.rs.gov.br/ws/NfeConsulta/NfeConsulta4.asmx",
            "NfeStatusServico": "https://nfe.svrs.rs.gov.br/ws/NfeStatusServico/NfeStatusServico4.asmx",
            "RecepcaoEvento": "https://nfe.svrs.rs.gov.br/ws/recepcaoevento/recepcaoevento4.asmx",
            "NfeInutilizacao": "https://nfe.svrs.rs.gov.br/ws/nfeinutilizacao/nfeinutilizacao4.asmx",
        },
        "2": {
            "NfeAutorizacao": "https://nfe-homologacao.svrs.rs.gov.br/ws/NfeAutorizacao/NFeAutorizacao4.asmx",
            "NfeRetAutorizacao": "https://nfe-homologacao.svrs.rs.gov.br/ws/NfeRetAutorizacao/NFeRetAutorizacao4.asmx",
            "NfeConsultaProtocolo": "https://nfe-homologacao.svrs.rs.gov.br/ws/NfeConsulta/NfeConsulta4.asmx",
            "NfeStatusServico": "https://nfe-homologacao.svrs.rs.gov.br/ws/NfeStatusServico/NfeStatusServico4.asmx",
            "RecepcaoEvento": "https://nfe-homologacao.svrs.rs.gov.br/ws/recepcaoevento/recepcaoevento4.asmx",
            "NfeInutilizacao": "https://nfe-homologacao.svrs.rs.gov.br/ws/nfeinutilizacao/nfeinutilizacao4.asmx",
        }
    }
}

# Mapeamento de UF para autorizador
UF_AUTORIZADOR = {
    "AC": "SVRS", "AL": "SVRS", "AP": "SVRS", "AM": "AM", "BA": "BA",
    "CE": "CE", "DF": "SVRS", "ES": "SVRS", "GO": "GO", "MA": "SVRS",
    "MT": "MT", "MS": "MS", "MG": "MG", "PA": "SVRS", "PB": "SVRS",
    "PR": "PR", "PE": "PE", "PI": "SVRS", "RJ": "SVRS", "RN": "SVRS",
    "RS": "RS", "RO": "SVRS", "RR": "SVRS", "SC": "SVRS", "SP": "SP",
    "SE": "SVRS", "TO": "SVRS"
}


class SEFAZTransmitter:
    """Transmissor de documentos para a SEFAZ"""
    
    def __init__(self, empresa):
        """
        Inicializa o transmissor
        
        Args:
            empresa: Nome da empresa
        """
        self.empresa = empresa
        self.config = self._get_config()
        self.cert_file = None
        self.key_file = None
        self._prepare_certificate()
    
    def _get_config(self):
        """Obtém configuração fiscal da empresa"""
        from erpnext_fiscal_br.fiscal_br.doctype.configuracao_fiscal.configuracao_fiscal import ConfiguracaoFiscal
        
        config = ConfiguracaoFiscal.get_config_for_company(self.empresa)
        if not config:
            frappe.throw(_("Configuração fiscal não encontrada"))
        return config
    
    def _prepare_certificate(self):
        """Prepara os arquivos de certificado para uso com requests"""
        from erpnext_fiscal_br.fiscal_br.doctype.certificado_digital.certificado_digital import CertificadoDigital
        
        cert_doc = CertificadoDigital.get_valid_certificate(self.empresa)
        if not cert_doc:
            frappe.throw(_("Certificado digital não encontrado"))
        
        # Obtém PEM
        cert_pem = cert_doc.get_pem_certificate()
        key_pem = cert_doc.get_pem_private_key()
        
        if not cert_pem or not key_pem:
            frappe.throw(_("Erro ao obter certificado em formato PEM"))
        
        # Cria arquivos temporários
        self.cert_file = tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False)
        self.cert_file.write(cert_pem)
        self.cert_file.close()
        
        self.key_file = tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False)
        self.key_file.write(key_pem)
        self.key_file.close()
    
    def __del__(self):
        """Limpa arquivos temporários"""
        try:
            if self.cert_file and os.path.exists(self.cert_file.name):
                os.unlink(self.cert_file.name)
            if self.key_file and os.path.exists(self.key_file.name):
                os.unlink(self.key_file.name)
        except:
            pass
    
    def _get_url(self, servico, modelo="55"):
        """Obtém URL do serviço"""
        uf = self.config.uf_emissao
        ambiente = self.config.get_ambiente_codigo()
        
        # Determina autorizador
        autorizador = UF_AUTORIZADOR.get(uf, "SVRS")
        
        # Para NFCe, ajusta serviço
        if modelo == "65" and servico in ["NfeAutorizacao", "NfeRetAutorizacao"]:
            servico = servico.replace("Nfe", "Nfce")
        
        urls = SEFAZ_URLS.get(autorizador, SEFAZ_URLS.get("SVRS"))
        urls_ambiente = urls.get(ambiente, urls.get("2"))
        
        return urls_ambiente.get(servico)
    
    def _send_request(self, url, xml_body, soap_action):
        """Envia requisição SOAP para a SEFAZ"""
        # Envelope SOAP
        soap_envelope = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap12:Envelope xmlns:soap12="http://www.w3.org/2003/05/soap-envelope" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <soap12:Body>
        {xml_body}
    </soap12:Body>
</soap12:Envelope>'''
        
        headers = {
            'Content-Type': 'application/soap+xml; charset=utf-8',
            'SOAPAction': soap_action
        }
        
        timeout = self.config.timeout_sefaz or 30
        
        try:
            response = requests.post(
                url,
                data=soap_envelope.encode('utf-8'),
                headers=headers,
                cert=(self.cert_file.name, self.key_file.name),
                timeout=timeout,
                verify=True
            )
            
            response.raise_for_status()
            return response.text
            
        except requests.exceptions.SSLError as e:
            frappe.log_error(f"Erro SSL na comunicação com SEFAZ: {str(e)}")
            raise Exception(f"Erro de certificado: {str(e)}")
        
        except requests.exceptions.Timeout:
            raise Exception("Timeout na comunicação com a SEFAZ")
        
        except requests.exceptions.RequestException as e:
            frappe.log_error(f"Erro na comunicação com SEFAZ: {str(e)}")
            raise Exception(f"Erro de comunicação: {str(e)}")
    
    def _parse_response(self, response_xml, tag_retorno):
        """Parse da resposta da SEFAZ"""
        try:
            # Remove namespaces para facilitar parse
            response_xml = response_xml.replace('xmlns:', 'xmlns_')
            root = etree.fromstring(response_xml.encode('utf-8'))
            
            # Procura tag de retorno
            retorno = root.find(f'.//{tag_retorno}')
            if retorno is None:
                # Tenta com namespace
                for elem in root.iter():
                    if tag_retorno in elem.tag:
                        retorno = elem
                        break
            
            if retorno is None:
                return {"cStat": "999", "xMotivo": "Resposta inválida da SEFAZ"}
            
            resultado = {}
            
            # Extrai campos principais
            for campo in ['cStat', 'xMotivo', 'nProt', 'dhRecbto', 'chNFe', 'cUF', 'tpAmb']:
                elem = retorno.find(f'.//{campo}')
                if elem is not None and elem.text:
                    resultado[campo] = elem.text
            
            # Procura protNFe
            prot_nfe = retorno.find('.//protNFe')
            if prot_nfe is not None:
                inf_prot = prot_nfe.find('.//infProt')
                if inf_prot is not None:
                    for campo in ['cStat', 'xMotivo', 'nProt', 'dhRecbto', 'chNFe', 'digVal']:
                        elem = inf_prot.find(f'.//{campo}')
                        if elem is not None and elem.text:
                            resultado[campo] = elem.text
            
            return resultado
            
        except Exception as e:
            frappe.log_error(f"Erro ao parsear resposta SEFAZ: {str(e)}\n{response_xml}")
            return {"cStat": "999", "xMotivo": f"Erro ao processar resposta: {str(e)}"}
    
    def consultar_status_servico(self):
        """Consulta status do serviço da SEFAZ"""
        url = self._get_url("NfeStatusServico")
        
        ambiente = self.config.get_ambiente_codigo()
        uf = self.config.codigo_uf
        
        xml_body = f'''<nfeDadosMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeStatusServico4">
    <consStatServ xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
        <tpAmb>{ambiente}</tpAmb>
        <cUF>{uf}</cUF>
        <xServ>STATUS</xServ>
    </consStatServ>
</nfeDadosMsg>'''
        
        response = self._send_request(url, xml_body, "http://www.portalfiscal.inf.br/nfe/wsdl/NFeStatusServico4/nfeStatusServicoNF")
        return self._parse_response(response, "retConsStatServ")
    
    def enviar_nfe(self, xml_assinado, modelo="55"):
        """
        Envia NFe/NFCe para autorização
        
        Args:
            xml_assinado: XML da NFe assinado
            modelo: "55" para NFe, "65" para NFCe
        
        Returns:
            dict: Resultado da autorização
        """
        url = self._get_url("NfeAutorizacao", modelo)
        
        ambiente = self.config.get_ambiente_codigo()
        uf = self.config.codigo_uf
        
        # Monta lote
        id_lote = str(int(now_datetime().timestamp()))[-15:]
        
        # Remove declaração XML do documento assinado
        xml_nfe = xml_assinado
        if xml_nfe.startswith('<?xml'):
            xml_nfe = xml_nfe.split('?>', 1)[1].strip()
        
        xml_body = f'''<nfeDadosMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4">
    <enviNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
        <idLote>{id_lote}</idLote>
        <indSinc>1</indSinc>
        {xml_nfe}
    </enviNFe>
</nfeDadosMsg>'''
        
        response = self._send_request(
            url, 
            xml_body, 
            "http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4/nfeAutorizacaoLote"
        )
        
        resultado = self._parse_response(response, "retEnviNFe")
        
        # Se foi processamento assíncrono, consulta recibo
        if resultado.get("cStat") == "103":  # Lote recebido com sucesso
            recibo = resultado.get("nRec")
            if recibo:
                return self.consultar_recibo(recibo, modelo)
        
        # Extrai XML processado se autorizado
        if resultado.get("cStat") in ["100", "150"]:
            try:
                root = etree.fromstring(response.encode('utf-8'))
                proc_nfe = root.find('.//{http://www.portalfiscal.inf.br/nfe}protNFe')
                if proc_nfe is not None:
                    # Monta procNFe
                    resultado["xml_proc"] = self._montar_proc_nfe(xml_assinado, etree.tostring(proc_nfe, encoding='unicode'))
            except:
                pass
        
        return resultado
    
    def consultar_recibo(self, recibo, modelo="55"):
        """Consulta resultado do processamento de um lote"""
        url = self._get_url("NfeRetAutorizacao", modelo)
        
        ambiente = self.config.get_ambiente_codigo()
        
        xml_body = f'''<nfeDadosMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRetAutorizacao4">
    <consReciNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
        <tpAmb>{ambiente}</tpAmb>
        <nRec>{recibo}</nRec>
    </consReciNFe>
</nfeDadosMsg>'''
        
        response = self._send_request(
            url,
            xml_body,
            "http://www.portalfiscal.inf.br/nfe/wsdl/NFeRetAutorizacao4/nfeRetAutorizacaoLote"
        )
        
        return self._parse_response(response, "retConsReciNFe")
    
    def consultar_nfe(self, chave_acesso):
        """Consulta uma NFe pela chave de acesso"""
        url = self._get_url("NfeConsultaProtocolo")
        
        ambiente = self.config.get_ambiente_codigo()
        
        xml_body = f'''<nfeDadosMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeConsultaProtocolo4">
    <consSitNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
        <tpAmb>{ambiente}</tpAmb>
        <xServ>CONSULTAR</xServ>
        <chNFe>{chave_acesso}</chNFe>
    </consSitNFe>
</nfeDadosMsg>'''
        
        response = self._send_request(
            url,
            xml_body,
            "http://www.portalfiscal.inf.br/nfe/wsdl/NFeConsultaProtocolo4/nfeConsultaNF"
        )
        
        return self._parse_response(response, "retConsSitNFe")
    
    def cancelar_nfe(self, chave_acesso, protocolo, justificativa):
        """
        Cancela uma NFe
        
        Args:
            chave_acesso: Chave de acesso da NFe
            protocolo: Protocolo de autorização
            justificativa: Justificativa do cancelamento (mín. 15 caracteres)
        
        Returns:
            dict: Resultado do cancelamento
        """
        from erpnext_fiscal_br.services.signer import XMLSigner
        
        url = self._get_url("RecepcaoEvento")
        
        ambiente = self.config.get_ambiente_codigo()
        cnpj = self.config.cnpj
        
        # Monta evento de cancelamento
        data_evento = now_datetime().strftime("%Y-%m-%dT%H:%M:%S-03:00")
        id_evento = f"ID110111{chave_acesso}01"
        
        xml_evento = f'''<?xml version="1.0" encoding="UTF-8"?>
<evento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00">
    <infEvento Id="{id_evento}">
        <cOrgao>{self.config.codigo_uf}</cOrgao>
        <tpAmb>{ambiente}</tpAmb>
        <CNPJ>{cnpj}</CNPJ>
        <chNFe>{chave_acesso}</chNFe>
        <dhEvento>{data_evento}</dhEvento>
        <tpEvento>110111</tpEvento>
        <nSeqEvento>1</nSeqEvento>
        <verEvento>1.00</verEvento>
        <detEvento versao="1.00">
            <descEvento>Cancelamento</descEvento>
            <nProt>{protocolo}</nProt>
            <xJust>{justificativa}</xJust>
        </detEvento>
    </infEvento>
</evento>'''
        
        # Assina evento
        signer = XMLSigner(self.empresa)
        xml_assinado = signer.sign(xml_evento)
        
        # Remove declaração XML
        if xml_assinado.startswith('<?xml'):
            xml_assinado = xml_assinado.split('?>', 1)[1].strip()
        
        xml_body = f'''<nfeDadosMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4">
    <envEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00">
        <idLote>{int(now_datetime().timestamp())}</idLote>
        {xml_assinado}
    </envEvento>
</nfeDadosMsg>'''
        
        response = self._send_request(
            url,
            xml_body,
            "http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4/nfeRecepcaoEvento"
        )
        
        return self._parse_response(response, "retEnvEvento")
    
    def carta_correcao(self, chave_acesso, correcao, sequencia=1):
        """
        Envia carta de correção (CCe)
        
        Args:
            chave_acesso: Chave de acesso da NFe
            correcao: Texto da correção
            sequencia: Número sequencial do evento
        
        Returns:
            dict: Resultado do envio
        """
        from erpnext_fiscal_br.services.signer import XMLSigner
        
        url = self._get_url("RecepcaoEvento")
        
        ambiente = self.config.get_ambiente_codigo()
        cnpj = self.config.cnpj
        
        data_evento = now_datetime().strftime("%Y-%m-%dT%H:%M:%S-03:00")
        id_evento = f"ID110110{chave_acesso}{str(sequencia).zfill(2)}"
        
        xml_evento = f'''<?xml version="1.0" encoding="UTF-8"?>
<evento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00">
    <infEvento Id="{id_evento}">
        <cOrgao>{self.config.codigo_uf}</cOrgao>
        <tpAmb>{ambiente}</tpAmb>
        <CNPJ>{cnpj}</CNPJ>
        <chNFe>{chave_acesso}</chNFe>
        <dhEvento>{data_evento}</dhEvento>
        <tpEvento>110110</tpEvento>
        <nSeqEvento>{sequencia}</nSeqEvento>
        <verEvento>1.00</verEvento>
        <detEvento versao="1.00">
            <descEvento>Carta de Correcao</descEvento>
            <xCorrecao>{correcao}</xCorrecao>
            <xCondUso>A Carta de Correcao e disciplinada pelo paragrafo 1o-A do art. 7o do Convenio S/N, de 15 de dezembro de 1970 e pode ser utilizada para regularizacao de erro ocorrido na emissao de documento fiscal, desde que o erro nao esteja relacionado com: I - as variaveis que determinam o valor do imposto tais como: base de calculo, aliquota, diferenca de preco, quantidade, valor da operacao ou da prestacao; II - a correcao de dados cadastrais que implique mudanca do remetente ou do destinatario; III - a data de emissao ou de saida.</xCondUso>
        </detEvento>
    </infEvento>
</evento>'''
        
        # Assina evento
        signer = XMLSigner(self.empresa)
        xml_assinado = signer.sign(xml_evento)
        
        if xml_assinado.startswith('<?xml'):
            xml_assinado = xml_assinado.split('?>', 1)[1].strip()
        
        xml_body = f'''<nfeDadosMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4">
    <envEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00">
        <idLote>{int(now_datetime().timestamp())}</idLote>
        {xml_assinado}
    </envEvento>
</nfeDadosMsg>'''
        
        response = self._send_request(
            url,
            xml_body,
            "http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4/nfeRecepcaoEvento"
        )
        
        return self._parse_response(response, "retEnvEvento")
    
    def inutilizar_numeracao(self, serie, numero_inicial, numero_final, justificativa, modelo="55"):
        """
        Inutiliza uma faixa de numeração
        
        Args:
            serie: Série da numeração
            numero_inicial: Número inicial
            numero_final: Número final
            justificativa: Justificativa da inutilização
            modelo: "55" para NFe, "65" para NFCe
        
        Returns:
            dict: Resultado da inutilização
        """
        from erpnext_fiscal_br.services.signer import XMLSigner
        
        url = self._get_url("NfeInutilizacao")
        
        ambiente = self.config.get_ambiente_codigo()
        cnpj = self.config.cnpj
        ano = now_datetime().strftime("%y")
        
        # ID: ID + cUF + Ano + CNPJ + mod + serie + nNFIni + nNFFin
        id_inut = f"ID{self.config.codigo_uf}{ano}{cnpj}{modelo}{str(serie).zfill(3)}{str(numero_inicial).zfill(9)}{str(numero_final).zfill(9)}"
        
        xml_inut = f'''<?xml version="1.0" encoding="UTF-8"?>
<inutNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
    <infInut Id="{id_inut}">
        <tpAmb>{ambiente}</tpAmb>
        <xServ>INUTILIZAR</xServ>
        <cUF>{self.config.codigo_uf}</cUF>
        <ano>{ano}</ano>
        <CNPJ>{cnpj}</CNPJ>
        <mod>{modelo}</mod>
        <serie>{serie}</serie>
        <nNFIni>{numero_inicial}</nNFIni>
        <nNFFin>{numero_final}</nNFFin>
        <xJust>{justificativa}</xJust>
    </infInut>
</inutNFe>'''
        
        # Assina
        signer = XMLSigner(self.empresa)
        xml_assinado = signer.sign(xml_inut)
        
        if xml_assinado.startswith('<?xml'):
            xml_assinado = xml_assinado.split('?>', 1)[1].strip()
        
        xml_body = f'''<nfeDadosMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeInutilizacao4">
    {xml_assinado}
</nfeDadosMsg>'''
        
        response = self._send_request(
            url,
            xml_body,
            "http://www.portalfiscal.inf.br/nfe/wsdl/NFeInutilizacao4/nfeInutilizacaoNF"
        )
        
        return self._parse_response(response, "retInutNFe")
    
    def _montar_proc_nfe(self, xml_nfe, xml_prot):
        """Monta o XML processado (procNFe)"""
        # Remove declarações XML
        if xml_nfe.startswith('<?xml'):
            xml_nfe = xml_nfe.split('?>', 1)[1].strip()
        if xml_prot.startswith('<?xml'):
            xml_prot = xml_prot.split('?>', 1)[1].strip()
        
        proc_nfe = f'''<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
{xml_nfe}
{xml_prot}
</nfeProc>'''
        
        return proc_nfe
