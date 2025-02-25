from flask import Flask, jsonify
import traceback
from api.routes import Routes

class FlaskApplication:
    """
    Main Flask application class that encapsulates the app creation and configuration
    """
    
    def __init__(self):
        """Initialize the Flask application"""
        # Create the Flask app instance
        self.app = Flask(__name__)
        
        # Register all routes
        self._register_routes()
        
        # Register error handlers
        self._register_error_handlers()
    
    def _register_routes(self):
        """Register all application routes"""
        Routes.register(self.app)
    
    def _register_error_handlers(self):
        """Register error handlers for the application"""
        @self.app.errorhandler(Exception)
        def handle_exception(e):
            # Log the exception details
            print(f"Unhandled Exception: {str(e)}")
            print(traceback.format_exc())
            
            # Return a JSON response for API consistency
            return jsonify({
                "error": "Internal Server Error",
                "message": str(e)
            }), 500
    
    def get_app(self):
        """
        Get the Flask application instance
        
        Returns:
            Flask application instance
        """
        return self.app