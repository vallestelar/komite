from __future__ import annotations

import base64
from datetime import date
from io import BytesIO
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class ResidenceCertificateService:
    months = [
        "enero",
        "febrero",
        "marzo",
        "abril",
        "mayo",
        "junio",
        "julio",
        "agosto",
        "septiembre",
        "octubre",
        "noviembre",
        "diciembre",
    ]

    def build_pdf_base64(
        self,
        *,
        condominium: Any,
        unit: Any,
        contact: Any,
        signer: Any,
        purpose: str | None = None,
        nationality: str | None = None,
        issued_on: date | None = None,
        signature_image: bytes | None = None,
        komite_logo: bytes | None = None,
        company_logo: bytes | None = None,
    ) -> str:
        output = BytesIO()
        today = issued_on or date.today()

        document = SimpleDocTemplate(
            output,
            pagesize=LETTER,
            rightMargin=2.2 * cm,
            leftMargin=2.2 * cm,
            topMargin=2.0 * cm,
            bottomMargin=2.0 * cm,
            title="Certificado de residencia",
            author="Komite",
        )

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="CertificateTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=17, leading=22, alignment=TA_CENTER, spaceAfter=30))
        styles.add(ParagraphStyle(name="CertificateBody", parent=styles["BodyText"], fontName="Helvetica", fontSize=11.5, leading=19, alignment=TA_JUSTIFY, spaceAfter=14))
        styles.add(ParagraphStyle(name="CertificateSmall", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5, leading=13, textColor=colors.HexColor("#4b5563"), alignment=TA_CENTER))
        styles.add(ParagraphStyle(name="CertificateMeta", parent=styles["BodyText"], fontName="Helvetica", fontSize=10, leading=14, alignment=TA_LEFT))

        city = condominium.city or condominium.commune or ""
        place = city or "Chile"
        condominium_address = self._address(condominium)
        signer_name = getattr(signer, "full_name", None) or "Administrador"
        signer_document = getattr(signer, "document_number", None) or ""
        signer_position = getattr(signer, "organization_position", None) or "Administrador"
        resident_document = contact.document_number or "no informado"
        resident_nationality = nationality or self._metadata_value(contact, "nationality") or self._metadata_value(getattr(contact, "user", None), "nationality") or "chilena"
        tower = self._tower(unit)
        unit_text = f"{unit.identifier}"
        if tower:
            unit_text = f"{unit.identifier}, de la torre {tower}"
        requested_purpose = purpose.strip() if purpose and purpose.strip() else "los fines que estime convenientes"

        signer_document_text = f", Cédula de Identidad N° {signer_document}" if signer_document else ""

        story = [
            self._logo_header(komite_logo, company_logo, getattr(condominium, "company", None), styles),
            Spacer(1, 0.6 * cm),
            Paragraph("CERTIFICADO DE RESIDENCIA", styles["CertificateTitle"]),
            Paragraph(
                f"En {place}, a {today.day} de {self.months[today.month - 1]} de {today.year}, "
                f"{signer_name}{signer_document_text}, {signer_position} del condominio {condominium.name}, "
                f"ubicado en {condominium_address}.",
                styles["CertificateBody"],
            ),
            Paragraph("<b>Certifica:</b>", styles["CertificateBody"]),
            Paragraph(
                f"Que, {contact.full_name}, Cédula de Identidad N° {resident_document}, de nacionalidad {resident_nationality}, "
                f"es residente permanente del departamento {unit_text} de este condominio.",
                styles["CertificateBody"],
            ),
            Paragraph(
                f"Que, se extiende el presente certificado a solicitud de la persona interesada y para {requested_purpose}.",
                styles["CertificateBody"],
            ),
            Paragraph(
                "El certificado de residencia es considerado una declaración prestada bajo juramento. "
                "Por lo tanto, el solicitante acredita que los datos proporcionados son los correctos. "
                "Asumiendo que de lo contrario se expone a las responsabilidades legales que correspondan.",
                styles["CertificateBody"],
            ),
            Spacer(1, 2.0 * cm),
            self._signature_table(signer_name, signer_position, signer_document, styles, signature_image),
            Spacer(1, 0.5 * cm),
            Paragraph(
                f"Emitido y firmado el {today.strftime('%d/%m/%Y')}.",
                styles["CertificateSmall"],
            ),
        ]

        document.build(story)
        return base64.b64encode(output.getvalue()).decode("ascii")

    def build_docx_base64(
        self,
        *,
        condominium: Any,
        unit: Any,
        contact: Any,
        signer: Any,
        purpose: str | None = None,
        nationality: str | None = None,
        issued_on: date | None = None,
        signature_image: bytes | None = None,
        komite_logo: bytes | None = None,
        company_logo: bytes | None = None,
    ) -> str:
        today = issued_on or date.today()
        context = self._certificate_context(
            condominium=condominium,
            unit=unit,
            contact=contact,
            signer=signer,
            purpose=purpose,
            nationality=nationality,
            today=today,
        )

        images: list[tuple[str, bytes]] = []
        komite_logo = self._normalized_image(komite_logo)
        company_logo = self._normalized_image(company_logo)
        signature_image = self._normalized_image(signature_image)
        if komite_logo:
            images.append(("komite_logo", komite_logo))
        if company_logo:
            images.append(("company_logo", company_logo))
        if signature_image:
            images.append(("signature", signature_image))

        rels = {name: f"rId{index + 1}" for index, (name, _) in enumerate(images)}
        output = BytesIO()
        with ZipFile(output, "w", ZIP_DEFLATED) as docx:
            docx.writestr("[Content_Types].xml", self._docx_content_types(images))
            docx.writestr("_rels/.rels", self._docx_root_rels())
            docx.writestr("word/_rels/document.xml.rels", self._docx_document_rels(images, rels))
            docx.writestr("word/styles.xml", self._docx_styles())
            docx.writestr("word/document.xml", self._docx_document_xml(context, rels, dict(images)))
            for name, image in images:
                docx.writestr(f"word/media/{name}.png", image)
        return base64.b64encode(output.getvalue()).decode("ascii")

    def _certificate_context(
        self,
        *,
        condominium: Any,
        unit: Any,
        contact: Any,
        signer: Any,
        purpose: str | None,
        nationality: str | None,
        today: date,
    ) -> dict[str, str]:
        city = condominium.city or condominium.commune or ""
        place = city or "Chile"
        signer_name = getattr(signer, "full_name", None) or "Administrador"
        signer_document = getattr(signer, "document_number", None) or ""
        signer_position = getattr(signer, "organization_position", None) or "Administrador"
        resident_document = contact.document_number or "no informado"
        resident_nationality = nationality or self._metadata_value(contact, "nationality") or self._metadata_value(getattr(contact, "user", None), "nationality") or "chilena"
        tower = self._tower(unit)
        unit_text = f"{unit.identifier}"
        if tower:
            unit_text = f"{unit.identifier}, de la torre {tower}"
        requested_purpose = purpose.strip() if purpose and purpose.strip() else "los fines que estime convenientes"
        signer_document_text = f", Cédula de Identidad N° {signer_document}" if signer_document else ""
        return {
            "place": place,
            "issued_text": f"{today.day} de {self.months[today.month - 1]} de {today.year}",
            "issued_short": today.strftime("%d/%m/%Y"),
            "condominium_name": condominium.name,
            "condominium_address": self._address(condominium),
            "company_name": getattr(getattr(condominium, "company", None), "name", None) or "",
            "signer_name": signer_name,
            "signer_document": signer_document,
            "signer_position": signer_position,
            "signer_document_text": signer_document_text,
            "resident_name": contact.full_name,
            "resident_document": resident_document,
            "resident_nationality": resident_nationality,
            "unit_text": unit_text,
            "requested_purpose": requested_purpose,
        }

    def _docx_document_xml(self, context: dict[str, str], rels: dict[str, str], images: dict[str, bytes]) -> str:
        komite_cell = self._docx_image(rels["komite_logo"], images["komite_logo"], 1440000, 576000) if "komite_logo" in rels else self._run("Komite")
        company_cell = self._docx_image(rels["company_logo"], images["company_logo"], 1440000, 576000) if "company_logo" in rels else self._run(context["company_name"])
        signature = self._docx_image(rels["signature"], images["signature"], 2592000, 1008000) if "signature" in rels else ""
        body = [
            self._docx_logo_table(komite_cell, company_cell),
            self._paragraph("CERTIFICADO DE RESIDENCIA", align="center", bold=True, size=32, spacing_after=420),
            self._paragraph(
                f"En {context['place']}, a {context['issued_text']}, {context['signer_name']}{context['signer_document_text']}, "
                f"{context['signer_position']} del condominio {context['condominium_name']}, ubicado en {context['condominium_address']}.",
                align="both",
            ),
            self._paragraph("Certifica:", bold=True),
            self._paragraph(
                f"Que, {context['resident_name']}, Cédula de Identidad N° {context['resident_document']}, "
                f"de nacionalidad {context['resident_nationality']}, es residente permanente del departamento {context['unit_text']} de este condominio.",
                align="both",
            ),
            self._paragraph(
                f"Que, se extiende el presente certificado a solicitud de la persona interesada y para {context['requested_purpose']}.",
                align="both",
            ),
            self._paragraph(
                "El certificado de residencia es considerado una declaración prestada bajo juramento. "
                "Por lo tanto, el solicitante acredita que los datos proporcionados son los correctos. "
                "Asumiendo que de lo contrario se expone a las responsabilidades legales que correspondan.",
                align="both",
            ),
            self._paragraph("", spacing_after=760),
            self._paragraph(signature, align="center", raw=True, spacing_after=0),
            self._signature_line_xml(context),
            self._paragraph(f"Emitido y firmado el {context['issued_short']}.", align="center", size=19, color="4B5563", spacing_before=460),
        ]
        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
  <w:body>
    {''.join(body)}
    <w:sectPr>
      <w:pgSz w:w="12240" w:h="15840"/>
      <w:pgMar w:top="1134" w:right="1247" w:bottom="1134" w:left="1247" w:header="720" w:footer="720" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>"""

    def _docx_logo_table(self, left_cell: str, right_cell: str) -> str:
        return f"""<w:tbl>
  <w:tblPr><w:tblW w:w="9746" w:type="dxa"/><w:tblBorders><w:top w:val="nil"/><w:left w:val="nil"/><w:bottom w:val="nil"/><w:right w:val="nil"/><w:insideH w:val="nil"/><w:insideV w:val="nil"/></w:tblBorders></w:tblPr>
  <w:tblGrid><w:gridCol w:w="4873"/><w:gridCol w:w="4873"/></w:tblGrid>
  <w:tr>
    <w:tc><w:tcPr><w:tcW w:w="4873" w:type="dxa"/></w:tcPr>{self._paragraph(left_cell, raw=True)}</w:tc>
    <w:tc><w:tcPr><w:tcW w:w="4873" w:type="dxa"/></w:tcPr>{self._paragraph(right_cell, align="right", raw=True)}</w:tc>
  </w:tr>
