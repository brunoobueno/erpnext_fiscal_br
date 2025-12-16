"""
XML Signer - Assinatura digital de XML
Assina documentos XML com certificado digital A1
"""

import frappe
from frappe import _
from lxml import etree
import hashlib
import base64

try:
    from signxml import XMLSigner as SignXMLSigner, methods
    HAS_SIGNXML = True
except ImportError:
    HAS_SIGNXML = False

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.serialization import pkcs12
    from cryptography.hazmat.backends import default_backend
    from cryptography import x509
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


class XMLSigner:
    """Assinador de XML para NFe/NFCe"""
    
    def __init__(self, empresa):
        """
        Inicializa o assinador
        
        Args:
            empresa: Nome da empresa
        """
        self.empresa = empresa
        self.certificate = None
        self.private_key = None
        self._load_certificate()
    
    def _load_certificate(self):
        """Carrega o certificado digital da empresa"""
        from erpnext_fiscal_br.fiscal_br.doctype.certificado_digital.certificado_digital import CertificadoDigital
        
        cert_doc = CertificadoDigital.get_valid_certificate(self.empresa)
        
        if not cert_doc:
            frappe.throw(_("Nenhum certificado digital válido encontrado para a empresa {0}").format(self.empresa))
        
        self.private_key, self.certificate = cert_doc.get_certificate_and_key()
        
        if not self.private_key or not self.certificate:
            frappe.throw(_("Erro ao carregar certificado digital"))
    
    def sign(self, xml_string):
        """
        Assina um XML
        
        Args:
            xml_string: XML em formato string
        
        Returns:
            str: XML assinado
        """
        if not HAS_SIGNXML:
            return self._sign_manual(xml_string)
        
        return self._sign_with_signxml(xml_string)
    
    def _sign_with_signxml(self, xml_string):
        """Assina usando a biblioteca signxml"""
        try:
            # Remove declaração XML se existir
            xml_clean = xml_string
            if xml_clean.startswith('<?xml'):
                xml_clean = xml_clean.split('?>', 1)[1].strip()
            
            # Parse do XML
            root = etree.fromstring(xml_clean.encode('utf-8'))
            
            # Encontra o elemento a ser assinado (infNFe)
            ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
            inf_nfe = root.find('.//nfe:infNFe', ns)
            
            if inf_nfe is None:
                # Tenta sem namespace
                inf_nfe = root.find('.//infNFe')
            
            if inf_nfe is None:
                frappe.throw(_("Elemento infNFe não encontrado no XML"))
            
            # Obtém o ID para referência
            id_value = inf_nfe.get('Id')
            
            # Converte certificado e chave para PEM
            cert_pem = self.certificate.public_bytes(serialization.Encoding.PEM)
            key_pem = self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            # Configura o assinador
            signer = SignXMLSigner(
                method=methods.enveloped,
                signature_algorithm="rsa-sha1",
                digest_algorithm="sha1",
                c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"
            )
            
            # Assina o elemento infNFe
            signed_root = signer.sign(
                root,
                key=key_pem,
                cert=cert_pem,
                reference_uri=f"#{id_value}" if id_value else None
            )
            
            # Converte para string sem formatação
            xml_assinado = etree.tostring(signed_root, encoding='unicode')
            
            # Adiciona declaração XML
            xml_assinado = '<?xml version="1.0" encoding="UTF-8"?>' + xml_assinado
            
            return xml_assinado
            
        except Exception as e:
            frappe.log_error(f"Erro ao assinar XML com signxml: {str(e)}")
            # Tenta método manual como fallback
            return self._sign_manual(xml_string)
    
    def _sign_manual(self, xml_string):
        """
        Assina XML manualmente (fallback)
        Implementação da assinatura XMLDSig para NFe
        """
        try:
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import padding
            
            NS_NFE = '{http://www.portalfiscal.inf.br/nfe}'
            
            # Remove declaração XML se existir (será adicionada no final)
            xml_clean = xml_string
            if xml_clean.startswith('<?xml'):
                xml_clean = xml_clean.split('?>', 1)[1].strip()
            
            # Parse do XML
            root = etree.fromstring(xml_clean.encode('utf-8'))
            
            # Encontra infNFe
            inf_nfe = root.find(f'.//{NS_NFE}infNFe')
            if inf_nfe is None:
                inf_nfe = root.find('.//infNFe')
            
            if inf_nfe is None:
                frappe.throw(_("Elemento infNFe não encontrado"))
            
            id_value = inf_nfe.get('Id')
            
            # Canonicaliza o elemento a ser assinado (C14N inclusivo sem comentários)
            # IMPORTANTE: Para NFe, deve-se usar C14N inclusivo
            c14n_inf_nfe = etree.tostring(inf_nfe, method='c14n', exclusive=False, with_comments=False)
            
            # Calcula digest (SHA-1)
            digest = hashlib.sha1(c14n_inf_nfe).digest()
            digest_b64 = base64.b64encode(digest).decode()
            
            # Cria SignedInfo como string para garantir formato correto
            signed_info_xml = (
                '<SignedInfo xmlns="http://www.w3.org/2000/09/xmldsig#">'
                '<CanonicalizationMethod Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"/>'
                '<SignatureMethod Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1"/>'
                f'<Reference URI="#{id_value}">'
                '<Transforms>'
                '<Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"/>'
                '<Transform Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"/>'
                '</Transforms>'
                '<DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"/>'
                f'<DigestValue>{digest_b64}</DigestValue>'
                '</Reference>'
                '</SignedInfo>'
            )
            
            # Parse SignedInfo para canonicalização
            signed_info_elem = etree.fromstring(signed_info_xml.encode('utf-8'))
            
            # Canonicaliza SignedInfo para calcular assinatura
            signed_info_c14n = etree.tostring(signed_info_elem, method='c14n', exclusive=False, with_comments=False)
            
            # Assina SignedInfo com a chave privada
            signature_bytes = self.private_key.sign(
                signed_info_c14n,
                padding.PKCS1v15(),
                hashes.SHA1()
            )
            signature_b64 = base64.b64encode(signature_bytes).decode()
            
            # Certificado em base64 (DER format)
            cert_der = self.certificate.public_bytes(serialization.Encoding.DER)
            cert_b64 = base64.b64encode(cert_der).decode()
            
            # Cria elemento Signature completo como string
            # Remove xmlns do SignedInfo interno pois já está no Signature
            signed_info_inner = signed_info_xml.replace(' xmlns="http://www.w3.org/2000/09/xmldsig#"', '')
            
            signature_xml = (
                '<Signature xmlns="http://www.w3.org/2000/09/xmldsig#">'
                f'{signed_info_inner}'
                f'<SignatureValue>{signature_b64}</SignatureValue>'
                '<KeyInfo>'
                '<X509Data>'
                f'<X509Certificate>{cert_b64}</X509Certificate>'
                '</X509Data>'
                '</KeyInfo>'
                '</Signature>'
            )
            
            # Parse Signature
            signature_elem = etree.fromstring(signature_xml.encode('utf-8'))
            
            # Insere Signature após infNFe (dentro do mesmo parent)
            inf_nfe.addnext(signature_elem)
            
            # Converte para string sem pretty print
            xml_assinado = etree.tostring(root, encoding='unicode')
            
            # Adiciona declaração XML
            xml_assinado = '<?xml version="1.0" encoding="UTF-8"?>' + xml_assinado
            
            return xml_assinado
            
        except Exception as e:
            frappe.log_error(f"Erro ao assinar XML manualmente: {str(e)}")
            raise
    
    def _create_signed_info(self, reference_id, digest_value):
        """Cria o elemento SignedInfo"""
        return f'<SignedInfo xmlns="http://www.w3.org/2000/09/xmldsig#"><CanonicalizationMethod Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"/><SignatureMethod Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1"/><Reference URI="#{reference_id}"><Transforms><Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"/><Transform Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"/></Transforms><DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"/><DigestValue>{digest_value}</DigestValue></Reference></SignedInfo>'
    
    def _create_signature_element(self, signed_info, signature_value, certificate):
        """Cria o elemento Signature completo"""
        # Remove declaração xmlns do SignedInfo para inserção
        signed_info_clean = signed_info.replace(' xmlns="http://www.w3.org/2000/09/xmldsig#"', '')
        
        return f'<Signature xmlns="http://www.w3.org/2000/09/xmldsig#">{signed_info_clean}<SignatureValue>{signature_value}</SignatureValue><KeyInfo><X509Data><X509Certificate>{certificate}</X509Certificate></X509Data></KeyInfo></Signature>'
    
    def sign_evento(self, xml_string, reference_id):
        """
        Assina um XML de evento (cancelamento, CCe, etc.)
        
        Args:
            xml_string: XML do evento
            reference_id: ID de referência para assinatura
        
        Returns:
            str: XML assinado
        """
        # Usa o mesmo processo de assinatura
        return self.sign(xml_string)


def assinar_xml(empresa, xml_string):
    """
    Função utilitária para assinar XML
    
    Args:
        empresa: Nome da empresa
        xml_string: XML a ser assinado
    
    Returns:
        str: XML assinado
    """
    signer = XMLSigner(empresa)
    return signer.sign(xml_string)
