"""
Tarefas agendadas do módulo fiscal
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, add_days, getdate


def check_certificate_expiry():
    """
    Verifica certificados próximos do vencimento
    Executado diariamente
    """
    # Busca certificados que expiram em 30 dias ou menos
    certificates = frappe.get_all(
        "Certificado Digital",
        filters={
            "status": ["in", ["Válido", "Expirando"]]
        },
        fields=["name", "empresa", "validade_fim", "dias_para_expirar"]
    )
    
    for cert in certificates:
        # Atualiza status
        cert_doc = frappe.get_doc("Certificado Digital", cert.name)
        cert_doc.atualizar_status()
        cert_doc.save(ignore_permissions=True)
        
        # Envia alerta se estiver expirando
        if cert_doc.status == "Expirando":
            send_certificate_alert(cert_doc)
        elif cert_doc.status == "Expirado":
            send_certificate_expired_alert(cert_doc)
    
    frappe.db.commit()


def send_certificate_alert(cert):
    """Envia alerta de certificado expirando"""
    # Busca usuários com role Fiscal Manager
    users = frappe.get_all(
        "Has Role",
        filters={"role": "Fiscal Manager"},
        fields=["parent"]
    )
    
    for user in users:
        frappe.sendmail(
            recipients=[user.parent],
            subject=_("Certificado Digital Expirando - {0}").format(cert.empresa),
            message=_("""
                <p>O certificado digital da empresa <b>{0}</b> está expirando.</p>
                <p><b>Validade:</b> {1}</p>
                <p><b>Dias restantes:</b> {2}</p>
                <p>Por favor, providencie a renovação do certificado.</p>
            """).format(cert.empresa, cert.validade_fim, cert.dias_para_expirar)
        )


def send_certificate_expired_alert(cert):
    """Envia alerta de certificado expirado"""
    users = frappe.get_all(
        "Has Role",
        filters={"role": "Fiscal Manager"},
        fields=["parent"]
    )
    
    for user in users:
        frappe.sendmail(
            recipients=[user.parent],
            subject=_("URGENTE: Certificado Digital Expirado - {0}").format(cert.empresa),
            message=_("""
                <p><b>ATENÇÃO:</b> O certificado digital da empresa <b>{0}</b> está <b>EXPIRADO</b>.</p>
                <p><b>Validade:</b> {1}</p>
                <p>Não será possível emitir notas fiscais até que um novo certificado seja instalado.</p>
            """).format(cert.empresa, cert.validade_fim)
        )


def retry_pending_notes():
    """
    Tenta reenviar notas pendentes
    Executado a cada hora
    """
    # Busca notas com status Pendente ou Processando há mais de 5 minutos
    from datetime import timedelta
    
    cutoff_time = now_datetime() - timedelta(minutes=5)
    
    pending_notes = frappe.get_all(
        "Nota Fiscal",
        filters={
            "status": ["in", ["Pendente", "Processando"]],
            "modified": ["<", cutoff_time]
        },
        fields=["name"]
    )
    
    for note in pending_notes:
        try:
            nf = frappe.get_doc("Nota Fiscal", note.name)
            
            # Verifica se tem configuração e certificado
            from erpnext_fiscal_br.fiscal_br.doctype.configuracao_fiscal.configuracao_fiscal import ConfiguracaoFiscal
            from erpnext_fiscal_br.fiscal_br.doctype.certificado_digital.certificado_digital import CertificadoDigital
            
            config = ConfiguracaoFiscal.get_config_for_company(nf.empresa)
            cert = CertificadoDigital.get_valid_certificate(nf.empresa)
            
            if config and cert:
                # Tenta emitir novamente
                nf.emitir()
                frappe.db.commit()
                
        except Exception as e:
            frappe.log_error(
                f"Erro ao reenviar nota {note.name}: {str(e)}",
                "Retry Pending Notes"
            )


def daily_fiscal_report():
    """
    Gera relatório diário de notas fiscais
    Executado às 6h
    """
    yesterday = add_days(getdate(), -1)
    
    # Conta notas por status
    stats = {}
    for status in ["Autorizada", "Cancelada", "Rejeitada"]:
        count = frappe.db.count(
            "Nota Fiscal",
            filters={
                "status": status,
                "creation": ["between", [yesterday, getdate()]]
            }
        )
        stats[status] = count
    
    # Se não houver notas, não envia
    total = sum(stats.values())
    if total == 0:
        return
    
    # Envia relatório
    users = frappe.get_all(
        "Has Role",
        filters={"role": "Fiscal Manager"},
        fields=["parent"]
    )
    
    for user in users:
        frappe.sendmail(
            recipients=[user.parent],
            subject=_("Relatório Fiscal Diário - {0}").format(yesterday),
            message=_("""
                <h3>Relatório de Notas Fiscais - {0}</h3>
                <table border="1" cellpadding="5">
                    <tr><th>Status</th><th>Quantidade</th></tr>
                    <tr><td>Autorizadas</td><td>{1}</td></tr>
                    <tr><td>Canceladas</td><td>{2}</td></tr>
                    <tr><td>Rejeitadas</td><td>{3}</td></tr>
                    <tr><td><b>Total</b></td><td><b>{4}</b></td></tr>
                </table>
            """).format(
                yesterday,
                stats.get("Autorizada", 0),
                stats.get("Cancelada", 0),
                stats.get("Rejeitada", 0),
                total
            )
        )


def cleanup_old_xml_files():
    """
    Remove arquivos XML antigos (mais de 5 anos)
    Executado mensalmente
    """
    # Implementação futura
    pass
