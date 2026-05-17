"""
Water Quality Analysis – BOD & COD Calculator (Jan–Dec 2025)
Flask Backend Application
"""

from flask import Flask, render_template, request, jsonify, send_file
import json
import os
import io
import base64
import math

# ReportLab imports for PDF generation
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, Line, String, PolyLine
from reportlab.graphics import renderPDF
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.widgets.markers import makeMarker

app = Flask(__name__)

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def calculate_bod_cod(do_initial, do_final):
    """
    Calculate BOD and COD from dissolved oxygen readings.
    BOD (Biochemical Oxygen Demand) = DO_initial - DO_final
    COD (Chemical Oxygen Demand) = BOD × 1.8  (simplified academic relation)
    """
    bod = round(do_initial - do_final, 3)
    cod = round(bod * 1.8, 3)
    return bod, cod


@app.route("/")
def index():
    return render_template("index.html", months=MONTHS)


@app.route("/calculate", methods=["POST"])
def calculate():
    """Receive monthly DO values, compute BOD & COD, return JSON."""
    data = request.get_json()
    results = []
    for i, month in enumerate(MONTHS):
        try:
            do_i = float(data["do_initial"][i])
            do_f = float(data["do_final"][i])
        except (KeyError, ValueError, IndexError):
            do_i, do_f = 0.0, 0.0
        bod, cod = calculate_bod_cod(do_i, do_f)
        results.append({
            "month": month,
            "do_initial": do_i,
            "do_final": do_f,
            "bod": bod,
            "cod": cod
        })
    return jsonify({"results": results})


