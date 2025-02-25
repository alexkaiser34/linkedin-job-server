from flask import Flask, jsonify
import traceback

# Create Flask app
app = Flask(__name__)

# Import routes (must be after app creation to avoid circular imports)
from api.routes.main_routes import main_bp
from api.routes.webhook_routes import webhook_bp

# Register blueprints
app.register_blueprint(main_bp)
app.register_blueprint(webhook_bp)

# Add an error handler to catch and log exceptions
@app.errorhandler(Exception)
def handle_exception(e):
    # Log the exception details
    print(f"Unhandled Exception: {str(e)}")
    print(traceback.format_exc())
    
    # Return a JSON response for API consistency
    return jsonify({
        "error": "Internal Server Error",
        "message": str(e)
    }), 500

if __name__ == '__main__':
    app.run(debug=True) 