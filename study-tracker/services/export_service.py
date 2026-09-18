from __future__ import annotations
import io
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)

class ExportService:
    """Generates professionally styled Excel (.xlsx) workbooks for study logs and analytics."""

    def generate_excel_export(self, export_data: Dict[str, Any], display_name: str) -> io.BytesIO:
        """
        Creates a complete multi-sheet Excel study report:
        - Sheet 1: 📊 Overview & Scorecard
        - Sheet 2: 📚 Study Logs & Sessions
        - Sheet 3: 📝 Topics & Revision Notes
        """
        wb = openpyxl.Workbook()
        
        # Style Definitions
        font_title = Font(name="Segoe UI", size=16, bold=True, color="FFFFFF")
        font_section = Font(name="Segoe UI", size=12, bold=True, color="1E293B")
        font_header = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        font_kpi_num = Font(name="Segoe UI", size=14, bold=True, color="0F172A")
        font_kpi_label = Font(name="Segoe UI", size=9, bold=False, color="64748B")
        font_regular = Font(name="Segoe UI", size=10, bold=False, color="1E293B")
        font_bold = Font(name="Segoe UI", size=10, bold=True, color="1E293B")
        
        fill_title = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid") # Dark Slate
        fill_header = PatternFill(start_color="334155", end_color="334155", fill_type="solid") # Slate Header
        fill_header_accent = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid") # Royal Blue
        fill_kpi = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
        fill_zebra = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
        
        border_thin = Border(
            left=Side(style="thin", color="E2E8F0"),
            right=Side(style="thin", color="E2E8F0"),
            top=Side(style="thin", color="E2E8F0"),
            bottom=Side(style="thin", color="E2E8F0")
        )
        border_kpi = Border(
            left=Side(style="medium", color="CBD5E1"),
            right=Side(style="medium", color="CBD5E1"),
            top=Side(style="medium", color="CBD5E1"),
            bottom=Side(style="medium", color="CBD5E1")
        )

        align_center = Alignment(horizontal="center", vertical="center")
        align_left = Alignment(horizontal="left", vertical="center")
        align_wrap_left = Alignment(horizontal="left", vertical="top", wrap_text=True)

        profile = export_data.get("profile", {})
        rank_info = export_data.get("rank_info", {})
        streak = export_data.get("streak", {})
        sessions = export_data.get("sessions", [])
        topics = export_data.get("topics", [])
        badges = export_data.get("badges", [])

        # ==========================================
        # SHEET 1: 📊 Overview & Scorecard
        # ==========================================
        ws1 = wb.active
        ws1.title = "Overview & Scorecard"
        ws1.views.sheetView[0].showGridLines = True

        # Header Title Banner
        ws1.merge_cells("A1:F2")
        title_cell = ws1["A1"]
        title_cell.value = f"STUDY TRACKER & PREPARATION REPORT: {display_name.upper()}"
        title_cell.font = font_title
        title_cell.fill = fill_title
        title_cell.alignment = align_center

        # Generated Timestamp
        ws1["A3"] = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')} • Candidate Discord ID: {export_data.get('discord_id', 'N/A')}"
        ws1["A3"].font = Font(name="Segoe UI", size=9, italic=True, color="64748B")

        # KPI Metric Cards (Row 5-7)
        kpis = [
            ("Current Rank", f"{rank_info.get('title', 'Novice')} (Lvl {rank_info.get('level', 1)})", "A", "B"),
            ("Topics Mastered", str(profile.get("total_topics_count", 0)), "C", "C"),
            ("Study Time (Hours)", str(round(profile.get("total_study_minutes", 0) / 60, 1)), "D", "D"),
            ("Active Streak", f"{streak.get('current_streak', 0)} Days", "E", "E"),
            ("Best Streak", f"{streak.get('longest_streak', 0)} Days", "F", "F")
        ]

        for label, val, start_col, end_col in kpis:
            col_range_top = f"{start_col}5:{end_col}5"
            col_range_val = f"{start_col}6:{end_col}6"
            if start_col != end_col:
                ws1.merge_cells(col_range_top)
                ws1.merge_cells(col_range_val)
            
            c_top = ws1[f"{start_col}5"]
            c_top.value = label
            c_top.font = font_kpi_label
            c_top.fill = fill_kpi
            c_top.alignment = align_center

            c_val = ws1[f"{start_col}6"]
            c_val.value = val
            c_val.font = font_kpi_num
            c_val.fill = fill_kpi
            c_val.alignment = align_center

            for col_l in range(ord(start_col), ord(end_col) + 1):
                col_char = chr(col_l)
                ws1[f"{col_char}5"].border = border_kpi
                ws1[f"{col_char}6"].border = border_kpi

        # Section: Profile Details (Row 8)
        ws1["A8"] = "Candidate Target & Profile Details"
        ws1["A8"].font = font_section
        
        prof_rows = [
            ("Target Role:", profile.get("target_role", "Software Engineer")),
            ("Target Companies:", profile.get("target_companies", "Google, Microsoft, Amazon")),
            ("Total Days Studied:", f"{streak.get('total_days_studied', 0)} Active Days"),
            ("Problems Solved:", f"{profile.get('total_problems_solved', 0)} Problems"),
            ("Total Sessions Logged:", f"{len(sessions)} Sessions")
        ]

        for idx, (lbl, val) in enumerate(prof_rows, start=9):
            ws1[f"A{idx}"] = lbl
            ws1[f"A{idx}"].font = font_bold
            ws1[f"B{idx}"] = val
            ws1[f"B{idx}"].font = font_regular

        # Section: Unlocked Badges (Row 15)
        ws1["A15"] = "Unlocked Achievement Badges"
        ws1["A15"].font = font_section

        ws1["A16"] = "Badge Icon"
        ws1["B16"] = "Badge Title"
        ws1["C16"] = "Description"
        ws1["D16"] = "Unlocked Date"
        ws1.merge_cells("D16:F16")

        for col in ["A16", "B16", "C16", "D16", "E16", "F16"]:
            ws1[col].font = font_header
            ws1[col].fill = fill_header_accent
            ws1[col].alignment = align_center
            ws1[col].border = border_thin

        if badges:
            for b_idx, b in enumerate(badges, start=17):
                ws1[f"A{b_idx}"] = b.get("icon", "🎖️")
                ws1[f"B{b_idx}"] = b.get("title", "")
                ws1[f"C{b_idx}"] = b.get("description", "")
                ws1[f"D{b_idx}"] = str(b.get("unlocked_at", ""))[:19]
                ws1.merge_cells(f"D{b_idx}:F{b_idx}")

                ws1[f"A{b_idx}"].alignment = align_center
                ws1[f"B{b_idx}"].font = font_bold
                for c in ["A", "B", "C", "D", "E", "F"]:
                    cell = ws1[f"{c}{b_idx}"]
                    cell.border = border_thin
                    if b_idx % 2 == 0:
                        cell.fill = fill_zebra
        else:
            ws1["A17"] = "No badges unlocked yet. Keep logging topics to earn achievements!"
            ws1.merge_cells("A17:F17")
            ws1["A17"].font = Font(name="Segoe UI", size=10, italic=True, color="64748B")

        # ==========================================
        # SHEET 2: 📚 Study Logs & Sessions
        # ==========================================
        ws2 = wb.create_sheet(title="Study Logs")
        ws2.views.sheetView[0].showGridLines = True

        log_headers = [
            "Log ID", "Session Date", "Category", "Duration (Mins)",
            "Problems Solved", "Topics Covered", "Attached Notes & Key Takeaways", "Logged At (UTC)"
        ]

        for col_idx, h in enumerate(log_headers, start=1):
            cell = ws2.cell(row=1, column=col_idx, value=h)
            cell.font = font_header
            cell.fill = fill_header
            cell.alignment = align_center
            cell.border = border_thin

        for row_idx, s in enumerate(sessions, start=2):
            topics_str = "\n".join([f"• {t}" for t in s.get("topics", [])]) or "General Study"
            notes_str = s.get("notes") or ""

            ws2.cell(row=row_idx, column=1, value=s.get("id")).alignment = align_center
            ws2.cell(row=row_idx, column=2, value=s.get("session_date")).alignment = align_center
            ws2.cell(row=row_idx, column=3, value=s.get("category", "General")).alignment = align_center
            ws2.cell(row=row_idx, column=4, value=s.get("duration_minutes", 0)).alignment = align_center
            ws2.cell(row=row_idx, column=5, value=s.get("problems_solved", 0)).alignment = align_center
            ws2.cell(row=row_idx, column=6, value=topics_str).alignment = align_wrap_left
            ws2.cell(row=row_idx, column=7, value=notes_str).alignment = align_wrap_left
            ws2.cell(row=row_idx, column=8, value=str(s.get("logged_at", ""))[:19]).alignment = align_center

            fill_row = fill_zebra if row_idx % 2 == 0 else PatternFill(fill_type=None)
            for c_idx in range(1, len(log_headers) + 1):
                c = ws2.cell(row=row_idx, column=c_idx)
                c.font = font_regular
                c.border = border_thin
                if fill_row.fill_type:
                    c.fill = fill_row

        # ==========================================
        # SHEET 3: 📝 Topics & Revision Notes
        # ==========================================
        ws3 = wb.create_sheet(title="Topics & Notes Archive")
        ws3.views.sheetView[0].showGridLines = True

        topic_headers = [
            "Topic ID", "Topic Name", "Domain / Category", "Problems Solved", "Revisions / Sessions", "Logged Date", "Attached Notes & Revision Summary"
        ]

        for col_idx, h in enumerate(topic_headers, start=1):
            cell = ws3.cell(row=1, column=col_idx, value=h)
            cell.font = font_header
            cell.fill = fill_header_accent
            cell.alignment = align_center
            cell.border = border_thin

        for row_idx, t in enumerate(topics, start=2):
            ws3.cell(row=row_idx, column=1, value=t.get("id")).alignment = align_center
            ws3.cell(row=row_idx, column=2, value=t.get("topic_name", "")).alignment = align_left
            ws3.cell(row=row_idx, column=3, value=t.get("category", "General")).alignment = align_center
            ws3.cell(row=row_idx, column=4, value=t.get("problems_solved", 0)).alignment = align_center
            ws3.cell(row=row_idx, column=5, value=t.get("revision_count", 1)).alignment = align_center
            ws3.cell(row=row_idx, column=6, value=t.get("logged_date", "")).alignment = align_center
            ws3.cell(row=row_idx, column=7, value=t.get("notes") or "").alignment = align_wrap_left

            fill_row = fill_zebra if row_idx % 2 == 0 else PatternFill(fill_type=None)
            for c_idx in range(1, len(topic_headers) + 1):
                c = ws3.cell(row=row_idx, column=c_idx)
                c.font = font_regular
                c.border = border_thin
                if fill_row.fill_type:
                    c.fill = fill_row

        # Adjust Column Widths Across Sheets
        for ws in [ws1, ws2, ws3]:
            for col in ws.columns:
                max_len = 0
                col_letter = get_column_letter(col[0].column)
                for cell in col:
                    if cell.value:
                        lines = str(cell.value).split("\n")
                        line_len = max(len(l) for l in lines)
                        if line_len > max_len:
                            max_len = line_len
                ws.column_dimensions[col_letter].width = max(12, min(max_len + 4, 60))

        # Output to BytesIO
        output_stream = io.BytesIO()
        wb.save(output_stream)
        output_stream.seek(0)
        return output_stream

export_service = ExportService()
