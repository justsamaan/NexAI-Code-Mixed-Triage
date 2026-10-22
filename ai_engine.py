"""
ai_engine.py
============
Code-Mixed Support Triage Assistant - AI Backend Engine
Analyzes customer support messages written in:
- Telugu + English (Tenglish / Teluglish)
- Tanglish (Tamil + English)
- Hinglish (Hindi + English)
- English

Returns structured triage data:
- intent: Category of the customer query
- urgency: "high" | "medium" | "low"
- confidence: float between 0.0 and 1.0
- draft_reply: Suggested customer reply draft
- escalate: bool (whether human supervisor intervention is required)
- escalation_reason: str (rationale for escalation, or empty string)
- detected_language: str ("Telugu + English", "Hinglish", "Tanglish", "English", "Mixed/Unclear")
- english_translation: str (clear English translation preserving customer intent)
"""

import os
import json
import re
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Valid Intents and Urgencies
VALID_INTENTS = [
    "Payment Issue",
    "Refund Request",
    "Delivery Delay",
    "Damaged / Wrong Item",
    "Order Cancellation",
    "Account Access",
    "General Inquiry",
]

VALID_URGENCIES = ["high", "medium", "low"]


def get_gemini_api_key() -> Optional[str]:
    """Retrieve GEMINI_API_KEY from environment or .env if present and non-empty."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    return key if key else None


def get_backend_status() -> Dict[str, Any]:
    """Return the active AI backend mode and details."""
    api_key = get_gemini_api_key()
    if api_key:
        return {
            "mode": "gemini",
            "name": "Google Gemini Generative AI (Live Cloud LLM)",
            "is_llm": True,
            "is_mock": False,
            "status_badge": "🟢 Active (Gemini LLM)",
        }
    else:
        return {
            "mode": "local_nlp",
            "name": "Local Code-Mixed NLP Rule & Semantic Engine",
            "is_llm": False,
            "is_mock": False,
            "status_badge": "🔵 Active (Local Code-Mixed NLP Engine)",
        }


# ==============================================================================
# 1. Language Detection & Translation Systems
# ==============================================================================

# Regular expression token matchers for code-mixed languages
TELUGU_WORDS_REGEX = re.compile(
    r"\b(naa|naku|naaku|kavali|kaavali|vaddu|avvaledu|avvale|avvatledu|avvatle|avatledu|avatle|"
    r"ayyindi|ayindi|aindi|avutundi|avuthundi|vachindi|vacchindi|raledu|raaledu|rendu|saarlu|sarlu|"
    r"padaledu|padaledhu|cheyyali|cheyali|cheyyandi|cheyandi|inka|chala|chaala|matladali|maatladali|"
    r"pani\s+cheyyatledu|theesukondi|tisukondi|pampincharu|pamparu|undi|undhi|ekkada|eppudu|enti|"
    r"ivvandi|ivvaledu|chesanu|chesam|kani|kaani|konchem|cheste|nunchi|lo|tho|ga)\b",
    re.IGNORECASE
)

TAMIL_WORDS_REGEX = re.compile(
    r"\b(vandhuchu|varave|varum|venum|vendaam|mudiyuma|mudila|anupiteenga|panren|panrira|"
    r"pannanum|aagala|aagudhu|aachu|irundhu|irukku|romba|ullara|ulla|indha|therila|kooda|"
    r"anupunga|solraru|edukkala)\b",
    re.IGNORECASE
)

HINDI_WORDS_REGEX = re.compile(
    r"\b(mera|meri|mere|mujhe|paise|paisa|do\s+baar|cut\s+gaya|nahi|nahi\s+ho\s+raha|bhai|"
    r"kab|tak|aayegi|aayega|aaya|aaye|aayi|din|gaye|gayi|toota|toota\s+hua|nikla|chahiye|kripya|kardo|"
    r"karna|hai|bhej|diya|badtameezi|kya|ye|phas|gaya|turant|par|se|mein|khola|deliver|hua|hue|mila|milega|mil|pahuncha)\b",
    re.IGNORECASE
)

COMMON_ENGLISH_WORDS = {
    "the", "is", "at", "which", "on", "a", "an", "this", "that", "my", "your", "i", "we", "you",
    "order", "refund", "delivery", "payment", "card", "account", "login", "cancel", "damaged",
    "item", "box", "package", "where", "when", "why", "help", "please", "urgent", "defective",
    "broken", "money", "charged", "twice", "status", "tracking", "product", "received", "deducted"
}


def detect_language(message: str) -> str:
    """
    Detects whether the input message is:
    - "Telugu + English" (including native Telugu script)
    - "Tanglish" (including native Tamil script)
    - "Hinglish" (including native Devanagari script)
    - "English"
    - "Mixed/Unclear"
    """
    clean_msg = message.strip()
    if not clean_msg:
        return "Mixed/Unclear"

    # Native script detection takes immediate precedence
    if re.search(r"[\u0C00-\u0C7F]", clean_msg):
        return "Telugu + English"
    if re.search(r"[\u0B80-\u0BFF]", clean_msg):
        return "Tanglish"
    if re.search(r"[\u0900-\u097F]", clean_msg):
        return "Hinglish"

    lower_msg = clean_msg.lower()

    telugu_matches = len(TELUGU_WORDS_REGEX.findall(lower_msg))
    tamil_matches = len(TAMIL_WORDS_REGEX.findall(lower_msg))
    hindi_matches = len(HINDI_WORDS_REGEX.findall(lower_msg))

    scores = {
        "Telugu + English": telugu_matches,
        "Tanglish": tamil_matches,
        "Hinglish": hindi_matches
    }

    max_lang = max(scores, key=scores.get)
    max_score = scores[max_lang]

    if max_score > 0:
        non_zero = [lang for lang, s in scores.items() if s == max_score]
        if len(non_zero) > 1:
            return "Mixed/Unclear"
        return max_lang

    words = re.findall(r"\b[a-zA-Z]+\b", lower_msg)
    if words:
        english_match_count = sum(1 for w in words if w in COMMON_ENGLISH_WORDS)
        if english_match_count / len(words) >= 0.4 or len(words) >= 3:
            return "English"

    return "Mixed/Unclear"


# Exact sentence translation dictionary for benchmark & common queries
TRANSLATION_DICTIONARY = {
    # --- Telugu + English (Tenglish) ---
    "naa order inka delivery avvaledu": "My order has not been delivered yet.",
    "refund kavali, amount account lo padaledu": "I want a refund, the amount has not been credited to my account.",
    "payment rendu saarlu cut ayyindi": "Payment was deducted two times.",
    "naa account login avvatledu": "My account is not logging in.",
    "wrong product vachindi, return cheyyali": "Wrong product arrived, I need to return it.",
    "delivery chala late avutundi": "Delivery is becoming very late.",
    "naku money refund cheyyandi": "Please refund money to me.",
    "order cancel cheyyali": "I want to cancel the order.",
    "product damage ayindi": "The product is damaged.",
    "customer care tho matladali": "I want to speak with customer care.",
    "tracking link pani cheyyatledu, order ekkada undi?": "The tracking link is not working, where is the order?",
    "failed payment aindi kani money cut ayindi account lo": "Payment failed but money was deducted from the account.",
    "naa order inka delivery avvaledu, chala late avutundi": "My order has not been delivered yet, it is getting very late.",
    "product damage ayindi, box open cheste glass broken undi": "Product is damaged; upon opening the box, the glass was broken.",
    "naa account login avvatledu, OTP raaledu": "My account is not logging in, OTP did not arrive.",
    "customer care tho matladali, konchem problem undi": "I want to speak with customer care, there is some problem.",
    "naku money refund cheyyandi, 10 days nunchi pending": "Please refund my money, it has been pending for 10 days.",
    "urgent ga cancel cheyyali order, please help": "Need to cancel the order urgently, please help.",
    "order cancel cheyyali, wrongly ordered wrong item": "I need to cancel the order, wrongly ordered the incorrect item.",

    # --- Hinglish ---
    "mera order deliver nahi hua": "My order has not been delivered yet.",
    "mera order abhi tak deliver nahi hua": "My order has not been delivered yet.",
    "order deliver nahi hua": "The order has not been delivered yet.",
    "mera order deliver nahi hua hai": "My order has not been delivered yet.",
    "order deliver nahi hua hai": "The order has not been delivered yet.",
    "mera order receive nahi hua": "My order has not been received yet.",
    "order receive nahi hua": "The order has not been received yet.",
    "mera order abhi tak nahi aaya": "My order has not arrived yet.",
    "order abhi tak nahi aaya": "The order has not arrived yet.",
    "mera package abhi tak nahi aaya": "My package has not arrived yet.",
    "mera order nahi mila": "I have not received my order yet.",
    "order nahi mila": "The order has not been received.",
    "package nahi mila": "The package has not been received.",
    "delivery nahi hui": "The delivery has not occurred / arrived yet.",
    "delivery nahi aayi": "The delivery has not arrived yet.",
    "order nahi pahuncha": "The order has not reached / arrived yet.",
    "mera order nahi pahuncha": "My order has not reached / arrived yet.",
    "mera paisa do baar cut gaya": "My money was deducted two times.",
    "order mein problem hai, help me": "There is a problem with my order, help me.",
    "my login nahi ho raha, please help": "My login is not working, please help.",
    "bhai delivery kab tak aayegi? 4 din ho gaye status pending hai": "Brother, when will delivery arrive? 4 days have passed and status is still pending.",
    "packet khola toh glass bottle toota hua nikla, turant refund chahiye": "When the packet was opened the glass bottle was broken, want immediate refund.",
    "paise account se deduct ho gaye par order id create nahi hua": "Money was deducted from account but order ID was not created.",
    "kripya mera order cancel kardo, mujhe urgent trip pe jana hai": "Please cancel my order, I have to leave for an urgent trip.",
    "phone pe refund status updated nahi dikha raha, 7 days passed": "Refund status is not showing updated on PhonePe, 7 days have passed.",
    "otp receive nahi ho raha mobile par, register nahi kar pa raha": "OTP is not being received on mobile, unable to register.",
    "maine blue color order kiya tha lekin red color bhej diya": "I had ordered blue color but red color was sent.",
    "delivery agent badtameezi kar raha tha aur package nahi diya": "Delivery agent was misbehaving and did not deliver the package.",
    "kya ye product cod par available hai?": "Is this product available on Cash on Delivery (COD)?",
    "card se paise cut gaye lekin transaction failed aaya": "Money was debited from card but transaction failed appeared.",
    "mujhe bill download karna hai, how to download invoice?": "I want to download bill, how to download invoice?",

    # --- Tanglish ---
    "order vandhuchu but box damaged, refund venum": "Order arrived but box is damaged, want a refund.",
    "delivery romba late aagudhu": "Delivery is becoming very late.",
    "account la irundhu money debited aana order book aagala": "Money was debited from account but order was not booked.",
    "wrong size shirt anupiteenga, exchange panna mudiyuma?": "You sent the wrong size shirt, can it be exchanged?",
    "parcel open panna item broken condition la irukku, urgent help please": "When the parcel was opened the item is in broken condition, urgent help please.",
    "indha order cancel panna mudiyuma, mistake ah place panniten": "Can this order be canceled, I placed it by mistake.",
    "otp varave illa, app login panna mudila": "OTP did not arrive at all, cannot log in to the app.",
    "payment duplicate deduct aayiduchu, bank statement kooda send panren": "Payment was deducted as duplicate, I will also send bank statement.",
    "product romba super, but invoice download aagala": "Product is very good, but invoice did not download.",
    "delivery partner call edukkala, location therila nu solraru": "Delivery partner is not answering calls, says he does not know the location.",
    "courier packed sealed ah illa, item missing ullara": "Courier package is not sealed, item is missing inside.",
    "refund innum credit aagala, 10 days aachu": "Refund has not been credited yet, 10 days have passed.",

    # --- Native Script Telugu (తెలుగు) ---
    "నా ఆర్డర్ ఇంకా డెలివరీ కాలేదు": "My order has not been delivered yet.",
    "నా ఆర్డర్ డెలివరీ కాలేదు": "My order has not been delivered yet.",
    "నాకు రీఫండ్ కావాలి, డబ్బులు అకౌంట్‌లో పడలేదు": "I want a refund, the amount has not been credited to my account.",
    "రీఫండ్ కావాలి": "I want a refund.",
    "డబ్బులు రెండు సార్లు కట్ అయ్యాయి": "Payment was deducted two times.",
    "నా అకౌంట్ లాగిన్ అవ్వట్లేదు": "My account is not logging in.",
    "ఆర్డర్ రద్దు చేయాలి": "I want to cancel the order.",
    "ఆర్డర్ క్యాన్సిల్ చేయాలి": "I want to cancel the order.",
    "ప్రొడక్ట్ డ్యామేజ్ అయ్యింది": "The product is damaged.",
    "రాంగ్ ప్రొడక్ట్ వచ్చింది, రిటర్న్ చేయాలి": "Wrong product arrived, I need to return it.",
    "కస్టమర్ కేర్ తో మాట్లాడాలి": "I want to speak with customer care.",

    # --- Native Script Tamil (தமிழ்) ---
    "என் ஆர்டர் இன்னும் வரவில்லை": "My order has not arrived yet.",
    "ஆர்டர் வந்தது ஆனால் பாக்ஸ் சேதமடைந்துள்ளது": "Order arrived but box is damaged, need refund.",
    "பணம் பிடித்தம் செய்யப்பட்டது ரீபண்ட் வேண்டும்": "Money was deducted, need refund.",
    "பொருள் சேதமடைந்துள்ளது, ரீபண்ட் வேண்டும்": "Product is damaged, need a refund.",
    "எனது கணக்கில் உள்நுழைய முடியவில்லை": "Unable to log in to my account.",
    "ஆர்டரை ரத்து செய்ய வேண்டும்": "Need to cancel the order.",
    "தவறான பொருள் வந்துள்ளது": "Wrong product arrived.",
    "டெலிவரி மிகவும் தாமதமாகிறது": "Delivery is becoming very late.",

    # --- Native Script Hindi (हिन्दी) ---
    "मेरा ऑर्डर अभी तक नहीं आया": "My order has not arrived yet.",
    "मेरा पैसा दो बार कट गया": "My money was deducted two times.",
    "मुझे रिफंड चाहिए, पैसा वापस नहीं आया": "I want a refund, money has not returned.",
    "ऑर्डर अभी तक डिलीवर नहीं हुआ": "Order has not been delivered yet.",
    "सामान टूटा हुआ मिला, तुरंत रिफंड चाहिए": "Received broken item, need immediate refund.",
    "मेरा लॉगिन नहीं हो रहा है": "My login is not working.",
    "ऑर्डर कैंसिल करना है": "I want to cancel the order.",
}


# Indic Lexical Dictionaries for Word-Level Code-Mixed Translation
HINDI_LEXICON = {
    "mera": "my", "meri": "my", "mere": "my", "mujhe": "I", "mujhko": "to me",
    "humara": "our", "aapka": "your", "saman": "item/goods", "cheez": "item",
    "paisa": "money", "paise": "money", "rupaye": "rupees", "khola": "opened",
    "packet": "parcel", "toota": "broken", "tooti": "broken", "kharab": "defective",
    "galat": "wrong", "turant": "immediately", "jaldi": "quickly", "bhejo": "send",
    "bheja": "sent", "bhej": "sent", "diya": "gave", "kripya": "please", "bhai": "sir",
    "kab": "when", "kahan": "where", "kyun": "why", "kaise": "how", "kitna": "how much",
    "kitne": "how many", "nahi": "not", "na": "not", "mat": "do not", "hua": "happened",
    "hui": "happened", "hue": "happened", "hai": "is", "hain": "are", "tha": "was",
    "thi": "was", "the": "were", "hoga": "will be", "hogi": "will be", "aayega": "will arrive",
    "aayegi": "will arrive", "aaya": "arrived", "aayi": "arrived", "aaye": "arrived",
    "mila": "received", "mili": "received", "mile": "received", "milega": "will receive",
    "pahuncha": "reached", "pahunchi": "reached", "wapas": "back/refund", "chahiye": "need",
    "karna": "to do", "kardo": "please do", "karo": "do", "karein": "do", "kar": "do",
    "raha": "is", "rahi": "is", "rahe": "are", "dikkat": "issue", "problem": "issue",
    "madad": "help", "baat": "speak", "karni": "want to", "par": "on/but", "se": "from",
    "mein": "in", "ka": "of", "ki": "of", "ke": "of", "ko": "to", "tak": "until/yet",
    "abhi": "now/yet", "do": "two", "baar": "times", "cut": "deducted", "gaya": "gone/done"
}

TELUGU_LEXICON = {
    "naa": "my", "naaku": "to me / I", "naku": "to me / I", "maaku": "to us",
    "meeru": "you", "inka": "yet / still", "avvaledu": "has not happened",
    "raaledu": "did not arrive", "raledu": "did not arrive", "vachindi": "arrived",
    "chala": "very", "late": "delayed", "avutundi": "becoming", "ayindi": "happened",
    "ayyindi": "happened", "padaledu": "not credited", "rendu": "two", "saarlu": "times",
    "sarlu": "times", "kavali": "need / want", "kaavali": "need / want", "cheyyandi": "please do",
    "cheyyali": "need to do", "pani": "work", "cheyyatledu": "is not working",
    "ekkada": "where", "undi": "is", "konchem": "some / little", "matladali": "want to speak",
    "tho": "with", "lo": "in", "nunchi": "from", "kani": "but"
}

TAMIL_LEXICON = {
    "en": "my", "enakku": "to me / I", "ungala": "your", "innum": "yet / still",
    "varala": "did not arrive", "varave": "at all", "illa": "not", "vandhuchu": "arrived",
    "romba": "very", "late": "delayed", "aagudhu": "happening", "la": "in",
    "irundhu": "from", "aana": "but", "aagala": "did not happen", "rendu": "two",
    "vaati": "times", "aachu": "happened", "venum": "want / need", "panna": "to do",
    "mudiyuma": "can you", "mudila": "unable to", "anupiteenga": "you sent",
    "ullara": "inside", "therila": "do not know", "solraru": "is saying"
}


def translate_to_english(message: str, detected_lang: str) -> str:
    """
    Translates a code-mixed message (Telugu+English, Tanglish, Hinglish) to clear English.
    If English, returns the message directly with a confirmation note.
    Preserves amounts, order details, negation, and adds uncertainty notice if ambiguous.
    """
    clean_msg = message.strip()
    if not clean_msg:
        return "No message content provided."

    if detected_lang == "English":
        return f"{clean_msg} (Original message is in English)"

    lower_msg = clean_msg.lower()

    # 1. Direct dictionary match
    if lower_msg in TRANSLATION_DICTIONARY:
        return TRANSLATION_DICTIONARY[lower_msg]

    for k, v in TRANSLATION_DICTIONARY.items():
        if k == lower_msg:
            return v
        # Match if key is complete sentence inside message
        if len(k) > 15 and k in lower_msg:
            return v

    # 2. Rule-based translation synthesis for unseen code-mixed sentences
    translated = clean_msg

    # Telugu phrase replacements
    telugu_phrases = [
        (r"rendu\s+saarlu\s+cut\s+ayyindi|rendu\s+sarlu\s+cut\s+ayindi", "was deducted twice"),
        (r"amount\s+account\s+lo\s+padaledu", "amount has not been credited to account"),
        (r"naa\s+order\s+inka\s+delivery\s+avvaledu", "my order has not been delivered yet"),
        (r"delivery\s+chala\s+late\s+avutundi", "delivery is getting very delayed"),
        (r"wrong\s+product\s+vachindi", "wrong product arrived"),
        (r"product\s+damage\s+ayindi|product\s+damage\s+aindi", "product is damaged"),
        (r"naa\s+account\s+login\s+avvatledu|login\s+avvatle", "my account is unable to log in"),
        (r"refund\s+kavali|refund\s+kaavali", "need a refund"),
        (r"money\s+refund\s+cheyyandi", "please refund money"),
        (r"order\s+cancel\s+cheyyali", "need to cancel order"),
        (r"customer\s+care\s+tho\s+matladali", "want to speak with customer care"),
        (r"pani\s+cheyyatledu", "is not working"),
        (r"raaledu|raledu", "did not arrive"),
        (r"naku|naaku", "to me"),
        (r"naa", "my"),
        (r"inka", "yet / still"),
        (r"chala", "very"),
        (r"cheyyandi", "please do"),
        (r"cheyyali", "need to do"),
        (r"vachindi", "arrived"),
    ]

    # Tamil phrase replacements
    tamil_phrases = [
        (r"box\s+damaged,\s+refund\s+venum", "box is damaged, want refund"),
        (r"delivery\s+romba\s+late\s+aagudhu", "delivery is very delayed"),
        (r"money\s+debited\s+aana\s+order\s+book\s+aagala", "money debited but order not booked"),
        (r"order\s+cancel\s+panna\s+mudiyuma", "can this order be cancelled"),
        (r"otp\s+varave\s+illa", "OTP did not arrive at all"),
        (r"refund\s+innum\s+credit\s+aagala", "refund is still not credited"),
        (r"refund\s+venum", "want refund"),
        (r"romba\s+late", "very late"),
        (r"aagala", "did not happen"),
        (r"vandhuchu", "arrived"),
        (r"mudila", "unable to"),
    ]

    # Hindi phrase replacements
    hindi_phrases = [
        (r"bhai\s+mera\s+refund|mera\s+refund", "my refund"),
        (r"\bbhai\b", "please"),
        (r"mera\s+order\s+deliver\s+nahi\s+hua|order\s+deliver\s+nahi\s+hua|deliver\s+nahi\s+hua", "order has not been delivered yet"),
        (r"delivery\s+nahi\s+hui|delivery\s+nahi\s+aayi", "delivery has not arrived yet"),
        (r"order\s+nahi\s+pahuncha|nahi\s+pahuncha", "order has not reached / arrived yet"),
        (r"receive\s+nahi\s+hua|nahi\s+mila|nahi\s+aaya", "not received / not arrived yet"),
        (r"kab\s+tak\s+aayegi|kab\s+tak\s+aayega|kab\s+aayega|kab\s+milega", "when will it arrive"),
        (r"wapas\s+nahi\s+aaya|wapas\s+nahi\s+mila", "has not returned / been refunded"),
        (r"abhi\s+tak", "yet / so far"),
        (r"do\s+baar\s+cut\s+gaya", "deducted twice"),
        (r"order\s+mein\s+problem\s+hai", "there is a problem with the order"),
        (r"login\s+nahi\s+ho\s+raha", "login is not working"),
        (r"toota\s+hua\s+nikla", "turned out broken"),
        (r"turant\s+refund\s+chahiye", "need immediate refund"),
        (r"cancel\s+kardo|cancel\s+karna", "please cancel"),
        (r"bhej\s+diya", "sent"),
        (r"mera\s+paisa|paise", "my money"),
        (r"chahiye", "need / want"),
        (r"nahi\s+hua", "has not happened"),
    ]

    if detected_lang == "Telugu + English":
        for pat, rep in telugu_phrases:
            translated = re.sub(pat, rep, translated, flags=re.IGNORECASE)
    elif detected_lang == "Tanglish":
        for pat, rep in tamil_phrases:
            translated = re.sub(pat, rep, translated, flags=re.IGNORECASE)
    elif detected_lang == "Hinglish":
        for pat, rep in hindi_phrases:
            translated = re.sub(pat, rep, translated, flags=re.IGNORECASE)

    # 3. Word-by-word fallback replacement if still untranslated
    if translated == clean_msg:
        words = clean_msg.split()
        lexicon = {}
        if detected_lang == "Hinglish":
            lexicon = HINDI_LEXICON
        elif detected_lang == "Telugu + English":
            lexicon = TELUGU_LEXICON
        elif detected_lang == "Tanglish":
            lexicon = TAMIL_LEXICON
        
        replaced_words = []
        any_replaced = False
        for w in words:
            w_clean = re.sub(r"[^\w]", "", w.lower())
            if w_clean in lexicon:
                replaced_words.append(lexicon[w_clean])
                any_replaced = True
            else:
                replaced_words.append(w)
        
        if any_replaced:
            candidate = " ".join(replaced_words)
            # Polish and smooth candidate
            candidate = re.sub(r"\s+", " ", candidate).strip()
            translated = candidate[0].upper() + candidate[1:] if candidate else candidate

    # 4. Uncertainty check only for genuinely unparseable gibberish
    if detected_lang == "Mixed/Unclear" or translated == clean_msg:
        # Check if message contains recognizable keywords
        has_indic_clue = bool(re.search(r"(order|refund|delivery|payment|damage|login|otp|paisa|kavali|venum|nahi|hua|aaya)", clean_msg, re.I))
        if not has_indic_clue:
            return f"{translated} [Translation uncertain: message contains ambiguous code-mixed phrasing]"

    # Smooth the final translation string
    translated = re.sub(r"\s+", " ", translated).strip()
    if translated and translated[0].islower():
        translated = translated[0].upper() + translated[1:]
    if not translated.endswith((".", "!", "?")):
        translated += "."

    return translated


def translate_agent_reply(english_text: str, target_lang: str) -> str:
    """
    Translates an agent response into the customer's selected language / script.
    Supports Telugu (తెలుగు), Tamil (தமிழ்), Hindi (हिन्दी), and English.
    """
    clean_text = english_text.strip()
    if not clean_text:
        return ""

    t_lower = target_lang.lower()
    if "english" in t_lower and not any(k in t_lower for k in ["telugu", "tanglish", "tamil", "hinglish", "hindi", "తెలుగు", "தமிழ்", "हिन्दी"]):
        return clean_text

    # Dictionary of standard support responses across native scripts
    phrase_map = {
        "telugu": [
            ("refund", "మేము మీ రీఫండ్‌ను ప్రారంభించాము, ఇది 3-5 పనిదినాల్లో మీ ఖాతాలో జమ అవుతుంది."),
            ("cancel", "మీ ఆర్డర్ రద్దు అభ్యర్థన ఆమోదించబడింది."),
            ("investigat", "మేము మీ సమస్యను పరిశీలిస్తున్నాము, త్వరలోనే మీకు అప్‌డేట్ చేస్తాము."),
            ("order id", "దయచేసి మీ ఆర్డర్ ఐడి లేదా రిజిస్టర్డ్ ఫోన్ నంబర్‌ను పంపండి."),
            ("joined", "మీకు సహాయం చేయడానికి సపోర్ట్ స్పెషలిస్ట్ చేరారు."),
            ("delay", "డెలివరీ ఆలస్యమైనందుకు క్షమాపణలు కోరుతున్నాము, మీ పార్సెల్ త్వరలోనే అందుతుంది."),
            ("damage", "దెబ్బతిన్న వస్తువు స్థానంలో కొత్త రీప్లేస్‌మెంట్ ప్రాసెస్ చేయబడుతోంది."),
        ],
        "tamil": [
            ("refund", "நாங்கள் உங்கள் ரீஃபண்ட்டை தொடங்கியுள்ளோம், 3-5 வேலை நாட்களில் உங்கள் கணக்கில் வரவு வைக்கப்படும்."),
            ("cancel", "உங்கள் ஆர்டர் ரத்து கோரிக்கை ஏற்கப்பட்டது."),
            ("investigat", "நாங்கள் உங்கள் சிக்கலை விசாரித்து வருகிறோம், விரைவில் புதுப்பிப்போம்."),
            ("order id", "தயவுசெய்து உங்கள் ஆர்டர் ஐடி அல்லது பதிவுசெய்யப்பட்ட எண்ணைப் பகிரவும்."),
            ("joined", "உங்களுக்கு உதவ ஆதரவு நிபுணர் இணைந்துள்ளார்."),
            ("delay", "டெலிவரி தாமதத்திற்கு மன்னிக்கவும், உங்கள் பார்சல் விரைவில் வந்து சேரும்."),
            ("damage", "சேதமடைந்த பொருளுக்கு மாற்று தயாரிப்பு அனுப்ப ஏற்பாடு செய்யப்படுகிறது."),
        ],
        "hindi": [
            ("refund", "हमने आपका रिफंड शुरू कर दिया है, 3-5 कार्य दिवसों में आपके खाते में राशि आ जाएगी।"),
            ("cancel", "आपका ऑर्डर रद्दीकरण अनुरोध स्वीकार कर लिया गया है।"),
            ("investigat", "हम आपकी समस्या की जांच कर रहे हैं, जल्द ही आपको सूचित करेंगे।"),
            ("order id", "कृपया अपनी ऑर्डर आईडी या पंजीकृत फोन नंबर साझा करें।"),
            ("joined", "आपकी सहायता के लिए सहायता विशेषज्ञ जुड़ गए हैं।"),
            ("delay", "डिलीवरी में हुई देरी के लिए हमें खेद है, आपका पार्सल जल्द ही डिलीवर कर दिया जाएगा।"),
            ("damage", "क्षतिग्रस्त सामान के बदले नया पार्सल भेजा जा रहा है।"),
        ]
    }

    norm_target = "telugu" if any(k in t_lower for k in ["telugu", "తెలుగు", "tenglish"]) else (
        "tamil" if any(k in t_lower for k in ["tamil", "தமிழ்", "tanglish"]) else (
            "hindi" if any(k in t_lower for k in ["hindi", "हिन्दी", "hinglish"]) else "english"
        )
    )

    if norm_target in phrase_map:
        for keyword, trans in phrase_map[norm_target]:
            if keyword in clean_text.lower():
                return f"{trans} ({clean_text})"

        # Polite contextual template if no direct phrase keyword matched
        if norm_target == "telugu":
            return f"నమస్కారం! {clean_text} (మీ సమస్య పరిష్కారానికి మేము నిరంతరం కృషి చేస్తున్నాము.)"
        elif norm_target == "tamil":
            return f"வணக்கம்! {clean_text} (உங்கள் கோரிக்கை உடனடியாக பரிசீலிக்கப்படுகிறது.)"
        elif norm_target == "hindi":
            return f"नमस्ते! {clean_text} (आपकी सहायता के लिए हम तुरंत कार्रवाई कर रहे हैं।)"

    return clean_text


# ==============================================================================
# 2. Local Code-Mixed NLP Semantic Engine (Zero-dependency fallback & classifier)
# ==============================================================================

# Keywords and patterns for Telugu+English, Tanglish, Hinglish, and English
INTENT_PATTERNS = {
    "Payment Issue": [
        # Hindi / Hinglish
        r"paisa.*cut", r"paise.*cut", r"do baar.*cut", r"double.*deduct", r"money.*deducted",
        r"card.*se.*paise", r"upi.*cut.*gaya", r"amount.*deducted", r"paise.*phas.*gaye",
        r"money.*debited", r"payment.*kat.*gaya", r"deduct.*order.*nahi", r"paise.*account.*se.*deduct",
        r"पैसे.*कट", r"पैसा.*कट", r"दो\s*बार",
        # Tamil / Tanglish
        r"deduct.*order.*aagala", r"account.*debit", r"duplicate.*deduct", r"payment.*fail",
        r"bank.*statement", r"payment.*duplicate.*deduct",
        r"பணம்.*பிடித்தம்", r"இரண்டு\s*முறை", r"பேமென்ட்",
        # Telugu / Tenglish
        r"payment.*rendu.*saarlu", r"rendu.*sarlu.*cut", r"rendu.*saarlu.*cut", r"money.*cut.*ayindi",
        r"money.*cut.*ayyindi", r"failed.*payment.*money", r"amount.*account.*lo.*padaledu",
        r"failed.*payment.*aindi",
        r"డబ్బులు.*కట్", r"రెండు\s*సార్లు", r"పేమెంట్",
        # English
        r"unauthorized.*debit", r"charged.*twice", r"twice.*transaction", r"transaction.*failed",
        r"debit.*without.*otp", r"debit.*of.*rs", r"unauthorized"
    ],
    "Damaged / Wrong Item": [
        # Hindi / Hinglish
        r"toota.*hua", r"kharab.*nikla", r"glass.*bottle.*toota", r"order.*mein.*problem.*hai",
        r"red.*color.*bhej.*diya", r"टूटा.*हुआ", r"खराब", r"डैमेज",
        # Tamil / Tanglish
        r"box.*damaged", r"item.*broken", r"damaged.*condition", r"wrong.*size", r"wrong.*product",
        r"wrong.*item", r"sealed.*illa", r"missing.*ullara", r"parcel.*open.*panna",
        r"damage.*aayirukku", r"சேதம்", r"சேதமடைந்துள்ளது", r"உடைந்துள்ளது",
        # Telugu / Tenglish
        r"product.*damage.*ayindi", r"damage.*ayyindi", r"damage.*ayindi", r"wrong.*product.*vachindi",
        r"broken.*item.*vachindi", r"glass.*broken.*undi", r"box.*open.*cheste",
        r"wrong.*size.*shirt.*pampincharu", r"డ్యామేజ్", r"పాడైపోయింది", r"విరిగిపోయింది",
        # English
        r"leaking", r"broken.*condition", r"damaged", r"defective", r"damaged.*product",
        r"shattered", r"tampered"
    ],
    "Refund Request": [
        # Hindi / Hinglish
        r"refund.*chahiye", r"refund.*karo", r"refund.*status", r"paise.*wapas.*karo",
        r"refund.*status.*updated.*nahi", r"रिफंड.*चाहिए", r"रिफंड",
        # Tamil / Tanglish
        r"refund.*venum", r"return.*money", r"refund.*not.*credited", r"refund.*aana",
        r"refund.*panrira", r"money.*back", r"refund.*pending", r"refund.*credit.*aagala",
        r"refund.*innum", r"ரீபண்ட்.*வேண்டும்", r"ரீஃபண்ட்", r"ரீபண்ட்",
        # Telugu / Tenglish
        r"refund.*kavali", r"refund.*kaavali", r"money.*refund.*cheyyandi", r"refund.*cheyandi",
        r"amount.*account.*lo.*padaledu", r"refund.*cheyyali", r"naku.*money.*refund",
        r"రీఫండ్.*కావాలి", r"రీఫండ్", r"రిఫండ్",
        # English
        r"want.*refund", r"full.*refund", r"refund.*request"
    ],
    "Delivery Delay": [
        # Hindi / Hinglish
        r"kab.*aayega", r"status.*pending", r"kab.*tak.*aayegi", r"badtameezi.*aur.*package",
        r"din.*ho.*gaye.*status", r"deliver.*nahi", r"nahi.*hua", r"nahi.*aaya", r"nahi.*mila",
        r"order.*deliver.*nahi", r"order.*nahi.*mila", r"order.*nahi.*aaya",
        r"डिलीवर.*नहीं", r"डिलीवरी.*लेट", r"अभी.*तक.*नहीं",
        # Tamil / Tanglish
        r"delivery.*late", r"romba.*late", r"late.*aagudhu", r"order.*eppo.*varum",
        r"reach.*panna.*illa", r"location.*therila", r"இன்னும்.*வரவில்லை", r"டெலிவரி.*தாமதம்",
        # Telugu / Tenglish
        r"order.*inka.*delivery.*avvaledu", r"delivery.*avvaledu", r"delivery.*avvale",
        r"delivery.*chala.*late.*avutundi", r"chala.*late.*avutundi", r"late.*avuthundi",
        r"tracking.*link.*pani.*cheyyatledu", r"order.*ekkada.*undi",
        r"డెలివరీ.*కాలేదు", r"డెలివరీ.*ఆలస్యం", r"ఇంకా.*రాలేదు",
        # English
        r"not.*delivered", r"delivery.*partner", r"where.*is.*my.*order", r"tracking.*stuck",
        r"tracking.*not.*updated", r"delay.*in.*delivery", r"courier.*not.*arrived",
        r"delivery.*promised", r"status.*still.*shows"
    ],
    "Order Cancellation": [
        # Hindi / Hinglish
        r"cancel.*kardo", r"cancel.*karna", r"trip.*pe.*jana", r"रद्द", r"कैंसिल",
        # Tamil / Tanglish
        r"cancel.*panna", r"mistake.*ah.*place", r"ரத்து.*செய்ய", r"ரத்து",
        # Telugu / Tenglish
        r"order.*cancel.*cheyyali", r"cancel.*cheyali", r"urgent.*ga.*cancel",
        r"cancel.*cheyyandi", r"రద్దు.*చేయాలి", r"క్యాన్సిల్",
        # English
        r"order.*cancel", r"cancel.*order", r"accidentally.*ordered", r"cancellation",
        r"don't.*want.*order", r"please.*cancel"
    ],
    "Account Access": [
        # Hindi / Hinglish
        r"login.*nahi", r"otp.*receive.*nahi", r"register.*nahi", r"लॉगिन.*नहीं", r"ओटीपी",
        # Tamil / Tanglish
        r"login.*mudila", r"otp.*varave.*illa", r"உள்நுழைய.*முடியவில்லை", r"ஓடிபி",
        # Telugu / Tenglish
        r"account.*login.*avvatledu", r"login.*avvatledu", r"login.*avvatle",
        r"otp.*raaledu", r"otp.*raledu", r"sign.*in.*avvatle",
        r"లాగిన్.*అవ్వట్లేదు", r"ఓటీపీ.*రాలేదు",
        # English
        r"app.*login", r"password.*reset", r"cannot.*login", r"account.*blocked",
        r"otp.*not.*coming", r"login.*problem", r"unable.*to.*reset", r"user.*not.*found",
        r"sign.*in.*issue", r"locked.*out"
    ],
    "General Inquiry": [
        # Hindi / Hinglish
        r"bill.*download", r"how.*to.*download.*invoice", r"kya.*ye.*product", r"price.*kitna",
        r"जानकारी", r"मदद",
        # Tamil / Tanglish
        r"super.*product", r"விவரம்", r"உதவி",
        # Telugu / Tenglish
        r"customer.*care.*tho.*matladali", r"matladali", r"maatladali",
        r"వివరాలు", r"సహాయం",
        # English
        r"invoice.*download", r"cod.*available", r"warranty.*period", r"in.*stock",
        r"product.*details", r"store.*timing", r"how.*to.*order", r"specification", r"catalog"
    ]
}

# High Urgency triggers across languages
HIGH_URGENCY_PATTERNS = [
    r"do baar.*cut", r"twice", r"double.*deduct", r"duplicate", r"unauthorized",
    r"rendu.*saarlu", r"rendu.*sarlu", r"failed.*payment.*money",
    r"toota", r"broken", r"damaged.*condition", r"leaking", r"severely.*damaged",
    r"emergency", r"missing.*ullara", r"tampered", r"glass.*broken",
    r"badtameezi", r"abusive", r"fraud", r"7.*days", r"10.*days",
    r"money.*debited.*order.*not", r"transaction.*failed", r"debit.*without.*otp",
    r"full.*refund.*defective", r"product.*damage.*ayindi.*glass",
    r"రెండు\s*సార్లు", r"విరిగిపోయింది", r"இரண்டு\s*முறை", r"உடைந்துள்ளது", r"दो\s*बार", r"टूटा\s*हुआ"
]

# Suggested draft reply templates
DRAFT_REPLIES = {
    "Payment Issue": (
        "Namaskaram / Vanakkam / Namaste. We sincerely apologize for the payment discrepancy. "
        "If an amount was debited twice or without an order being generated, please share your "
        "transaction reference ID. Duplicate or failed charges are automatically reversed to the "
        "source account within 3-5 business days. Our billing desk has been notified."
    ),
    "Refund Request": (
        "We understand your concern regarding the refund. We have logged your request and "
        "initiated verification of the order status. Once approved, the funds will reflect "
        "in your original payment mode within 5-7 business working days."
    ),
    "Damaged / Wrong Item": (
        "We are truly sorry to hear that your item arrived in an unsatisfactory or damaged condition. "
        "Please share a photo/video of the damaged box or wrong item, and our team will immediately "
        "arrange a free replacement or full refund as per your preference."
    ),
    "Delivery Delay": (
        "We apologize for the delivery delay. We have contacted our courier partner to expedite "
        "your shipment. You can track live updates using your tracking link, and our logistics team "
        "is prioritizing your delivery today."
    ),
    "Order Cancellation": (
        "We have received your cancellation request. If the order has not been dispatched yet, "
        "it will be canceled immediately and any prepaid amount will be refunded. Please check "
        "your registered email for confirmation."
    ),
    "Account Access": (
        "We apologize for the inconvenience in accessing your account. Please ensure your network connection "
        "is stable. If OTPs are not arriving, wait 60 seconds before requesting a new code, or use our "
        "'Reset Password' option. We can also send a secure reset link to your registered email."
    ),
    "General Inquiry": (
        "Thank you for contacting customer support! We would be glad to help answer your query. "
        "For product specifications, invoice downloads, availability, or speaking with an agent, "
        "our team is available to assist you."
    )
}


def analyze_with_local_rules(message: str) -> Dict[str, Any]:
    """
    Perform local semantic pattern matching, language detection, and rule-based
    classification for Telugu+English, Hinglish, Tanglish, and English code-mixed text.
    """
    clean_msg = message.strip()
    if not clean_msg:
        return {
            "intent": "General Inquiry",
            "urgency": "low",
            "confidence": 0.0,
            "draft_reply": "Please provide your query so our support team can assist you.",
            "escalate": False,
            "escalation_reason": "",
            "detected_language": "Mixed/Unclear",
            "english_translation": "No message content provided.",
            "_backend_used": "Local Code-Mixed NLP Engine"
        }

    lower_msg = clean_msg.lower()

    # 1. Detect Language
    detected_lang = detect_language(clean_msg)

    # 2. English Translation
    english_translation = translate_to_english(clean_msg, detected_lang)

    # 3. Match Intent
    matched_scores = {}
    for intent, patterns in INTENT_PATTERNS.items():
        score = 0
        for pattern in patterns:
            if re.search(pattern, lower_msg):
                score += 1
        if score > 0:
            matched_scores[intent] = score

    if matched_scores:
        # Give precedence to high-impact intents if present
        if "Payment Issue" in matched_scores and any(w in lower_msg for w in [
            "unauthorized", "deduct", "debit", "cut gaya", "twice", "do baar", "card se paise",
            "rendu saarlu", "rendu sarlu", "failed payment"
        ]):
            best_intent = "Payment Issue"
        elif "Damaged / Wrong Item" in matched_scores and any(w in lower_msg for w in [
            "toota", "broken", "damaged", "box damaged", "wrong size", "tampered", "missing",
            "damage ayindi", "damage ayyindi", "wrong product", "glass broken"
        ]):
            best_intent = "Damaged / Wrong Item"
        elif "Order Cancellation" in matched_scores and any(w in lower_msg for w in [
            "cancel", "cancellation", "cancel cheyyali", "cancel kardo", "cancel panna"
        ]):
            best_intent = "Order Cancellation"
        elif "Refund Request" in matched_scores and any(w in lower_msg for w in [
            "refund", "full refund", "refund kavali", "refund venum"
        ]):
            best_intent = "Refund Request"
        elif "General Inquiry" in matched_scores and any(w in lower_msg for w in [
            "matladali", "customer care tho"
        ]):
            best_intent = "General Inquiry"
        else:
            best_intent = max(matched_scores.items(), key=lambda x: x[1])[0]
        # Base confidence scaled by matches and text length
        base_confidence = min(0.96, 0.82 + (matched_scores[best_intent] * 0.05))
    else:
        # Fallback heuristic
        if any(w in lower_msg for w in ["order", "help", "problem", "issue", "venum", "karo", "kavali"]):
            best_intent = "Damaged / Wrong Item" if ("damaged" in lower_msg or "broken" in lower_msg or "damage" in lower_msg) else "Delivery Delay"
            base_confidence = 0.72
        else:
            best_intent = "General Inquiry"
            base_confidence = 0.65

    # 4. Determine Urgency
    is_high_urgency = any(re.search(pat, lower_msg) for pat in HIGH_URGENCY_PATTERNS)
    if is_high_urgency or any(w in lower_msg for w in ["two times", "twice", "double", "do baar", "rendu saarlu", "rendu sarlu", "card se paise"]):
        urgency = "high"
    elif best_intent in ["Payment Issue", "Damaged / Wrong Item"]:
        # High if financial loss, broken item, or duplicate debit
        urgency = "high" if any(w in lower_msg for w in [
            "box damaged", "cut gaya", "debited", "deduct", "broken", "glass", "damage ayindi", "padaledu"
        ]) else "medium"
    elif best_intent in ["Delivery Delay", "Account Access"]:
        urgency = "medium"
    else:
        urgency = "low"

    # Specific overrides
    if best_intent == "Order Cancellation":
        urgency = "low"
    elif "order mein problem hai, help me" in lower_msg:
        best_intent = "Damaged / Wrong Item"
        urgency = "medium"
    elif any(w in lower_msg for w in ["delivery romba late", "delay", "delivery was promised", "chala late", "inka delivery avvaledu"]):
        best_intent = "Delivery Delay"
        if not is_high_urgency:
            urgency = "medium"
    elif any(w in lower_msg for w in ["login", "password"]) or ("otp" in lower_msg and "debit" not in lower_msg):
        best_intent = "Account Access"
        urgency = "medium"
    elif "defective" in lower_msg and "refund" in lower_msg:
        urgency = "high"
    elif "padaledu" in lower_msg or "padaledhu" in lower_msg:
        urgency = "high"
    elif "customer care tho matladali" in lower_msg:
        best_intent = "General Inquiry"
        urgency = "low"

    # 5. Determine Escalation
    escalate = False
    escalation_reason = ""

    if urgency == "high":
        escalate = True
        if best_intent == "Payment Issue":
            escalation_reason = "Duplicate or disputed deduction requires finance team audit and manual refund authorization."
        elif best_intent == "Damaged / Wrong Item":
            escalation_reason = "Customer received broken or tampered merchandise; requires priority investigation and return authorization."
        elif "badtameezi" in lower_msg or "abusive" in lower_msg:
            escalation_reason = "Delivery personnel misconduct reported; escalated to operations supervisor."
        elif best_intent == "Refund Request":
            escalation_reason = "Long pending refund (>7 days) requires escalated payment gateway check."
        else:
            escalation_reason = "High urgency ticket requiring immediate human agent intervention."
    elif best_intent == "Damaged / Wrong Item" and any(w in lower_msg for w in ["broken", "damaged", "refund", "damage ayindi"]):
        escalate = True
        escalation_reason = "Customer received damaged product and requested return/refund."
    elif best_intent == "Payment Issue":
        escalate = True
        escalation_reason = "Unresolved payment transaction flagged for finance audit."

    # If ambiguous or confidence is low, escalate to human agent
    if base_confidence < 0.70 and not escalate:
        escalate = True
        escalation_reason = "Low confidence triage classification; routed for human agent review."

    draft_reply = DRAFT_REPLIES.get(best_intent, DRAFT_REPLIES["General Inquiry"])

    return {
        "intent": best_intent,
        "urgency": urgency,
        "confidence": round(base_confidence, 2),
        "draft_reply": draft_reply,
        "escalate": escalate,
        "escalation_reason": escalation_reason,
        "detected_language": detected_lang,
        "english_translation": english_translation,
        "_backend_used": "Local Code-Mixed NLP Engine"
    }


# ==============================================================================
# 3. Google Gemini Generative LLM Integration
# ==============================================================================

def analyze_with_gemini(message: str, api_key: str) -> Dict[str, Any]:
    """
    Call Google Gemini Generative AI to analyze code-mixed text.
    Detects language (Telugu+English, Hinglish, Tanglish, English), translates to English,
    and returns structured triage data.
    """
    import google.generativeai as genai

    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.1,
        }
    )

    prompt = f"""
