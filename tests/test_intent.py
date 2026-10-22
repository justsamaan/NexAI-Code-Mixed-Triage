"""
Unit tests for intent classifier, predictions, and uncertainty estimation.
"""

import pytest
from src.intent_model import get_intent_classifier
from src.normalize import normalize_message


@pytest.fixture(scope="module")
def classifier():
    return get_intent_classifier()


def test_classifier_is_loaded(classifier):
    assert classifier is not None
    assert classifier.pipeline is not None
    assert len(classifier.classes_) == 27


def test_predict_cancel_order_hinglish(classifier):
    norm = normalize_message("Plz cancel kardo mera order #ORD-9912")
    pred = classifier.predict(norm)
    assert pred.intent == "cancel_order"
    assert pred.category == "CANCEL"
    assert pred.confidence > 0.50
    assert pred.margin >= 0.0


def test_predict_track_order_tanglish(classifier):
    norm = normalize_message("Ennoda order tracking status kahan hai eppo varum?")
    pred = classifier.predict(norm)
    assert pred.intent in ("track_order", "delivery_period")
    assert pred.confidence > 0.40


def test_predict_password_recovery(classifier):
    norm = normalize_message("Password bhul gaya hu reset link bhejo")
    pred = classifier.predict(norm)
    assert pred.intent == "recover_password"
    assert pred.category == "ACCOUNT"


def test_empty_message_handling(classifier):
    norm = normalize_message("")
    pred = classifier.predict(norm)
    assert pred.intent == "out_of_scope"
    assert pred.is_uncertain is True
