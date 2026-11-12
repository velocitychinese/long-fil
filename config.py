"""VELOCITY LONGFORM - 16:9 chapter lesson, brand and motion constants."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = BASE_DIR / "output"
LESSONS_DIR = OUTPUT_DIR / "lessons"
HISTORY_DIR = OUTPUT_DIR / "history"
SCENE_DIR = BASE_DIR / "scene"

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30

TARGET_CHAPTERS = 8
PHRASES_PER_CHAPTER = 7
TARGET_PHRASES = TARGET_CHAPTERS * PHRASES_PER_CHAPTER

# ---------------------------------------------------------------- brand

BRAND = "VELOCITY FILIPINO"
BRAND_LOCKUP_TOP = "VELOCITY"
BRAND_LOCKUP_BOTTOM = "FILIPINO"
HANDLE = "@velocityfilipino"
MASCOT_NAME = "Velo"

# ==== LANGUAGE PACK START ====
LANGUAGE = {'code': 'fil',
 'name': 'Filipino',
 'native_name': 'Filipino',
 'history_key': 'filipino',
 'english_voice': 'en-US-AvaNeural',
 'english_fallback_voice': 'en-US-GuyNeural',
 'native_voice': 'fil-PH-AngeloNeural',
 'native_fallback_voice': 'fil-PH-BlessicaNeural',
 'native_engine': 'edge',
 'native_lang_code': 'fil',
 'english_rate': '-4%',
 'native_rate': '-10%',
 'english_pitch': '+0Hz',
 'native_pitch': '+0Hz',
 'native_label': 'FILIPINO',
 'translit_label': 'SAY IT LIKE',
 'flag': 'ph',
 'greeting': 'Kumusta!',
 'encouragement': 'Magaling!',
 'rtl': False,
 'char_tiles': False,
 'script_font': '',
 'glyphs': 'ABCDEFGHIJKLMNOPQRSTUVWXYZÑñ'}
# ==== LANGUAGE PACK END ====

# ==== CATEGORIES START ====
CATEGORIES = {'Motivation': 'Motibasyon',
 'Love': 'Pag-ibig',
 'Success': 'Tagumpay',
 'Wisdom': 'Karunungan',
 'Happiness': 'Kaligayahan',
 'Self Improvement': 'Pagpapaunlad sa Sarili',
 'Gratitude': 'Pasasalamat',
 'Friendship': 'Pagkakaibigan',
 'Hope': 'Pag-asa',
 'Creativity': 'Pagkamalikhain',
 'Inner Peace': 'Panloob na Kapayapaan',
 'Confidence': 'Kumpiyansa sa Sarili',
 'Perseverance': 'Tiyaga',
 'Inspiration': 'Inspirasyon',
 'Positive Life': 'Positibong Buhay',
 'Courage': 'Tapang',
 'Kindness': 'Kabaitan',
 'Patience': 'Pasensya',
 'Forgiveness': 'Pagpapatawad',
 'Strength': 'Lakas',
 'Joy': 'Kagalakan',
 'Balance': 'Balanse',
 'Growth': 'Paglago',
 'Purpose': 'Layunin',
 'Mindfulness': 'Pag-iisip',
 'Travel & Airport': 'Paglalakbay at Paliparan',
 'Ordering Food & Dining': 'Pag-order ng Pagkain at Pagkain sa Labas',
 'Shopping & Prices': 'Pamimili at Presyo',
 'Asking for Directions': 'Pagtatanong ng Direksyon',
 'Hotel & Accommodation': 'Hotel at Tirahan',
 'Daily Routine': 'Pang-araw-araw na Gawain',
 'Meeting People & Greetings': 'Pakikipagkilala at Pagbati',
 'Emergency & Health': 'Pang-emergency at Kalusugan',
 'Public Transportation': 'Pampublikong Transportasyon',
 'Work & Office': 'Trabaho at Opisina',
 'Weather & Small Talk': 'Panahon at Maliit na Usapan',
 'Coffee Shop & Bakery': 'Kapehan at Panaderya',
 'Family & Home': 'Pamilya at Tahanan',
 'Hobbies & Free Time': 'Libangan at Libreng Oras',
 'Dating & Romance': 'Pakikipag-date at Romansa',
 'Phone Calls & Messages': 'Mga Tawag sa Telepono at Mensahe',
 'Banking & Money': 'Pagbabangko at Pera',
 'Doctor & Pharmacy': 'Doktor at Parmasya',
 'Sports & Fitness': 'Isports at Pag-eehersisyo',
 'Celebrations & Parties': 'Mga Pagdiriwang at Partido',
 'Feelings & Emotions': 'Mga Damdamin at Emosyon',
 'Agreeing & Disagreeing': 'Pagsang-ayon at Pagtutol',
 'Making Plans': 'Paggawa ng mga Plano',
 'Common Native Slang': 'Karaniwang Lokal na Balbal',
 'Cultural Traditions': 'Mga Tradisyong Kultural'}
# ==== CATEGORIES END ====

CATEGORY_NAMES = list(CATEGORIES.keys())

AI_MODEL = os.getenv("AI_MODEL", "openai/gpt-5.4-nano")
AI_FALLBACK_MODEL = os.getenv("AI_FALLBACK_MODEL", "gemini-fast")
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")

# ---------------------------------------------------------------- timing (seconds)

INTRO_DURATION = 7.2
CHAPTER_INTRO_DURATION = 4.4
OUTRO_DURATION = 13.0

EN_CARD_IN = 0.70
GAP_EN_NATIVE = 0.60
NATIVE_CARD_LEAD = 0.40
GAP_BEFORE_REPEAT = 1.00
TAIL_HOLD = 1.30

# ---------------------------------------------------------------- palette

INK = "#30303A"
MUTED = "#8A8A8A"
CREAM = "#FFF8E7"
GREEN = "#58CC02"
GREEN_DARK = "#46A302"
GREEN_DEEP = "#3D8F00"
BLUE = "#1CB0F6"
PURPLE = "#7C5CFF"
ORANGE = "#FF7A00"
RED = "#FF4B4B"
YELLOW = "#F5A700"
TEAL = "#00A889"
PINK = "#E056A0"

# ==== HASHTAGS START ====
HASHTAGS = ['#learnfilipino',
 '#filipinolessons',
 '#filipinoforbeginners',
 '#languagelearning',
 '#filipinovocabulary',
 '#velocityfilipino',
 '#dailyfilipino',
 '#filipino',
 '#learnlanguages',
 '#speakfilipino']
# ==== HASHTAGS END ====
