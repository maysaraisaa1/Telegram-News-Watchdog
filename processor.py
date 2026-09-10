"""
processor.py - News Filtering, Deduplication, Relevance Scoring & Advanced Arabic Intelligence
وكيل الرصد والذكاء الإخباري الشامل (AI & Sports Autonomous Watchdog)
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import re
import time
from typing import Dict, List, Optional, Set, Tuple
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator, MyMemoryTranslator
import requests
import config
from database import NewsDatabase
from fetcher import RawNewsItem


class ArabicTranslatorService:
    """
    Advanced multi-provider Arabic translation service with entity preservation,
    journalistic terminology normalization, caching, and resilient failover.
    """

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
        "Llm": "النماذج اللغوية (LLM)",
        "Champions League": "دوري أبطال أوروبا",
        "Ucl": "دوري الأبطال",
        "UCL": "دوري الأبطال",
        "La Liga": "الدوري الإسباني",
        "Premier League": "الدوري الإنجليزي الممتاز",
        "Serie A": "الدوري الإيطالي",
        "Update": "تحديث جديد",
        "Announces": "إعلان رسمي",
        "Tech/AI": "التقنية والذكاء الاصطناعي",
        "Football": "كرة القدم الأوروبية",
    }

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "ar,en;q=0.9",
        })
        self.mymemory = MyMemoryTranslator(source="en-US", target="ar-SA")
        self.google_fallback = GoogleTranslator(source="auto", target="ar")
        self.cache: Dict[str, str] = {}

    @staticmethod
    def is_valid_translation(text: Optional[str]) -> bool:
        """Ensures translation does not contain HTTP error responses or server warnings."""
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

    def _translate_google_direct(self, text: str) -> Optional[str]:
        """Translates via direct Google web endpoint using browser-mimicking headers."""
        try:
            url = "https://translate.google.com/m"
            params = {"tl": "ar", "sl": "auto", "q": text}
            resp = self.session.get(url, params=params, timeout=8)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                container = soup.find("div", class_="result-container")
                if container:
                    res_text = container.get_text().strip()
                    if self.is_valid_translation(res_text):
                        return res_text
        except Exception:
            pass
        return None

    def _translate_mymemory(self, text: str) -> Optional[str]:
        """Translates via MyMemory free API."""
        try:
            res = self.mymemory.translate(text)
            if self.is_valid_translation(res):
                return res.strip()
        except Exception:
            pass
        return None

    def polish_arabic_text(self, text: str) -> str:
        """
        Refines translated Arabic text to sound journalistic, authoritative,
        and accurate, replacing literal transliterations with correct Arabic names and idioms.
        """
        if not text:
            return ""

        t = text.strip()

        # 1. Clean English media outlet signatures and brackets
        t = re.sub(r"(?i)\s*-\s*(BBC Sport|The Verge|TechCrunch|Barca Universal|Barca Blaugranes|Sky Sports|FC Barcelona|Football Espana|Marca|AS\.com|Dev\.to|Ars Technica).*$", "", t)
        t = re.sub(r"(?i)\s*\|\s*(FC Barcelona|Sky Sports|BBC).*$", "", t)
        t = re.sub(r"\[\s*LIVE\s*\]|\[\s*OFFICIAL\s*\]", "", t, flags=re.IGNORECASE)

        # 2. Fix literal English connectors like 'and' transliterated to 'آند'
        t = re.sub(r"\bآند\b", "و", t)
        t = re.sub(r"\s*&\s*", " و ", t)

        # 3. Football & Barcelona Named Entities & Terms
        replacements = [
            (r"\bهانزي فليك\b", "هانسي فليك"),
            (r"\bفليك\b", "هانسي فليك"),
            (r"\bالأمين يامال\b|\bلامين جمال\b", "لامين يامال"),
            (r"\bأراوجو\b", "أراوخو"),
            (r"\bدي يونج\b", "دي يونغ"),
            (r"\bديكو\b", "ديكو"),
            (r"\bباو كوبارسي\b|\bكوبارسي\b", "باو كوبارسي"),
            (r"\bمارك كاسادو\b|\bكاسادو\b", "مارك كاسادو"),
            (r"\bروبرت ليفاندوفسكي\b|\bليفاندوفسكي\b", "روبرت ليفاندوفسكي"),
            (r"\bداني أولمو\b|\bأولمو\b", "داني أولمو"),
            (r"\bفيران توريس\b|\bفيران\b", "فيران توريس"),
            (r"\bخوان لابورتا\b|\bلابورتا\b", "خوان لابورتا"),
            (r"\bمارك أندريه تير شتيغن\b|\bتير شتيغن\b|\bتير شتيجن\b", "تير شتيغن"),
            (r"\bأليخاندرو بالدي\b|\bبالدي\b", "أليخاندرو بالدي"),
            (r"\bماركوس راشفورد\b|\bراشفورد\b", "ماركوس راشفورد"),
            (r"\bجوليان ألفاريز\b|\bألفاريز\b", "جوليان ألفاريز"),
            (r"\bإرلينغ هالاند\b|\bهالاند\b", "إرلينغ هالاند"),
            (r"\bكيليان مبابي\b|\bمبابي\b", "كيليان مبابي"),
            (r"\bرودري\b", "رودري"),
            (r"\bفينورد\b|\bفاينورد\b", "فينورد"),
            (r"\bدوري أبطال أوروبا\b|\bدوري الأبطال\b", "دوري أبطال أوروبا"),
            (r"\bالدوري الإسباني\b", "الدوري الإسباني"),
            (r"\bالدوري الإنجليزي الممتاز\b|\bالدوري الإنجليزي\b", "الدوري الإنجليزي الممتاز"),
            # Sports Idioms
            (r"اللاعب رقم 9|صيد الرقم 9|البحث عن رقم 9", "مهاجم صريح (رقم 9)"),
            (r"ناقلات الصيف|نافذة الانتقالات", "سوق الانتقالات"),
            (r"هنا نذهب", "حسم الصفقة (Here We Go)"),
            # Tech & AI Entities & Terms
            (r"\bOpenAI\b|\bOpenai\b|أوبن أيه آي|أوبن اي اي", "أوبن إيه آي (OpenAI)"),
            (r"\bChatGPT\b|\bChatgpt\b|شات جي بي تي", "شات جي بي تي (ChatGPT)"),
            (r"\bGemini\b|جيميني", "جيميني (Gemini)"),
            (r"\bClaude\b|كلود", "كلود (Claude)"),
            (r"\bAnthropic\b|أنثروبيك", "أنثروبيك (Anthropic)"),
            (r"\bDeepMind\b|\bDeepmind\b|ديب مايند", "ديب مايند (DeepMind)"),
            (r"\bMistral AI\b|\bMistral\b|ميسترال", "ميسترال للذكاء الاصطناعي"),
            (r"\bMeta\b", "ميتا"),
            (r"\bNvidia\b|إنفيديا", "إنفيديا (Nvidia)"),
            (r"\bGitHub Copilot\b", "جيت هاب كوبايلوت"),
            (r"وكيل برمجة|وكيل ترميز|وكيل التكويد", "وكيل برمجة ذكي (Coding Agent)"),
            (r"وكلاء برمجة|وكلاء ترميز", "وكلاء البرمجة الذكية (Coding Agents)"),
            (r"النماذج اللغوية الكبيرة|نماذج لغوية كبيرة|\bLLMs\b|\bLLM\b", "النماذج اللغوية (LLM)"),
            (r"ما تم شحنه|ما شحنته", "ما أطلقته رسمياً"),
        ]

        for pattern, repl in replacements:
            t = re.sub(pattern, repl, t, flags=re.IGNORECASE)

        # 4. Clean spacing & punctuation
        t = re.sub(r"\s{2,}", " ", t)
        t = t.strip(" -:؛|")
        return t

    def translate(self, text: str) -> str:
        """Translates text to Arabic using primary and fallback engines, then polishes."""
        if not text or not text.strip():
            return ""
        clean_text = text.strip()
        if clean_text in self.cache:
            return self.cache[clean_text]

        # Clean headline artifacts before translating
        to_trans = clean_text
        to_trans = re.sub(r"\s*-\s*[A-Za-z0-9\.\s]+$", "", to_trans)

        result_ar = None

        # 1. Primary: Direct Google browser translation
        result_ar = self._translate_google_direct(to_trans)

        # 2. Secondary: MyMemory free API
        if not result_ar:
            result_ar = self._translate_mymemory(to_trans)

        # 3. Tertiary: deep-translator GoogleTranslator fallback
        if not result_ar:
            try:
                cand = self.google_fallback.translate(to_trans)
                if self.is_valid_translation(cand):
                    result_ar = cand
            except Exception:
                pass

        # Final fallback: Return original cleaned text if all failed
        final_text = result_ar if result_ar else to_trans
        polished = self.polish_arabic_text(final_text)
        self.cache[clean_text] = polished
        return polished

    def translate_tags(self, tags: List[str]) -> List[str]:
        """Maps tags to standard Arabic equivalents without unnecessary API calls."""
        ar_tags = []
        for t in tags:
            clean_t = t.strip()
            if clean_t in self.TAGS_MAP:
                ar_tags.append(self.TAGS_MAP[clean_t])
            else:
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

    def generate_crisp_takeaway(self, item: ProcessedNewsItem) -> str:
        """
        Generates an executive, highly valuable 1-2 sentence Arabic takeaway ("الزبدة")
        from article details, avoiding repetitive title echoes.
        """
        raw_summary = (item.summary or "").strip()
        norm_title = self.normalize_title(item.title)
        norm_summary = self.normalize_title(raw_summary)

        # 1. Clean boilerplate from raw summary (e.g. WordPress, TechCrunch, Barca Universal)
        clean_summary = raw_summary
        clean_summary = re.sub(r"(?i)the post .* appeared first on .*", "", clean_summary)
        clean_summary = re.sub(r"(?i)photo (by|via) .*", "", clean_summary)
        clean_summary = re.sub(r"(?i)read more (at|on) .*", "", clean_summary)
        clean_summary = re.sub(r"\[\s*…\s*\]|\[\s*\.\.\.\s*\]", "", clean_summary)
        clean_summary = " ".join(clean_summary.split())

        # Check if the summary contains real, substantial content beyond the title
        has_real_content = (
            len(clean_summary) > 40
            and norm_summary != norm_title
            and not norm_summary.startswith(norm_title)
        )

        if has_real_content:
            sentences = [s.strip() for s in re.split(r"[.!?]\s+", clean_summary) if len(s.strip()) > 20]
            if sentences:
                candidate = sentences[0]
                if len(candidate) < 90 and len(sentences) > 1:
                    candidate = f"{candidate}. {sentences[1]}"
                if len(candidate) > 180:
                    candidate = candidate[:177].rsplit(" ", 1)[0] + "..."

                trans_ar = self.translator.translate(candidate)
                polished_ar = self.translator.polish_arabic_text(trans_ar)
                if self.translator.is_valid_translation(polished_ar) and len(polished_ar) > 20:
                    return polished_ar

        # 2. Contextual executive synthesis if summary was trivial/empty (e.g., Google News)
        title_lower = item.title.lower()
        if item.category == "sports":
            if any(k in title_lower for k in ["transfer", "signing", "sign", "deal", "target", "bid", "agree", "fee", "departure", "exit", "contract", "talks"]):
                return "تحركات حاسمة لإدارة برشلونة وهانسي فليك في سوق الانتقالات لحسم الصفقات وتدعيم المراكز الهجومية والدفاعية المطلوبة."
            if any(k in title_lower for k in ["injury", "medical", "surgery", "hamstring", "knee", "fitness", "return", "training", "rehab"]):
                return "متابعة تطورات الحالة البدنية والجاهزية الطبية للاعبي الفريق والبرنامج التأهيلي للعودة إلى حسابات المباريات القادمة."
            if any(k in title_lower for k in ["champions league", "ucl", "feyenoord", "match", "win", "defeat", "draw", "squad", "lineup", "tactics"]):
                return "استعدادات فنية وتكتيكية مكثفة وتحليل لخيارات التشكيل لمواصلة المنافسة بقوة وحسم المواجهات الأوروبية والمحلية."
            if any(k in title_lower for k in ["flick", "hansi flick", "press", "conference", "comments", "interview", "explains"]):
                return "رؤية فنية وخطة عمل واضحة يضعها المدرب هانسي فليك لتطوير مستوى الأداء الجماعي للفريق وفرض أسلوبه الهجومي."
            if any(k in title_lower for k in ["yamal", "lamine", "pedri", "gavi", "raphinha", "lewandowski", "cubarsi", "olmo"]):
                return "تسليط الضوء على الأداء الاستثنائي والتأثير التكتيكي الحاسم لنجوم الفريق في حسم المباريات وصناعة الفارق داخل الملعب."
            return "تغطية شاملة لأهم المستجدات وردود الأفعال داخل معقل النادي وتأثيرها المباشر على المرحلة القادمة."

        elif item.category == "tech_ai":
            if any(k in title_lower for k in ["gemini", "google", "deepmind"]):
                return "خطوات متسارعة من جوجل لترقية قدرات نماذج جيميني وتعزيز دمج الذكاء الاصطناعي التوليدي عبر خدماتها وأنظمتها السحابية."
            if any(k in title_lower for k in ["chatgpt", "openai", "sora", "reasoning", "o1", "gpt"]):
                return "إعلانات نوعية من أوبن إيه آي لتوسيع ريادتها في نماذج الاستدلال والتفكير العميق ومنافسة عمالقة التكنولوجيا عالمياً."
            if any(k in title_lower for k in ["claude", "anthropic"]):
                return "تحديثات تقنية من أنثروبيك لرفع كفاءة نماذج كلود في كتابة الأكواد والتحليلات المنطقية وحل المشكلات البرمجية المعقدة."
            if any(k in title_lower for k in ["meta", "llama", "open-source", "open source"]):
                return "استراتيجية استباقية من شركة ميتا لنشر النماذج المفتوحة وتمكين مجتمع المطورين بأحدث تقنيات وحزم الذكاء الاصطناعي."
            if any(k in title_lower for k in ["chip", "chips", "hardware", "nvidia", "samsung", "apple", "billion", "invest", "funding"]):
                return "استثمارات مليارية وشراكات كبرى لتصنيع رقاقات المعالجة العصبية المتطورة لدعم متطلبات الحوسبة الفائقة للذكاء الاصطناعي."
            if any(k in title_lower for k in ["agent", "agents", "coding", "developer", "tool", "copilot", "library", "framework"]):
                return "طفرة متقدمة في وكلاء البرمجة الذاتية لتسريع عجلة تطوير التطبيقات وأتمتة المهام الهندسية الشاقة للمطورين."
            return "رصد تحليلي متقدم لأحدث الابتكارات التقنية وانعكاساتها المباشرة على قطاع الذكاء الاصطناعي والمنظومة البرمجية."

        return "متابعة دقيقة لأهم تفاصيل الحدث وأبعاده الاستراتيجية وتأثيره الفعلي على هذا المسار."

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
                    key_takeaway="",
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
        Ranks processed news, translates the top highlights into fluent, authoritative Arabic,
        crafts the executive takeaways, and synthesizes the brief.
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

        print("      [+] Translating & synthesizing Arabic intelligence for top highlights...")

        # Process Tech & AI Highlights
        for item in tech_items:
            clean_title = re.sub(r"(?i)\s*-\s*(BBC Sport|The Verge|TechCrunch|Barca Universal|Barca Blaugranes|Sky Sports|FC Barcelona|Dev\.to|Ars Technica).*$", "", item.title).strip()
            item.title_ar = self.translator.translate(clean_title)
            item.key_takeaway_ar = self.generate_crisp_takeaway(item)
            item.key_takeaway = item.key_takeaway_ar
            item.tags_ar = self.translator.translate_tags(item.tags)
            time.sleep(0.2)

        # Process Sports Highlights
        for item in sports_items:
            clean_title = re.sub(r"(?i)\s*-\s*(BBC Sport|The Verge|TechCrunch|Barca Universal|Barca Blaugranes|Sky Sports|FC Barcelona|Football Espana|Marca|AS\.com).*$", "", item.title).strip()
            item.title_ar = self.translator.translate(clean_title)
            item.key_takeaway_ar = self.generate_crisp_takeaway(item)
            item.key_takeaway = item.key_takeaway_ar
            item.tags_ar = self.translator.translate_tags(item.tags)
            time.sleep(0.2)

        # Synthesize executive briefs
        if tech_items:
            tech_summary_en = (
                f"Scanned {len(tech_items)} prioritized breakthroughs in AI and Big Tech. "
                f"Top headline: '{tech_items[0].title}' (Score: {tech_items[0].score}/100)."
            )
            tech_summary_ar = (
                f"تم رصد {len(tech_items)} من أهم التطورات المتسارعة في قطاع الذكاء الاصطناعي والشركات الكبرى. "
                f"الخبر الأبرز: '{tech_items[0].title_ar}'."
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
                f"الخبر الأبرز: '{sports_items[0].title_ar}'."
            )
        else:
            sports_summary_en = "No new major football developments discovered in this cycle."
            sports_summary_ar = "لم يتم رصد أي تطورات رياضية كبرى جديدة خلال هذه الدورة."

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
