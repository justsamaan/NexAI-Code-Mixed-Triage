"""
Intent Classification Engine for Code-Mixed Customer Support.
Combines subword character/word TF-IDF n-grams with calibrated linear modeling
and code-mixed transliteration semantic mapping.
"""

import os
import pickle
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

from src.config import ALL_INTENTS, BITEXT_CATEGORIES, MODEL_PATH
from src.data_loader import get_dataset_splits
from src.normalize import NormalizedText, normalize_message

# Lexical priors for code-mixed Hindi/Tamil patterns to boost recall on extreme transliterations
CODE_MIXED_PRIORS: Dict[str, List[str]] = {
    "cancel_order": [
        "cancel kardo", "cancel karna", "order cancel", "cancel pannu", "cancel pannunga",
        "nahi chahiye order", "vendaam order", "order radd", "cancel my purchase"
    ],
    "get_refund": [
        "paisa wapas", "paise wapas", "refund chahiye", "refund do", "kaasu thirumba",
        "panam venum", "refund kidaikala", "return kardo", "money back", "deduct hua refund"
    ],
    "track_order": [
        "kahan hai order", "order kab aayega", "delivery status", "parcel enga",
        "order eppo varum", "track karna", "order status", "dispatch hua", "tracking details",
        "kab deliver hoga", "deliver kab hoga", "deliver hoga", "kab aayega"
    ],
    "track_refund": [
        "refund status", "refund kab aayega", "refund eppo varum", "refund nahi aaya",
        "refund varala", "refund tracking", "paisa kab milega"
    ],
    "complaint": [
        "bahut bekar", "fraud company", "worst service", "romba worstu", "kharab service",
        "gussa aa raha", "cheat", "scam", "shikayat", "case karunga", "consumer court"
    ],
    "recover_password": [
        "password bhul gaya", "password marandhutten", "reset password", "password nahi chal raha",
        "login nahi ho raha", "otp nahi aaya", "forgot password", "password mathu"
    ],
    "payment_issue": [
        "paisa kat gaya", "payment fail", "kaasu pochu", "amount debited", "payment nahi hua",
        "double payment", "upi fail", "bank se cut gaya", "failed transaction"
    ],
    "change_shipping_address": [
        "address badalna", "address change", "delivery address change", "veedu address mathu",
        "galat address", "shipping address update"
    ],
    "contact_human_agent": [
        "human se baat", "agent se connect", "manager se baat", "real person",
        "customer care number", "call karo", "agent call"
    ],
    "delete_account": [
        "account band kardo", "account delete", "profile delete", "account closed"
    ],
    "edit_account": [
        "profile update", "naam badalna", "email change", "phone number update"
    ],
    "get_invoice": [
        "bill chahiye", "invoice bhejo", "bill download", "tax invoice", "receipt do"
    ],
}

@dataclass
class IntentPrediction:
    """Structured intent classification output."""
    intent: str
    category: str
    confidence: float
    raw_score: float
    margin: float
    entropy: float
    is_uncertain: bool
    top_candidates: List[Tuple[str, float]]
    evidence_tokens: List[str]
    model_version: str


