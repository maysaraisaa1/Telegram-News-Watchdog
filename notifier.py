"""
notifier.py - Telegram Bot Alerting & Fully Arabic Dark HTML Dashboard Generator
وكيل الرصد والذكاء الإخباري الشامل (AI & Sports Autonomous Watchdog)
"""

from datetime import datetime, timezone
import html
from pathlib import Path
import shutil
from typing import List, Optional
import webbrowser
import requests
import config
from processor import ExecutiveBrief, ProcessedNewsItem


class ReportNotifier:
    """Dispatches executive briefings via Telegram and generates sleek Arabic local HTML dashboards."""

    def __init__(self, reports_dir: Optional[Path] = None) -> None:
        self.reports_dir = reports_dir or config.REPORTS_DIR
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    # =========================================================================
    # 1. Telegram Bot Delivery
    # =========================================================================
    def send_telegram_alert(self, brief: ExecutiveBrief) -> bool:
        """Sends the formatted executive brief to Telegram if configured."""
        token = config.TELEGRAM_BOT_TOKEN
        chat_id = config.TELEGRAM_CHAT_ID

        if not token or not chat_id:
            print("  [i] Telegram Bot Token/Chat ID not set. Skipping Telegram notification.")
            return False

        message_chunks = self._format_telegram_messages(brief)
        url = f"https://api.telegram.org/bot{token}/sendMessage"

        success_all = True
        for idx, chunk in enumerate(message_chunks, start=1):
            payload = {
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }
            try:
                resp = requests.post(url, json=payload, timeout=15)
                if resp.status_code == 200:
                    print(f"  [✓] Telegram message part {idx}/{len(message_chunks)} sent successfully.")
                else:
                    print(f"  [X] Telegram API error ({resp.status_code}): {resp.text}")
                    # Try fallback without HTML parse mode if entity parsing failed
                    fallback_payload = {
                        "chat_id": chat_id,
                        "text": chunk.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", "").replace("<code>", "").replace("</code>", ""),
                        "disable_web_page_preview": True,
                    }
                    fb_resp = requests.post(url, json=fallback_payload, timeout=15)
                    if fb_resp.status_code == 200:
                        print(f"  [✓] Telegram message part {idx} sent successfully via fallback mode.")
                    else:
                        success_all = False
            except requests.RequestException as e:
                print(f"  [X] Failed to connect to Telegram API: {e}")
                success_all = False

        return success_all

    def _format_telegram_messages(self, brief: ExecutiveBrief) -> List[str]:
        """Formats brief into clean, structured Arabic Telegram message chunks."""
        chunks: List[str] = []

        # ==================== Section 1: Tech & AI ====================
        tech_lines = [
            "🚀 <b>وكيل الرصد والذكاء الإخباري الشامل</b>",
            "━━━━━━━━━━━━━━━━━━━━━━━━━",
            "🤖 <b>أخبار التقنية والذكاء الاصطناعي</b>",
            "<i>(Google, Apple, Gemini, Claude, OpenAI...)</i>",
            f"📅 التوقيت: <code>{brief.timestamp}</code>",
            f"📊 تم فحص <b>{brief.total_scanned}</b> مقالاً | عُثر على <b>{brief.new_found}</b> خبراً جديداً\n",
            f"📝 <b>الموجز السريع:</b>\n<i>{html.escape(brief.tech_ai_summary_ar)}</i>\n",
            "────────── أهم الأخبار ──────────\n",
        ]

        for i, item in enumerate(brief.tech_ai_highlights, 1):
            title = html.escape(item.title_ar or item.title)
            takeaway = html.escape(item.key_takeaway_ar or item.key_takeaway)
            tags = " ".join([f"#{t.replace(' ', '_')}" for t in (item.tags_ar or item.tags)])
            tech_lines.append(
                f"{i}️⃣ <b>{title}</b>\n"
                f"🎯 <b>التقييم:</b> {item.score}/100 | {tags}\n"
                f"💡 <b>الملخص:</b> {takeaway}\n"
                f"🔗 <b>المصدر ({html.escape(item.source)}):</b> <a href='{item.link}'>اضغط لقراءة الخبر كاملاً ↗</a>\n"
            )

        chunks.append("\n".join(tech_lines))

        # ==================== Section 2: Sports & FC Barcelona ====================
        sports_lines = [
            "⚽ <b>أخبار نادي برشلونة والكرة الأوروبية</b>",
            "<i>(FC Barcelona, UCL, La Liga, Premier League...)</i>",
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n",
            f"📝 <b>الموجز الرياضي:</b>\n<i>{html.escape(brief.sports_summary_ar)}</i>\n",
            "────────── أهم الأخبار ──────────\n",
        ]

        for i, item in enumerate(brief.sports_highlights, 1):
            title = html.escape(item.title_ar or item.title)
            takeaway = html.escape(item.key_takeaway_ar or item.key_takeaway)
            tags = " ".join([f"#{t.replace(' ', '_')}" for t in (item.tags_ar or item.tags)])
            sports_lines.append(
                f"{i}️⃣ <b>{title}</b>\n"
                f"🔥 <b>الأهمية:</b> {item.score}/100 | {tags}\n"
                f"📌 <b>الملخص:</b> {takeaway}\n"
                f"🏟️ <b>المصدر ({html.escape(item.source)}):</b> <a href='{item.link}'>اضغط لقراءة الخبر كاملاً ↗</a>\n"
            )

        chunks.append("\n".join(sports_lines))

        return chunks

    # =========================================================================
    # 2. Modern Fully Arabic Dark Dashboard HTML Generator
    # =========================================================================
    def generate_html_dashboard(
        self, brief: ExecutiveBrief, auto_open: bool = config.AUTO_OPEN_BROWSER
    ) -> Path:
        """
        Generates a premium, 100% Arabic RTL dark-mode Glassmorphism dashboard.
        Saves both a timestamped version and a latest.html copy.
        """
        now_clean = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f"watchdog_report_{now_clean}.html"
        latest_file = self.reports_dir / "latest.html"

        def render_cards(items: List[ProcessedNewsItem], accent_color: str) -> str:
            if not items:
                return """
                <div class="empty-state">
                    <p>لم يتم العثور على تحديثات ذات أولوية قصوى خلال هذه الدورة.</p>
                </div>
                """
            html_cards = []
            for item in items:
                tags_list = item.tags_ar if item.tags_ar else item.tags
                tags_html = "".join([f'<span class="badge badge-tag">{html.escape(t)}</span>' for t in tags_list])
                display_title = item.title_ar or item.title
                display_takeaway = item.key_takeaway_ar or item.key_takeaway

                card_html = f"""
                <article class="news-card" data-category="{item.category}" data-search="{html.escape(display_title.lower())} {html.escape(item.title.lower())} {' '.join(tags_list).lower()}">
                    <div class="card-header">
                        <div class="badges-row">
                            <span class="badge badge-score" style="background: {accent_color};">{item.score} / 100</span>
                            {tags_html}
                        </div>
                        <span class="source-tag">{html.escape(item.source)}</span>
                    </div>
                    <h3 class="news-title">
                        <a href="{item.link}" target="_blank" rel="noopener noreferrer">{html.escape(display_title)}</a>
                    </h3>
                    <div class="original-title-ref">
                        <span>Original:</span> {html.escape(item.title)}
                    </div>
                    <div class="takeaway-box">
                        <span class="takeaway-icon">⚡</span>
                        <p class="takeaway-text">{html.escape(display_takeaway)}</p>
                    </div>
                    <div class="card-footer">
                        <span class="pub-date">🕒 {html.escape(item.published_at[:16] if item.published_at else 'مؤخراً')}</span>
                        <a href="{item.link}" target="_blank" rel="noopener noreferrer" class="read-btn">
                            قراءة المصدر كاملاً ↗
                        </a>
                    </div>
                </article>
                """
                html_cards.append(card_html)
            return "\n".join(html_cards)

        tech_cards_html = render_cards(brief.tech_ai_highlights, "linear-gradient(135deg, #06b6d4, #3b82f6)")
        sports_cards_html = render_cards(brief.sports_highlights, "linear-gradient(135deg, #ec4899, #ef4444)")

        full_html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة الرصد والذكاء الإخباري | AI & Sports Watchdog</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-base: #0a0e17;
            --bg-surface: #111827;
            --bg-card: rgba(17, 24, 39, 0.78);
            --border-glass: rgba(255, 255, 255, 0.08);
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
            --tech-glow: #06b6d4;
            --sports-glow: #ec4899;
            --radius-xl: 18px;
            --radius-md: 10px;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Cairo', sans-serif;
            background: var(--bg-base);
            color: var(--text-main);
            min-height: 100vh;
            padding: 2rem 1.5rem;
            direction: rtl;
            text-align: right;
            background-image: 
                radial-gradient(at 10% 10%, rgba(6, 182, 212, 0.12) 0px, transparent 50%),
                radial-gradient(at 90% 90%, rgba(236, 72, 153, 0.12) 0px, transparent 50%);
            background-attachment: fixed;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        header {{
            background: var(--bg-card);
            border: 1px solid var(--border-glass);
            backdrop-filter: blur(16px);
            border-radius: var(--radius-xl);
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            gap: 1.5rem;
        }}

        .brand-title h1 {{
            font-size: 2rem;
            font-weight: 900;
            background: linear-gradient(135deg, #38bdf8, #818cf8, #f472b6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .brand-title p {{
            color: var(--text-muted);
            margin-top: 0.5rem;
            font-size: 0.95rem;
        }}

        .metrics-bar {{
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
        }}

        .metric-pill {{
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--border-glass);
            padding: 0.6rem 1.2rem;
            border-radius: var(--radius-md);
            text-align: center;
        }}

        .metric-val {{
            font-size: 1.3rem;
            font-weight: 800;
            color: #38bdf8;
            font-family: 'JetBrains Mono', monospace;
        }}

        .metric-label {{
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
        }}

        .toolbar {{
            margin-bottom: 2rem;
            display: flex;
            gap: 1rem;
            align-items: center;
            flex-wrap: wrap;
        }}

        .search-input {{
            flex: 1;
            min-width: 280px;
            background: var(--bg-card);
            border: 1px solid var(--border-glass);
            padding: 0.9rem 1.25rem;
            border-radius: var(--radius-md);
            color: var(--text-main);
            font-family: 'Cairo', sans-serif;
            font-size: 1rem;
            outline: none;
            transition: border-color 0.2s, box-shadow 0.2s;
        }}

        .search-input:focus {{
            border-color: var(--tech-glow);
            box-shadow: 0 0 12px rgba(6, 182, 212, 0.3);
        }}

        .tracks-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(580px, 1fr));
            gap: 2rem;
        }}

        @media (max-width: 768px) {{
            .tracks-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        .track-column {{
            background: var(--bg-card);
            border: 1px solid var(--border-glass);
            backdrop-filter: blur(12px);
            border-radius: var(--radius-xl);
            padding: 1.75rem;
            box-shadow: 0 8px 24px rgba(0,0,0,0.3);
        }}

        .track-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 1.25rem;
            border-bottom: 1px solid var(--border-glass);
            margin-bottom: 1.5rem;
        }}

        .track-header h2 {{
            font-size: 1.4rem;
            font-weight: 800;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .track-tech h2 {{ color: #38bdf8; }}
        .track-sports h2 {{ color: #f472b6; }}

        .track-summary {{
            background: rgba(255, 255, 255, 0.03);
            border-right: 4px solid var(--tech-glow);
            padding: 0.9rem 1.1rem;
            border-radius: 6px;
            font-size: 0.95rem;
            line-height: 1.6;
            color: #d1d5db;
            margin-bottom: 1.5rem;
        }}

        .track-sports .track-summary {{
            border-right-color: var(--sports-glow);
        }}

        .cards-list {{
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
        }}

        .news-card {{
            background: rgba(255, 255, 255, 0.025);
            border: 1px solid var(--border-glass);
            border-radius: var(--radius-md);
            padding: 1.35rem;
            transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
        }}

        .news-card:hover {{
            transform: translateY(-3px);
            border-color: rgba(255, 255, 255, 0.2);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.5);
        }}

        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}

        .badges-row {{
            display: flex;
            gap: 0.4rem;
            flex-wrap: wrap;
            align-items: center;
        }}

        .badge {{
            font-size: 0.78rem;
            font-weight: 700;
            padding: 0.2rem 0.65rem;
            border-radius: 9999px;
            color: #fff;
        }}

        .badge-score {{
            font-family: 'JetBrains Mono', monospace;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
        }}

        .badge-tag {{
            background: rgba(255, 255, 255, 0.08);
            color: #cbd5e1;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}

        .source-tag {{
            font-size: 0.75rem;
            color: var(--text-muted);
            background: rgba(0, 0, 0, 0.35);
            padding: 0.25rem 0.55rem;
            border-radius: 4px;
        }}

        .news-title {{
            font-size: 1.15rem;
            font-weight: 700;
            line-height: 1.5;
            margin-bottom: 0.5rem;
        }}

        .news-title a {{
            color: var(--text-main);
            text-decoration: none;
            transition: color 0.2s;
        }}

        .news-title a:hover {{
            color: #38bdf8;
        }}

        .original-title-ref {{
            font-size: 0.78rem;
            color: #6b7280;
            margin-bottom: 0.75rem;
            direction: ltr;
            text-align: left;
            font-family: sans-serif;
        }}

        .original-title-ref span {{
            color: #4b5563;
            font-weight: bold;
        }}

        .takeaway-box {{
            display: flex;
            gap: 0.6rem;
            background: rgba(0, 0, 0, 0.28);
            padding: 0.75rem 0.95rem;
            border-radius: 8px;
            margin-bottom: 0.95rem;
            align-items: flex-start;
        }}

        .takeaway-icon {{
            font-size: 1rem;
            color: #f59e0b;
        }}

        .takeaway-text {{
            font-size: 0.9rem;
            color: #e5e7eb;
            line-height: 1.5;
        }}

        .card-footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.82rem;
            color: var(--text-muted);
        }}

        .read-btn {{
            color: #38bdf8;
            text-decoration: none;
            font-weight: 700;
            padding: 0.3rem 0.75rem;
            border-radius: 6px;
            background: rgba(56, 189, 248, 0.12);
            transition: background 0.2s, color 0.2s;
        }}

        .read-btn:hover {{
            background: rgba(56, 189, 248, 0.3);
            color: #fff;
        }}

        footer {{
            text-align: center;
            margin-top: 3rem;
            color: var(--text-muted);
            font-size: 0.9rem;
            padding-bottom: 2rem;
        }}

        .empty-state {{
            padding: 3rem;
            text-align: center;
            color: var(--text-muted);
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header>
            <div class="brand-title">
                <h1>🛡️ وكيل الرصد والذكاء الإخباري الشامل</h1>
                <p>وكيل مستقل للرصد الذكي للأخبار والتحليلات الفورية | مدمج مع تيليجرام ومهام Antigravity</p>
            </div>
            <div class="metrics-bar">
                <div class="metric-pill">
                    <div class="metric-val">{brief.total_scanned}</div>
                    <div class="metric-label">إجمالي الأخبار المفحوصة</div>
                </div>
                <div class="metric-pill">
                    <div class="metric-val">{brief.new_found}</div>
                    <div class="metric-label">الأخبار الجديدة</div>
                </div>
                <div class="metric-pill">
                    <div class="metric-val">{len(brief.tech_ai_highlights) + len(brief.sports_highlights)}</div>
                    <div class="metric-label">أهم الاختيارات</div>
                </div>
                <div class="metric-pill">
                    <div class="metric-val">100%</div>
                    <div class="metric-label">حالة النظام</div>
                </div>
            </div>
        </header>

        <!-- Search Bar -->
        <div class="toolbar">
            <input type="text" id="liveSearch" class="search-input" placeholder="🔍 ابحث في العناوين والكلمات المفتاحية (مثال: برشلونة، فليك، يامال، جيميني، آبل، كلود)..." onkeyup="filterNews()">
        </div>

        <!-- Two Track Layout -->
        <div class="tracks-grid">
            <!-- Track 1: Tech & AI -->
            <section class="track-column track-tech">
                <div class="track-header">
                    <h2>🤖 قطاع التقنية والذكاء الاصطناعي</h2>
                    <span class="badge" style="background: var(--tech-glow);">أهم 5 أحداث</span>
                </div>
                <div class="track-summary">
                    {html.escape(brief.tech_ai_summary_ar)}
                </div>
                <div class="cards-list">
                    {tech_cards_html}
                </div>
            </section>

            <!-- Track 2: Sports & FC Barcelona -->
            <section class="track-column track-sports">
                <div class="track-header">
                    <h2>⚽ قطاع الرياضة وكرة القدم الأوروبية</h2>
                    <span class="badge" style="background: var(--sports-glow);">أهم 5 أحداث</span>
                </div>
                <div class="track-summary">
                    {html.escape(brief.sports_summary_ar)}
                </div>
                <div class="cards-list">
                    {sports_cards_html}
                </div>
            </section>
        </div>

        <footer>
            تم التوليد تلقائياً بواسطة <b>AI & Sports Autonomous Watchdog</b> في {brief.timestamp} • متوافق مع تيليجرام وجدولة Antigravity
        </footer>
    </div>

    <script>
        function filterNews() {{
            const query = document.getElementById('liveSearch').value.toLowerCase().trim();
            const cards = document.querySelectorAll('.news-card');
            cards.forEach(card => {{
                const searchData = card.getAttribute('data-search') || '';
                if (!query || searchData.includes(query)) {{
                    card.style.display = 'block';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
        }}
    </script>
</body>
</html>
"""
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(full_html)

        # Mirror as latest.html
        shutil.copyfile(report_file, latest_file)
        print(f"  [✓] Fully Arabic Dark Dashboard generated: {report_file}")
        print(f"  [✓] Updated quick view: {latest_file}")

        if auto_open:
            try:
                webbrowser.open(latest_file.resolve().as_uri())
            except Exception as e:
                print(f"  [!] Note: Could not launch browser automatically: {e}")

        return latest_file
