"""
main.py - Autonomous Watchdog Pipeline & CLI Controller
وكيل الرصد والذكاء الإخباري الشامل (AI & Sports Autonomous Watchdog)
"""

import argparse
import os
import sys
import time
from typing import List, Optional

# Ensure UTF-8 output encoding across Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import colorama
from colorama import Fore, Style
import config
from database import NewsDatabase
from fetcher import RSSFetcher, RawNewsItem
from notifier import ReportNotifier
from processor import NewsProcessor

# Initialize terminal colors
colorama.init(autoreset=True)


def print_banner() -> None:
    """Prints a styled startup banner."""
    banner = f"""
{Fore.CYAN}{Style.BRIGHT}========================================================================
   🛡️  AI & SPORTS AUTONOMOUS WATCHDOG
   وكيل الرصد والذكاء الإخباري الشامل — Antigravity Scheduled Agent
========================================================================{Style.RESET_ALL}
{Fore.WHITE}  • Track 1: AI & LLMs (Gemini, ChatGPT, Claude, Dev Tools, Tech Giants)
  • Track 2: European Football (FC Barcelona, UCL, La Liga, Premier League)
{Fore.CYAN}------------------------------------------------------------------------{Style.RESET_ALL}"""
    print(banner)


def run_pipeline(
    force: bool = False,
    auto_open: bool = True,
    dry_run: bool = False,
    track: str = "all",
) -> int:
    """
    Executes the full end-to-end intelligence collection pipeline:
    1. Initialize Database
    2. Fetch RSS Feeds
    3. Filter Duplicates & Compute Relevance Scores
    4. Generate Executive Brief (Top 5 highlights per sector)
    5. Dispatch Notifier (Telegram alert + Modern Dark HTML Dashboard)
    """
    start_time = time.time()
    print_banner()

    # Step 1: Initialize Database
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}[1/5] Initializing Database & Deduplication Engine...{Style.RESET_ALL}")
    db = NewsDatabase()
    stats = db.get_statistics()
    print(
        f"      SQLite DB Active: {config.DATABASE_PATH} "
        f"({stats['total_stored_articles']} existing records archived, {stats['total_watchdog_runs']} past runs)"
    )

    # Step 2: Fetch RSS Feeds
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}[2/5] Fetching Live Feeds from Monitored Sources...{Style.RESET_ALL}")
    sources_to_fetch = config.ALL_FEEDS
    if track == "tech":
        sources_to_fetch = config.TECH_AI_FEEDS
    elif track == "sports":
        sources_to_fetch = config.SPORTS_FEEDS

    print(f"      Scanning {len(sources_to_fetch)} live sources...")
    fetcher = RSSFetcher()
    raw_items: List[RawNewsItem] = fetcher.fetch_all(sources_to_fetch)
    print(f"{Fore.GREEN}      ✓ Scraped {len(raw_items)} total entries across all endpoints.{Style.RESET_ALL}")

    if not raw_items:
        print(f"{Fore.RED}      [!] No items could be retrieved. Please check network connectivity.{Style.RESET_ALL}")
        db.record_run(0, 0, 0, status="EMPTY_OR_FAILED")
        return 1

    # Step 3: Deduplication & Relevance Scoring
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}[3/5] Deduplicating & Computing Relevance Scores...{Style.RESET_ALL}")
    processor = NewsProcessor(db=db)
    processed_items = processor.process_raw_items(raw_items, force_process_all=force)

    print(
        f"{Fore.GREEN}      ✓ Filtered down to {len(processed_items)} actionable news items "
        f"({len(raw_items) - len(processed_items)} duplicates/previously logged skipped).{Style.RESET_ALL}"
    )

    if not processed_items:
        print(f"{Fore.CYAN}      [i] All scraped items were already processed in earlier runs.{Style.RESET_ALL}")
        if not force:
            print("      💡 Tip: Run with --force to generate a report including previously seen items.")
            db.record_run(len(raw_items), 0, 0, status="NO_NEW_ITEMS")
            return 0
        else:
            print("      Re-processing batch due to --force flag...")
            processed_items = processor.process_raw_items(raw_items, force_process_all=True)

    # Step 4: Generate Executive Brief (Top 5 per sector)
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}[4/5] Synthesizing Executive Intelligence Brief (Top Highlights)...{Style.RESET_ALL}")
    brief = processor.build_executive_brief(
        processed_items=processed_items,
        total_scanned=len(raw_items),
        top_n=config.TOP_N_ITEMS_PER_CATEGORY,
    )

    # Print Terminal Highlights Summary
    print(f"\n{Fore.CYAN}{Style.BRIGHT}--- 🤖 أهم أخبار التقنية والذكاء الاصطناعي (Tech & AI) ---{Style.RESET_ALL}")
    for idx, item in enumerate(brief.tech_ai_highlights, 1):
        tags_str = f"[{', '.join(item.tags_ar or item.tags)}]" if (item.tags_ar or item.tags) else ""
        title_disp = item.title_ar or item.title
        takeaway_disp = item.key_takeaway_ar or item.key_takeaway
        print(f"  {Fore.GREEN}{idx}. {title_disp}{Style.RESET_ALL}")
        print(f"     التقييم: {item.score}/100 | {tags_str} | المصدر: {item.source}")
        print(f"     💡 {takeaway_disp[:120]}...")

    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}--- ⚽ أهم أخبار نادي برشلونة والكرة الأوروبية (Sports & Football) ---{Style.RESET_ALL}")
    for idx, item in enumerate(brief.sports_highlights, 1):
        tags_str = f"[{', '.join(item.tags_ar or item.tags)}]" if (item.tags_ar or item.tags) else ""
        title_disp = item.title_ar or item.title
        takeaway_disp = item.key_takeaway_ar or item.key_takeaway
        print(f"  {Fore.YELLOW}{idx}. {title_disp}{Style.RESET_ALL}")
        print(f"     التقييم: {item.score}/100 | {tags_str} | المصدر: {item.source}")
        print(f"     ⚽ {takeaway_disp[:120]}...")

    # Step 5: Save to DB & Dispatch Notifiers
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}[5/5] Dispatching Notifier & Generating Dark Dashboard...{Style.RESET_ALL}")

    if not dry_run:
        # Save processed items to DB
        saved_count = 0
        for item in processed_items:
            saved = db.save_item(
                guid_hash=item.guid_hash,
                title=item.title,
                link=item.link,
                category=item.category,
                sub_category=item.sub_category,
                source=item.source,
                score=item.score,
                tags=",".join(item.tags),
                published_at=item.published_at,
            )
            if saved:
                saved_count += 1

        top_total = len(brief.tech_ai_highlights) + len(brief.sports_highlights)
        db.record_run(
            total_fetched=len(raw_items),
            new_articles=saved_count,
            top_picked=top_total,
            status="SUCCESS",
        )
        print(f"      Archived {saved_count} new records in SQLite database.")
    else:
        print("      [Dry Run] Skipped writing to SQLite database.")

    # Generate HTML Dashboard & Dispatch Alerts
    notifier = ReportNotifier()
    dashboard_path = notifier.generate_html_dashboard(brief, auto_open=auto_open)
    notifier.send_telegram_alert(brief, dashboard_path=dashboard_path)

    elapsed = round(time.time() - start_time, 2)
    print(f"\n{Fore.GREEN}{Style.BRIGHT}========================================================================")
    print(f"   ✓ PIPELINE COMPLETE in {elapsed}s | Dashboard: {dashboard_path}")
    print(f"========================================================================{Style.RESET_ALL}\n")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AI & Sports Autonomous Watchdog - وكيل الرصد والذكاء الإخباري الشامل"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force full processing and report generation including previously archived items.",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not automatically launch the web browser after generating dashboard.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without modifying SQLite database.",
    )
    parser.add_argument(
        "--track",
        choices=["all", "tech", "sports"],
        default="all",
        help="Monitored sector track to execute (default: all).",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Display watchdog database metrics and exit.",
    )

    args = parser.parse_args()

    if args.stats:
        db = NewsDatabase()
        stats = db.get_statistics()
        print(f"\n{Fore.CYAN}{Style.BRIGHT}=== Watchdog Intelligence Statistics ==={Style.RESET_ALL}")
        for k, v in stats.items():
            print(f"  {k}: {v}")
        sys.exit(0)

    exit_code = run_pipeline(
        force=args.force,
        auto_open=not args.no_browser,
        dry_run=args.dry_run,
        track=args.track,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
