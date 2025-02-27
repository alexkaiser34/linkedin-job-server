# This is the entry point for both Vercel and local development
import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Check if we're running on Vercel or locally
if os.environ.get('VERCEL'):
    # On Vercel, import directly
    from app import FlaskApplication
else:
    # Locally, import from the api package
    try:
        from api.app import FlaskApplication
    except ImportError:
        from app import FlaskApplication

import argparse

# Create the Flask application
flask_app = FlaskApplication()
app = flask_app.get_app()

# Vercel looks for a variable named 'app' to serve

if __name__ == '__main__':
    # This block only executes when the script is run directly
    # It won't run when imported by Vercel
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the Flask application')
    parser.add_argument('--port', type=int, default=5000, 
                        help='Port number to run the server on (default: 5000)')
    args = parser.parse_args()
    
    # Get the port number from arguments
    port = args.port
    
    # Determine if we're in debug mode based on whether port was explicitly specified
    # Check if --port was explicitly provided in the command line arguments
    debug_mode = '--port' in sys.argv
    
    # Run the Flask application
    app.run(debug=debug_mode, port=port)
    
    print(f"Flask application started on port {port}")
    print(f"Debug mode: {'enabled' if debug_mode else 'disabled'}")
    print("Use Ctrl+C to stop the server") 