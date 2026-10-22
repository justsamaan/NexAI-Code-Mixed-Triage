"""
RESTful API for Code-Mixed Support Triage Assistant.
Conforms to TRD Section 6 API Contracts.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS

from src.config import APP_NAME, APP_VERSION, CONFIDENCE_THRESHOLD
from src.evaluation import run_evaluation_suite
from src.persistence import (
    get_dashboard_metrics,
    get_ticket,
    init_db,
    list_tickets,
    update_ticket_status,
)
from src.service import process_support_message

app = Flask(__name__)
CORS(app)

# Initialize database on startup
init_db()


@app.route("/health", methods=["GET"])
def health_check():
    """Health and readiness endpoint."""
    return jsonify({
        "status": "healthy",
        "service": APP_NAME,
        "version": APP_VERSION,
        "model_loaded": True
    }), 200


@app.route("/api/triage", methods=["POST"])
def api_triage():
    """Main triage endpoint."""
    data = request.get_json(silent=True) or {}
    raw_message = data.get("raw_text") or data.get("message")
    if not raw_message:
        return jsonify({"status": "error", "message": "Missing 'raw_text' or 'message' field"}), 400

    language_hint = data.get("language_hint")
    save_to_db = data.get("save_to_db", True)
    conf_thresh = float(data.get("confidence_threshold", CONFIDENCE_THRESHOLD))

    result = process_support_message(
        raw_text=raw_message,
        language_hint=language_hint,
        save_to_db=save_to_db,
        confidence_threshold=conf_thresh
    )

    status_code = 400 if result.get("status") == "error" else 200
    return jsonify(result), status_code


@app.route("/api/tickets", methods=["GET"])
def api_list_tickets():
    """Lists tickets with query parameters."""
    status = request.args.get("status")
    urgency = request.args.get("urgency")
    language = request.args.get("language")
    intent = request.args.get("intent")
    search = request.args.get("search")
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))

    tickets, total = list_tickets(
        status=status,
        urgency=urgency,
        language=language,
        intent=intent,
        search_query=search,
        limit=limit,
        offset=offset
    )
    return jsonify({
        "total": total,
        "limit": limit,
        "offset": offset,
        "tickets": tickets
    }), 200


@app.route("/api/tickets/<ticket_id>", methods=["GET"])
def api_get_ticket(ticket_id: str):
    """Retrieves single ticket with audit trail."""
    t = get_ticket(ticket_id)
    if not t:
        return jsonify({"error": f"Ticket '{ticket_id}' not found"}), 404
    return jsonify(t), 200


@app.route("/api/tickets/<ticket_id>", methods=["PATCH"])
def api_update_ticket(ticket_id: str):
    """Reviews, approves, rejects, or escalates a ticket."""
    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    if not new_status:
        return jsonify({"error": "Missing 'status' field"}), 400

    agent_response = data.get("agent_response")
    actor = data.get("actor", "support_agent")

    success = update_ticket_status(
        ticket_id=ticket_id,
        new_status=new_status,
        agent_response=agent_response,
        actor=actor
    )

    if not success:
        return jsonify({"error": f"Ticket '{ticket_id}' not found or update failed"}), 404

    return jsonify({"message": "Ticket updated successfully", "ticket_id": ticket_id, "status": new_status}), 200


@app.route("/api/metrics", methods=["GET"])
def api_metrics():
    """Operational metrics for dashboards."""
    metrics = get_dashboard_metrics()
    return jsonify(metrics), 200


@app.route("/api/evaluation", methods=["GET"])
def api_evaluation():
    """Runs or fetches evaluation results on the held-out code-mixed challenge set."""
    results = run_evaluation_suite()
    return jsonify(results), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
