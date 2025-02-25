from flask import request, jsonify
from api.routes.base_route import BaseRoute
from api.services.supabase_service import process_supabase_webhook

class WebhookRoutes(BaseRoute):
    """
    Routes for handling webhooks
    """
    
    # Define blueprint name and URL prefix
    blueprint_name = 'webhook'
    url_prefix = '/webhook'
    
    @classmethod
    def get_blueprint(cls):
        """
        Create and configure the blueprint for webhook routes
        
        Returns:
            Flask Blueprint instance
        """
        blueprint = cls.create_blueprint()
        
        # Define routes
        @blueprint.route('/supabase', methods=['POST'])
        def supabase_webhook():
            """Endpoint for receiving Supabase webhooks"""
            if not request.json:
                return jsonify({"error": "Invalid request"}), 400
            
            # Process the webhook data using our service
            result = process_supabase_webhook(request.json)
            
            # Check if processing was successful
            if result.get('success'):
                # Return success response immediately
                return jsonify({
                    "success": True,
                    "message": "Webhook received and queued for processing",
                    "queue_info": {
                        "size": result.get('data', {}).get('queue_size', 0),
                        "batch_started": result.get('data', {}).get('batch_processing_started', False)
                    }
                })
            else:
                # If there was an error parsing the data, return the error
                return jsonify(result), 400
        
        return blueprint 