</w:tbl>"""

    def _signature_line_xml(self, context: dict[str, str]) -> str:
        return f"""<w:tbl>
  <w:tblPr><w:jc w:val="center"/><w:tblW w:w="5670" w:type="dxa"/></w:tblPr>
  <w:tblGrid><w:gridCol w:w="5670"/></w:tblGrid>
  <w:tr><w:tc><w:tcPr><w:tcW w:w="5670" w:type="dxa"/><w:tcBorders><w:top w:val="single" w:sz="8" w:space="0" w:color="111827"/><w:left w:val="nil"/><w:bottom w:val="nil"/><w:right w:val="nil"/></w:tcBorders></w:tcPr>{self._paragraph(context["signer_name"], align="center", size=19, color="4B5563", spacing_after=0)}{self._paragraph(context["signer_position"], align="center", size=19, color="4B5563", spacing_after=0)}{self._paragraph(f"RUT {context['signer_document']}" if context["signer_document"] else "", align="center", size=19, color="4B5563", spacing_after=0)}</w:tc></w:tr>
</w:tbl>"""

    def _paragraph(self, text: str, *, align: str = "left", bold: bool = False, size: int = 23, color: str | None = None, raw: bool = False, spacing_after: int = 260, spacing_before: int = 0) -> str:
        run = text if raw else self._run(text, bold=bold, size=size, color=color)
        return f"""<w:p><w:pPr><w:jc w:val="{align}"/><w:spacing w:before="{spacing_before}" w:after="{spacing_after}" w:line="300" w:lineRule="auto"/></w:pPr>{run}</w:p>"""

    def _run(self, text: str, *, bold: bool = False, size: int = 23, color: str | None = None) -> str:
        bold_xml = "<w:b/>" if bold else ""
        color_xml = f'<w:color w:val="{color}"/>' if color else ""
        safe_text = escape(text).encode("ascii", "xmlcharrefreplace").decode("ascii")
        return f'<w:r><w:rPr>{bold_xml}{color_xml}<w:sz w:val="{size}"/></w:rPr><w:t xml:space="preserve">{safe_text}</w:t></w:r>'

    def _docx_image(self, rel_id: str, image_bytes: bytes, max_width_emu: int, max_height_emu: int) -> str:
        width_emu, height_emu = self._fit_image_emu(image_bytes, max_width_emu, max_height_emu)
        return f"""<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{width_emu}" cy="{height_emu}"/><wp:docPr id="{escape(rel_id.removeprefix('rId') or '1')}" name="Imagen"/><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic><pic:nvPicPr><pic:cNvPr id="0" name="image.png"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="{rel_id}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{width_emu}" cy="{height_emu}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>"""

    def _fit_image_emu(self, image_bytes: bytes, max_width_emu: int, max_height_emu: int) -> tuple[int, int]:
        try:
            from PIL import Image as PilImage

            with PilImage.open(BytesIO(image_bytes)) as image:
                width_px, height_px = image.size
            if width_px <= 0 or height_px <= 0:
                return max_width_emu, max_height_emu
            scale = min(max_width_emu / width_px, max_height_emu / height_px)
            return max(1, round(width_px * scale)), max(1, round(height_px * scale))
        except Exception:
            return max_width_emu, max_height_emu

    def _docx_content_types(self, images: list[tuple[str, bytes]]) -> str:
        image_override = "".join(f'<Override PartName="/word/media/{name}.png" ContentType="image/png"/>' for name, _ in images)
        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>{image_override}<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>"""

    def _docx_root_rels(self) -> str:
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>"""

    def _docx_document_rels(self, images: list[tuple[str, bytes]], rels: dict[str, str]) -> str:
        image_rels = "".join(f'<Relationship Id="{rels[name]}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{name}.png"/>' for name, _ in images)
        style_rel_id = f"rId{len(images) + 1}"
        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{image_rels}<Relationship Id="{style_rel_id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>"""

    def _docx_styles(self) -> str:
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:sz w:val="23"/></w:rPr></w:style></w:styles>"""

    def _logo_header(self, komite_logo: bytes | None, company_logo: bytes | None, company: Any, styles: dict[str, Any]) -> Table:
        company_name = getattr(company, "name", None) or ""
        data = [[self._logo_cell(komite_logo, "Komite", styles, "LEFT"), self._logo_cell(company_logo, company_name, styles, "RIGHT")]]
        table = Table(data, colWidths=[8.4 * cm, 8.4 * cm])
        table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (0, 0), "LEFT"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        return table

    def _logo_cell(self, image_bytes: bytes | None, fallback_label: str, styles: dict[str, Any], align: str) -> Any:
        normalized = self._normalized_image(image_bytes)
        if normalized:
            logo = Image(BytesIO(normalized), width=4.0 * cm, height=1.6 * cm, kind="proportional")
            logo.hAlign = align
            return logo
        return Paragraph(fallback_label, styles["CertificateSmall"]) if fallback_label else ""

    def _normalized_image(self, image_bytes: bytes | None) -> bytes | None:
        if not image_bytes:
            return None
        try:
            from PIL import Image as PilImage, ImageOps

            with PilImage.open(BytesIO(image_bytes)) as image:
                image = ImageOps.exif_transpose(image)
                if image.mode not in {"RGB", "RGBA", "LA"}:
                    image = image.convert("RGBA")
                output = BytesIO()
                image.save(output, format="PNG", optimize=True)
                return output.getvalue()
        except Exception:
            return None

    def _signature_table(self, signer_name: str, signer_position: str, signer_document: str, styles: dict[str, Any], signature_image: bytes | None) -> Table:
        document_line = f"RUT {signer_document}" if signer_document else ""
        signature_cell: Any = ""
        if signature_image:
            signature = Image(BytesIO(signature_image), width=7.2 * cm, height=2.8 * cm, kind="proportional")
            signature.hAlign = "CENTER"
            signature_cell = signature
        data = [
            [signature_cell],
            [Paragraph(signer_name, styles["CertificateSmall"])],
            [Paragraph(signer_position, styles["CertificateSmall"])],
            [Paragraph(document_line, styles["CertificateSmall"])],
        ]
        table = Table(data, colWidths=[10.0 * cm])
        table.setStyle(
            TableStyle(
                [
                    ("LINEABOVE", (0, 1), (0, 1), 1, colors.HexColor("#111827")),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("TOPPADDING", (0, 1), (0, 1), 8),
                    ("BOTTOMPADDING", (0, 0), (0, 0), 4),
                    ("BOTTOMPADDING", (0, 1), (-1, -1), 2),
                ]
            )
        )
        return table

    def _address(self, condominium: Any) -> str:
        parts = [condominium.address, condominium.commune, condominium.city]
        return ", ".join(part for part in parts if part) or "dirección no informada"

    def _tower(self, unit: Any) -> str:
        if getattr(unit, "building", None):
            return unit.building.name
        metadata = unit.metadata or {}
        return str(metadata.get("tower") or metadata.get("torre") or "").strip()

    def _metadata_value(self, entity: Any, key: str) -> str:
        if not entity:
            return ""
        metadata = getattr(entity, "metadata", None) or {}
        return str(metadata.get(key) or "").strip()
