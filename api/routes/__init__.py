# This file makes the routes directory a Python package 

from flask import Flask
from .main_routes import MainRoutes
from .webhook_routes import WebhookRoutes

class Routes:
    """
    Central class for managing all application routes
    """
    
    # List of all route classes
    route_classes = [
        MainRoutes,
        WebhookRoutes
    ]
    
    @classmethod
    def register(cls, app: Flask):
        """
        Register all route blueprints with the Flask application
        
        Args:
            app: The Flask application instance
        """
        # Register each route class
        for route_class in cls.route_classes:
            route_class.register(app) 