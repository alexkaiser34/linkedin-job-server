from flask import jsonify, send_from_directory, current_app
import os
from api.routes.base_route import BaseRoute

class MainRoutes(BaseRoute):
    """
    Main application routes
    """
    
    # Define blueprint name and URL prefix
    blueprint_name = 'main'
    url_prefix = None  # Root routes
    
    @classmethod
    def get_blueprint(cls):
        """
        Create and configure the blueprint for main routes
        
        Returns:
            Flask Blueprint instance
        """
        blueprint = cls.create_blueprint()
        
        # Define routes
        @blueprint.route('/', methods=['GET'])
        def home():
            """Home endpoint that returns a welcome message"""
            return jsonify({"message": "Welcome to the Flask RESTful API"})
        
        @blueprint.route('/favicon.ico')
        def favicon():
            """Handle favicon requests"""
            # Return a 204 No Content response
            return '', 204
        
        return blueprint 