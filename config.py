"""
config.py - Central Configuration Module
وكيل الرصد والذكاء الإخباري الشامل (AI & Sports Autonomous Watchdog)
"""

from dataclasses import dataclass, field
from pathlib import Path
import os
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables from .env file if available
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()


@dataclass(frozen=True)
class RSSFeedSource:
    name: str
    url: str
    category: str  # "tech_ai" or "sports"
    sub_category: str  # e.g., "llm", "giants", "dev_tools", "barca", "euro_football"
    weight: float = 1.0


# 1. Tech & Artificial Intelligence Feeds
TECH_AI_FEEDS: List[RSSFeedSource] = [
    RSSFeedSource(
        name="Google News - AI & LLMs (Gemini, ChatGPT, Claude)",
        url="https://news.google.com/rss/search?q=Artificial+Intelligence+OR+Gemini+OR+ChatGPT+OR+Claude+OR+LLM&hl=en-US&gl=US&ceid=US:en",
        category="tech_ai",
        sub_category="llm",
        weight=1.2,
    ),
    RSSFeedSource(
        name="Google News - Tech Giants (Google, Apple, Samsung)",
        url="https://news.google.com/rss/search?q=Apple+OR+Google+OR+Samsung+technology&hl=en-US&gl=US&ceid=US:en",
        category="tech_ai",
        sub_category="giants",
        weight=1.1,
    ),
    RSSFeedSource(
        name="TechCrunch AI",
        url="https://techcrunch.com/category/artificial-intelligence/feed/",
        category="tech_ai",
        sub_category="llm",
        weight=1.15,
    ),
    RSSFeedSource(
        name="The Verge - Tech",
        url="https://www.theverge.com/rss/index.xml",
        category="tech_ai",
        sub_category="giants",
        weight=1.0,
    ),
    RSSFeedSource(
        name="Ars Technica - Technology Lab",
        url="https://feeds.arstechnica.com/arstechnica/technology-lab",
        category="tech_ai",
        sub_category="llm",
        weight=1.05,
    ),
    RSSFeedSource(
        name="Dev.to - Developer Ecosystem",
        url="https://dev.to/feed",
        category="tech_ai",
        sub_category="dev_tools",
        weight=1.0,
    ),
]

# 2. Sports & European Football Feeds (Focus on FC Barcelona & Top Competitions)
SPORTS_FEEDS: List[RSSFeedSource] = [
    RSSFeedSource(
        name="Google News - FC Barcelona (Exclusive & Transfers)",
        url="https://news.google.com/rss/search?q=FC+Barcelona+OR+Barca+news+transfers&hl=en-US&gl=US&ceid=US:en",
        category="sports",
        sub_category="barca",
        weight=1.3,
    ),
    RSSFeedSource(
        name="Google News - UEFA Champions League & Top Leagues",
        url="https://news.google.com/rss/search?q=Champions+League+OR+La+Liga+OR+Premier+League+OR+Serie+A&hl=en-US&gl=US&ceid=US:en",
        category="sports",
        sub_category="euro_football",
        weight=1.1,
    ),
    RSSFeedSource(
        name="BBC Sport - Football",
        url="https://feeds.bbci.co.uk/sport/football/rss.xml",
        category="sports",
        sub_category="euro_football",
        weight=1.15,
    ),
    RSSFeedSource(
        name="Sky Sports - Football News",
        url="https://www.skysports.com/rss/12040",
        category="sports",
        sub_category="euro_football",
        weight=1.05,
    ),
]

# Combined Master Feeds List
ALL_FEEDS: List[RSSFeedSource] = TECH_AI_FEEDS + SPORTS_FEEDS

# Keywords dictionary for Relevance Scoring & Tagging
KEYWORDS: Dict[str, Dict[str, List[str]]] = {
    "tech_ai": {
        "giants": [
            "google", "apple", "samsung", "microsoft", "meta", "nvidia", "amazon", "qualcomm", "intel", "amd"
        ],
        "llm": [
            "gemini", "chatgpt", "claude", "openai", "anthropic", "deepmind", "llm", "large language model",
            "llama", "mistral", "qwen", "reasoning model", "gpt-4o", "gpt-5", "sora", "multimodal", "generative ai",
            "artificial intelligence", "deep learning", "neural network", "transformer", "diffusion"
        ],
        "dev_tools": [
            "python", "framework", "library", "sdk", "api", "github", "open-source", "open source", "developer",
            "coding", "docker", "kubernetes", "rust", "typescript", "agentic", "agent", "autonomous", "tools"
        ],
        "impact_bonus": [
            "breakthrough", "launch", "release", "benchmark", "announces", "unveils", "state of the art",
            "revolution", "vulnerability", "zero-day", "milestone", "official", "update"
        ],
    },
    "sports": {
        "barca": [
            "barcelona", "barça", "fc barcelona", "hansi flick", "flick", "yamal", "lamine yamal",
            "lewandowski", "pedri", "gavi", "raphinha", "cubarsi", "camp nou", "montjuic", "laporta",
            "deco", "la masia", "blaugrana", "culers", "el clasico"
        ],
        "euro_football": [
            "champions league", "ucl", "la liga", "premier league", "serie a", "bundesliga", "real madrid",
            "manchester city", "arsenal", "liverpool", "bayern", "paris saint-germain", "psg", "inter milan",
            "juventus", "ac milan", "atletico madrid", "uefa"
        ],
        "impact_bonus": [
            "breaking", "official", "confirmed", "transfer", "here we go", "deal agreed", "contract",
            "signing", "injury", "surgery", "hat-trick", "red card", "final", "semifinal", "champion",
            "derby", "comeback", "stoppage time", "draw"
        ],
    },
}

# General Application Settings
DATABASE_PATH: Path = BASE_DIR / os.getenv("DATABASE_PATH", "data/watchdog.db")
REPORTS_DIR: Path = BASE_DIR / os.getenv("REPORTS_DIR", "reports")

# Telegram Bot Notifications
TELEGRAM_BOT_TOKEN: str = (
    os.getenv("TELEGRAM_BOT_TOKEN", "8915515328:AAElgeh3FxP3YhtH_ihlg5P3H3NOu54_UVo")
    .strip()
    .strip('"')
    .strip("'")
)
TELEGRAM_CHAT_ID: str = (
    os.getenv("TELEGRAM_CHAT_ID", "1777660042")
    .strip()
    .strip('"')
    .strip("'")
)

# Network & Fetching Settings
REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "12"))
MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
USER_AGENT: str = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 AI-Watchdog/1.0",
)

# Processing & Scoring Settings
TOP_N_ITEMS_PER_CATEGORY: int = int(os.getenv("TOP_N_ITEMS_PER_CATEGORY", "5"))
MIN_RELEVANCE_SCORE: float = float(os.getenv("MIN_RELEVANCE_SCORE", "15.0"))
AUTO_OPEN_BROWSER: bool = os.getenv("AUTO_OPEN_BROWSER", "true").lower() in ("true", "1", "yes")

# Ensure required directories exist
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