@app.route("/download_pdf", methods=["POST"])
def download_pdf():
    """Generate a professional PDF report using ReportLab and return it."""
    data = request.get_json()

    student = data.get("student", {})
    location = data.get("location", {})
    results = data.get("results", [])
    year = data.get("year", 2025)
    chart_image_b64 = data.get("chart_image", None)

    pdf_path = os.path.join(OUTPUT_DIR, "report.pdf")

    # builder pdf
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=20,
        textColor=colors.HexColor("#0a3d62"),
        spaceAfter=6,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER
    )
    subtitle_style = ParagraphStyle(
        "SubTitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#1a7db5"),
        spaceAfter=4,
        fontName="Helvetica",
        alignment=TA_CENTER
    )
    section_style = ParagraphStyle(
        "SectionHead",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#0a3d62"),
        spaceBefore=12,
        spaceAfter=6,
        fontName="Helvetica-Bold",
        borderPad=4
    )
    normal_style = ParagraphStyle(
        "NormalCustom",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#2c3e50"),
        fontName="Helvetica"
    )
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#7f8c8d"),
        alignment=TA_CENTER
    )

    story = []

    # head bar 
    header_data = [[f"WATER QUALITY ANALYSIS REPORT – {year}"]]
    header_table = Table(header_data, colWidths=[17*cm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#0a3d62")),
        ("TEXTCOLOR", (0,0), (-1,-1), colors.white),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 16),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 14),
        ("BOTTOMPADDING", (0,0), (-1,-1), 14),
        ("ROUNDEDCORNERS", [6,6,6,6]),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.3*cm))

    sub = Paragraph(f"BOD &amp; COD Analysis | January – December {year}", subtitle_style)
    story.append(sub)
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a7db5")))
    story.append(Spacer(1, 0.4*cm))

    # ── Student Details ────────────────────────────────────────────────────
    story.append(Paragraph("Student Information", section_style))
    sd = [
        ["Name", ":", student.get("name", "—"),
         "Register No.", ":", student.get("register_no", "—")],
        ["Branch", ":", student.get("branch", "—"),
         "Section", ":", student.get("section", "—")],
    ]
    sd_table = Table(sd, colWidths=[2.5*cm, 0.5*cm, 5*cm, 2.5*cm, 0.5*cm, 6*cm])
    sd_table.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME", (3,0), (3,-1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0,0), (-1,-1), colors.HexColor("#2c3e50")),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.HexColor("#eaf4fb"), colors.white]),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(sd_table)
    story.append(Spacer(1, 0.3*cm))

    # ── Location Details ───────────────────────────────────────────────────
    story.append(Paragraph("Location Information", section_style))
    ld = [[
        "Hometown", ":", location.get("hometown", "—"),
        "District", ":", location.get("district", "—"),
        "State", ":", location.get("state", "—"),
    ]]
    ld_table = Table(ld, colWidths=[2*cm, 0.5*cm, 4*cm, 2*cm, 0.5*cm, 4*cm, 1.5*cm, 0.5*cm, 2.5*cm])
    ld_table.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME", (3,0), (3,-1), "Helvetica-Bold"),
        ("FONTNAME", (6,0), (6,-1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0,0), (-1,-1), colors.HexColor("#2c3e50")),
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#eaf4fb")),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(ld_table)
    story.append(Spacer(1, 0.4*cm))

    # ── Results Table ──────────────────────────────────────────────────────
    story.append(Paragraph(f"BOD &amp; COD Results (Jan–Dec {year})", section_style))

    table_data = [["Month", "DO Initial (mg/L)", "DO Final (mg/L)", "BOD (mg/L)", "COD (mg/L)"]]
    row_bg = []
    for idx, r in enumerate(results):
        table_data.append([
            r["month"],
            f"{r['do_initial']:.2f}",
            f"{r['do_final']:.2f}",
            f"{r['bod']:.3f}",
            f"{r['cod']:.3f}",
        ])
        bg = colors.HexColor("#eaf4fb") if idx % 2 == 0 else colors.white
        row_bg.append(bg)

    res_table = Table(table_data, colWidths=[3.2*cm, 3.5*cm, 3.5*cm, 3.2*cm, 3.6*cm])
    style_cmds = [
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0a3d62")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#bdc3c7")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#eaf4fb"), colors.white]),
    ]
    res_table.setStyle(TableStyle(style_cmds))
    story.append(res_table)
    story.append(Spacer(1, 0.5*cm))

    # ── Chart (drawn with ReportLab graphics) ─────────────────────────────
    story.append(Paragraph(f"BOD &amp; COD Trend – {year}", section_style))

    bod_vals = [r["bod"] for r in results]
    cod_vals = [r["cod"] for r in results]

    # ── Feature 3: Insert chart image from frontend (dynamic scaling) ──────
    # Page width minus left+right margins = 17cm usable width
    page_width = A4[0]
    left_margin = 2 * cm
    right_margin = 2 * cm
    max_chart_width = page_width - left_margin - right_margin  # ~487 pts

    if chart_image_b64:
        # Strip data URL prefix if present (e.g. "data:image/png;base64,...")
        if "," in chart_image_b64:
            chart_image_b64 = chart_image_b64.split(",", 1)[1]
        chart_bytes = base64.b64decode(chart_image_b64)
        chart_buf = io.BytesIO(chart_bytes)

        # Determine native image dimensions for aspect ratio
        from PIL import Image as PILImage
        pil_img = PILImage.open(io.BytesIO(chart_bytes))
        native_w, native_h = pil_img.size  # pixels
        aspect = native_h / native_w if native_w > 0 else 0.5

        chart_draw_w = max_chart_width
        chart_draw_h = chart_draw_w * aspect
        # Cap height so chart never overflows page
        max_chart_height = 8 * cm
        if chart_draw_h > max_chart_height:
            chart_draw_h = max_chart_height
            chart_draw_w = chart_draw_h / aspect

        chart_img = Image(chart_buf, width=chart_draw_w, height=chart_draw_h)
        story.append(chart_img)
    else:
        # Fallback: draw chart using ReportLab graphics if no image supplied
        chart_w, chart_h = 480, 200
        d = Drawing(chart_w, chart_h)
        d.add(Rect(0, 0, chart_w, chart_h, fillColor=colors.HexColor("#f0f8ff"),
                   strokeColor=colors.HexColor("#bdc3c7"), strokeWidth=1))
        mx, my, mw, mh = 55, 25, 390, 150
        max_val = max(max(cod_vals), 1)
        steps = 5
        for s in range(steps + 1):
            y_val = s * max_val / steps
            y_px = my + (y_val / max_val) * mh
            d.add(Line(mx, y_px, mx + mw, y_px,
                       strokeColor=colors.HexColor("#dce8f0"), strokeWidth=0.5))
            d.add(String(mx - 4, y_px - 3, f"{y_val:.1f}", fontSize=6,
                         fillColor=colors.HexColor("#7f8c8d"), textAnchor="end"))
        for i, m in enumerate(MONTHS):
            x_px = mx + i * mw / 11
            d.add(String(x_px, my - 12, m[:3], fontSize=6,
                         fillColor=colors.HexColor("#555"), textAnchor="middle"))
        bod_pts = []
        for i, v in enumerate(bod_vals):
            x_px = mx + i * mw / 11
            y_px = my + (v / max_val) * mh if max_val > 0 else my
            bod_pts.extend([x_px, y_px])
        if len(bod_pts) >= 4:
            d.add(PolyLine(bod_pts, strokeColor=colors.HexColor("#1a7db5"), strokeWidth=2))
        cod_pts = []
        for i, v in enumerate(cod_vals):
            x_px = mx + i * mw / 11
            y_px = my + (v / max_val) * mh if max_val > 0 else my
            cod_pts.extend([x_px, y_px])
        if len(cod_pts) >= 4:
            d.add(PolyLine(cod_pts, strokeColor=colors.HexColor("#e74c3c"), strokeWidth=2))
        d.add(Rect(mx, chart_h - 18, 14, 6, fillColor=colors.HexColor("#1a7db5"), strokeColor=None))
        d.add(String(mx + 17, chart_h - 16, "BOD (mg/L)", fontSize=8,
                     fillColor=colors.HexColor("#2c3e50")))
        d.add(Rect(mx + 80, chart_h - 18, 14, 6, fillColor=colors.HexColor("#e74c3c"), strokeColor=None))
        d.add(String(mx + 97, chart_h - 16, "COD (mg/L)", fontSize=8,
                     fillColor=colors.HexColor("#2c3e50")))
        story.append(d)
    story.append(Spacer(1, 0.5*cm))

    # ── Formula note ──────────────────────────────────────────────────────
    formula_data = [["Formulae Used:  BOD = DO_initial − DO_final     |     COD = BOD × 1.8  (Simplified academic relation)"]]
    f_table = Table(formula_data, colWidths=[17*cm])
    f_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#eaf4fb")),
        ("TEXTCOLOR", (0,0), (-1,-1), colors.HexColor("#0a3d62")),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica-Oblique"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#1a7db5")),
    ]))
    story.append(f_table)
    story.append(Spacer(1, 0.8*cm))

    # ── Footer ─────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#bdc3c7")))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(f"Generated by Water Quality Analysis System • BOD &amp; COD Calculator {year}", footer_style))

    doc.build(story)

    return send_file(
        pdf_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="Water_Quality_Report_2025.pdf"
    )


if __name__ == "__main__":
    app.run(debug=True)