class IntentClassifier:
    """
    Production-grade Intent Classifier combining word n-grams (semantics)
    and subword char n-grams (phonetic/transliteration invariance).
    """

    def __init__(self, model_path: str = MODEL_PATH):
        self.model_path = model_path
        self.pipeline: Optional[Pipeline] = None
        self.classes_: List[str] = ALL_INTENTS
        self.version = "1.1.0-hybrid-ngram"
        self._load_or_initialize()

    def _build_pipeline(self) -> Pipeline:
        """Constructs a dual-stream feature union pipeline."""
        union = FeatureUnion([
            (
                "word_tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 3),
                    sublinear_tf=True,
                    max_features=25000,
                    token_pattern=r"\b[a-zA-Z0-9_\'-]+\b"
                )
            ),
            (
                "char_tfidf",
                TfidfVectorizer(
                    analyzer="char_wb",
                    ngram_range=(2, 5),
                    sublinear_tf=True,
                    max_features=35000
                )
            )
        ])

        clf = LogisticRegression(
            C=2.0,
            max_iter=1000,
            class_weight="balanced",
            solver="lbfgs",
            random_state=42
        )

        return Pipeline([
            ("features", union),
            ("classifier", clf)
        ])

    def train(self, texts: List[str], labels: List[str]) -> "IntentClassifier":
        """Trains the hybrid TF-IDF + Logistic Regression model."""
        self.pipeline = self._build_pipeline()
        self.pipeline.fit(texts, labels)
        self.classes_ = list(self.pipeline.named_steps["classifier"].classes_)
        self.save()
        return self

    def save(self):
        """Serializes model pipeline to disk."""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, "wb") as f:
            pickle.dump({
                "pipeline": self.pipeline,
                "classes": self.classes_,
                "version": self.version
            }, f)

    def _load_or_initialize(self):
        """Loads saved model or automatically trains on Bitext dataset."""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, "rb") as f:
                    data = pickle.load(f)
                    self.pipeline = data["pipeline"]
                    self.classes_ = data["classes"]
                    self.version = data.get("version", self.version)
                return
            except Exception as e:
                print(f"Warning: Failed to load model from {self.model_path}: {e}. Retraining...")

        # If model doesn't exist, train from Bitext data
        print("Training baseline IntentClassifier on Bitext dataset...")
        splits = get_dataset_splits()
        train_df = splits["train"]
        self.train(train_df["instruction"].tolist(), train_df["intent"].tolist())
        print("IntentClassifier baseline training complete.")

    def _find_category(self, intent: str) -> str:
        """Finds the high-level category for a given intent."""
        for cat, intents in BITEXT_CATEGORIES.items():
            if intent in intents:
                return cat
        return "GENERAL"

    def predict(
        self,
        norm_text: NormalizedText,
        confidence_threshold: float = 0.62
    ) -> IntentPrediction:
        """
        Predicts intent with calibrated confidence, margin, and entropy.
        Applies code-mixed subword and lexical prior enrichment.
        """
        if self.pipeline is None:
            raise RuntimeError("Model pipeline is not initialized or trained.")

        text_input = norm_text.cleaned_text
        if not text_input:
            return IntentPrediction(
                intent="out_of_scope",
                category="GENERAL",
                confidence=0.0,
                raw_score=0.0,
                margin=0.0,
                entropy=1.0,
                is_uncertain=True,
                top_candidates=[("out_of_scope", 1.0)],
                evidence_tokens=[],
                model_version=self.version
            )

        # Get probability distribution from classifier
        probs = self.pipeline.predict_proba([text_input])[0]
        classes = self.classes_

        # Calculate entropy: H(X) = -sum(p * log(p))
        eps = 1e-9
        entropy = float(-np.sum(probs * np.log(probs + eps)) / np.log(len(classes)))

        # Top candidates
        top_indices = np.argsort(probs)[::-1]
        top_candidates = [(classes[i], round(float(probs[i]), 4)) for i in top_indices[:5]]

        top_intent = top_candidates[0][0]
        top_prob = top_candidates[0][1]
        second_prob = top_candidates[1][1] if len(top_candidates) > 1 else 0.0
        margin = round(float(top_prob - second_prob), 4)

        # Check code-mixed prior boost if top model confidence is borderline (< 0.65)
        # or if strong phrase match occurs
        text_lower = text_input.lower()
        evidence_tokens: List[str] = []
        prior_matched_intent = None

        for intent, patterns in CODE_MIXED_PRIORS.items():
            for pat in patterns:
                if pat in text_lower:
                    evidence_tokens.append(pat)
                    prior_matched_intent = intent
                    break
            if prior_matched_intent:
                break

        final_intent = top_intent
        final_confidence = top_prob

        # If a strong code-mixed prior matched and aligns or refines borderline model output
        if prior_matched_intent:
            if prior_matched_intent == top_intent:
                final_confidence = min(0.98, top_prob + 0.15)
            elif top_prob < 0.50:
                # Prior overrides weak model on explicit phrase
                final_intent = prior_matched_intent
                final_confidence = 0.78
                top_candidates.insert(0, (prior_matched_intent, 0.78))

        # Check uncertainty
        is_uncertain = (final_confidence < confidence_threshold) or (margin < 0.10)

        # Extract salient tokens as evidence
        if not evidence_tokens:
            evidence_tokens = [t for t in norm_text.tokens if len(t) > 3][:4]

        category = self._find_category(final_intent)

        return IntentPrediction(
            intent=final_intent,
            category=category,
            confidence=round(float(final_confidence), 3),
            raw_score=round(float(top_prob), 3),
            margin=margin,
            entropy=round(entropy, 3),
            is_uncertain=is_uncertain,
            top_candidates=top_candidates[:3],
            evidence_tokens=evidence_tokens,
            model_version=self.version
        )


# Singleton instance accessor
_INTENT_CLASSIFIER_INSTANCE: Optional[IntentClassifier] = None

def get_intent_classifier() -> IntentClassifier:
    """Returns singleton instance of the IntentClassifier."""
    global _INTENT_CLASSIFIER_INSTANCE
    if _INTENT_CLASSIFIER_INSTANCE is None:
        _INTENT_CLASSIFIER_INSTANCE = IntentClassifier()
    return _INTENT_CLASSIFIER_INSTANCE
