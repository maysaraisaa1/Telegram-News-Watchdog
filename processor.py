"""
processor.py - News Filtering, Deduplication, Relevance Scoring & Arabic Translation
وكيل الرصد والذكاء الإخباري الشامل (AI & Sports Autonomous Watchdog)
"""

from dataclasses import dataclass, field
import hashlib
import re
import time
from typing import Dict, List, Optional, Set, Tuple
from deep_translator import MyMemoryTranslator, GoogleTranslator
import config
from database import NewsDatabase
from fetcher import RawNewsItem


class ArabicTranslatorService:
    """Provides resilient multi-provider translation service with validation and caching."""

    TAGS_MAP = {
        "FC Barcelona": "برشلونة",
        "Barcelona": "برشلونة",
        "Barca": "برشلونة",
        "Hansi Flick": "هانسي فليك",
        "Flick": "هانسي فليك",
        "Lamine Yamal": "لامين يامال",
        "Yamal": "لامين يامال",
        "Lewandowski": "ليفاندوفسكي",
        "Pedri": "بيدري",
        "Gavi": "جافي",
        "Raphinha": "رافينيا",
        "Cubarsi": "كوبارسي",
        "Transfer": "سوق الانتقالات",
        "Transfers": "سوق الانتقالات",
        "Signing": "تعاقد رسمي",
        "Official": "رسمي",
        "Breaking": "عاجل",
        "Gemini": "جيميني",
        "Chatgpt": "شات جي بي تي",
        "ChatGPT": "شات جي بي تي",
        "Claude": "كلود",
        "Openai": "أوبن إيه آي",
        "OpenAI": "أوبن إيه آي",
        "Deepmind": "ديب مايند",
        "Mistral": "ميسترال",
        "Google": "جوجل",
        "Apple": "آبل",
        "Samsung": "سامسونج",
        "Microsoft": "مايكروسوفت",
        "Meta": "ميتا",
        "Nvidia": "إنفيديا",
        "Llm": "نماذج الذكاء الاصطناعي (LLM)",
        "Champions League": "دوري أبطال أوروبا",
        "Ucl": "دوري الأبطال",
        "UCL": "دوري الأبطال",
        "La Liga": "الدوري الإسباني",
        "Premier League": "الدوري الإنجليزي",
        "Serie A": "الدوري الإيطالي",
        "Update": "تحديث جديد",
        "Announces": "إعلان رسمي",
        "Tech/AI": "التقنية والذكاء الاصطناعي",
        "Football": "كرة القدم الأوروبية",
    }

    def __init__(self) -> None:
        self.mymemory = MyMemoryTranslator(source="en-US", target="ar-SA")
        self.google = GoogleTranslator(source="auto", target="ar")
        self.cache: Dict[str, str] = {}

    @staticmethod
    def is_valid_translation(text: Optional[str]) -> bool:
        """Ensures translation does not contain HTTP error responses or warnings."""
        if not text or not text.strip():
            return False
        lower = text.lower()
        bad_indicators = (
            "error 500",
            "server error",
            "that’s an error",
            "that's an error",
            "please try again later",
            "mymemory warning",
            "quota exceeded",
            "<!doctype",
            "<html",
        )
        return not any(bad in lower for bad in bad_indicators)

    def translate(self, text: str) -> str:
        """Translates text to Arabic with caching, multi-provider fallback, and sanitation."""
        if not text or not text.strip():
            return ""
        clean_text = text.strip()
        if clean_text in self.cache:
            return self.cache[clean_text]

        # Clean headline artifacts before translating
        to_trans = clean_text
        to_trans = re.sub(r"\s*-\s*[A-Za-z0-9\.\s]+$", "", to_trans)

        # 1. Primary: MyMemory Translator (Stable and free)
        try:
            res = self.mymemory.translate(to_trans)
            if self.is_valid_translation(res):
                self.cache[clean_text] = res
                return res
        except Exception:
            pass

        # 2. Secondary: Google Translator
        try:
            res = self.google.translate(to_trans)
            if self.is_valid_translation(res):
                self.cache[clean_text] = res
                return res
        except Exception:
            pass

        # 3. Clean fallback: Return original cleaned text if both fail
        return to_trans

    def translate_tags(self, tags: List[str]) -> List[str]:
        """Maps tags to standard Arabic equivalents without unnecessary API calls."""
        ar_tags = []
        for t in tags:
            clean_t = t.strip()
            if clean_t in self.TAGS_MAP:
                ar_tags.append(self.TAGS_MAP[clean_t])
            else:
                # Direct check case-insensitively
                found = False
                for k, v in self.TAGS_MAP.items():
                    if k.lower() == clean_t.lower():
                        ar_tags.append(v)
                        found = True
                        break
                if not found:
                    trans = self.translate(clean_t)
                    ar_tags.append(trans if self.is_valid_translation(trans) else clean_t)
        return ar_tags


