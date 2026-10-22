"""
evaluate.py
===========
Evaluation harness and metric calculation for Code-Mixed Support Triage Assistant.
Evaluates predictions from ai_engine against ground truth test cases.

Can be run directly via CLI:
    python evaluate.py

Or imported into the Streamlit app:
    from evaluate import evaluate_dataset
"""

import sys
import pandas as pd
from typing import Dict, Any, List, Optional, Callable
from test_cases import TEST_CASES
import ai_engine


def evaluate_dataset(
    test_cases: Optional[List[Dict[str, Any]]] = None,
    analyzer: Optional[Callable[[str], Dict[str, Any]]] = None,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> Dict[str, Any]:
    """
    Runs evaluation over the provided test cases using the given analyzer function.
    Tracks intent, urgency, and escalation accuracy along with failure reasons.

    Args:
        test_cases: List of test case dicts. Defaults to TEST_CASES from test_cases.py.
        analyzer: Function that takes a string message and returns a triage dict.
                  Defaults to ai_engine.analyze_message.
        progress_callback: Optional callback(current_idx, total_count) for progress bars.

    Returns:
        Dictionary containing evaluation summary metrics, detailed results rows,
        and confusion matrix data.
    """
    if test_cases is None:
        test_cases = TEST_CASES
    if analyzer is None:
        analyzer = ai_engine.analyze_message

    backend_info = ai_engine.get_backend_status()
    is_mock = backend_info.get("is_mock", False)

    results = []
    total_count = len(test_cases)

    intent_correct = 0
    urgency_correct = 0
    escalate_correct = 0
    escalate_applicable = 0
    total_passed = 0
    total_errors = 0

    # For language breakdowns
    lang_stats = {}

    for idx, tc in enumerate(test_cases):
        if progress_callback:
            progress_callback(idx + 1, total_count)

        tc_id = tc.get("id", idx + 1)
        msg = tc.get("message", "")
        lang = tc.get("language", "Unknown")
        exp_intent = tc.get("expected_intent")
        exp_urgency = tc.get("expected_urgency")
        exp_escalate = tc.get("expected_escalate")

        if lang not in lang_stats:
            lang_stats[lang] = {"total": 0, "passed": 0, "intent_correct": 0, "urgency_correct": 0}
        lang_stats[lang]["total"] += 1

        failed_fields = []
        is_error = False
        error_msg = ""
        prediction = {}

        try:
            prediction = analyzer(msg)
            if not isinstance(prediction, dict):
                raise ValueError(f"Analyzer returned non-dict response: {type(prediction)}")
        except Exception as e:
            is_error = True
            error_msg = str(e)
            total_errors += 1

        pred_intent = prediction.get("intent", "ERROR" if is_error else "Unknown")
        pred_urgency = prediction.get("urgency", "ERROR" if is_error else "Unknown")
        pred_escalate = prediction.get("escalate", None)
        pred_conf = prediction.get("confidence", 0.0)
        pred_reason = prediction.get("escalation_reason", "")
        pred_lang = prediction.get("detected_language", "Unknown")
        pred_trans = prediction.get("english_translation", "")

        # Check Intent Match
        intent_match = (str(pred_intent).strip().lower() == str(exp_intent).strip().lower())
        if intent_match:
            intent_correct += 1
            lang_stats[lang]["intent_correct"] += 1
        else:
            failed_fields.append("Intent")

        # Check Urgency Match
        urgency_match = (str(pred_urgency).strip().lower() == str(exp_urgency).strip().lower())
        if urgency_match:
            urgency_correct += 1
            lang_stats[lang]["urgency_correct"] += 1
        else:
            failed_fields.append("Urgency")

        # Check Escalation Match (if specified in test case)
        escalate_match = True
        if exp_escalate is not None:
            escalate_applicable += 1
            escalate_match = (bool(pred_escalate) == bool(exp_escalate))
            if escalate_match:
                escalate_correct += 1
            else:
                failed_fields.append("Escalation")

        if is_error:
            overall_status = "ERROR"
        elif len(failed_fields) == 0:
            overall_status = "PASS"
            total_passed += 1
            lang_stats[lang]["passed"] += 1
        else:
            overall_status = "FAIL"

        results.append({
            "id": tc_id,
            "language": lang,
            "detected_language": pred_lang,
            "message": msg,
            "english_translation": pred_trans,
            "expected_intent": exp_intent,
            "predicted_intent": pred_intent,
            "intent_match": intent_match,
            "expected_urgency": exp_urgency,
            "predicted_urgency": pred_urgency,
            "urgency_match": urgency_match,
            "expected_escalate": exp_escalate,
            "predicted_escalate": pred_escalate,
            "escalate_match": escalate_match,
            "confidence": pred_conf,
            "escalation_reason": pred_reason,
            "status": overall_status,
            "failed_fields": ", ".join(failed_fields) if failed_fields else "None",
            "error_message": error_msg
        })

    # Summary calculations
    total_tests = len(test_cases)
    overall_pass_rate = (total_passed / total_tests * 100.0) if total_tests > 0 else 0.0
    intent_accuracy = (intent_correct / total_tests * 100.0) if total_tests > 0 else 0.0
    urgency_accuracy = (urgency_correct / total_tests * 100.0) if total_tests > 0 else 0.0
    escalate_accuracy = (escalate_correct / escalate_applicable * 100.0) if escalate_applicable > 0 else 0.0

    df_results = pd.DataFrame(results)

    # Confusion matrix for Intent
    intent_cm = None
    if not df_results.empty:
        try:
            intent_cm = pd.crosstab(
                df_results["expected_intent"],
                df_results["predicted_intent"],
                rownames=["Expected"],
                colnames=["Predicted"],
                margins=True
            )
        except Exception:
            intent_cm = None

    # Confusion matrix for Urgency
    urgency_cm = None
    if not df_results.empty:
        try:
            urgency_cm = pd.crosstab(
                df_results["expected_urgency"],
                df_results["predicted_urgency"],
                rownames=["Expected"],
                colnames=["Predicted"],
                margins=True
            )
        except Exception:
            urgency_cm = None

    return {
        "metrics": {
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_tests - total_passed - total_errors,
            "total_errors": total_errors,
            "overall_pass_rate": round(overall_pass_rate, 1),
            "intent_accuracy": round(intent_accuracy, 1),
            "urgency_accuracy": round(urgency_accuracy, 1),
            "escalate_accuracy": round(escalate_accuracy, 1),
            "by_language": lang_stats,
        },
        "results_df": df_results,
        "intent_confusion_matrix": intent_cm,
        "urgency_confusion_matrix": urgency_cm,
        "backend_info": backend_info,
        "is_mock": is_mock,
    }


def main():
    """Command-line runner for evaluation."""
    print("=" * 70)
    print("Code-Mixed Support Triage Assistant - Evaluation Suite")
    print("=" * 70)

    backend = ai_engine.get_backend_status()
    print(f"Active Backend: {backend['name']}")
    if backend.get("is_mock"):
        print(">>> WARNING: MOCK MODE ACTIVE. Scores are simulated placeholder values. <<<")
    print("-" * 70)

    eval_output = evaluate_dataset()
    m = eval_output["metrics"]

    print(f"Total Test Cases   : {m['total_tests']}")
    print(f"Passed All Checks  : {m['total_passed']}")
    print(f"Failed Any Check   : {m['total_failed']}")
    print(f"Runtime Errors     : {m['total_errors']}")
    print("-" * 70)
    print(f"Overall Pass Rate  : {m['overall_pass_rate']}%")
    print(f"Intent Accuracy    : {m['intent_accuracy']}%")
    print(f"Urgency Accuracy   : {m['urgency_accuracy']}%")
    print(f"Escalation Accuracy: {m['escalate_accuracy']}%")
    print("=" * 70)

    print("\nLanguage Breakdown:")
    for lang, s in m["by_language"].items():
        pass_rate = round(s["passed"] / s["total"] * 100, 1) if s["total"] else 0
        print(f"  {lang:<10}: {s['passed']}/{s['total']} passed ({pass_rate}%) | Intent: {s['intent_correct']}/{s['total']} | Urgency: {s['urgency_correct']}/{s['total']}")

    # Failed tests breakdown
    df = eval_output["results_df"]
    fails = df[df["status"] != "PASS"]
    if not fails.empty:
        print(f"\nDiscrepancies ({len(fails)}):")
        for _, row in fails.iterrows():
            print(f"  ID #{row['id']} [{row['language']}] - Failed: {row['failed_fields']}")
            print(f"    Message: '{row['message']}'")
            print(f"    Expected: Intent={row['expected_intent']}, Urgency={row['expected_urgency']}, Escalate={row['expected_escalate']}")
            print(f"    Predicted: Intent={row['predicted_intent']}, Urgency={row['predicted_urgency']}, Escalate={row['predicted_escalate']}")
    else:
        print("\nAll test cases PASSED perfectly!")

    print("=" * 70)


if __name__ == "__main__":
    main()
