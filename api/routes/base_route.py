from flask import Flask, Blueprint

class BaseRoute:
    """
    Base class for all route classes
    
    This class provides common functionality for route classes and
    defines the interface that all route classes should implement.
    """
    
    # Blueprint name and URL prefix should be defined by subclasses
    blueprint_name = None
    url_prefix = None
    
    @classmethod
    def create_blueprint(cls):
        """
        Create a Flask blueprint for this route class
        
        Returns:
            Flask Blueprint instance
        """
        if cls.blueprint_name is None:
            raise ValueError(f"blueprint_name not defined for {cls.__name__}")
            
        return Blueprint(cls.blueprint_name, __name__, url_prefix=cls.url_prefix)
    
    @classmethod
    def register(cls, app: Flask):
        """
        Register this route class with the Flask application
        
        Args:
            app: The Flask application instance
        """
        blueprint = cls.get_blueprint()
        app.register_blueprint(blueprint)
    
    @classmethod
    def get_blueprint(cls):
        """
        Get the blueprint for this route class
        
        This method should be implemented by subclasses to return
        their blueprint with all routes defined.
        
        Returns:
            Flask Blueprint instance
        """
        raise NotImplementedError("Subclasses must implement get_blueprint()") 