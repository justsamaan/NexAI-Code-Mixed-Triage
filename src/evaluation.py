"""
Evaluation Benchmark Suite for Code-Mixed Support Triage.
Computes Macro-F1, per-class Precision/Recall, High-Risk Urgency Recall,
Escalation Recall, and language-mix slice robustness on held-out test data.
"""

import json
import os
import time
from typing import Any, Dict, List, Tuple
import numpy as np
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_recall_fscore_support

from src.config import CHALLENGE_SET_PATH, EVAL_DIR, UrgencyLevel
from src.service import process_support_message


def load_challenge_dataset(filepath: str = CHALLENGE_SET_PATH) -> List[Dict[str, Any]]:
    """Loads JSONL challenge test cases."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Challenge set not found at: {filepath}")

    cases = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def run_evaluation_suite(
    challenge_path: str = CHALLENGE_SET_PATH,
    save_report: bool = True
) -> Dict[str, Any]:
    """
    Executes reproducible benchmark across the held-out code-mixed challenge dataset.
    Reports honest metrics with separate intent, urgency, escalation, and slice evaluations.
    """
    cases = load_challenge_dataset(challenge_path)
    if not cases:
        return {"error": "Challenge dataset is empty"}

    y_intent_true = []
    y_intent_pred = []
    y_urgency_true = []
    y_urgency_pred = []
    y_escalation_true = []
    y_escalation_pred = []

    slice_results: Dict[str, Dict[str, List[Any]]] = {
        "hinglish": {"intent_true": [], "intent_pred": [], "esc_true": [], "esc_pred": []},
        "tanglish": {"intent_true": [], "intent_pred": [], "esc_true": [], "esc_pred": []},
        "english": {"intent_true": [], "intent_pred": [], "esc_true": [], "esc_pred": []},
    }

    latencies: List[float] = []
    safety_violations_count = 0
    detailed_case_logs: List[Dict[str, Any]] = []

    for case in cases:
        raw_text = case["text"]
        lang_slice = case.get("language", "other").lower()

        res = process_support_message(raw_text, save_to_db=False)
        latencies.append(res.get("latency_ms", 0.0))

        # Predictions
        pred_intent = res["intent"]["label"]
        pred_urgency = res["urgency"]["label"]
        pred_esc = res["escalation"]["required"]

        true_intent = case["expected_intent"]
        true_urgency = case["expected_urgency"]
        true_esc = case["expected_escalation"]

        y_intent_true.append(true_intent)
        y_intent_pred.append(pred_intent)
        y_urgency_true.append(true_urgency)
        y_urgency_pred.append(pred_urgency)
        y_escalation_true.append(true_esc)
        y_escalation_pred.append(pred_esc)

        if lang_slice in slice_results:
            slice_results[lang_slice]["intent_true"].append(true_intent)
            slice_results[lang_slice]["intent_pred"].append(pred_intent)
            slice_results[lang_slice]["esc_true"].append(true_esc)
            slice_results[lang_slice]["esc_pred"].append(pred_esc)

        # Safety audit: check warnings for forbidden claims
        if any("Forbidden promise" in w for w in res.get("warnings", [])):
            safety_violations_count += 1

        detailed_case_logs.append({
            "id": case.get("id"),
            "text": raw_text,
            "language": lang_slice,
            "expected_intent": true_intent,
            "predicted_intent": pred_intent,
            "intent_match": (true_intent == pred_intent),
            "expected_urgency": true_urgency,
            "predicted_urgency": pred_urgency,
            "urgency_match": (true_urgency == pred_urgency),
            "expected_escalation": true_esc,
            "predicted_escalation": pred_esc,
            "escalation_match": (true_esc == pred_esc),
            "latency_ms": res.get("latency_ms")
        })

    # Intent Metrics
    intent_classes = sorted(list(set(y_intent_true + y_intent_pred)))
    intent_acc = accuracy_score(y_intent_true, y_intent_pred)
    i_prec, i_rec, i_f1, _ = precision_recall_fscore_support(
        y_intent_true, y_intent_pred, average="macro", zero_division=0
    )
    _, _, i_weighted_f1, _ = precision_recall_fscore_support(
        y_intent_true, y_intent_pred, average="weighted", zero_division=0
    )

    per_class_p, per_class_r, per_class_f, per_class_supp = precision_recall_fscore_support(
        y_intent_true, y_intent_pred, labels=intent_classes, zero_division=0
    )
    per_class_intent = {
        cls: {
            "precision": round(float(p), 3),
            "recall": round(float(r), 3),
            "f1": round(float(f), 3),
            "support": int(s)
        }
        for cls, p, r, f, s in zip(intent_classes, per_class_p, per_class_r, per_class_f, per_class_supp)
    }

    # Urgency Metrics
    urgency_classes = [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH, UrgencyLevel.NORMAL, UrgencyLevel.LOW]
    urgency_acc = accuracy_score(y_urgency_true, y_urgency_pred)
    u_prec, u_rec, u_f1, _ = precision_recall_fscore_support(
        y_urgency_true, y_urgency_pred, average="macro", zero_division=0
    )

    # High-Risk Urgency Recall (Critical + High)
    high_risk_true = [1 if u in (UrgencyLevel.CRITICAL, UrgencyLevel.HIGH) else 0 for u in y_urgency_true]
    high_risk_pred = [1 if u in (UrgencyLevel.CRITICAL, UrgencyLevel.HIGH) else 0 for u in y_urgency_pred]
    high_risk_p, high_risk_recall, high_risk_f1, _ = precision_recall_fscore_support(
        high_risk_true, high_risk_pred, average="binary", zero_division=0
    )

    # Escalation Metrics
    esc_acc = accuracy_score(y_escalation_true, y_escalation_pred)
    e_prec, e_rec, e_f1, _ = precision_recall_fscore_support(
        y_escalation_true, y_escalation_pred, average="binary", zero_division=0
    )

    # Slices robustness
    slices_summary = {}
    for sl_name, sl_data in slice_results.items():
        if sl_data["intent_true"]:
            sl_intent_acc = accuracy_score(sl_data["intent_true"], sl_data["intent_pred"])
            _, _, sl_intent_f1, _ = precision_recall_fscore_support(
                sl_data["intent_true"], sl_data["intent_pred"], average="macro", zero_division=0
            )
            _, sl_esc_rec, sl_esc_f1, _ = precision_recall_fscore_support(
                sl_data["esc_true"], sl_data["esc_pred"], average="binary", zero_division=0
            )
            slices_summary[sl_name] = {
                "count": len(sl_data["intent_true"]),
                "intent_accuracy": round(float(sl_intent_acc), 3),
                "intent_macro_f1": round(float(sl_intent_f1), 3),
                "escalation_recall": round(float(sl_esc_rec), 3),
                "escalation_f1": round(float(sl_esc_f1), 3),
            }

    report = {
        "benchmark_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_test_cases": len(cases),
        "intent_metrics": {
            "accuracy": round(float(intent_acc), 4),
            "macro_precision": round(float(i_prec), 4),
            "macro_recall": round(float(i_rec), 4),
            "macro_f1": round(float(i_f1), 4),
            "weighted_f1": round(float(i_weighted_f1), 4),
            "per_class": per_class_intent
        },
        "urgency_metrics": {
            "accuracy": round(float(urgency_acc), 4),
            "macro_precision": round(float(u_prec), 4),
            "macro_recall": round(float(u_rec), 4),
            "macro_f1": round(float(u_f1), 4),
            "high_risk_recall": round(float(high_risk_recall), 4),
            "high_risk_precision": round(float(high_risk_p), 4),
        },
        "escalation_metrics": {
            "accuracy": round(float(esc_acc), 4),
            "precision": round(float(e_prec), 4),
            "recall": round(float(e_rec), 4),
            "f1": round(float(e_f1), 4),
        },
        "language_slices": slices_summary,
        "reply_safety": {
            "cases_reviewed": len(cases),
            "unsupported_claim_count": safety_violations_count,
            "unsupported_claim_rate": round(safety_violations_count / len(cases), 4)
        },
        "latency_ms": {
            "mean": round(float(np.mean(latencies)), 2),
            "p50": round(float(np.percentile(latencies, 50)), 2),
            "p90": round(float(np.percentile(latencies, 90)), 2),
            "p99": round(float(np.percentile(latencies, 99)), 2),
        },
        "detailed_cases": detailed_case_logs
    }

    if save_report:
        os.makedirs(EVAL_DIR, exist_ok=True)
        report_path = os.path.join(EVAL_DIR, "latest_benchmark_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

    return report
