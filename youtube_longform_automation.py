"""
YouTube Long-Form Video Automation - Bilingual English/Filipino Content Generator
GENERATES 10-MINUTE VIDEOS with improved backgrounds for YouTube
"""

import os
import sys
import json
import random
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
IMAGES_DIR = OUTPUT_DIR / "images"
AUDIO_DIR = OUTPUT_DIR / "audio"
VIDEO_DIR = OUTPUT_DIR / "video"
HISTORY_DIR = OUTPUT_DIR / "history"
LONGFORM_DIR = OUTPUT_DIR / "longform_videos"

for d in [OUTPUT_DIR, IMAGES_DIR, AUDIO_DIR, VIDEO_DIR, HISTORY_DIR, LONGFORM_DIR]:
    d.mkdir(exist_ok=True)

# Video settings (16:9 horizontal for YouTube long-form)
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30
TARGET_DURATION_MINUTES = 5
TARGET_PHRASES = 120

# English category names
CATEGORIES_ENGLISH = [
    "Motivation", "Love", "Success", "Wisdom", "Happiness",
    "Self Improvement", "Gratitude", "Friendship", "Hope", "Creativity",
    "Inner Peace", "Confidence", "Perseverance", "Inspiration", "Positive Life",
    "Courage", "Kindness", "Patience", "Forgiveness", "Strength",
    "Joy", "Balance", "Growth", "Purpose", "Mindfulness",
]

# Filipino translations
CATEGORIES_FILIPINO = {
    "Motivation": "Motibasyon",
    "Love": "Pag-ibig",
    "Success": "Tagumpay",
    "Wisdom": "Karunungan",
    "Happiness": "Kaligayahan",
    "Self Improvement": "Pagpapaunlad sa Sarili",
    "Gratitude": "Pasasalamat",
    "Friendship": "Pagkakaibigan",
    "Hope": "Pag-asa",
    "Creativity": "Pagkamalikhain",
    "Inner Peace": "Panloob na Kapayapaan",
    "Confidence": "Kumpiyansa sa Sarili",
    "Perseverance": "Tiyaga",
    "Inspiration": "Inspirasyon",
    "Positive Life": "Positibong Buhay",
    "Courage": "Tapang",
    "Kindness": "Kabaitan",
    "Patience": "Pasensya",
    "Forgiveness": "Pagpapatawad",
    "Strength": "Lakas",
    "Joy": "Kagalakan",
    "Balance": "Balanse",
    "Growth": "Paglago",
    "Purpose": "Layunin",
    "Mindfulness": "Pag-iisip",
}

# Edge TTS voices
ENGLISH_VOICE = "en-US-GuyNeural"
LANG_VOICE = "fil-PH-BlessicaNeural"

# Phrase history file
PHRASE_HISTORY_FILE = HISTORY_DIR / "all_generated_phrases.json"

# Viral hook styles for engagement
VIRAL_STYLES = [
    "surprising fact",
    "common mistake correction",
    "quick tip",
    "must-know phrase",
    "local secret",
    "travel hack",
    "flirty phrase",
    "funny expression",
    "cultural insight",
    "word origin story"
]

# AI Model
AI_MODEL = os.getenv("AI_MODEL")

if not AI_MODEL:
    raise ValueError(
        "AI_MODEL not set! Please add 'AI_MODEL=gemini-fast' to your .env file."
    )


# ============== PHRASE HISTORY MANAGEMENT ==============

