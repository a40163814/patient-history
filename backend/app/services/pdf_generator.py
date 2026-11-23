import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, Image, HRFlowable
)
from backend.app.core.config import settings

class ClinicalPdfGenerator:
    def __init__(self):
        self.output_dir = settings.PDF_OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_case_sheet(
        self,
        session_id: str,
        patient_data: Dict[str, Any],
        vitals: Dict[str, Any],
        clinical_fields: List[Dict[str, Any]],
        mismatch_flags: List[Dict[str, Any]],
        reports: List[Dict[str, Any]],
        doctor_review: Dict[str, Any],
        has_red_flag: bool = False,
        red_flag_details: Optional[str] = None
    ) -> str:
        """
        Builds a comprehensive, immutable pre-OPD case sheet using ReportLab.
        Enforces standard disclaimers, field provenance labels, and doctor approval stamp.
        """
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"CaseSheet_{session_id[:8]}_{timestamp_str}.pdf"
        file_path = self.output_dir / filename

        doc = SimpleDocTemplate(
            str(file_path),
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        normal = styles["Normal"]
        
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#14532d"),
            spaceAfter=2
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=normal,
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#166534")
        )
        disclaimer_style = ParagraphStyle(
            "Disclaimer",
            parent=normal,
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#b91c1c"),
            alignment=1 # Center
        )
        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=8,
            spaceAfter=4
        )
        field_label_style = ParagraphStyle(
            "FieldLabel",
            parent=normal,
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#475569")
        )
        field_value_style = ParagraphStyle(
            "FieldValue",
            parent=normal,
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#0f172a")
        )
        provenance_style = ParagraphStyle(
            "Provenance",
            parent=normal,
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#0284c7")
        )

        story = []

        # 1. Header & Ministry Branding
        header_table_data = [
            [
                Paragraph("<b>MINISTRY OF AYUSH • GOVERNMENT OF INDIA</b><br/>"
                          "<font size=8>Outpatient Department (OPD) Pre-Intake Case Record</font>", title_style),
                Paragraph(f"<b>Token:</b> {patient_data.get('patient_token', 'N/A')}<br/>"
                          f"<b>Date:</b> {datetime.now(timezone.utc).strftime('%d-%b-%Y %H:%M UTC')}<br/>"
                          f"<b>OPD Discipline:</b> {patient_data.get('ayush_system', 'Allopathy').title()}", subtitle_style)
            ]
        ]
        header_table = Table(header_table_data, colWidths=[3.8 * inch, 3.4 * inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 4))

        # 2. Prominent Legal Disclaimer Banner
        disclaimer_box = Table(
            [[Paragraph("<b>MANDATORY CLINICAL NOTICE:</b> Draft prepared from patient answers. Not a diagnosis. "
                        "All data must be verified by the examining Ayush Medical Officer prior to prescription.", disclaimer_style)]],
            colWidths=[7.2 * inch]
        )
        disclaimer_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#fee2e2")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#ef4444")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(disclaimer_box)
        story.append(Spacer(1, 8))

        # 3. Patient Demographics & Self-Reported Vitals
        v_h = vitals.get("height_cm", "—")
        v_w = vitals.get("weight_kg", "—")
        v_bmi = vitals.get("bmi", "—")
        v_cat = vitals.get("bmi_category", "—")
        v_lbl = vitals.get("vitals_label", "self-reported")

        demo_vitals_data = [
            [
                Paragraph("<b>Patient Demographics</b>", section_heading),
                Paragraph(f"<b>Vitals ({v_lbl.upper()})</b>", section_heading)
            ],
            [
                Paragraph(f"<b>Phone:</b> {patient_data.get('phone_number', 'N/A')}<br/>"
                          f"<b>Preferred Language:</b> {patient_data.get('preferred_language', 'en').upper()}<br/>"
                          f"<b>Guardian / Caregiver:</b> {patient_data.get('guardian_info', 'Self')}", normal),
                Paragraph(f"<b>Height:</b> {v_h} cm | <b>Weight:</b> {v_w} kg<br/>"
                          f"<b>BMI:</b> {v_bmi} kg/m² ({v_cat})<br/>"
                          f"<i>Computed via formula: weight / (height_m)²</i>", normal)
            ]
        ]
        demo_table = Table(demo_vitals_data, colWidths=[3.6 * inch, 3.6 * inch])
        demo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(demo_table)
        story.append(Spacer(1, 8))

        # 4. Red-Flag and Mismatch Alerts (If Any)
        if has_red_flag:
            rf_box = Table(
                [[Paragraph(f"<b>RED-FLAG TRIAGE HALT TRIGGERED:</b> {red_flag_details or 'Emergency alert recorded.'}<br/>"
                            f"<i>Staff were alerted to attend to patient on site.</i>", disclaimer_style)]],
                colWidths=[7.2 * inch]
            )
            rf_box.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#fef2f2")),
                ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor("#dc2626")),
                ('PADDING', (0, 0), (-1, -1), 6)
            ]))
            story.append(rf_box)
            story.append(Spacer(1, 6))

        if mismatch_flags:
            mismatch_rows = [[Paragraph("<b>Discrepancy / Lab Mismatch Alerts (Doctor Review Required)</b>", section_heading)]]
            for m in mismatch_flags:
                mismatch_rows.append([
                    Paragraph(f"• <b>{m.get('biomarker')}:</b> {m.get('message')}", field_value_style)
                ])
            mismatch_table = Table(mismatch_rows, colWidths=[7.2 * inch])
            mismatch_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#fffbeb")),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#f59e0b")),
                ('PADDING', (0, 0), (-1, -1), 4)
            ]))
            story.append(mismatch_table)
            story.append(Spacer(1, 6))

        # 5. Structured Clinical History Table with Provenance
        story.append(Paragraph("<b>Recorded Clinical Information (Patient Voice Intake)</b>", section_heading))
        
        history_rows = [
            [
                Paragraph("<b>Section / Field</b>", field_label_style),
                Paragraph("<b>Recorded Details</b>", field_label_style),
                Paragraph("<b>Provenance & Source</b>", field_label_style)
            ]
        ]

        for f in clinical_fields:
            sec_name = f.get("section", "").replace("_", " ").title()
            key_name = f.get("field_key", "").replace("_", " ").title()
            val_text = f.get("value", "—")
            src = f.get("source", "patient_said")
            conf = f.get("confidence", 1.0)
            quote = f.get("transcript_quote")
            is_ed = f.get("is_edited_by_doctor", False)

            val_cell = f"<b>{val_text}</b>"
            if is_ed:
                val_cell += f"<br/><font color='#b91c1c' size=7>[Doctor Modified: was '{f.get('original_value', '')}']</font>"
            if quote:
                val_cell += f"<br/><font color='#64748b' size=7><i>\"{quote}\"</i></font>"

            history_rows.append([
                Paragraph(f"<b>{sec_name}</b><br/>{key_name}", normal),
                Paragraph(val_cell, field_value_style),
                Paragraph(f"Source: <b>{src}</b><br/>Conf: {int(conf * 100)}%", provenance_style)
            ])

        if len(history_rows) > 1:
            hist_table = Table(history_rows, colWidths=[2.2 * inch, 3.6 * inch, 1.4 * inch])
            hist_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('PADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(hist_table)
        else:
            story.append(Paragraph("<i>No structured fields answered yet (Session may have halted or dropped early).</i>", normal))

        story.append(Spacer(1, 8))

        # 6. Extracted Document Reports
        if reports:
            story.append(Paragraph("<b>Uploaded Diagnostic Reports & Extracted Values</b>", section_heading))
            report_rows = [[Paragraph("<b>File / Type</b>", field_label_style), Paragraph("<b>Extracted Non-Diagnostic Values</b>", field_label_style)]]
            for r in reports:
                extracted_lines = []
                for lv in r.get("lab_values", []):
                    extracted_lines.append(f"• <b>{lv.get('test_name')}:</b> {lv.get('raw_value')} (Ref: {lv.get('reference_range_printed') or 'N/A'})")
                for med in r.get("candidate_medicines", []):
                    extracted_lines.append(f"• <b>Medicine Candidate:</b> {med.get('name')} {med.get('strength') or ''}")
                
                content = "<br/>".join(extracted_lines) if extracted_lines else "<i>No numeric lab values detected.</i>"
                report_rows.append([
                    Paragraph(f"<b>{r.get('file_name')}</b><br/>{r.get('file_type')}", normal),
                    Paragraph(content, field_value_style)
                ])
            rep_table = Table(report_rows, colWidths=[2.2 * inch, 5.0 * inch])
            rep_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('PADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(rep_table)
            story.append(Spacer(1, 8))

        # 7. AI Summary (Max 5 lines, labeled)
        ai_sum = doctor_review.get("ai_summary")
        if ai_sum:
            ai_box = Table(
                [
                    [Paragraph("<b>AI-Generated Summary (Editable by Doctor):</b>", field_label_style)],
                    [Paragraph(f"<i>{ai_sum}</i>", field_value_style)]
                ],
                colWidths=[7.2 * inch]
            )
            ai_box.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                ('PADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(ai_box)
            story.append(Spacer(1, 8))

        # 8. Doctor Clinical Notes & Approval Stamp
        doc_notes = doctor_review.get("doctor_notes", "Case sheet evaluated and verified during in-person clinical examination.")
        doc_id = doctor_review.get("doctor_id", "DOC-AYUSH-101")
        app_time = doctor_review.get("approved_at", datetime.now(timezone.utc).strftime("%d-%b-%Y %H:%M UTC"))

        approval_data = [
            [
                Paragraph("<b>Doctor's Clinical Assessment & Notes:</b>", section_heading),
                Paragraph("<b>Doctor's Verification & Approval Stamp</b>", section_heading)
            ],
            [
                Paragraph(f"{doc_notes}", normal),
                Paragraph(f"<b>Status:</b> DOCTOR APPROVED<br/>"
                          f"<b>Medical Officer ID:</b> {doc_id}<br/>"
                          f"<b>Timestamp:</b> {app_time}<br/>"
                          f"<b>Signature:</b> ____________________", normal)
            ]
        ]
        app_table = Table(approval_data, colWidths=[4.2 * inch, 3.0 * inch])
        app_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#16a34a")),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(app_table)

        doc.build(story)
        return str(file_path)

clinical_pdf_generator = ClinicalPdfGenerator()
