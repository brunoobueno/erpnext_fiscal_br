"""
Certificado Digital
Gerencia certificados digitais A1 para assinatura de NFe/NFCe
"""

import os
import re
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, date_diff, getdate
from datetime import datetime

try:
    from cryptography import x509
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.serialization import pkcs12
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


class CertificadoDigital(Document):
    def validate(self):
        if self.arquivo_pfx and self.senha:
            self.extrair_dados_certificado()
    
    def before_save(self):
        self.atualizar_status()
    
    def extrair_dados_certificado(self):
        """Extrai informações do certificado digital"""
        if not HAS_CRYPTOGRAPHY:
            frappe.msgprint(_("Biblioteca cryptography não instalada. Instale com: pip install cryptography"))
            return
        
        try:
            # Obtém o conteúdo do arquivo
            pfx_content = self.get_pfx_content()
            if not pfx_content:
                return
            
            senha = self.get_password("senha")
            if not senha:
                frappe.throw(_("Senha do certificado é obrigatória"))
            
            # Carrega o certificado
            private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
                pfx_content,
                senha.encode(),
                default_backend()
            )
            
            if certificate is None:
                frappe.throw(_("Não foi possível carregar o certificado"))
            
            # Extrai informações
            self.validade_inicio = certificate.not_valid_before_utc
            self.validade_fim = certificate.not_valid_after_utc
            self.serial_number = str(certificate.serial_number)
            
            # Extrai o subject (razão social e CNPJ)
            subject = certificate.subject
            for attr in subject:
                if attr.oid == x509.oid.NameOID.COMMON_NAME:
                    cn = attr.value
                    self.razao_social_certificado = cn
                    # Tenta extrair CNPJ do CN
                    cnpj_match = re.search(r'\d{14}', cn.replace(".", "").replace("/", "").replace("-", ""))
                    if cnpj_match:
                        self.cnpj_certificado = cnpj_match.group()
            
            # Extrai emissor
            issuer = certificate.issuer
            for attr in issuer:
                if attr.oid == x509.oid.NameOID.COMMON_NAME:
                    self.emissor = attr.value
                    break
            
            # Calcula fingerprint
            self.fingerprint = certificate.fingerprint(
                certificate.signature_hash_algorithm
            ).hex().upper()
            
            # Tipo sempre A1 para .pfx
            self.tipo_certificado = "A1"
            
        except Exception as e:
            frappe.log_error(f"Erro ao extrair dados do certificado: {str(e)}")
            self.status = "Inválido"
            frappe.throw(_("Erro ao ler certificado: {0}. Verifique se a senha está correta.").format(str(e)))
    
    def get_pfx_content(self):
        """Obtém o conteúdo binário do arquivo PFX"""
        if not self.arquivo_pfx:
            return None
        
        try:
            file_doc = frappe.get_doc("File", {"file_url": self.arquivo_pfx})
            file_path = file_doc.get_full_path()
            
            with open(file_path, "rb") as f:
                return f.read()
        except Exception as e:
            frappe.log_error(f"Erro ao ler arquivo PFX: {str(e)}")
            return None
    
    def atualizar_status(self):
        """Atualiza o status do certificado baseado na validade"""
        if not self.validade_fim:
            self.status = "Pendente"
            return
        
        hoje = now_datetime()
        validade = self.validade_fim
        
        if isinstance(validade, str):
            validade = datetime.fromisoformat(validade.replace("Z", "+00:00"))
        
        # Calcula dias para expirar
        if hasattr(validade, 'date'):
            dias = date_diff(validade.date(), hoje.date())
        else:
            dias = date_diff(validade, hoje.date())
        
        self.dias_para_expirar = dias
        
        if dias < 0:
            self.status = "Expirado"
        elif dias <= 30:
            self.status = "Expirando"
        else:
            self.status = "Válido"
    
    def get_certificate_and_key(self):
        """
        Retorna o certificado e chave privada para assinatura
        
        Returns:
            tuple: (private_key, certificate) ou (None, None) se erro
        """
        if not HAS_CRYPTOGRAPHY:
            frappe.throw(_("Biblioteca cryptography não instalada"))
        
        try:
            pfx_content = self.get_pfx_content()
            senha = self.get_password("senha")
            
            private_key, certificate, _ = pkcs12.load_key_and_certificates(
                pfx_content,
                senha.encode(),
                default_backend()
            )
            
            return private_key, certificate
            
        except Exception as e:
            frappe.log_error(f"Erro ao carregar certificado: {str(e)}")
            return None, None
    
    def get_pem_certificate(self):
        """Retorna o certificado em formato PEM"""
        private_key, certificate = self.get_certificate_and_key()
        
        if certificate:
            return certificate.public_bytes(serialization.Encoding.PEM).decode()
        return None
    
    def get_pem_private_key(self):
        """Retorna a chave privada em formato PEM"""
        private_key, certificate = self.get_certificate_and_key()
        
        if private_key:
            return private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode()
        return None
    
    @staticmethod
    def get_valid_certificate(empresa):
        """
        Retorna um certificado válido para a empresa
        
        Args:
            empresa: Nome da empresa
        
        Returns:
            CertificadoDigital: Documento do certificado ou None
        """
        cert_name = frappe.db.get_value(
            "Certificado Digital",
            {
                "empresa": empresa,
                "status": ["in", ["Válido", "Expirando"]]
            },
            "name",
            order_by="validade_fim desc"
        )
        
        if cert_name:
            return frappe.get_doc("Certificado Digital", cert_name)
        
        return None


@frappe.whitelist()
def verificar_certificado(name):
    """
    Verifica e atualiza o status de um certificado
    
    Args:
        name: Nome do documento do certificado
    
    Returns:
        dict: Status atualizado
    """
    cert = frappe.get_doc("Certificado Digital", name)
    cert.atualizar_status()
    cert.save(ignore_permissions=True)
    
    return {
        "status": cert.status,
        "dias_para_expirar": cert.dias_para_expirar,
        "validade_fim": cert.validade_fim
    }


@frappe.whitelist()
def get_certificado_empresa(empresa):
    """
    Retorna informações do certificado válido de uma empresa
    
    Args:
        empresa: Nome da empresa
    
    Returns:
        dict: Dados do certificado ou erro
    """
    cert = CertificadoDigital.get_valid_certificate(empresa)
    
    if not cert:
        return {
            "success": False,
            "message": _("Nenhum certificado válido encontrado para a empresa {0}").format(empresa)
        }
    
    return {
        "success": True,
        "certificado": cert.name,
        "status": cert.status,
        "validade_fim": cert.validade_fim,
        "dias_para_expirar": cert.dias_para_expirar,
        "cnpj": cert.cnpj_certificado
    }
