import io
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

logger = logging.getLogger(__name__)

# Dark Theme Palette
BG_COLOR = "#18191C"
PANEL_COLOR = "#232428"
TEXT_COLOR = "#F2F3F5"
MUTED_TEXT = "#949BA4"
GRID_COLOR = "#35373C"

COLOR_BLURPLE = "#5865F2"
COLOR_GREEN = "#57F287"
COLOR_YELLOW = "#FEE75C"
COLOR_PINK = "#EB459E"
COLOR_CYAN = "#00C7FF"
COLOR_ORANGE = "#E67E22"
COLOR_PURPLE = "#9B59B6"

CATEGORY_COLORS = {
    "MICROSERVICES": COLOR_CYAN,
    "DSA": COLOR_BLURPLE,
    "LLD": COLOR_PINK,
    "HLD": COLOR_YELLOW,
    "CORE_CS": COLOR_GREEN,
    "MOCK_INTERVIEW": COLOR_ORANGE,
    "CUSTOM": COLOR_PURPLE
}

class ChartService:
    def generate_progress_chart(
        self,
        display_name: str,
        summary: Dict[str, Any],
        daily_logs: List[Dict[str, Any]],
        topic_stats: Optional[Dict[str, int]] = None
    ) -> io.BytesIO:
        """
        Generate a multi-panel visual analytics progress card using matplotlib.
        Returns a BytesIO buffer containing the PNG image.
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 9), facecolor=BG_COLOR)
        fig.suptitle(
            f"Interview Preparation Analytics: {display_name}",
            fontsize=18,
            fontweight="bold",
            color=TEXT_COLOR,
            y=0.97
        )

        plt.subplots_adjust(hspace=0.35, wspace=0.25, top=0.90, bottom=0.08, left=0.07, right=0.95)

        # ---------------------------------------------------------------------
        # Panel 1 (Top-Left): 14-Day Daily Study Time (Bar Chart)
        # ---------------------------------------------------------------------
        ax1 = axes[0, 0]
        ax1.set_facecolor(PANEL_COLOR)
        ax1.set_title("Last 14 Days Study Minutes", color=TEXT_COLOR, fontsize=13, fontweight="bold", pad=10)

        now = datetime.now(timezone.utc)
        dates = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(13, -1, -1)]
        short_labels = [(now - timedelta(days=i)).strftime("%d %b") for i in range(13, -1, -1)]
        
        minutes_map = {d: 0 for d in dates}
        for log in daily_logs:
            d_str = log.get("date")
            if d_str in minutes_map:
                minutes_map[d_str] += log.get("minutes", 0)

        vals = [minutes_map[d] for d in dates]
        bars = ax1.bar(short_labels, vals, color=COLOR_BLURPLE, edgecolor=COLOR_CYAN, linewidth=0.8, alpha=0.9, width=0.6)
        
        # Highlight non-zero days
        for bar, val in zip(bars, vals):
            if val > 0:
                bar.set_color(COLOR_CYAN)
                ax1.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 1,
                    f"{int(val)}m",
                    ha="center",
                    va="bottom",
                    color=TEXT_COLOR,
                    fontsize=8,
                    fontweight="bold"
                )

        ax1.tick_params(colors=MUTED_TEXT, labelsize=8)
        ax1.set_xticks(range(len(short_labels)))
        ax1.set_xticklabels(short_labels, rotation=45, ha="right")
        ax1.set_ylabel("Minutes", color=MUTED_TEXT, fontsize=10)
        ax1.grid(axis="y", color=GRID_COLOR, linestyle="--", alpha=0.6)
        ax1.spines["top"].set_visible(False)
        ax1.spines["right"].set_visible(False)
        ax1.spines["left"].set_color(GRID_COLOR)
        ax1.spines["bottom"].set_color(GRID_COLOR)

        # ---------------------------------------------------------------------
        # Panel 2 (Top-Right): Cumulative Study Hours Growth Trend
        # ---------------------------------------------------------------------
        ax2 = axes[0, 1]
        ax2.set_facecolor(PANEL_COLOR)
        ax2.set_title("Cumulative Study Hours Trajectory", color=TEXT_COLOR, fontsize=13, fontweight="bold", pad=10)

        cum_hours = []
        running_total = 0.0
        for v in vals:
            running_total += v / 60.0
            cum_hours.append(running_total)

        ax2.plot(short_labels, cum_hours, color=COLOR_GREEN, linewidth=2.5, marker="o", markersize=4, label="Hours Studied")
        ax2.fill_between(short_labels, cum_hours, color=COLOR_GREEN, alpha=0.15)

        ax2.tick_params(colors=MUTED_TEXT, labelsize=8)
        ax2.set_xticks(range(len(short_labels)))
        ax2.set_xticklabels(short_labels, rotation=45, ha="right")
        ax2.set_ylabel("Total Hours", color=MUTED_TEXT, fontsize=10)
        ax2.grid(True, color=GRID_COLOR, linestyle="--", alpha=0.6)
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_visible(False)
        ax2.spines["left"].set_color(GRID_COLOR)
        ax2.spines["bottom"].set_color(GRID_COLOR)

        # ---------------------------------------------------------------------
        # Panel 3 (Bottom-Left): Categorical Distribution (Donut Chart)
        # ---------------------------------------------------------------------
        ax3 = axes[1, 0]
        ax3.set_facecolor(PANEL_COLOR)
        ax3.set_title("Preparation Distribution by Category", color=TEXT_COLOR, fontsize=13, fontweight="bold", pad=10)

        cats = summary.get("categories", {})
        cat_labels = []
        cat_values = []
        colors = []

        for c_key, data in cats.items():
            h = data.get("total_hours", 0)
            if h > 0:
                cat_labels.append(f"{c_key} ({h}h)")
                cat_values.append(h)
                colors.append(CATEGORY_COLORS.get(c_key, COLOR_PURPLE))

        if not cat_values:
            cat_labels = ["No Sessions Yet"]
            cat_values = [1]
            colors = [GRID_COLOR]

        wedges, texts, autotexts = ax3.pie(
            cat_values,
            labels=cat_labels,
            autopct="%1.0f%%" if sum(cat_values) > 0 and cat_labels[0] != "No Sessions Yet" else "",
            colors=colors,
            startangle=140,
            pctdistance=0.75,
            textprops={"color": TEXT_COLOR, "fontsize": 9},
            wedgeprops={"width": 0.45, "edgecolor": BG_COLOR, "linewidth": 2}
        )
        for at in autotexts:
            at.set_color(BG_COLOR)
            at.set_fontweight("bold")

        # ---------------------------------------------------------------------
        # Panel 4 (Bottom-Right): Topic Checklist Completion Status
        # ---------------------------------------------------------------------
        ax4 = axes[1, 1]
        ax4.set_facecolor(PANEL_COLOR)
        ax4.set_title("Syllabus Topic Completion", color=TEXT_COLOR, fontsize=13, fontweight="bold", pad=10)

        t_stats = topic_stats or {"COMPLETED": 0, "IN_PROGRESS": 0, "TODO": 0}
        completed = t_stats.get("COMPLETED", 0)
        in_prog = t_stats.get("IN_PROGRESS", 0)
        todo = t_stats.get("TODO", 0)
        total_topics = completed + in_prog + todo

        if total_topics == 0:
            total_topics = 1
            todo = 1

        y_pos = [0]
        ax4.barh(y_pos, [completed], color=COLOR_GREEN, edgecolor=BG_COLOR, height=0.4, label=f"Completed ({completed})")
        ax4.barh(y_pos, [in_prog], left=[completed], color=COLOR_YELLOW, edgecolor=BG_COLOR, height=0.4, label=f"In Progress ({in_prog})")
        ax4.barh(y_pos, [todo], left=[completed + in_prog], color="#4E5058", edgecolor=BG_COLOR, height=0.4, label=f"To-Do ({todo})")

        pct_done = (completed / total_topics) * 100.0 if total_topics > 0 else 0
        ax4.text(
            total_topics / 2,
            0.3,
            f"Overall Completion: {pct_done:.1f}% ({completed}/{total_topics} Topics)",
            ha="center",
            va="center",
            color=TEXT_COLOR,
            fontsize=11,
            fontweight="bold"
        )

        ax4.set_xlim(0, max(1, total_topics))
        ax4.set_yticks([])
        ax4.tick_params(colors=MUTED_TEXT, labelsize=9)
        ax4.set_xlabel("Number of Topics", color=MUTED_TEXT, fontsize=10)
        ax4.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=3, frameon=False, labelcolor=TEXT_COLOR, fontsize=9)
        ax4.spines["top"].set_visible(False)
        ax4.spines["right"].set_visible(False)
        ax4.spines["left"].set_visible(False)
        ax4.spines["bottom"].set_color(GRID_COLOR)

        # Output to BytesIO
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, facecolor=BG_COLOR, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return buf

chart_service = ChartService()