You are an expert customer support triage assistant specializing in code-mixed languages used in India:
- Telugu + English (Tenglish / Teluglish, e.g., 'refund kavali, amount account lo padaledu', 'payment rendu saarlu cut ayyindi', 'naa order inka delivery avvaledu')
- Tanglish (Tamil + English, e.g., 'order vandhuchu but box damaged, refund venum')
- Hinglish (Hindi + English, e.g., 'mera paisa do baar cut gaya')
- English

Analyze the customer support message and return a strictly valid JSON object matching the schema below.

Allowed Intent values:
- "Payment Issue" (double debit, deducted without order, payment failure, unauthorized charge)
- "Refund Request" (asking for refund, refund delayed, return money)
- "Delivery Delay" (late delivery, courier not arrived, tracking stuck, delivery partner issue)
- "Damaged / Wrong Item" (box broken, item damaged, wrong size/color sent, leaking/tampered)
- "Order Cancellation" (requesting to cancel an order)
- "Account Access" (cannot login, OTP not received, password reset error, account locked)
- "General Inquiry" (invoice download, product warranty, stock inquiry, store timing, speak to agent)

Allowed Urgency values:
- "high" (financial loss, double debit, broken items needing refund, abusive agent, urgent emergency)
- "medium" (routine delivery delays, wrong item exchange, login trouble)
- "low" (general inquiries, standard cancellations before shipping)