@dataclass
class ProcessedNewsItem:
    """Represents a scored, tagged, translated, and deduplicated news item ready for reporting."""
    guid_hash: str
    title: str
    link: str
    summary: str
    source: str
    category: str
    sub_category: str
    score: float
    tags: List[str]
    published_at: str
    key_takeaway: str
    title_ar: str = ""
    key_takeaway_ar: str = ""
    tags_ar: List[str] = field(default_factory=list)


@dataclass
class ExecutiveBrief:
    """Aggregated executive intelligence summary across monitored sectors."""
    timestamp: str
    tech_ai_highlights: List[ProcessedNewsItem]
    sports_highlights: List[ProcessedNewsItem]
    tech_ai_summary_text: str
    sports_summary_text: str
    tech_ai_summary_ar: str
    sports_summary_ar: str
    total_scanned: int
    new_found: int


class NewsProcessor:
    """Handles news deduplication, relevance scoring, translation, and executive briefing synthesis."""

    def __init__(self, db: Optional[NewsDatabase] = None) -> None:
        self.db = db or NewsDatabase()
        self.translator = ArabicTranslatorService()

    @staticmethod
    def generate_guid(link: str, title: str) -> str:
        """Generates a unique, deterministic SHA-256 hash from normalized URL and title."""
        normalized_str = f"{link.strip().lower()}|{title.strip().lower()}"
        return hashlib.sha256(normalized_str.encode("utf-8")).hexdigest()

    @staticmethod
    def normalize_title(title: str) -> str:
        """Simplifies a title for fuzzy duplicate detection across different media outlets."""
        simplified = re.sub(r"[^a-zA-Z0-9\u0600-\u06FF\s]", " ", title.lower())
        return " ".join(simplified.split())

    def calculate_relevance(
        self,
        title: str,
        summary: str,
        category: str,
        sub_category: str,
        feed_weight: float = 1.0,
    ) -> Tuple[float, List[str]]:
        """
        Calculates a relevance score (0.0 to 100.0) based on targeted keywords,
        weights, and sector priorities. Also extracts meaningful category badges.
        """
        score = 15.0 * feed_weight  # Base score from reputable feed
        tags: Set[str] = set()

        text_title = title.lower()
        text_full = f"{title} {summary}".lower()

        keywords_map = config.KEYWORDS.get(category, {})

        if category == "tech_ai":
            # 1. AI Models and Labs (Highest priority)
            for kw in keywords_map.get("llm", []):
                if re.search(r"\b" + re.escape(kw) + r"\b", text_title):
                    score += 18.0
                    tags.add(kw.title())
                elif re.search(r"\b" + re.escape(kw) + r"\b", text_full):
                    score += 6.0
                    if len(tags) < 3:
                        tags.add(kw.title())

            # 2. Tech Giants
            for kw in keywords_map.get("giants", []):
                if re.search(r"\b" + re.escape(kw) + r"\b", text_title):
                    score += 12.0
                    tags.add(kw.title())
                elif re.search(r"\b" + re.escape(kw) + r"\b", text_full):
                    score += 4.0

            # 3. Developer Tools & Frameworks
            for kw in keywords_map.get("dev_tools", []):
                if re.search(r"\b" + re.escape(kw) + r"\b", text_title):
                    score += 10.0
                    tags.add(kw.title())
                elif re.search(r"\b" + re.escape(kw) + r"\b", text_full):
                    score += 3.0

        elif category == "sports":
            # 1. FC Barcelona (Top priority)
            for kw in keywords_map.get("barca", []):
                if re.search(r"\b" + re.escape(kw) + r"\b", text_title):
                    score += 25.0
                    tags.add("FC Barcelona")
                    if kw in ["yamal", "lamine yamal", "flick", "hansi flick", "lewandowski", "pedri", "gavi", "raphinha"]:
                        tags.add(kw.title())
                elif re.search(r"\b" + re.escape(kw) + r"\b", text_full):
                    score += 8.0
                    tags.add("FC Barcelona")

            # 2. European Football & Top Competitions
            for kw in keywords_map.get("euro_football", []):
                if re.search(r"\b" + re.escape(kw) + r"\b", text_title):
                    score += 10.0
                    tags.add(kw.upper() if len(kw) <= 4 else kw.title())
                elif re.search(r"\b" + re.escape(kw) + r"\b", text_full):
                    score += 3.5

        # 4. Impact event bonus (Transfers, releases, benchmarks, breaks)
        for kw in keywords_map.get("impact_bonus", []):
            if re.search(r"\b" + re.escape(kw) + r"\b", text_title):
                score += 14.0
                tags.add(kw.title())
            elif re.search(r"\b" + re.escape(kw) + r"\b", text_full):
                score += 4.0

        # Cap score at 100.0 and round to 1 decimal place
        final_score = min(100.0, round(score, 1))

        # Default fallback tag if none found
        if not tags:
            default_tag = "Tech/AI" if category == "tech_ai" else "Football"
            tags.add(default_tag)

        # Limit tags to max 3 relevant badges
        sorted_tags = sorted(list(tags), key=lambda x: (x != "FC Barcelona", -len(x)))[:3]

        return final_score, sorted_tags

    @staticmethod
    def extract_key_takeaway(title: str, summary: str) -> str:
        """Generates a crisp, one-sentence executive takeaway for the headline."""
        if summary and len(summary) > 25:
            first_sentence = summary.split(". ")[0].strip()
            if len(first_sentence) > 160:
                first_sentence = first_sentence[:157] + "..."
            return first_sentence
        return title

    def process_raw_items(
        self, raw_items: List[RawNewsItem], force_process_all: bool = False
    ) -> List[ProcessedNewsItem]:
        """
        Deduplicates raw items against SQLite and in-memory batch,
        scores relevance, and creates ProcessedNewsItem records.
        """
        processed: List[ProcessedNewsItem] = []
        seen_batch_guids: Set[str] = set()
        seen_normalized_titles: Set[str] = set()

        for item in raw_items:
            guid = self.generate_guid(item.link, item.title)
            norm_title = self.normalize_title(item.title)

            # In-memory deduplication for identical or near-identical items across RSS feeds
            if guid in seen_batch_guids or norm_title in seen_normalized_titles:
                continue

            # Database deduplication check (unless --force is passed)
            if not force_process_all and self.db.is_duplicate(guid):
                continue

            seen_batch_guids.add(guid)
            seen_normalized_titles.add(norm_title)

            score, tags = self.calculate_relevance(
                title=item.title,
                summary=item.summary,
                category=item.category,
                sub_category=item.sub_category,
                feed_weight=item.feed_weight,
            )

            takeaway = self.extract_key_takeaway(item.title, item.summary)

            processed.append(
                ProcessedNewsItem(
                    guid_hash=guid,
                    title=item.title,
                    link=item.link,
                    summary=item.summary,
                    source=item.source_name,
                    category=item.category,
                    sub_category=item.sub_category,
                    score=score,
                    tags=tags,
                    published_at=item.published_at,
                    key_takeaway=takeaway,
                )
            )

        return processed

    def build_executive_brief(
        self,
        processed_items: List[ProcessedNewsItem],
        total_scanned: int,
        top_n: int = config.TOP_N_ITEMS_PER_CATEGORY,
    ) -> ExecutiveBrief:
        """
        Ranks processed news, translates the top highlights into fluent Arabic,
        and synthesizes the executive brief.
        """
        # Separate by track and sort by score descending
        tech_items = sorted(
            [item for item in processed_items if item.category == "tech_ai"],
            key=lambda x: x.score,
            reverse=True,
        )[:top_n]

        sports_items = sorted(
            [item for item in processed_items if item.category == "sports"],
            key=lambda x: x.score,
            reverse=True,
        )[:top_n]

        print("      [+] Translating top highlights to Arabic via deep-translator...")

        # Translate Tech & AI Highlights
        for item in tech_items:
            item.title_ar = self.translator.translate(item.title)
            item.key_takeaway_ar = self.translator.translate(item.key_takeaway)
            item.tags_ar = self.translator.translate_tags(item.tags)
            time.sleep(0.3)

        # Translate Sports Highlights
        for item in sports_items:
            item.title_ar = self.translator.translate(item.title)
            item.key_takeaway_ar = self.translator.translate(item.key_takeaway)
            item.tags_ar = self.translator.translate_tags(item.tags)
            time.sleep(0.3)

        # Synthesize Arabic and English executive summaries
        if tech_items:
            tech_summary_en = (
                f"Scanned {len(tech_items)} prioritized breakthroughs in AI and Big Tech. "
                f"Top headline: '{tech_items[0].title}' (Score: {tech_items[0].score}/100)."
            )
            tech_summary_ar = (
                f"تم رصد {len(tech_items)} من أهم التطورات المتسارعة في قطاع الذكاء الاصطناعي والشركات الكبرى. "
                f"الخبر الأبرز: '{tech_items[0].title_ar}' (التقييم: {tech_items[0].score}/100)."
            )
        else:
            tech_summary_en = "No new significant Tech/AI updates discovered in this cycle."
            tech_summary_ar = "لم يتم رصد تحديثات تقنية جوهرية جديدة خلال دورة الفحص الحالية."

        if sports_items:
            barca_count = sum(1 for item in sports_items if "FC Barcelona" in item.tags or "barca" in item.sub_category)
            sports_summary_en = (
                f"Monitored European football with special emphasis on FC Barcelona ({barca_count} key updates). "
                f"Top headline: '{sports_items[0].title}' (Score: {sports_items[0].score}/100)."
            )
            sports_summary_ar = (
                f"متابعة دقيقة ومكثفة لكرة القدم الأوروبية مع التركيز على نادي برشلونة ({barca_count} أحداث رئيسية). "
                f"الخبر الأبرز: '{sports_items[0].title_ar}' (التقييم: {sports_items[0].score}/100)."
            )
        else:
            sports_summary_en = "No new major football developments discovered in this cycle."
            sports_summary_ar = "لم يتم رصد أي تطورات رياضية كبرى جديدة خلال هذه الدورة."

        from datetime import datetime, timezone
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        return ExecutiveBrief(
            timestamp=now_str,
            tech_ai_highlights=tech_items,
            sports_highlights=sports_items,
            tech_ai_summary_text=tech_summary_en,
            sports_summary_text=sports_summary_en,
            tech_ai_summary_ar=tech_summary_ar,
            sports_summary_ar=sports_summary_ar,
            total_scanned=total_scanned,
            new_found=len(processed_items),
        )
