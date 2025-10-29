from flask import Blueprint, jsonify
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, OperationalError, ProgrammingError

errors_bp = Blueprint("errors", __name__)

@errors_bp.app_errorhandler(ValidationError)
def on_validation_error(err):
    return jsonify({"error": "validation_error", "messages": err.messages}), 400

@errors_bp.app_errorhandler(IntegrityError)
def on_integrity_error(err):
    # FK/unique violations – conflict
    return jsonify({"error": "integrity_error", "message": str(err.orig)}), 409

@errors_bp.app_errorhandler(OperationalError)
def on_operational_error(err):
    # SQLite “no such table”/locking, etc. – treat as server error but clearer
    return jsonify({"error": "operational_error", "message": str(err.orig)}), 500

@errors_bp.app_errorhandler(ProgrammingError)
def on_programming_error(err):
    return jsonify({"error": "programming_error", "message": str(err.orig)}), 500

@errors_bp.app_errorhandler(404)
def on_404(err):
    return jsonify({"error": "not_found"}), 404

@errors_bp.app_errorhandler(Exception)
def on_exception(err):
    return jsonify({"error": "server_error", "message": str(err)}), 500