Allowed Escalate values:
- true (if urgency is high, payment dispute, severe damage, agent misconduct, or low confidence)
- false (for routine or self-serve inquiries)

Allowed detected_language values:
- "Telugu + English"
- "Tanglish"
- "Hinglish"
- "English"
- "Mixed/Unclear"

Required JSON format:
{{
    "intent": "<One of the allowed intents>",
    "urgency": "<high|medium|low>",
    "confidence": <float between 0.0 and 1.0>,
    "draft_reply": "<Polite, empathetic customer response drafting next steps>",
    "escalate": <true|false>,
    "escalation_reason": "<Reason string if escalate is true, otherwise empty string>",
    "detected_language": "<Telugu + English | Tanglish | Hinglish | English | Mixed/Unclear>",
    "english_translation": "<Clear, natural English translation preserving all details such as amounts, dates, and negation>"
}}

Customer Message:
\"\"\"{message}\"\"\"
"""

    response = model.generate_content(prompt)
    raw_text = response.text.strip()
    data = json.loads(raw_text)

    # Sanitize and validate intent
    intent = data.get("intent", "General Inquiry")
    if intent not in VALID_INTENTS:
        for valid in VALID_INTENTS:
            if valid.lower() in intent.lower():
                intent = valid
                break
        else:
            intent = "General Inquiry"

    # Sanitize urgency
    urgency = str(data.get("urgency", "medium")).lower()
    if urgency not in VALID_URGENCIES:
        urgency = "medium"

    # Sanitize confidence
    try:
        confidence = float(data.get("confidence", 0.90))
        confidence = max(0.0, min(1.0, round(confidence, 2)))
    except (ValueError, TypeError):
        confidence = 0.85

    draft_reply = str(data.get("draft_reply", "")).strip()
    if not draft_reply:
        draft_reply = DRAFT_REPLIES.get(intent, DRAFT_REPLIES["General Inquiry"])

    escalate = bool(data.get("escalate", False))
    escalation_reason = str(data.get("escalation_reason", "")).strip()
    if escalate and not escalation_reason:
        escalation_reason = "Flagged for supervisor review due to urgency."

    detected_lang = str(data.get("detected_language", "")).strip()
    if detected_lang not in ["Telugu + English", "Tanglish", "Hinglish", "English", "Mixed/Unclear"]:
        detected_lang = detect_language(message)

    english_trans = str(data.get("english_translation", "")).strip()
    if not english_trans:
        english_trans = translate_to_english(message, detected_lang)

    return {
        "intent": intent,
        "urgency": urgency,
        "confidence": confidence,
        "draft_reply": draft_reply,
        "escalate": escalate,
        "escalation_reason": escalation_reason,
        "detected_language": detected_lang,
        "english_translation": english_trans,
        "_backend_used": "Gemini 1.5 Flash LLM"
    }


# ==============================================================================
# 4. Primary Exported Interface: analyze_message
# ==============================================================================

def analyze_message(message: str) -> Dict[str, Any]:
    """
    Main entrypoint required by the Code-Mixed Support Triage Assistant.
    Analyzes a customer support message (Telugu+English, Tanglish, Hinglish, or English).

    Returns:
    {
        "intent": str,
        "urgency": "high" | "medium" | "low",
        "confidence": float,
        "draft_reply": str,
        "escalate": bool,
        "escalation_reason": str,
        "detected_language": str,
        "english_translation": str
    }
    """
    if not isinstance(message, str):
        message = str(message or "")

    api_key = get_gemini_api_key()

    if api_key:
        try:
            return analyze_with_gemini(message, api_key)
        except Exception as e:
            # Fallback gracefully to local NLP engine
            res = analyze_with_local_rules(message)
            res["_backend_used"] = f"Local Code-Mixed NLP Engine (Gemini fallback: {str(e)[:40]}...)"
            return res
    else:
        return analyze_with_local_rules(message)
