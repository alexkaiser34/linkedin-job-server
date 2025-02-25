# Flask RESTful API with Supabase Webhook Integration

A RESTful API built with Flask that processes Supabase webhooks for job data, ready for deployment on Vercel.

## Application Architecture

### Project Structure

```
api/
├── __init__.py
├── app.py                # Flask application instance
├── config.py             # Application configuration
├── routes/               # Route definitions
│   ├── __init__.py       # Routes registration
│   ├── base_route.py     # Base route class
│   ├── main_routes.py    # Main application routes
│   └── webhook_routes.py # Webhook handling routes
└── services/             # Business logic services
    ├── __init__.py
    └── supabase_service.py  # Supabase webhook processing
```

### Class-Based Routes

The application uses a class-based architecture for routes:

- `BaseRoute`: Abstract base class that all route classes inherit from
- `MainRoutes`: Handles main application endpoints
- `WebhookRoutes`: Processes incoming webhooks
- `Routes`: Central class that registers all route classes with the Flask app

### Webhook Processing Flow

1. **Webhook Reception**: 
   - Supabase sends webhooks to `/webhook/supabase` when job records are inserted/updated/deleted
   - Each webhook contains data about the database change

2. **Queueing System**:
   - Incoming webhooks are parsed into structured objects
   - Valid payloads are added to a thread-safe queue
   - A quiet period timer (10 seconds) is started/restarted with each webhook

3. **Batch Processing**:
   - After 10 seconds with no new webhooks, the timer triggers batch processing
   - All queued webhooks are processed together in a background thread
   - The queue is cleared and ready for the next cycle

4. **Processing Logic**:
   - Webhooks are grouped by type (INSERT, UPDATE, DELETE)
   - Each type is processed according to business logic
   - Processing happens asynchronously without blocking API responses

## Endpoints

- `GET /`: Welcome message
- `POST /webhook/supabase`: Endpoint for Supabase webhooks

## Running the Application

### Development Environment

1. Install dependencies:
   ```
   pip3 install -r requirements.txt
   ```

2. Run the Flask application on port 5002 (recommended for development):
   ```
   python3 index.py --port 5002
   ```

3. Set up ngrok to create a public URL for your local server:
   ```
   ngrok http 5002
   ```

4. Configure Supabase webhook:
   - Go to Supabase Dashboard → Database → Webhooks
   - Create a new webhook pointing to your ngrok URL:
     - URL: `https://your-ngrok-url.ngrok.io/webhook/supabase`
     - HTTP Method: POST
     - Headers: 
       - `Content-Type: application/json`
       - `ngrok-skip-browser-warning: 1`

5. Test your webhook:
   - Make changes to your Supabase database
   - Check your Flask application logs for webhook processing

### Production Environment

1. Deploy to Vercel:
   - GitHub is linked to Vercel, so any changes to the `main` branch will automatically deploy to Vercel
   > **Note**: When deploying to Vercel, you don't need to specify a port. Vercel will automatically handle the port configuration.

2. Configure Supabase webhook for production:
   - Go to Supabase Dashboard → Database → Webhooks
   - Create a new webhook pointing to your Vercel URL:
     - URL: `https://your-project.vercel.app/webhook/supabase`
     - HTTP Method: POST
     - Headers: `Content-Type: application/json`

3. Monitor your application:
   - Check Vercel logs for webhook processing
   - Set up monitoring and alerts as needed

## Port Configuration

The application supports configuring the port via command-line arguments:

```
python3 index.py --port 5002
```

- Default port is 5000 if not specified
- For development, we recommend using port 5002
- For Vercel deployment, the port argument is ignored as Vercel manages its own port configuration

## Switching Between Environments

When switching between development and production:

1. Update your Supabase webhook URL to point to the correct environment
2. You can maintain separate webhooks for development and production
3. Use environment variables to configure environment-specific settings

## Extending the Application

### Adding New Routes

1. Create a new route class file in the `api/routes` directory:
   ```python
   from api.routes.base_route import BaseRoute
   
   class NewRoutes(BaseRoute):
       blueprint_name = 'new'
       url_prefix = '/new'
       
       @classmethod
       def get_blueprint(cls):
           blueprint = cls.create_blueprint()
           
           @blueprint.route('/', methods=['GET'])
           def new_endpoint():
               return {"message": "New endpoint"}
               
           return blueprint
   ```

2. Add your new route class to the list in `api/routes/__init__.py`:
   ```python
   from api.routes.new_routes import NewRoutes
   
   class Routes:
       route_classes = [
           MainRoutes,
           WebhookRoutes,
           NewRoutes  # Add your new route class here
       ]
   ```

## Troubleshooting

- **403 Errors with ngrok**: Add the `ngrok-skip-browser-warning: 1` header to your requests
- **Webhook not triggering**: Check Supabase logs to ensure webhooks are being sent
- **Processing not starting**: Verify that your quiet period timer is working correctly 