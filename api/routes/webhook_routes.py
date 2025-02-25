from flask import Blueprint, request, jsonify
from api.services.supabase_service import process_supabase_webhook

webhook_bp = Blueprint('webhook', __name__, url_prefix='/webhook')

@webhook_bp.route('/supabase', methods=['POST'])
def supabase_webhook():
    if not request.json:
        return jsonify({"error": "Invalid request"}), 400
    
    result = process_supabase_webhook(request.json)
    return jsonify(result) 