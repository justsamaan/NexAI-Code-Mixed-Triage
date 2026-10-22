"""
Unit tests for text normalization, entity extraction, and language identification.
"""

import pytest
from src.normalize import (
    detect_language,
    extract_entities,
    normalize_message,
    NormalizedText,
)


def test_raw_text_immutability():
    raw = "  Mera Order #ORD-1234  cancel kardo!!  "
    norm = normalize_message(raw)
    assert norm.raw_text == raw
    assert norm.cleaned_text == "Mera Order #ORD-1234 cancel kardo!!"


def test_entity_extraction_order_id_and_amounts():
    text = "Order #ORD-998812 paise kat gaye ₹1500 refund do"
    entities = extract_entities(text)
    assert "ORD-998812" in entities["order_ids"]
    assert "1500" in entities["amounts"]


def test_negation_preservation_hinglish():
    text = "Mujhe refund nahi chahiye, replacement order send kardo"
    norm = normalize_message(text)
    assert "nahi" in norm.negations_found


def test_negation_preservation_tanglish():
    text = "Enaku refund vendaam, items mathunga"
    norm = normalize_message(text)
    assert "vendaam" in norm.negations_found


def test_language_detection_hinglish():
    text = "Mera parcel abhi tak kyu nahi aaya? Jaldi batao"
    norm = normalize_message(text)
    assert norm.language_detected == "hinglish"
    assert norm.hinglish_score > 0.1


def test_language_detection_tanglish():
    text = "Ennoda order eppo varum? Tracking link kedaikala bro"
    norm = normalize_message(text)
    assert norm.language_detected == "tanglish"
    assert norm.tanglish_score > 0.1


def test_language_detection_english():
    text = "Where can I check the return policy for international shipments?"
    norm = normalize_message(text)
    assert norm.language_detected == "english"
