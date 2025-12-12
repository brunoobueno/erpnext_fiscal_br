"""
DANFE Generator - Gerador de DANFE (PDF)
Gera o Documento Auxiliar da Nota Fiscal Eletrônica
"""

import frappe
from frappe import _
from frappe.utils import flt, fmt_money
from io import BytesIO

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm, cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.pdfgen import canvas
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

try:
    import qrcode
    from qrcode.image.pil import PilImage
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

try:
    from barcode import Code128
    from barcode.writer import ImageWriter
    HAS_BARCODE = True
except ImportError:
    HAS_BARCODE = False


class DANFEGenerator:
    """Gerador de DANFE para NFe e NFCe"""
    
    def __init__(self, nota_fiscal):
        """
        Inicializa o gerador
        
        Args:
            nota_fiscal: Documento Nota Fiscal
        """
        self.nf = nota_fiscal
        self.width, self.height = A4
        self.margin = 10 * mm
    
    def generate(self):
        """
        Gera o DANFE em PDF
        
        Returns:
            bytes: Conteúdo do PDF
        """
        if not HAS_REPORTLAB:
            frappe.throw(_("Biblioteca reportlab não instalada. Execute: pip install reportlab"))
        
        if self.nf.modelo == "65":
            return self._generate_danfce()
        else:
            return self._generate_danfe()
    
    def _generate_danfe(self):
        """Gera DANFE para NFe (modelo 55)"""
        buffer = BytesIO()
        
        # Cria canvas
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # Posição inicial
        y = self.height - self.margin
        
        # Cabeçalho
        y = self._draw_header(c, y)
        
        # Dados do emitente
        y = self._draw_emitente(c, y)
        
        # Dados do destinatário
        y = self._draw_destinatario(c, y)
        
        # Dados dos produtos
        y = self._draw_produtos(c, y)
        
        # Totais
        y = self._draw_totais(c, y)
        
        # Informações adicionais
        y = self._draw_info_adicionais(c, y)
        
        c.save()
        
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
    
    def _generate_danfce(self):
        """Gera DANFE para NFCe (modelo 65) - formato simplificado"""
        buffer = BytesIO()
        
        # Tamanho de cupom (80mm de largura)
        page_width = 80 * mm
        page_height = 297 * mm  # Altura variável
        
        c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
        
        y = page_height - 5 * mm
        x_margin = 3 * mm
        
        # Título
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(page_width / 2, y, "DANFE NFC-e")
        y -= 5 * mm
        
        c.setFont("Helvetica", 7)
        c.drawCentredString(page_width / 2, y, "Documento Auxiliar da NFC-e")
        y -= 8 * mm
        
        # Dados do emitente
        company = frappe.get_doc("Company", self.nf.empresa)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(page_width / 2, y, company.company_name[:40])
        y -= 4 * mm
        
        c.setFont("Helvetica", 7)
        c.drawCentredString(page_width / 2, y, f"CNPJ: {self._format_cnpj(self.nf.cpf_cnpj_destinatario)}")
        y -= 8 * mm
        
        # Linha separadora
        c.line(x_margin, y, page_width - x_margin, y)
        y -= 5 * mm
        
        # Itens
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x_margin, y, "ITEM  DESCRIÇÃO")
        y -= 3 * mm
        c.drawString(x_margin, y, "QTD   UN   VL.UNIT   VL.TOTAL")
        y -= 4 * mm
        
        c.setFont("Helvetica", 6)
        for idx, item in enumerate(self.nf.itens, 1):
            c.drawString(x_margin, y, f"{idx:03d}   {item.item_name[:25]}")
            y -= 3 * mm
            c.drawString(x_margin, y, f"{flt(item.quantidade):.2f}  {item.unidade}  {flt(item.valor_unitario):.2f}  {flt(item.valor_total):.2f}")
            y -= 4 * mm
        
        # Linha separadora
        y -= 2 * mm
        c.line(x_margin, y, page_width - x_margin, y)
        y -= 5 * mm
        
        # Totais
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x_margin, y, "TOTAL R$")
        c.drawRightString(page_width - x_margin, y, f"{flt(self.nf.valor_total):.2f}")
        y -= 8 * mm
        
        # Forma de pagamento
        c.setFont("Helvetica", 7)
        c.drawString(x_margin, y, "FORMA DE PAGAMENTO: DINHEIRO")
        y -= 8 * mm
        
        # Linha separadora
        c.line(x_margin, y, page_width - x_margin, y)
        y -= 5 * mm
        
        # QR Code
        if self.nf.qrcode_url and HAS_QRCODE:
            qr_img = self._generate_qrcode(self.nf.qrcode_url)
            if qr_img:
                c.drawImage(qr_img, (page_width - 30*mm) / 2, y - 30*mm, 30*mm, 30*mm)
                y -= 35 * mm
        
        # Chave de acesso
        c.setFont("Helvetica", 6)
        c.drawCentredString(page_width / 2, y, "Chave de Acesso:")
        y -= 3 * mm
        
        chave = self.nf.chave_acesso or ""
        # Divide em grupos de 4
        chave_formatada = " ".join([chave[i:i+4] for i in range(0, len(chave), 4)])
        c.drawCentredString(page_width / 2, y, chave_formatada[:44])
        y -= 3 * mm
        c.drawCentredString(page_width / 2, y, chave_formatada[44:])
        y -= 5 * mm
        
        # Protocolo
        c.drawCentredString(page_width / 2, y, f"Protocolo: {self.nf.protocolo_autorizacao or ''}")
        y -= 3 * mm
        c.drawCentredString(page_width / 2, y, f"Data: {self.nf.data_autorizacao or ''}")
        
        c.save()
        
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
    
    def _draw_header(self, c, y):
        """Desenha o cabeçalho do DANFE"""
        x = self.margin
        box_height = 35 * mm
        
        # Box principal
        c.rect(x, y - box_height, self.width - 2 * self.margin, box_height)
        
        # Divisões internas
        col1 = 60 * mm  # Logo/Emitente
        col2 = 45 * mm  # DANFE
        col3 = self.width - 2 * self.margin - col1 - col2  # Código de barras
        
        c.line(x + col1, y, x + col1, y - box_height)
        c.line(x + col1 + col2, y, x + col1 + col2, y - box_height)
        
        # Coluna 1 - Identificação do emitente
        company = frappe.get_doc("Company", self.nf.empresa)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x + 2*mm, y - 8*mm, company.company_name[:35])
        
        c.setFont("Helvetica", 7)
        c.drawString(x + 2*mm, y - 14*mm, f"CNPJ: {self._format_cnpj(self.config_cnpj)}")
        c.drawString(x + 2*mm, y - 18*mm, f"IE: {self.config_ie}")
        
        # Coluna 2 - DANFE
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(x + col1 + col2/2, y - 8*mm, "DANFE")
        
        c.setFont("Helvetica", 7)
        c.drawCentredString(x + col1 + col2/2, y - 14*mm, "Documento Auxiliar da")
        c.drawCentredString(x + col1 + col2/2, y - 18*mm, "Nota Fiscal Eletrônica")
        
        # Entrada/Saída
        tipo = "SAÍDA" if self.nf.tipo_operacao and "1" in self.nf.tipo_operacao else "ENTRADA"
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(x + col1 + col2/2, y - 26*mm, f"0 - {tipo}")
        
        # Número e série
        c.setFont("Helvetica", 7)
        c.drawCentredString(x + col1 + col2/2, y - 31*mm, f"Nº {self.nf.numero} - Série {self.nf.serie}")
        
        # Coluna 3 - Código de barras
        if self.nf.chave_acesso and HAS_BARCODE:
            barcode_img = self._generate_barcode(self.nf.chave_acesso)
            if barcode_img:
                c.drawImage(barcode_img, x + col1 + col2 + 2*mm, y - 20*mm, col3 - 4*mm, 15*mm)
        
        # Chave de acesso
        c.setFont("Helvetica", 6)
        chave = self.nf.chave_acesso or ""
        c.drawCentredString(x + col1 + col2 + col3/2, y - 28*mm, chave[:22])
        c.drawCentredString(x + col1 + col2 + col3/2, y - 32*mm, chave[22:])
        
        return y - box_height - 2*mm
    
    def _draw_emitente(self, c, y):
        """Desenha dados do emitente"""
        # Simplificado - apenas natureza da operação e protocolo
        x = self.margin
        box_height = 12 * mm
        
        c.rect(x, y - box_height, self.width - 2 * self.margin, box_height)
        
        c.setFont("Helvetica", 6)
        c.drawString(x + 2*mm, y - 3*mm, "NATUREZA DA OPERAÇÃO")
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x + 2*mm, y - 9*mm, self.nf.natureza_operacao or "Venda de mercadoria")
        
        # Protocolo
        c.setFont("Helvetica", 6)
        c.drawString(x + 120*mm, y - 3*mm, "PROTOCOLO DE AUTORIZAÇÃO")
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x + 120*mm, y - 9*mm, f"{self.nf.protocolo_autorizacao or ''} - {self.nf.data_autorizacao or ''}")
        
        return y - box_height - 2*mm
    
    def _draw_destinatario(self, c, y):
        """Desenha dados do destinatário"""
        x = self.margin
        box_height = 25 * mm
        
        c.rect(x, y - box_height, self.width - 2 * self.margin, box_height)
        
        # Título
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x + 2*mm, y - 3*mm, "DESTINATÁRIO/REMETENTE")
        
        # Nome
        c.setFont("Helvetica", 6)
        c.drawString(x + 2*mm, y - 8*mm, "NOME/RAZÃO SOCIAL")
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x + 2*mm, y - 13*mm, self.nf.cliente_nome[:50])
        
        # CNPJ/CPF
        c.setFont("Helvetica", 6)
        c.drawString(x + 120*mm, y - 8*mm, "CNPJ/CPF")
        c.setFont("Helvetica-Bold", 8)
        doc = self.nf.cpf_cnpj_destinatario
        if len(doc) == 11:
            doc = self._format_cpf(doc)
        else:
            doc = self._format_cnpj(doc)
        c.drawString(x + 120*mm, y - 13*mm, doc)
        
        # Endereço
        c.setFont("Helvetica", 6)
        c.drawString(x + 2*mm, y - 18*mm, "ENDEREÇO")
        c.setFont("Helvetica-Bold", 7)
        endereco = f"{self.nf.logradouro}, {self.nf.numero_endereco} - {self.nf.bairro}"
        c.drawString(x + 2*mm, y - 22*mm, endereco[:60])
        
        # Cidade/UF
        c.setFont("Helvetica", 6)
        c.drawString(x + 120*mm, y - 18*mm, "MUNICÍPIO/UF")
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x + 120*mm, y - 22*mm, f"{self.nf.cidade}/{self.nf.uf}")
        
        return y - box_height - 2*mm
    
    def _draw_produtos(self, c, y):
        """Desenha tabela de produtos"""
        x = self.margin
        
        # Cabeçalho
        header_height = 8 * mm
        c.rect(x, y - header_height, self.width - 2 * self.margin, header_height)
        
        c.setFont("Helvetica-Bold", 6)
        cols = [
            (x + 2*mm, "CÓDIGO"),
            (x + 25*mm, "DESCRIÇÃO"),
            (x + 90*mm, "NCM"),
            (x + 105*mm, "CFOP"),
            (x + 118*mm, "UN"),
            (x + 128*mm, "QTD"),
            (x + 145*mm, "VL.UNIT"),
            (x + 165*mm, "VL.TOTAL"),
        ]
        
        for col_x, col_name in cols:
            c.drawString(col_x, y - 5*mm, col_name)
        
        y -= header_height
        
        # Itens
        c.setFont("Helvetica", 6)
        line_height = 4 * mm
        
        for item in self.nf.itens:
            if y < self.margin + 50*mm:  # Nova página se necessário
                c.showPage()
                y = self.height - self.margin
            
            c.drawString(x + 2*mm, y - 3*mm, str(item.item_code or "")[:12])
            c.drawString(x + 25*mm, y - 3*mm, str(item.item_name or "")[:35])
            c.drawString(x + 90*mm, y - 3*mm, str(item.ncm or ""))
            c.drawString(x + 105*mm, y - 3*mm, str(item.cfop or ""))
            c.drawString(x + 118*mm, y - 3*mm, str(item.unidade or "UN"))
            c.drawRightString(x + 143*mm, y - 3*mm, f"{flt(item.quantidade):.2f}")
            c.drawRightString(x + 163*mm, y - 3*mm, f"{flt(item.valor_unitario):.2f}")
            c.drawRightString(x + 185*mm, y - 3*mm, f"{flt(item.valor_total):.2f}")
            
            y -= line_height
        
        # Linha final
        c.line(x, y, self.width - self.margin, y)
        
        return y - 2*mm
    
    def _draw_totais(self, c, y):
        """Desenha totais da nota"""
        x = self.margin
        box_height = 15 * mm
        
        c.rect(x, y - box_height, self.width - 2 * self.margin, box_height)
        
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x + 2*mm, y - 3*mm, "CÁLCULO DO IMPOSTO")
        
        # Valores
        c.setFont("Helvetica", 6)
        valores = [
            ("BASE ICMS", self.nf.valor_icms),
            ("VALOR ICMS", self.nf.valor_icms),
            ("VALOR FRETE", self.nf.valor_frete),
            ("VALOR SEGURO", self.nf.valor_seguro),
            ("DESCONTO", self.nf.valor_desconto),
            ("OUTRAS DESP.", self.nf.valor_outras_despesas),
            ("VALOR IPI", self.nf.valor_ipi),
            ("TOTAL PRODUTOS", self.nf.valor_produtos),
            ("TOTAL NOTA", self.nf.valor_total),
        ]
        
        col_width = (self.width - 2 * self.margin) / len(valores)
        for i, (label, value) in enumerate(valores):
            col_x = x + i * col_width
            c.drawString(col_x + 1*mm, y - 8*mm, label)
            c.setFont("Helvetica-Bold", 7)
            c.drawString(col_x + 1*mm, y - 12*mm, f"{flt(value):.2f}")
            c.setFont("Helvetica", 6)
        
        return y - box_height - 2*mm
    
    def _draw_info_adicionais(self, c, y):
        """Desenha informações adicionais"""
        x = self.margin
        box_height = 20 * mm
        
        c.rect(x, y - box_height, self.width - 2 * self.margin, box_height)
        
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x + 2*mm, y - 3*mm, "INFORMAÇÕES COMPLEMENTARES")
        
        c.setFont("Helvetica", 6)
        info = self.nf.informacoes_complementares or ""
        
        # Quebra texto em linhas
        max_chars = 120
        lines = [info[i:i+max_chars] for i in range(0, len(info), max_chars)]
        
        y_text = y - 8*mm
        for line in lines[:3]:  # Máximo 3 linhas
            c.drawString(x + 2*mm, y_text, line)
            y_text -= 4*mm
        
        return y - box_height
    
    def _generate_barcode(self, code):
        """Gera código de barras"""
        if not HAS_BARCODE:
            return None
        
        try:
            buffer = BytesIO()
            barcode = Code128(code, writer=ImageWriter())
            barcode.write(buffer)
            buffer.seek(0)
            return buffer
        except:
            return None
    
    def _generate_qrcode(self, data):
        """Gera QR Code"""
        if not HAS_QRCODE:
            return None
        
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=1)
            qr.add_data(data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            return buffer
        except:
            return None
    
    def _format_cnpj(self, cnpj):
        """Formata CNPJ"""
        if not cnpj or len(cnpj) != 14:
            return cnpj or ""
        return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
    
    def _format_cpf(self, cpf):
        """Formata CPF"""
        if not cpf or len(cpf) != 11:
            return cpf or ""
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    
    @property
    def config_cnpj(self):
        """Obtém CNPJ da configuração"""
        from erpnext_fiscal_br.fiscal_br.doctype.configuracao_fiscal.configuracao_fiscal import ConfiguracaoFiscal
        config = ConfiguracaoFiscal.get_config_for_company(self.nf.empresa)
        return config.cnpj if config else ""
    
    @property
    def config_ie(self):
        """Obtém IE da configuração"""
        from erpnext_fiscal_br.fiscal_br.doctype.configuracao_fiscal.configuracao_fiscal import ConfiguracaoFiscal
        config = ConfiguracaoFiscal.get_config_for_company(self.nf.empresa)
        return config.inscricao_estadual if config else ""
