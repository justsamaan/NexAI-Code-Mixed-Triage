"""
Conservative normalization and language identification for code-mixed text.
Preserves raw text immutably while deriving clean tokens for ML and entity extraction.
Supports Latin-script Hinglish (Hindi-English) and Tanglish (Tamil-English).
"""

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

# Common Latin-script Hindi marker tokens (strictly vernacular Hindi markers, excluding shared English loanwords)
HINGLISH_LEXICON: Set[str] = {
    "nahi", "nahin", "nhi", "mat", "kya", "kyu", "kyun", "kaise", "kab", "kaha",
    "kahan", "mera", "meri", "mere", "apna", "apni", "apne", "aap", "tum", "hum",
    "karo", "kardo", "kijiye", "karunga", "karungi", "ho", "hai", "hain", "tha",
    "thi", "thay", "thein", "hoga", "hogi", "chahiye", "paisa", "paise", "rupaye",
    "wapas", "bhejo", "aaya", "aayi", "pahuncha", "pahunchi", "kharab", "bekar",
    "jaldi", "turant", "abhi", "baad", "mein", "pe", "par", "se", "ko", "aur",
    "ya", "lekin", "magar", "yaar", "madad", "madath", "shukriya", "dhanyawad",
    "dikkat", "pareshani", "kaat", "kata", "kaam", "chalu", "band", "ruk",
    "gaya", "gayi", "milega", "dekh", "bolo", "batao", "samajh", "bhejiye", "karna"
}

# Common Latin-script Tamil marker tokens (strictly vernacular Tamil markers, excluding shared English loanwords)
TANGLISH_LEXICON: Set[str] = {
    "illa", "illai", "ila", "vendam", "vendaam", "koodathu", "enna", "ethu",
    "eppadi", "eppo", "engu", "enge", "enga", "ennoda", "enoda", "unga", "ungala",
    "naan", "neenga", "namma", "pannunga", "pannu", "seyyunga", "irukku", "iruku",
    "irukanga", "aachu", "aayiduchu", "varala", "varum", "kedaikala", "kidaikala",
    "venum", "kaasu", "panam", "thirumba", "anupu", "anupunga", "vandhuchu",
    "vandhadhu", "seeram", "seekiram", "ippo", "udane", "aprom", "la", "ku",
    "le", "oda", "aana", "aanal", "ana", "thala", "nanba",
    "thappu", "vela", "mudiyala", "aagala", "podhum", "pochu",
    "kudunga", "pathu", "sollunga", "puriyala", "romba", "konjam"
}

# Negation tokens across languages (critical to preserve semantic polarity)
NEGATION_TOKENS: Set[str] = {
    "no", "not", "never", "none", "neither", "nor", "nothing", "nowhere", "hardly",
    "nahi", "nahin", "nhi", "mat", "na", "bina", "ghanta",
    "illa", "illai", "ila", "vendam", "vendaam", "koodathu", "aagathu", "mudiyadhu", "mudiyala"
}

# Regular expressions for entity preservation
ORDER_ID_PATTERN = re.compile(r"(?i)\b(?:order|ord|ref|invoice|inv|id|ticket)[\s#:-]*([a-z0-9_-]{4,20})\b")
AMOUNT_PATTERN = re.compile(r"(?i)(?:rs\.?|inr|₹|\$)\s*([0-9]+(?:,[0-9]{3})*(?:\.[0-9]{1,2})?)|([0-9]+(?:,[0-9]{3})*(?:\.[0-9]{1,2})?)\s*(?:rs\.?|inr|rupees|bucks)")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
PHONE_PATTERN = re.compile(r"\b(?:\+?91[\s-]?)?[6789]\d{9}\b")

@dataclass(frozen=True)
class NormalizedText:
    """Immutable data container preserving raw text and derived representations."""
    raw_text: str
    cleaned_text: str
    tokens: List[str]
    language_detected: str
    language_confidence: float
    hinglish_score: float
    tanglish_score: float
    english_score: float
    negations_found: List[str]
    entities: Dict[str, List[str]]
    character_count: int
    word_count: int


