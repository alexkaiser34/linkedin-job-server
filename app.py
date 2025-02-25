from flask import Flask
from routes.main_routes import main_bp
from routes.webhook_routes import webhook_bp

app = Flask(__name__)

# Register blueprints
app.register_blueprint(main_bp)
app.register_blueprint(webhook_bp)

if __name__ == '__main__':
    app.run(debug=True) 