def load_phrase_history():
    if PHRASE_HISTORY_FILE.exists():
        with open(PHRASE_HISTORY_FILE, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return {"phrases": [], "last_updated": None}


def save_phrase_history(data):
    data["last_updated"] = datetime.now().isoformat()
    with open(PHRASE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_phrase_used(english_phrase):
    history = load_phrase_history()
    english_lower = english_phrase.lower().strip()
    for p in history.get("phrases", []):
        if p.get("english", "").lower().strip() == english_lower:
            return True
    return False


def is_phrase_similar(new_phrase, used_phrases, similarity_threshold=0.6):
    new_words = set(new_phrase.lower().split())
    if len(new_words) < 3:
        for used in used_phrases:
            if new_phrase.lower() in used.lower() or used.lower() in new_phrase.lower():
                return True
        return False
    for used in used_phrases:
        used_words = set(used.lower().split())
        if len(new_words) == 0 or len(used_words) == 0:
            continue
        intersection = len(new_words.intersection(used_words))
        union = len(new_words.union(used_words))
        similarity = intersection / union if union > 0 else 0
        if similarity >= similarity_threshold:
            return True
    return False


def filter_similar_phrases(phrases, history, similarity_threshold=0.6):
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    unique_phrases = []
    for phrase in phrases:
        english_text = phrase.get("english", "")
        if not is_phrase_similar(english_text, used_phrases, similarity_threshold):
            unique_phrases.append(phrase)
        else:
            print(f"[filter] Skipping similar: {english_text[:50]}...")
    return unique_phrases


def add_phrases_to_history(phrases, category):
    history = load_phrase_history()
    for phrase in phrases:
        history["phrases"].append({
            "english": phrase["english"],
            "filipino": phrase["filipino"],
            "category": category,
            "generated_at": datetime.now().isoformat()
        })
    save_phrase_history(history)
    print(f"[history] Added {len(phrases)} phrases to history (total: {len(history['phrases'])})")


# ============== CONTENT GENERATION ==============

def calculate_phrases_needed(target_minutes: int) -> int:
    avg_phrase_duration = 5.0
    total_seconds = target_minutes * 60
    return int(total_seconds / avg_phrase_duration)


def generate_phrases_for_longform(category_english: str, num_phrases: int) -> list:
    category_filipino = CATEGORIES_FILIPINO[category_english]
    history = load_phrase_history()
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    viral_style = random.choice(VIRAL_STYLES)
    all_phrases = []
    batch_size = 20
    max_attempts = 5

    for batch_num in range((num_phrases + batch_size - 1) // batch_size):
        remaining = num_phrases - len(all_phrases)
        current_batch_size = min(batch_size, remaining)
        if current_batch_size <= 0:
            break
        for attempt in range(max_attempts):
            try:
                import requests
                url = "https://gen.pollinations.ai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
                    "Content-Type": "application/json"
                }
                exclusion_note = ""
                if used_phrases:
                    recent = used_phrases[-30:] if len(used_phrases) > 30 else used_phrases
                    exclusion_note = f"\n\nAVOID these phrases (already used): {recent}"

                prompt = f"""Create {current_batch_size * 2} unique {category_english} phrases for English speakers learning Filipino.

Style: Make each phrase feel like a {viral_style} - something people would want to share!

CRITICAL RULE - ABSOLUTELY ZERO Filipino IN ENGLISH FIELD:
The "english" field must contain ONLY English words. NO Filipino words at all.
The "filipino" field contains the Filipino translation.
The "pronunciation" field is phonetic English spelling approximating Filipino sounds.

These are INSPIRATIONAL PHRASES about the topic, NOT language-learning tips.

WRONG (teaching tip with Filipino words): {{"english": "Don't say 'kumusta ka,' it means more than 'hello.'", ...}}
WRONG (Filipino word in english): {{"english": "Use 'salamat' for thank you", ...}}
WRONG (lesson tip): {{"english": "Say 'paalam' for goodbye", ...}}
CORRECT (pure english phrase): {{"english": "Knowledge is the key to wisdom.", "filipino": "Ang kaalaman ay susi sa karunungan.", "pronunciation": "ang ka-a-la-man ay su-si sa ka-ru-nga-nan"}}
CORRECT: {{"english": "A wise person listens more than they speak.", "filipino": "Ang isang marunong ay nakikinig nang higit sa pagsasalita.", "pronunciation": "ang i-sang ma-ru-nong ay na-ki-ki-nig nang hi-git sa pag-sa-sa-li-ta"}}

The english field MUST be 100% English words only. Absolutely NO Filipino words in the english field.

IMPORTANT RULES FOR NATURAL SPEECH:
1. Keep phrases SHORT (5-12 words max per language)
2. Add NATURAL PAUSES using commas (e.g., "Dream big, start small")
3. Use punctuation for breathing room in TTS
4. Avoid long run-on sentences
5. Each phrase should be speakable in 3-5 seconds
6. Use everyday vocabulary - avoid exotic or rare words
7. Avoid complex grammar - keep it simple and practical
8. Vary sentence structure for natural flow

For each phrase:
1. English phrase (pure English, zero Filipino words) with commas for natural pauses
2. Filipino translation
3. Pronunciation guide (phonetic English spelling)

Return as JSON array:
[{{"english": "...", "filipino": "...", "pronunciation": "..."}}]

IMPORTANT: Create FRESH, UNIQUE phrases that haven't been used before.{exclusion_note}"""

                payload = {
                    "model": AI_MODEL,
                    "messages": [
                        {"role": "system", "content": "You create INSPIRATIONAL PHRASES for YouTube language learning videos. CRITICAL: The 'english' field must be PURE ENGLISH with ZERO Filipino words - no Filipino words at all. These are universal inspirational phrases, NOT language learning tips. Filipino goes ONLY in the 'filipino' field."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 1.0
                }

                response = requests.post(url, headers=headers, json=payload, timeout=90)
                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()

                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                phrases = json.loads(content)
                filtered_phrases = filter_similar_phrases(phrases, history)
                unique_phrases = []
                for phrase in filtered_phrases:
                    if len(phrase["english"].split()) > 15:
                        continue
                    if not is_phrase_used(phrase["english"]):
                        unique_phrases.append(phrase)
                for phrase in unique_phrases:
                    if len(all_phrases) < num_phrases:
                        all_phrases.append(phrase)
                if len(all_phrases) >= num_phrases:
                    break
            except Exception as e:
                print(f"[content] Batch {batch_num + 1}, Attempt {attempt + 1} failed: {e}")
        if len(all_phrases) < num_phrases:
            import time
            time.sleep(1)

    final_phrases = all_phrases[:num_phrases]
    if final_phrases:
        add_phrases_to_history(final_phrases, category_english)
    print(f"[content] Generated {len(final_phrases)} phrases for long-form video")
    return final_phrases


def get_fresh_fallback_phrases(category: str, num_phrases: int) -> list:
    all_fallbacks = {
        "Motivation": [
            {"english": "Believe in yourself.", "filipino": "Maniwala ka sa iyong sarili.", "pronunciation": "ma-ni-wa-la ka sa i-yong sa-ri-li"},
            {"english": "You are capable of amazing things.", "filipino": "Kaya mong gawin ang mga kamangha-manghang bagay.", "pronunciation": "ka-ya mong ga-win ang ma-ga ka-mang-ha-mang-hang ba-gay"},
            {"english": "Dream big, start small.", "filipino": "Mangarap ng malaki, magsimula ng maliit.", "pronunciation": "ma-nga-rap ng ma-la-ki, mag-si-mu-la ng ma-li-it"},
            {"english": "Your future is created by your actions.", "filipino": "Ang iyong kinabukasan ay nilikha ng iyong mga kilos.", "pronunciation": "ang i-yong ki-na-bu-ka-san ay ni-lik-ha ng i-yong ma-ga ki-los"},
            {"english": "Never give up on your dreams.", "filipino": "Huwag sumuko sa iyong mga pangarap.", "pronunciation": "hu-wag su-mu-ko sa i-yong ma-ga pa-nga-rap"},
            {"english": "Small steps lead to big changes.", "filipino": "Ang maliliit na hakbang ay humahantong sa malalaking pagbabago.", "pronunciation": "ang ma-li-li-it na hak-bang ay hu-ma-ha-n-tong sa ma-la-la-king pag-ba-ba-go"},
            {"english": "You are stronger than you think.", "filipino": "Mas malakas ka kaysa sa tingin mo.", "pronunciation": "mas ma-la-kas ka kay-sa sa ti-ngin mo"},
        ],
        "Love": [
            {"english": "Love yourself first.", "filipino": "Mahalin mo muna ang iyong sarili.", "pronunciation": "ma-ha-lin mo mu-na ang i-yong sa-ri-li"},
            {"english": "Love makes everything possible.", "filipino": "Ang pag-ibig ay gumagawa ng lahat ng posible.", "pronunciation": "ang pag-i-big ay gu-ma-ga-wa ng la-hat ng po-si-ble"},
            {"english": "My heart beats for you.", "filipino": "Ang puso ko ay tumitibok para sa iyo.", "pronunciation": "ang pu-so ko ay tu-mi-ti-bok pa-ra sa i-yo"},
            {"english": "You are my everything.", "filipino": "Ikaw ang lahat sa akin.", "pronunciation": "i-kaw ang la-hat sa a-kin"},
            {"english": "Together forever, hand in hand.", "filipino": "Magkasama magpakailanman, magkahawak kamay.", "pronunciation": "mag-ka-sa-ma mag-pa-ka-i-lan-man, mag-ka-ha-wak ka-may"},
        ],
        "Success": [
            {"english": "Success comes from hard work.", "filipino": "Ang tagumpay ay nagmumula sa pagsisikap.", "pronunciation": "ang ta-gum-pay ay nag-mu-mu-la sa pag-si-si-kap"},
            {"english": "Keep going, you're getting there.", "filipino": "Magpatuloy ka, malapit ka na.", "pronunciation": "mag-pa-tu-loy ka, ma-la-pit ka na"},
            {"english": "Winners never quit.", "filipino": "Ang mga nanalo ay hindi sumusuko.", "pronunciation": "ang ma-ga na-na-lo ay hin-di su-mu-su-ko"},
            {"english": "Your effort will pay off.", "filipino": "Ang iyong pagsisikap ay magbubunga.", "pronunciation": "ang i-yong pag-si-si-kap ay mag-bu-bu-nga"},
        ],
        "Wisdom": [
            {"english": "Knowledge is power.", "filipino": "Ang kaalaman ay kapangyarihan.", "pronunciation": "ang ka-a-la-man ay ka-pang-ya-ri-han"},
            {"english": "Learn from yesterday, live for today.", "filipino": "Matuto mula kahapon, mabuhay para ngayon.", "pronunciation": "ma-tu-to mu-la ka-ha-pon, ma-bu-hay pa-ra nga-yon"},
            {"english": "Think before you act.", "filipino": "Mag-isip bago kumilos.", "pronunciation": "mag-i-sip ba-go ku-mi-los"},
            {"english": "Experience is the best teacher.", "filipino": "Ang karanasan ay ang pinakamahusay na guro.", "pronunciation": "ang ka-ra-na-san ay ang pi-na-ka-ma-hu-say na gu-ro"},
        ],
        "Happiness": [
            {"english": "Happiness is a choice.", "filipino": "Ang kaligayahan ay isang pagpili.", "pronunciation": "ang ka-li-ga-ya-han ay i-sang pag-pi-li"},
            {"english": "Find joy in the little things.", "filipino": "Hanapin ang kagalakan sa maliliit na bagay.", "pronunciation": "ha-na-pin ang ka-ga-la-kan sa ma-li-li-it na ba-gay"},
            {"english": "Smile, it makes others happy.", "filipino": "Ngumiti, napapasaya nito ang iba.", "pronunciation": "ngu-mi-ti, na-pa-pa-sa-ya ni-to ang i-ba"},
            {"english": "Today is a gift.", "filipino": "Ang ngayon ay isang regalo.", "pronunciation": "ang nga-yon ay i-sang re-ga-lo"},
        ],
        "Self Improvement": [
            {"english": "Be better than yesterday.", "filipino": "Maging mas mahusay kaysa kahapon.", "pronunciation": "ma-ging mas ma-hu-say kay-sa ka-ha-pon"},
            {"english": "Grow through what you go through.", "filipino": "Lumago sa pinagdadaanan mo.", "pronunciation": "lu-ma-go sa pi-nag-da-da-a-nan mo"},
            {"english": "Invest in yourself daily.", "filipino": "Mamuhunan sa iyong sarili araw-araw.", "pronunciation": "ma-mu-hu-nan sa i-yong sa-ri-li a-raw-a-raw"},
        ],
        "Gratitude": [
            {"english": "Thank you for everything.", "filipino": "Salamat sa lahat.", "pronunciation": "sa-la-mat sa la-hat"},
            {"english": "I appreciate your help.", "filipino": "Pinapahalagahan ko ang iyong tulong.", "pronunciation": "pi-na-pa-ha-la-ga-han ko ang i-yong tu-long"},
            {"english": "Grateful for this moment.", "filipino": "Nagpapasalamat sa sandaling ito.", "pronunciation": "nap-pa-pa-sa-la-mat sa san-da-ling i-to"},
        ],
        "Friendship": [
            {"english": "Friends forever, no matter what.", "filipino": "Magkaibigan magpakailanman, kahit ano pa man.", "pronunciation": "mag-ka-i-bi-gan mag-pa-ka-i-lan-man, ka-hit a-no pa man"},
            {"english": "You are my best friend.", "filipino": "Ikaw ang aking matalik na kaibigan.", "pronunciation": "i-kaw ang a-king ma-ta-lik na ka-i-bi-gan"},
            {"english": "True friends stick together.", "filipino": "Ang tunay na magkaibigan ay nagsasama-sama.", "pronunciation": "ang tu-nay na mag-ka-i-bi-gan ay nag-sa-sa-ma-sa-ma"},
        ],
        "Hope": [
            {"english": "There is always hope.", "filipino": "Laging may pag-asa.", "pronunciation": "la-ging may pag-a-sa"},
            {"english": "Better days are coming.", "filipino": "Darating ang mas magagandang araw.", "pronunciation": "da-ra-ting ang mas ma-ga-gan-dang a-raw"},
            {"english": "Keep faith, keep going.", "filipino": "Manatili sa pananampalataya, magpatuloy.", "pronunciation": "ma-na-ti-li sa pa-na-nam-pa-la-ta-ya, mag-pa-tu-loy"},
        ],
        "Creativity": [
            {"english": "Create something beautiful today.", "filipino": "Lumikha ng isang bagay na maganda ngayon.", "pronunciation": "lu-mik-ha ng i-sang ba-gay na ma-gan-da nga-yon"},
            {"english": "Your imagination is unlimited.", "filipino": "Ang iyong imahinasyon ay walang limitasyon.", "pronunciation": "ang i-yong i-ma-hi-na-syon ay wa-lang li-mi-ta-syon"},
            {"english": "Art comes from the heart.", "filipino": "Ang sining ay nagmumula sa puso.", "pronunciation": "ang si-ning ay nag-mu-mu-la sa pu-so"},
            {"english": "Express yourself freely.", "filipino": "Ipahayag ang iyong sarili nang malaya.", "pronunciation": "i-pa-ha-yag ang i-yong sa-ri-li nang ma-la-ya"},
            {"english": "Innovation starts with curiosity.", "filipino": "Ang inobasyon ay nagsisimula sa pagiging mausisa.", "pronunciation": "ang i-no-ba-syon ay nag-si-si-mu-la sa pa-gi-ging ma-u-si-sa"},
        ],
        "Inner Peace": [
            {"english": "Find peace within yourself.", "filipino": "Hanapin ang kapayapaan sa iyong sarili.", "pronunciation": "ha-na-pin ang ka-pa-ya-paan sa i-yong sa-ri-li"},
            {"english": "Breathe, relax, let go.", "filipino": "Huminga, magpahinga, bitawan.", "pronunciation": "hu-mi-nga, mag-pa-hi-nga, bi-ta-wan"},
            {"english": "Calm mind, happy heart.", "filipino": "Kalmadong isip, masayang puso.", "pronunciation": "kal-ma-dong i-sip, ma-sa-yang pu-so"},
        ],
        "Confidence": [
            {"english": "You are enough, just as you are.", "filipino": "Sapat ka na, kung ano ka man.", "pronunciation": "sa-pat ka na, kung a-no ka man"},
            {"english": "Stand tall, speak up.", "filipino": "Tumayo nang tuwid, magsalita.", "pronunciation": "tu-ma-yo nang tu-wid, mag-sa-li-ta"},
            {"english": "Believe in your abilities.", "filipino": "Maniwala sa iyong mga kakayahan.", "pronunciation": "ma-ni-wa-la sa i-yong ma-ga ka-ka-ya-han"},
        ],
        "Perseverance": [
            {"english": "Never give up, keep pushing.", "filipino": "Huwag sumuko, patuloy na lumaban.", "pronunciation": "hu-wag su-mu-ko, pa-tu-loy na lu-ma-ban"},
            {"english": "Storms make trees take deeper roots.", "filipino": "Ang mga bagyo ay nagpapalalim ng ugat ng puno.", "pronunciation": "ang ma-ga bag-yo ay nag-pa-pa-la-lim ng u-gat ng pu-no"},
            {"english": "Patience and persistence win.", "filipino": "Ang pasensya at tiyaga ay nananalo.", "pronunciation": "ang pa-sen-sya at ti-ya-ga ay na-na-na-lo"},
        ],
        "Inspiration": [
            {"english": "Let your light shine bright.", "filipino": "Hayaang lumiwanag ang iyong ilaw.", "pronunciation": "ha-ya-ang lu-mi-wa-nag ang i-yong i-law"},
            {"english": "Inspire others by your actions.", "filipino": "Magbigay inspirasyon sa iba sa iyong mga kilos.", "pronunciation": "mag-bi-gay in-spi-ra-syon sa i-ba sa i-yong ma-ga ki-los"},
            {"english": "Be the change you want to see.", "filipino": "Maging pagbabago na nais mong makita.", "pronunciation": "ma-ging pag-ba-ba-go na na-is mong ma-ki-ta"},
        ],
        "Positive Life": [
            {"english": "Choose positivity every day.", "filipino": "Pumili ng positibidad araw-araw.", "pronunciation": "pu-mi-li ng po-si-ti-bi-dad a-raw-a-raw"},
            {"english": "Good vibes only.", "filipino": "Magandang vibes lamang.", "pronunciation": "ma-gan-dang vaybs la-mang"},
            {"english": "Life is what you make it.", "filipino": "Ang buhay ay kung ano ang gawin mo dito.", "pronunciation": "ang bu-hay ay kung a-no ang ga-win mo di-to"},
        ],
        "Courage": [
            {"english": "Be brave, take the first step.", "filipino": "Maging matapang, gawin ang unang hakbang.", "pronunciation": "ma-ging ma-ta-pang, ga-win ang u-nang hak-bang"},
            {"english": "Courage is not the absence of fear.", "filipino": "Ang tapang ay hindi kawalan ng takot.", "pronunciation": "ang ta-pang ay hin-di ka-wa-lan ng ta-kot"},
            {"english": "Face your fears head on.", "filipino": "Harapin ang iyong mga takot nang direkta.", "pronunciation": "ha-ra-pin ang i-yong ma-ga ta-kot nang di-rek-ta"},
        ],
        "Kindness": [
            {"english": "Be kind to everyone you meet.", "filipino": "Maging mabait sa lahat ng iyong makasalubong.", "pronunciation": "ma-ging ma-ba-it sa la-hat ng i-yong ma-ka-sa-lu-bong"},
            {"english": "Kindness costs nothing, means everything.", "filipino": "Ang kabaitan ay walang halaga, ngunit ang kahulugan ay lahat.", "pronunciation": "ang ka-ba-i-tan ay wa-lang ha-la-ga, ngu-nit ang ka-hu-lu-gan ay la-hat"},
            {"english": "Spread kindness wherever you go.", "filipino": "Ipakalat ang kabaitan saan ka man pumunta.", "pronunciation": "i-pa-ka-lat ang ka-ba-i-tan sa-an ka man pu-mun-ta"},
        ],
        "Patience": [
            {"english": "Good things take time.", "filipino": "Ang magagandang bagay ay nangangailangan ng panahon.", "pronunciation": "ang ma-ga-gan-dang ba-gay ay na-nga-nga-i-la-ngan ng pa-na-hon"},
            {"english": "Wait patiently, trust the process.", "filipino": "Maghintay nang may pasensya, magtiwala sa proseso.", "pronunciation": "mag-hin-tay nang may pa-sen-sya, mag-ti-wa-la sa pro-se-so"},
            {"english": "Rome wasn't built in a day.", "filipino": "Ang Roma ay hindi itinayo sa isang araw.", "pronunciation": "ang Ro-ma ay hin-di i-ti-na-yo sa i-sang a-raw"},
        ],
        "Forgiveness": [
            {"english": "Forgive and set yourself free.", "filipino": "Patawarin at palayain ang iyong sarili.", "pronunciation": "pa-ta-wa-rin at pa-la-ya-in ang i-yong sa-ri-li"},
            {"english": "Let go of grudges, find peace.", "filipino": "Bitawan ang sama ng loob, hanapin ang kapayapaan.", "pronunciation": "bi-ta-wan ang sa-ma ng lo-ob, ha-na-pin ang ka-pa-ya-paan"},
            {"english": "Forgiveness is a gift to yourself.", "filipino": "Ang pagpapatawad ay isang regalo sa iyong sarili.", "pronunciation": "ang pag-pa-pa-ta-wad ay i-sang re-ga-lo sa i-yong sa-ri-li"},
        ],
        "Strength": [
            {"english": "You are stronger than you know.", "filipino": "Mas malakas ka kaysa sa alam mo.", "pronunciation": "mas ma-la-kas ka kay-sa sa a-lam mo"},
            {"english": "Inner strength comes from within.", "filipino": "Ang panloob na lakas ay nagmumula sa loob.", "pronunciation": "ang pan-lo-ob na la-kas ay nag-mu-mu-la sa lo-ob"},
            {"english": "Challenges make you stronger.", "filipino": "Ang mga hamon ay nagpapalakas sa iyo.", "pronunciation": "ang ma-ga ha-mon ay nag-pa-pa-la-kas sa i-yo"},
        ],
        "Joy": [
            {"english": "Find joy in every moment.", "filipino": "Hanapin ang kagalakan sa bawat sandali.", "pronunciation": "ha-na-pin ang ka-ga-la-kan sa ba-wat san-da-li"},
            {"english": "Joy is contagious, spread it.", "filipino": "Ang kagalakan ay nakakahawa, ipalaganap ito.", "pronunciation": "ang ka-ga-la-kan ay na-ka-ka-ha-wa, i-pa-la-ga-nap i-to"},
            {"english": "Dance like nobody's watching.", "filipino": "Sumayaw na parang walang nakatingin.", "pronunciation": "su-ma-yaw na pa-rang wa-lang na-ka-ti-ngin"},
        ],
        "Balance": [
            {"english": "Find balance in your life.", "filipino": "Hanapin ang balanse sa iyong buhay.", "pronunciation": "ha-na-pin ang ba-lan-se sa i-yong bu-hay"},
            {"english": "Work hard, rest well.", "filipino": "Magtrabaho nang mabuti, magpahinga nang maayos.", "pronunciation": "mag-tra-ba-ho nang ma-bu-ti, mag-pa-hi-nga nang ma-a-yos"},
            {"english": "Too much of anything is not good.", "filipino": "Ang sobra sa anuman ay hindi mabuti.", "pronunciation": "ang sob-ra sa a-nu-man ay hin-di ma-bu-ti"},
        ],
        "Growth": [
            {"english": "Growth happens outside your comfort zone.", "filipino": "Ang paglago ay nangyayari sa labas ng iyong comfort zone.", "pronunciation": "ang pag-la-go ay nang-ya-ya-ri sa la-bas ng i-yong kom-port zown"},
            {"english": "Embrace change, grow stronger.", "filipino": "Yakapin ang pagbabago, lumakas pa.", "pronunciation": "ya-ka-pin ang pag-ba-ba-go, lu-ma-kas pa"},
            {"english": "Every challenge is a chance to grow.", "filipino": "Ang bawat hamon ay isang pagkakataon upang lumago.", "pronunciation": "ang ba-wat ha-mon ay i-sang pag-ka-ka-ta-on u-pang lu-ma-go"},
        ],
        "Purpose": [
            {"english": "Find your purpose, follow it.", "filipino": "Hanapin ang iyong layunin, sundan ito.", "pronunciation": "ha-na-pin ang i-yong la-yu-nin, sun-dan i-to"},
            {"english": "Your life has meaning.", "filipino": "Ang iyong buhay ay may kahulugan.", "pronunciation": "ang i-yong bu-hay ay may ka-hu-lu-gan"},
            {"english": "Live with intention, not accident.", "filipino": "Mabuhay nang may intensyon, hindi aksidente.", "pronunciation": "ma-bu-hay nang may in-ten-syon, hin-di ak-si-den-te"},
        ],
        "Mindfulness": [
            {"english": "Be present in this moment.", "filipino": "Maging naroroon sa sandaling ito.", "pronunciation": "ma-ging na-ro-roon sa san-da-ling i-to"},
            {"english": "Breathe deeply, stay grounded.", "filipino": "Huminga nang malalim, manatiling nakaugat.", "pronunciation": "hu-mi-nga nang ma-la-lim, ma-na-ti-ling na-ka-u-gat"},
            {"english": "Notice the little things around you.", "filipino": "Pansinin ang maliliit na bagay sa paligid mo.", "pronunciation": "pan-si-nin ang ma-li-li-it na ba-gay sa pa-li-gid mo"},
        ],
    }

    fallbacks = all_fallbacks.get(category, all_fallbacks["Motivation"])
    history = load_phrase_history()
    fresh_phrases = []
    for p in fallbacks:
        if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
            fresh_phrases.append(p)

    if len(fresh_phrases) < num_phrases:
        for cat, cat_fallbacks in all_fallbacks.items():
            if cat != category:
                for p in cat_fallbacks:
                    if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
                        fresh_phrases.append(p)
                    if len(fresh_phrases) >= num_phrases:
                        break
            if len(fresh_phrases) >= num_phrases:
                break

    return fresh_phrases[:num_phrases]


# ============== AUDIO GENERATION ==============

async def generate_single_audio(text: str, voice: str, output_path: str):
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"  TTS error: {e}")
        return False


def generate_all_audio(phrases: list, output_dir: str):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_files = []

    for i, phrase in enumerate(phrases):
        english_file = output_dir / f"english_{i}.mp3"
        lang_file = output_dir / f"lang_{i}.mp3"
        combined_file = output_dir / f"combined_{i}.mp3"

        if (i + 1) % 20 == 0:
            print(f"  Generating audio {i+1}/{len(phrases)}...")

        en_success = asyncio.run(generate_single_audio(phrase["english"], ENGLISH_VOICE, str(english_file)))
        if not en_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(english_file)]
            subprocess.run(cmd, capture_output=True)

        lang_success = asyncio.run(generate_single_audio(phrase["filipino"], LANG_VOICE, str(lang_file)))
        if not lang_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(lang_file)]
            subprocess.run(cmd, capture_output=True)

        en_duration = get_audio_duration(str(english_file))
        lang_duration = get_audio_duration(str(lang_file))

        pause_between = 0.5
        total_duration = en_duration + pause_between + lang_duration

        cmd = [
            "ffmpeg", "-y",
            "-i", str(english_file),
            "-i", str(lang_file),
            "-filter_complex", f"[0:a][1:a]concat=n=2:v=0:a=1[out]",
            "-map", "[out]",
            str(combined_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            concat_file = output_dir / f"concat_{i}.txt"
            with open(concat_file, "w", encoding="utf-8") as f:
                f.write(f"file '{english_file.as_posix()}'\n")
                f.write(f"file '{lang_file.as_posix()}'\n")
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_file),
                "-c:a", "aac",
                str(combined_file)
            ]
            subprocess.run(cmd, capture_output=True)
            if concat_file.exists():
                concat_file.unlink()

        actual_duration = get_audio_duration(str(combined_file))

        audio_files.append({
            "index": i,
            "english": str(english_file),
            "lang": str(lang_file),
            "combined": str(combined_file),
            "duration": actual_duration,
            "en_duration": en_duration,
            "lang_duration": lang_duration
        })

    print(f"\n[audio] Generated {len(audio_files)} phrase audios")
    return audio_files


def get_audio_duration(audio_file: str) -> float:
    if not Path(audio_file).exists():
        return 2.0
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 2.0


def create_final_narration(audio_files: list, output_file: str):
    n = len(audio_files)
    print(f"[audio] Combining {n} audio files...")
    concat_file = Path(output_file).parent / "narration_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for audio_info in audio_files:
            combined_path = Path(audio_info["combined"])
            if combined_path.exists():
                path_str = str(combined_path.resolve()).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{path_str}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c:a", "copy", str(output_file)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if concat_file.exists():
        concat_file.unlink()
    if result.returncode == 0 and Path(output_file).exists() and Path(output_file).stat().st_size > 0:
        size = Path(output_file).stat().st_size
        print(f"\n[audio] Final narration: {Path(output_file).name} ({size/1024:.1f} KB)")
        return True
    return False


# ============== BACKGROUND GENERATION ==============

def create_premium_background(category_english: str):
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        if ratio < 0.5:
            r, g, b = 255, 252, 245
        else:
            r = int(255 + (245 - 255) * ((ratio - 0.5) * 2))
            g = int(252 + (240 - 252) * ((ratio - 0.5) * 2))
            b = int(245 + (230 - 245) * ((ratio - 0.5) * 2))
        draw.rectangle([(0, y), (VIDEO_WIDTH, y + 1)], fill=(r, g, b))
    return img


def generate_complete_image(phrase_data: dict, category_english: str, output_path: str):
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
    except ImportError:
        print("PIL not available. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    # Font paths - check fonts/ directory first
    english_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    lang_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
        return ImageFont.load_default()

    font_category = load_font(english_font_paths, 42)
    font_english = load_font(english_font_paths, 68)
    font_lang = load_font(lang_font_paths, 82)
    font_pronunciation = load_font(lang_font_paths, 48)
    font_branding = load_font(english_font_paths, 38)

    english = phrase_data.get("english", "")
    filipino = phrase_data.get("filipino", "")
    pronunciation = phrase_data.get("pronunciation", "")

    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line: lines.append(' '.join(current_line))
                current_line = [word]
        if current_line: lines.append(' '.join(current_line))
        return lines

    # Header Bar
    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_category)
    cat_w = cat_bbox[2] - cat_bbox[0]
    badge_h = 75
    badge_pad_x = 40
    container_w = cat_w + (badge_pad_x * 2)
    container_x = 60
    container_y = 60
    draw.rounded_rectangle(
        [(container_x, container_y), (container_x + container_w, container_y + badge_h)],
        radius=15, fill=(45, 35, 65, 255)
    )
    draw.text(
        (container_x + container_w // 2, container_y + badge_h // 2 + 2),
        cat_text,
        fill=(255, 255, 255, 255),
        font=font_category,
        anchor="mm"
    )

    CONTENT_Y_CENTER = VIDEO_HEIGHT // 2
    GAP = 60

    en_lines = wrap_text(english, font_english, VIDEO_WIDTH - 300)
    en_line_h = 80
    en_total_h = len(en_lines) * en_line_h

    lang_lines = wrap_text(filipino, font_lang, VIDEO_WIDTH - 300)
    lang_line_h = 100
    lang_total_h = len(lang_lines) * lang_line_h

    pron_text = f"[{pronunciation}]"
    pron_lines = wrap_text(pron_text, font_pronunciation, VIDEO_WIDTH - 400)
    pron_line_h = 60
    pron_total_h = len(pron_lines) * pron_line_h

    total_content_h = en_total_h + lang_total_h + pron_total_h + (GAP * 2)
    y_start = CONTENT_Y_CENTER - (total_content_h // 2)

    box_w = VIDEO_WIDTH - 200
    box_x = (VIDEO_WIDTH - box_w) // 2

    # English Box
    en_box_h = en_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_start), (box_x + box_w, y_start + en_box_h)],
        radius=25, fill=(65, 50, 95, 255)
    )
    for i, line in enumerate(en_lines):
        draw.text((VIDEO_WIDTH // 2, y_start + 30 + (i * en_line_h) + en_line_h // 2),
                  line, fill=(255, 255, 255), font=font_english, anchor="mm")

    y_cursor = y_start + en_box_h + GAP

    # Filipino Section
    lang_box_h = lang_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_cursor), (box_x + box_w, y_cursor + lang_box_h)],
        radius=25, fill=(95, 80, 125, 255)
    )
    for i, line in enumerate(lang_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 30 + (i * lang_line_h) + lang_line_h // 2),
                  line, fill=(255, 255, 255), font=font_lang, anchor="mm")

    y_cursor += lang_box_h + (GAP // 2)

    # Pronunciation Section
    pron_box_h = pron_total_h + 40
    pron_box_w = box_w - 200
    pron_box_x = (VIDEO_WIDTH - pron_box_w) // 2
    draw.rounded_rectangle(
        [(pron_box_x, y_cursor), (pron_box_x + pron_box_w, y_cursor + pron_box_h)],
        radius=20, fill=(255, 210, 160, 255)
    )
    for i, line in enumerate(pron_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 20 + (i * pron_line_h) + pron_line_h // 2),
                  line, fill=(70, 45, 25), font=font_pronunciation, anchor="mm")

    # Branding
    brand_text = "VELOCITY FILIPINO"
    brand_bbox = draw.textbbox((0, 0), brand_text, font=font_branding)
    brand_w = brand_bbox[2] - brand_bbox[0]
    draw.text((VIDEO_WIDTH - brand_w - 60, VIDEO_HEIGHT - 80), brand_text,
              fill=(45, 35, 65, 255), font=font_branding)

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path


# ============== THUMBNAIL GENERATION ==============

def generate_thumbnail(category_english: str, category_filipino: str, output_path: str):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("PIL not available for thumbnail. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    english_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    lang_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try: return ImageFont.truetype(font_path, size)
            except: continue
        return ImageFont.load_default()

    font_huge = load_font(english_font_paths, 130)
    font_main = load_font(lang_font_paths, 110)
    font_sub = load_font(english_font_paths, 60)
    font_badge = load_font(english_font_paths, 45)

    draw.text((VIDEO_WIDTH // 2, 220), "MASTER FILIPINO", fill=(45, 35, 65), font=font_huge, anchor="mm")

    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_sub)
    cat_w = cat_bbox[2] - cat_bbox[0]
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - cat_w // 2 - 40, 320), (VIDEO_WIDTH // 2 + cat_w // 2 + 40, 410)],
        radius=20, fill=(65, 50, 95, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 365), cat_text, fill=(255, 255, 255), font=font_sub, anchor="mm")

    draw.text((VIDEO_WIDTH // 2, 530), category_filipino, fill=(45, 35, 65), font=font_main, anchor="mm")

    cta_text = "60 VIGTIGE FRASER"
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - 300, 650), (VIDEO_WIDTH // 2 + 300, 730)],
        radius=15, fill=(255, 210, 160, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 690), cta_text, fill=(70, 45, 25), font=font_badge, anchor="mm")

    draw.rectangle([(0, VIDEO_HEIGHT - 100), (VIDEO_WIDTH, VIDEO_HEIGHT)], fill=(45, 35, 65, 255))
    draw.text((VIDEO_WIDTH // 2, VIDEO_HEIGHT - 50), "VELOCITY FILIPINO", fill=(255, 255, 255), font=font_badge, anchor="mm")

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path


def extract_video_thumbnail(video_path: str, output_path: str, timestamp_seconds: int = 5):
    try:
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(timestamp_seconds),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and Path(output_path).exists():
            print(f"  Video thumbnail extracted: {Path(output_path).name}")
            return str(output_path)
        else:
            print(f"  Could not extract video thumbnail")
            return None
    except Exception as e:
        print(f"  Thumbnail extraction error: {e}")
        return None


# ============== TITLE & DESCRIPTION GENERATION ==============

def generate_title_description(category_english: str, category_filipino: str, phrases: list, duration_minutes: float, output_dir: str):
    titles = [
        f"Learn Filipino in 10 Minutes | {category_english} Phrases Every Beginner NEEDS to Know! ({category_filipino})",
        f"60 Filipino Phrases for {category_english} | Speak Filipino Like a Native! ({category_filipino})",
        f"Master Filipino {category_english} | 60 Essential Filipino Phrases with Pronunciation | Velocity Filipino",
        f"Filipino Learning Made Easy | {category_english} Vocabulary | 10 Minute Lesson",
        f"Speak Filipino Fluently | {category_english} Phrases | English + Filipino + Pronunciation",
    ]

    description = f"""\U0001F1F5\U0001F1ED Learn Filipino with Velocity Filipino! \U0001F1F5\U0001F1ED

In this video, you'll learn 60 essential Filipino phrases about {category_english} ({category_filipino}).
Perfect for beginners and intermediate learners!

\U0001F4DA WHAT YOU'LL LEARN:
\u2022 60 practical {category_english} phrases in Filipino
\u2022 Correct pronunciation guide
\u2022 Natural pauses for speaking practice
\u2022 Common expressions used by native speakers

\U0001F551 VIDEO TIMESTAMPS:
"""

    avg_phrase_duration = duration_minutes * 60 / len(phrases)
    for i in range(0, len(phrases), 10):
        timestamp = int(i * avg_phrase_duration / 60)
        minute = timestamp
        second = int((i * avg_phrase_duration) % 60)
        end_phrase = min(i + 10, len(phrases))
        description += f"{minute:02d}:{second:02d} Phrases {i+1}-{end_phrase}\n"

    description += """
\U0001F4DD ALL PHRASES IN THIS VIDEO:
"""

    for i, phrase in enumerate(phrases, 1):
        description += f"""
{i}. {phrase['english']}
   Filipino: {phrase['filipino']}
    Pronunciation: {phrase['pronunciation']}
"""

    description += """
\U0001F3AF PERFECT FOR:
\u2022 Filipino beginners wanting to expand vocabulary
\u2022 Intermediate learners practicing pronunciation
\u2022 Anyone interested in Filipino language and culture
\u2022 Language enthusiasts and polyglots
\u2022 Students preparing for exams

\U0001F4A1 TIPS FOR LEARNING:
1. Repeat each phrase out loud
2. Practice daily for best results
3. Use the pauses to speak along
4. Write down phrases you find difficult
5. Review this video multiple times

\U0001F514 SUBSCRIBE for more Filipino learning content!
\U0001F44D LIKE this video if you found it helpful!
\U0001F4AC COMMENT which phrases you want to learn next!

\U0001F4F1 FOLLOW VELOCITY FILIPINO:
[Add your social media links here]

\U0001F3B5 MUSIC:
[Add music credits if applicable]

\U0001F4D6 RELATED VIDEOS:
\u2022 Filipino Motivation Phrases
\u2022 Filipino Love Expressions
\u2022 Basic Filipino Greetings

#LearnFilipino #FilipinoPhrases #FilipinoLanguage #{category_english.replace(' ', '')} #VelocityFilipino #FilipinoForBeginners #SpeakFilipino #FilipinoVocabulary #Pronunciation #LanguageLearning #Filipino101 #FilipinoLesson

---
\u00A9 Velocity Filipino - Making Filipino learning accessible to everyone!
"""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "youtube_upload_info.txt", "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("YOUTUBE VIDEO UPLOAD INFORMATION\n")
        f.write("=" * 80 + "\n\n")
        f.write("RECOMMENDED TITLES (Choose one):\n")
        f.write("-" * 80 + "\n")
        for i, title in enumerate(titles, 1):
            f.write(f"\n{i}. {title}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("SELECTED TITLE (Recommended):\n")
        f.write("-" * 80 + "\n")
        f.write(f"\n{titles[0]}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("VIDEO DESCRIPTION:\n")
        f.write("-" * 80 + "\n\n")
        f.write(description)
        f.write("\n" + "=" * 80 + "\n")
        f.write("VIDEO TAGS (for YouTube):\n")
        f.write("-" * 80 + "\n")
        tags = [
            "Learn Filipino",
            "Filipino Phrases",
            "Filipino Language",
            category_english,
            "Velocity Filipino",
            "Filipino for Beginners",
            "Speak Filipino",
            "Filipino Vocabulary",
            "Pronunciation",
            "Language Learning",
            "Filipino 101",
            "Filipino Lesson"
        ]
        f.write(", ".join(tags) + "\n")

    metadata = {
        "recommended_titles": titles,
        "selected_title": titles[0],
        "description": description,
        "category_english": category_english,
        "category_filipino": category_filipino,
        "phrases_count": len(phrases),
        "duration_minutes": round(duration_minutes, 2),
        "tags": tags
    }

    with open(output_dir / "video_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n[metadata] Generated YouTube upload files")
    print(f"  youtube_upload_info.txt (title + description + tags)")
    print(f"  video_metadata.json")

    return metadata


# ============== VIDEO CREATION ==============

def create_video_from_images_audio(image_files: list, audio_files: list, combined_audio: str, output_file: str):
    print(f"\n[video] Creating long-form video from {len(image_files)} images...")

    temp_clips = []

    for i, (img_path, audio_info) in enumerate(zip(image_files, audio_files)):
        duration = audio_info['duration']
        print(f"  Image {i+1}/{len(image_files)}: {duration:.2f}s")

        temp_clip = Path(output_file).parent / f"temp_clip_{i:02d}.mp4"
        temp_clips.append(temp_clip)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-i", audio_info['combined'],
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={FPS}",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            "-shortest",
            "-vsync", "cfr",
            str(temp_clip)
        ]

        subprocess.run(cmd, check=True, capture_output=True)

    print("[video] Concatenating clips...")
    concat_file = Path(output_file).parent / "concat_list.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for clip in temp_clips:
            f.write(f"file '{clip.resolve().as_posix()}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(output_file)]
    subprocess.run(cmd, check=True, capture_output=True)

    if concat_file.exists():
        concat_file.unlink()

    video_duration = get_audio_duration(str(output_file))
    print(f"[video] Video created: {Path(output_file).name} ({video_duration:.2f}s)")

    for clip in temp_clips:
        if clip.exists():
            clip.unlink()


# ============== MAIN WORKFLOW ==============

def generate_longform_video(category_english: str = None, target_phrases: int = None):
    if not category_english:
        category_english = random.choice(CATEGORIES_ENGLISH)

    phrases_count = target_phrases if target_phrases else TARGET_PHRASES

    print(f"\n{'='*80}")
    print(f"LONG-FORM VIDEO - Category: {category_english} ({CATEGORIES_FILIPINO[category_english]})")
    print(f"Target Phrases: {phrases_count}")
    print(f"{'='*80}\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_dir = LONGFORM_DIR / f"{category_english}_longform_{timestamp}"
    video_dir.mkdir(exist_ok=True)

    print(f"[1/6] Generating {phrases_count} unique phrases (checking history)...")
    phrases = generate_phrases_for_longform(category_english, phrases_count)

    for i, phrase in enumerate(phrases, 1):
        print(f"  {i}. {phrase['english']} -> {phrase['filipino']}")

    print(f"\n[info] Total phrases: {len(phrases)}")

    print(f"\n[2/6] Generating {len(phrases)} images with premium backgrounds...")
    for i, phrase in enumerate(phrases):
        output_path = video_dir / f"phrase_{i:04d}.jpg"
        generate_complete_image(phrase, category_english, str(output_path))
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{len(phrases)} images...")

    print(f"\n[3/6] Generating thumbnail...")
    thumbnail_path = video_dir / "thumbnail.jpg"
    try:
        from generate_thumbnail import generate_scenic_image
        result = generate_scenic_image(category_english, category_english, str(thumbnail_path))
        if result and Path(result).exists():
            print(f"  gpt-image-2 thumbnail saved")
        else:
            print(f"  gpt-image-2 failed, using built-in")
            generate_thumbnail(category_english, CATEGORIES_FILIPINO[category_english], str(thumbnail_path))
    except Exception as e:
        print(f"  Thumbnail error: {e}, using built-in")
        generate_thumbnail(category_english, CATEGORIES_FILIPINO[category_english], str(thumbnail_path))

    video_thumbnail_path = video_dir / "video_thumbnail_frame.jpg"

    print(f"\n[4/6] Generating audio for {len(phrases)} phrases...")
    audio_files = generate_all_audio(phrases, str(video_dir))

    final_audio = video_dir / "narration.mp3"
    create_final_narration(audio_files, str(final_audio))

    total_duration = sum(a['duration'] for a in audio_files)
    print(f"\n[info] Total audio duration: {total_duration:.2f}s ({total_duration/60:.2f} minutes)")

    print(f"\n[5/6] Creating long-form video with transitions...")
    output_video = video_dir / "final_video.mp4"

    image_files = sorted([str(p) for p in video_dir.glob("phrase_*.jpg")])

    create_video_from_images_audio(
        image_files,
        audio_files,
        str(final_audio),
        str(output_video)
    )

    print(f"\n[5.5/6] Extracting video frame for thumbnail...")
    extract_video_thumbnail(str(output_video), str(video_thumbnail_path), timestamp_seconds=5)

    print(f"\n[6/6] Generating YouTube title, description, and metadata...")
    title_meta = generate_title_description(
        category_english,
        CATEGORIES_FILIPINO[category_english],
        phrases,
        total_duration / 60,
        str(video_dir)
    )

    import json as _json
    from pathlib import Path as _Path
    meta_out = {
        "title": title_meta.get("selected_title", f"Learn Filipino: {category_english}"),
        "description": title_meta.get("description", ""),
        "tags": ["Learn Filipino", "Filipino Phrases", "Filipino", category_english, "Velocity Filipino"],
        "category_english": category_english,
        "category_filipino": CATEGORIES_FILIPINO[category_english],
        "phrases_count": len(phrases),
        "duration_seconds": total_duration,
        "duration_minutes": total_duration / 60,
        "video_path": str(output_video),
        "thumbnail_path": str(thumbnail_path),
        "phrases": phrases,
        "generated_at": datetime.now().isoformat(),
    }
    _Path("output").mkdir(exist_ok=True)
    with open(_Path("output") / "latest_video.json", "w", encoding="utf-8") as f:
        _json.dump(meta_out, f, indent=2, ensure_ascii=False)
    with open(_Path("output") / "latest_upload_info.json", "w", encoding="utf-8") as f:
        _json.dump({"title": meta_out["title"], "description": meta_out["description"],
                     "category": category_english, "phrases_count": len(phrases)}, f, indent=2)

    print(f"\n{'='*80}")
    print(f"LONG-FORM VIDEO COMPLETE!")
    print(f"  {video_dir}")
    print(f"  {output_video.name}")
    print(f"  thumbnail.jpg (generated)")
    print(f"  {video_thumbnail_path.name} (from video)")
    print(f"  youtube_upload_info.txt (title + description + tags)")
    print(f"  Duration: {total_duration/60:.2f} minutes")
    print(f"  Phrases: {len(phrases)}")
    print(f"  Branding: Velocity Filipino")
    print(f"  Format: 16:9 (1920x1080)")
    print(f"{'='*80}\n")

    return meta_out


def generate_multiple_longform(count: int = 1, target_phrases: int = None):
    print(f"\nGenerating {count} long-form video(s)...")
    print("="*80)
    for i in range(count):
        print(f"\n{'='*80}")
        print(f"VIDEO {i+1}/{count}")
        print("="*80)
        generate_longform_video(target_phrases=target_phrases)
    print("\n" + "="*80)
    print(f"ALL {count} LONG-FORM VIDEOS COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Velocity Filipino YouTube Long-form Video Generator")
    parser.add_argument("--phrases", type=int, default=TARGET_PHRASES, help="Number of phrases to generate")
    parser.add_argument("--category", type=str, default=None, help="Specific category to generate")
    args = parser.parse_args()

    print("\n" + "="*80)
    print("VELOCITY FILIPINO - YOUTUBE LONG-FORM AUTOMATION")
    print("="*80)
    print("\nFEATURES:")
    print("  16:9 format (1920x1080) for YouTube long-form")
    print(f"  Target {args.phrases} phrases (~{args.phrases * 5.5 / 60:.1f} minute video)")
    print("  Light Theme (Cream background, dark/light purple + peach containers)")
    print("  Natural pauses with commas (non-robotic TTS)")
    print("  Perfect audio-video synchronization")
    print("  NEVER repeats phrases (permanent history tracking)")
    print(f"\nAVAILABLE CATEGORIES ({len(CATEGORIES_ENGLISH)} total):")
    for i, cat in enumerate(CATEGORIES_ENGLISH, 1):
        print(f"   {i:2d}. {cat} ({CATEGORIES_FILIPINO[cat]})")
    print(f"\nVIDEO SPECIFICATIONS:")
    print(f"  Resolution: {VIDEO_WIDTH}x{VIDEO_HEIGHT} (16:9)")
    print(f"  Frame Rate: {FPS} FPS")
    print(f"  Target Phrases: {args.phrases}")
    print(f"  Estimated Duration: ~{args.phrases * 5.5 / 60:.1f} minutes")
    print(f"  Phrase History: PERMANENT (never deletes)")
    print("="*80)

    generate_longform_video(category_english=args.category, target_phrases=args.phrases)