def detect_language(tokens: List[str]) -> Tuple[str, float, float, float, float]:
    """
    Detects whether text is Hinglish, Tanglish, English, or Other using token overlap
    and code-mixed morphological markers.
    Returns: (detected_lang, confidence, hinglish_score, tanglish_score, english_score)
    """
    if not tokens:
        return ("other", 0.0, 0.0, 0.0, 0.0)

    total_tokens = len(tokens)
    hinglish_matches = sum(1 for t in tokens if t in HINGLISH_LEXICON)
    tanglish_matches = sum(1 for t in tokens if t in TANGLISH_LEXICON)

    # Heuristic ratio
    h_ratio = hinglish_matches / total_tokens
    t_ratio = tanglish_matches / total_tokens

    # Check for suffix cues in Tanglish (e.g. -la, -ku, -oda, -um, -nga)
    tanglish_suffixes = sum(1 for t in tokens if len(t) > 4 and (t.endswith("nga") or t.endswith("aachu") or t.endswith("aagala")))
    t_ratio += (tanglish_suffixes * 0.1)

    # Check for suffix cues in Hinglish (e.g. -kar, -wala, -gaya, -raha, -rahi)
    hinglish_suffixes = sum(1 for t in tokens if len(t) > 4 and (t.endswith("gaya") or t.endswith("raha") or t.endswith("wala") or t.endswith("karo")))
    h_ratio += (hinglish_suffixes * 0.1)

    # English baseline
    eng_ratio = max(0.0, 1.0 - (h_ratio + t_ratio))

    if h_ratio >= 0.12 and h_ratio > t_ratio:
        conf = min(0.99, 0.5 + h_ratio)
        return ("hinglish", round(conf, 3), round(h_ratio, 3), round(t_ratio, 3), round(eng_ratio, 3))
    elif t_ratio >= 0.10 and t_ratio > h_ratio:
        conf = min(0.99, 0.5 + t_ratio)
        return ("tanglish", round(conf, 3), round(h_ratio, 3), round(t_ratio, 3), round(eng_ratio, 3))
    elif hinglish_matches == 0 and tanglish_matches == 0:
        return ("english", 0.90, 0.0, 0.0, 1.0)
    else:
        # Mixed or low margin
        if h_ratio > t_ratio:
            return ("hinglish", 0.60, round(h_ratio, 3), round(t_ratio, 3), round(eng_ratio, 3))
        elif t_ratio > h_ratio:
            return ("tanglish", 0.60, round(h_ratio, 3), round(t_ratio, 3), round(eng_ratio, 3))
        return ("english", 0.70, round(h_ratio, 3), round(t_ratio, 3), round(eng_ratio, 3))


def extract_entities(text: str) -> Dict[str, List[str]]:
    """Extracts explicit identifiers, monetary figures, emails, and phone numbers."""
    entities: Dict[str, List[str]] = {
        "order_ids": [],
        "amounts": [],
        "emails": [],
        "phones": []
    }

    # Order IDs
    for match in ORDER_ID_PATTERN.finditer(text):
        oid = match.group(1).strip()
        if oid and oid.upper() not in ["THE", "THIS", "MY", "PLEASE"]:
            entities["order_ids"].append(oid)

    # Amounts
    for match in AMOUNT_PATTERN.finditer(text):
        amt = match.group(1) or match.group(2)
        if amt:
            entities["amounts"].append(amt.replace(",", ""))

    # Emails & Phones
    entities["emails"] = EMAIL_PATTERN.findall(text)
    entities["phones"] = PHONE_PATTERN.findall(text)

    return entities


def normalize_message(raw_text: str, language_hint: Optional[str] = None) -> NormalizedText:
    """
    Conservative normalizer:
    1. Preserves raw text exactly.
    2. Strips harmful control characters while retaining standard whitespace.
    3. Normalizes Unicode to NFKC.
    4. Identifies negation tokens.
    5. Extracts structured entities.
    6. Produces clean lower-case alphanumeric tokens for classification.
    """
    if raw_text is None:
        raw_text = ""

    # Normalize unicode to NFKC
    nfkc_text = unicodedata.normalize("NFKC", str(raw_text))

    # Clean whitespace conservatively (no multiline stripping that breaks context)
    cleaned_text = re.sub(r"[\r\n\t]+", " ", nfkc_text)
    cleaned_text = re.sub(r" +", " ", cleaned_text).strip()

    # Tokenize preserving word characters and contractions
    # Lowercase for lexical matching
    raw_tokens = re.findall(r"\b[a-zA-Z0-9_\'-]+\b", cleaned_text.lower())

    # Detect negations
    negations = [t for t in raw_tokens if t in NEGATION_TOKENS]

    # Detect language
    det_lang, conf, h_score, t_score, e_score = detect_language(raw_tokens)

    # Override language if user explicitly supplied hint (and not 'auto')
    if language_hint and language_hint.lower() in ("hinglish", "tanglish", "english"):
        final_lang = language_hint.lower()
        conf = max(conf, 0.85)
    else:
        final_lang = det_lang

    entities = extract_entities(raw_text)

    return NormalizedText(
        raw_text=raw_text,
        cleaned_text=cleaned_text,
        tokens=raw_tokens,
        language_detected=final_lang,
        language_confidence=conf,
        hinglish_score=h_score,
        tanglish_score=t_score,
        english_score=e_score,
        negations_found=negations,
        entities=entities,
        character_count=len(raw_text),
        word_count=len(raw_tokens)
    )
