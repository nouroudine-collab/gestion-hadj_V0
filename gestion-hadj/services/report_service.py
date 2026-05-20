import os
import csv
import sqlite3
from datetime import datetime

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle

from services.settings_service import SettingsService

HEADER_GREEN = "#1B5E20"


class ReportService:
    def __init__(self, db_path="data/app.db"):
        self.db_path = db_path
        self._arabic_font_name = self._register_arabic_font()
        self._settings = SettingsService(db_path)

    def _register_arabic_font(self) -> str | None:
        """Enregistre une police Unicode pour afficher l'arabe."""
        candidates = [
            ("ArialUnicode", "C:/Windows/Fonts/arial.ttf"),
            ("TahomaUnicode", "C:/Windows/Fonts/tahoma.ttf"),
            ("SegoeUIUnicode", "C:/Windows/Fonts/segoeui.ttf"),
        ]
        for font_name, font_path in candidates:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                    return font_name
                except Exception:
                    continue
        return None

    def _format_amount(self, value: int) -> str:
        return f"{int(value):,} FCFA".replace(",", " ")

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _get_pilgrim_details(self, pilgrim_id: int):
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    p.id, p.lname, p.fname, p.sex, p.birth_date, p.birth_place, p.passport, p.total_cost,
                    q.fullname AS contact_urgence,
                    (SELECT number FROM numbers WHERE pilgrim_id = p.id LIMIT 1) AS tel1
                FROM pilgrims p
                LEFT JOIN persons_to_prevent q ON q.id = p.person_to_prevent_id
                WHERE p.id = ?
                """,
                (pilgrim_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def _get_pilgrim_tranches(self, pilgrim_id: int):
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT amount, date
                FROM payments
                WHERE pilgrim_id = ?
                ORDER BY date ASC, id ASC
                LIMIT 5
                """,
                (pilgrim_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def _get_top_pilgrims_summary(self, max_rows: int = 12):
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    p.id,
                    p.lname,
                    p.fname,
                    p.sex,
                    p.birth_date,
                    p.passport,
                    p.total_cost,
                    COALESCE((SELECT amount FROM payments WHERE pilgrim_id = p.id ORDER BY date ASC, id ASC LIMIT 1 OFFSET 0), 0) AS t1,
                    COALESCE((SELECT amount FROM payments WHERE pilgrim_id = p.id ORDER BY date ASC, id ASC LIMIT 1 OFFSET 1), 0) AS t2,
                    COALESCE((SELECT amount FROM payments WHERE pilgrim_id = p.id ORDER BY date ASC, id ASC LIMIT 1 OFFSET 2), 0) AS t3,
                    COALESCE((SELECT SUM(amount) FROM payments WHERE pilgrim_id = p.id), 0) AS total_verse
                FROM pilgrims p
                ORDER BY p.id ASC
                LIMIT ?
                """,
                (max_rows,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def generate_a4_dual_receipt(self, pilgrim_id: int, output_path: str | None = None) -> str:
        """Genere une facture A4 avec 2 copies identiques (client + archive)."""
        pilgrim = self._get_pilgrim_details(pilgrim_id)
        if not pilgrim:
            raise ValueError("Pelerin introuvable.")

        tranches = self._get_pilgrim_tranches(pilgrim_id)
        total_verse = sum(int(t["amount"] or 0) for t in tranches)
        total_cost = int(pilgrim.get("total_cost", 0) or 0)
        reliquat = max(total_cost - total_verse, 0)
        if total_verse == 0:
            statut = "NON"
        elif total_verse < total_cost:
            statut = "PARTIEL"
        elif total_verse == total_cost:
            statut = "PAYE"
        else:
            statut = "SOLDE"
        last_payment = tranches[-1] if tranches else {"amount": 0, "date": datetime.now().strftime("%Y-%m-%d")}
        recu_number = f"FAC-{datetime.now().strftime('%Y%m%d')}-{pilgrim_id:04d}"

        if not output_path:
            os.makedirs("exports/receipts", exist_ok=True)
            safe_name = f"{pilgrim['lname']}_{pilgrim['fname']}".replace(" ", "_").upper()
            output_path = os.path.join(
                "exports/receipts",
                f"recu_{pilgrim_id}_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            )

        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4
        margin = 10 * mm
        copy_height = (height - (2 * margin)) / 2

        def draw_invoice_copy(origin_y: float, copy_label: str):
            box_x = margin
            box_y = origin_y
            box_w = width - (2 * margin)
            box_h = copy_height - 4 * mm

            # Contour principal
            c.setStrokeColor(colors.HexColor("#dddddd"))
            c.rect(box_x, box_y, box_w, box_h, stroke=1, fill=0)

            agency_name = (self._settings.get("agency_name") or "DAROU SALAM").upper()
            season_label = self._settings.get("season") or "HADJ 2027"

            # En-tete epure (texte vert, sans email)
            header_h = 20 * mm
            c.setStrokeColor(colors.HexColor(HEADER_GREEN))
            c.setLineWidth(1.2)
            c.line(box_x, box_y + box_h - header_h, box_x + box_w, box_y + box_h - header_h)
            c.setLineWidth(1)

            logo_path = os.path.join("assets", "logo.png")
            if os.path.exists(logo_path):
                c.drawImage(
                    logo_path,
                    box_x + 3 * mm,
                    box_y + box_h - header_h + 1.5 * mm,
                    width=18 * mm,
                    height=18 * mm,
                    preserveAspectRatio=True,
                    mask="auto",
                )

            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(colors.HexColor(HEADER_GREEN))
            c.drawString(box_x + 25 * mm, box_y + box_h - 7.5 * mm, agency_name)
            c.setFont("Helvetica", 7.5)
            if self._arabic_font_name:
                c.setFont(self._arabic_font_name, 7.5)
                c.setFillColor(colors.HexColor(HEADER_GREEN))
                c.drawString(box_x + 25 * mm, box_y + box_h - 10 * mm, "وكالة دار السلام للحج والعمرة والسياحة بوركينا فاسو")
                c.setFont("Helvetica", 7.5)
            else:
                c.setFillColor(colors.HexColor(HEADER_GREEN))
                c.drawString(box_x + 25 * mm, box_y + box_h - 10 * mm, "Darou Salam - Hajj / Omra / Tourisme")
            c.setFillColor(colors.HexColor("#444444"))
            c.drawString(box_x + 25 * mm, box_y + box_h - 12.8 * mm, "Siege: Rue de la Republique, Bobo-Dioulasso")
            c.drawString(box_x + 25 * mm, box_y + box_h - 15.6 * mm, "Tel: +226 70 30 42 00 / 76 60 34 77 | WhatsApp: 78 01 01 18")

            c.setFont("Helvetica-Bold", 8)
            c.drawRightString(box_x + box_w - 3 * mm, box_y + box_h - 9 * mm, f"RECU N° {recu_number}")
            c.setFont("Helvetica", 7.5)
            c.drawRightString(box_x + box_w - 3 * mm, box_y + box_h - 14 * mm, f"Date: {datetime.now().strftime('%d/%m/%Y')}")
            c.drawRightString(box_x + box_w - 3 * mm, box_y + box_h - 19 * mm, copy_label)

            # Titre
            c.setFont("Helvetica-Bold", 9.5)
            c.setFillColor(colors.HexColor("#2e7d32"))
            c.drawCentredString(
                box_x + box_w / 2,
                box_y + box_h - header_h - 5 * mm,
                f"RECU DE VERSEMENT - {season_label}",
            )
            c.setFillColor(colors.black)

            # Blocs infos
            info_top = box_y + box_h - header_h - 9 * mm
            block_h = 23 * mm
            left_w = (box_w - 8 * mm) / 2
            right_w = left_w

            c.setStrokeColor(colors.HexColor("#dddddd"))
            c.rect(box_x + 3 * mm, info_top - block_h, left_w, block_h, stroke=1, fill=0)
            c.rect(box_x + 5 * mm + left_w, info_top - block_h, right_w, block_h, stroke=1, fill=0)

            c.setFont("Helvetica-Bold", 7.5)
            c.setFillColor(colors.HexColor("#666666"))
            c.drawString(box_x + 4 * mm, info_top - 4 * mm, "Informations du Pelerin")
            c.drawString(box_x + 6 * mm + left_w, info_top - 4 * mm, "Personne a prevenir")

            c.setFont("Helvetica", 7.3)
            c.setFillColor(colors.black)
            full_name = f"{pilgrim['lname']} {pilgrim['fname']}"
            c.drawString(box_x + 4 * mm, info_top - 8.0 * mm, f"Nom complet: {full_name}")
            c.drawString(box_x + 4 * mm, info_top - 11.4 * mm, f"Date naissance: {pilgrim.get('birth_date') or '-'}")
            c.drawString(box_x + 4 * mm, info_top - 14.8 * mm, f"Passeport: {pilgrim.get('passport') or '-'}")
            c.drawString(box_x + 4 * mm, info_top - 18.2 * mm, f"Tel: {pilgrim.get('tel1') or '-'}")

            c.drawString(box_x + 6 * mm + left_w, info_top - 8.5 * mm, f"Nom: {pilgrim.get('contact_urgence') or '-'}")
            c.drawString(box_x + 6 * mm + left_w, info_top - 12.8 * mm, "Telephone: -")
            c.drawString(box_x + 6 * mm + left_w, info_top - 17.1 * mm, "Lien: -")

            # Tableau operation
            table_top_y = info_top - block_h - 8 * mm
            rows = [["Designation de l'operation", "Montant (FCFA)"]]
            for idx, tr in enumerate(tranches, start=1):
                rows.append(
                    [
                        f"Tranche {idx} ({tr.get('date', '-')})",
                        f"{int(tr.get('amount', 0)):,}".replace(",", " "),
                    ]
                )
            if not tranches:
                rows.append(["Aucun versement", "0"])
            rows.append(["Total verse", f"{int(total_verse):,}".replace(",", " ")])
            t = Table(rows, colWidths=[box_w - 45 * mm, 35 * mm])
            t.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a4a8e")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
                        ("FONTSIZE", (0, 0), (-1, -1), 7.2),
                        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ]
                )
            )
            _, table_h = t.wrap(box_w - 6 * mm, box_h)
            t.drawOn(c, box_x + 3 * mm, table_top_y - table_h)

            # Totaux + signatures
            total_x = box_x + box_w - 67 * mm
            total_y = box_y + 18 * mm
            c.setFont("Helvetica-Bold", 7.7)
            c.drawString(total_x, total_y + 10 * mm, "Total verse a ce jour:")
            c.drawRightString(box_x + box_w - 4 * mm, total_y + 10 * mm, self._format_amount(total_verse))

            c.setFillColor(colors.HexColor("#c62828"))
            c.rect(total_x - 1 * mm, total_y + 2 * mm, 64 * mm, 6.8 * mm, stroke=0, fill=1)
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 7.7)
            c.drawString(total_x, total_y + 4.2 * mm, "RESTE A PAYER:")
            c.drawRightString(box_x + box_w - 4 * mm, total_y + 4.2 * mm, self._format_amount(reliquat))
            c.setFillColor(colors.black)

            c.setFont("Helvetica", 7.2)
            c.drawString(box_x + 12 * mm, box_y + 7 * mm, "Signature du Client")
            c.drawString(box_x + box_w - 48 * mm, box_y + 7 * mm, "La Direction (Cachet)")
            c.line(box_x + 9 * mm, box_y + 8.5 * mm, box_x + 55 * mm, box_y + 8.5 * mm)
            c.line(box_x + box_w - 53 * mm, box_y + 8.5 * mm, box_x + box_w - 7 * mm, box_y + 8.5 * mm)

            c.setFont("Helvetica-Bold", 7.2)
            c.drawString(box_x + 3 * mm, box_y + 3 * mm, f"Statut: {statut}")

        # Copie 1 (haut) + copie 2 (bas), identiques pour client/archive
        draw_invoice_copy(origin_y=height / 2 + 2 * mm, copy_label="Exemplaire Client")
        draw_invoice_copy(origin_y=margin, copy_label="Exemplaire Archive Agence")

        # Ligne de decoupe entre les deux
        c.setDash(2, 2)
        c.setStrokeColor(colors.grey)
        c.line(margin, height / 2, width - margin, height / 2)
        c.setDash()

        c.save()
        return output_path

    def generate_financial_report_pdf(self, output_path: str) -> str:
        """Rapport financier global en PDF (KPI + synthese comptes)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM pilgrims")
            total_pilgrims = int(cursor.fetchone()[0] or 0)
            cursor.execute("SELECT COALESCE(SUM(total_cost), 0) FROM pilgrims")
            total_target = int(cursor.fetchone()[0] or 0)
            cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM payments")
            total_paid = int(cursor.fetchone()[0] or 0)
            cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses")
            total_expenses = int(cursor.fetchone()[0] or 0)
            cursor.execute(
                """
                SELECT
                    p.id, p.lname, p.fname, p.total_cost,
                    COALESCE((SELECT SUM(amount) FROM payments WHERE pilgrim_id = p.id), 0) AS total_verse
                FROM pilgrims p
                ORDER BY (p.total_cost - COALESCE((SELECT SUM(amount) FROM payments WHERE pilgrim_id = p.id), 0)) DESC
                LIMIT 15
                """
            )
            priority_rows = cursor.fetchall()

        reliquat = max(total_target - total_paid, 0)
        recovery_rate = (total_paid / total_target * 100) if total_target > 0 else 0
        net_cash = total_paid - total_expenses

        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4
        margin = 15 * mm
        y = height - margin

        c.setFont("Helvetica-Bold", 14)
        c.drawString(margin, y, "DAROU SALAM - RAPPORT FINANCIER")
        y -= 6 * mm
        c.setFont("Helvetica", 9)
        c.drawString(margin, y, f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        y -= 10 * mm

        kpi_data = [
            ["KPI", "Valeur"],
            ["Total pelerins", str(total_pilgrims)],
            ["Montant cible", self._format_amount(total_target)],
            ["Total encaisse", self._format_amount(total_paid)],
            ["Total reliquat", self._format_amount(reliquat)],
            ["Depenses", self._format_amount(total_expenses)],
            ["Tresorerie nette", self._format_amount(net_cash)],
            ["Taux de recouvrement", f"{recovery_rate:.2f}%"],
        ]
        kpi_table = Table(kpi_data, colWidths=[70 * mm, 80 * mm])
        kpi_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B5E20")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ]
            )
        )
        kpi_table.wrapOn(c, width - 2 * margin, 70 * mm)
        kpi_table.drawOn(c, margin, y - 55 * mm)
        y -= 65 * mm

        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin, y, "Top pelerins prioritaires (plus fort reliquat)")
        y -= 6 * mm

        rows = [["ID", "Nom", "Cible", "Encaisse", "Reliquat"]]
        for pid, lname, fname, total_cost, total_verse in priority_rows:
            remain = max(int(total_cost or 0) - int(total_verse or 0), 0)
            rows.append(
                [
                    str(pid),
                    f"{lname} {fname}",
                    f"{int(total_cost or 0):,}".replace(",", " "),
                    f"{int(total_verse or 0):,}".replace(",", " "),
                    f"{remain:,}".replace(",", " "),
                ]
            )
        remain_table = Table(rows, colWidths=[15 * mm, 55 * mm, 30 * mm, 30 * mm, 30 * mm])
        remain_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1565C0")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                ]
            )
        )
        remain_table.wrapOn(c, width - 2 * margin, 120 * mm)
        remain_table.drawOn(c, margin, y - min(120 * mm, (len(rows) * 6.5 * mm)))

        c.save()
        return output_path

    def export_pilgrims_excel(self, output_path: str) -> str:
        """Export de la liste complete des pelerins en Excel."""
        wb = Workbook()
        ws = wb.active
        ws.title = "Pelerins"
        ws.append(
            [
                "ID",
                "Nom",
                "Prenom",
                "Sexe",
                "Date naissance",
                "Lieu naissance",
                "Passeport/CNI",
                "Montant prevu",
                "Montant verse",
                "Reliquat",
                "Statut",
            ]
        )

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    p.id, p.lname, p.fname, p.sex, p.birth_date, p.birth_place, p.passport, p.total_cost,
                    COALESCE((SELECT SUM(amount) FROM payments WHERE pilgrim_id = p.id), 0) AS total_verse
                FROM pilgrims p
                ORDER BY p.id ASC
                """
            )
            for row in cursor.fetchall():
                pid, lname, fname, sex, bdate, bplace, passport, total_cost, total_verse = row
                total_cost = int(total_cost or 0)
                total_verse = int(total_verse or 0)
                reliquat = max(total_cost - total_verse, 0)
                if total_verse == 0:
                    status = "NON"
                elif total_verse < total_cost:
                    status = "PARTIEL"
                elif total_verse == total_cost:
                    status = "PAYE"
                else:
                    status = "SOLDE"
                ws.append([pid, lname, fname, sex, bdate, bplace, passport, total_cost, total_verse, reliquat, status])

        wb.save(output_path)
        return output_path

    def export_expenses_csv(self, output_path: str) -> str:
        """Export CSV de l'historique des depenses."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT e.date, e.amount, COALESCE(a.name, '-') || ' ' || COALESCE(a.bank, '-') AS compte, COALESCE(e.motif, '-')
                FROM expenses e
                LEFT JOIN accounts a ON a.id = e.source_account_id
                ORDER BY e.date DESC, e.id DESC
                """
            )
            rows = cursor.fetchall()

        with open(output_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file, delimiter=";")
            writer.writerow(["Date", "Montant", "Compte source", "Motif"])
            writer.writerows(rows)

        return output_path

    def export_confirmed_departures_excel(self, output_path: str) -> str:
        wb = Workbook()
        ws = wb.active
        ws.title = "Departs confirmes"
        ws.append(["ID", "Nom", "Prenom", "Date naissance", "CNIB/Passeport", "Telephone", "Date confirmation"])
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    p.id, p.lname, p.fname, p.birth_date, p.passport,
                    COALESCE((SELECT number FROM numbers WHERE pilgrim_id = p.id LIMIT 1), '-') AS tel1,
                    COALESCE(p.departure_confirmed_date, '-')
                FROM pilgrims p
                WHERE COALESCE(p.departure_confirmed, 0) = 1
                ORDER BY p.departure_confirmed_date DESC, p.id DESC
                """
            )
            for row in cursor.fetchall():
                ws.append(list(row))
        wb.save(output_path)
        return output_path