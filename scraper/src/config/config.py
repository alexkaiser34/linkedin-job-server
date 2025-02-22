import os
from dotenv import load_dotenv
from pathlib import Path

class Config:
    def __init__(self):
        # Get the path to the .env file (in project root)
        env_path = Path(__file__).parents[2] / '.env'
        
        # Force reload of .env file with explicit path
        load_dotenv(dotenv_path=env_path, override=True)
        
        # LinkedIn credentials
        self.LINKEDIN_EMAIL = os.getenv('LINKEDIN_EMAIL')
        self.LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD')
        
        # Job search URL
        self.JOB_ALERT_URL = os.getenv('JOB_ALERT_URL')
        
        # Email configuration
        self.EMAIL_HOST = os.getenv('EMAIL_HOST')
        self.EMAIL_PORT = int(os.getenv('EMAIL_PORT', 465))  # Default to 465 if not set
        self.EMAIL_USER = os.getenv('EMAIL_USER')
        self.EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
        self.EMAIL_TO = os.getenv('EMAIL_TO')
        
        # Maximum number of jobs to process
        try:
            self.MAX_PROCESS_JOBS = int(os.getenv('MAX_PROCESS_JOBS'))
        except (TypeError, ValueError):
            print("Warning: Invalid MAX_PROCESS_JOBS value in .env, defaulting to 50")
            self.MAX_PROCESS_JOBS = 50
        
        # Selenium configuration
        self.WINDOW_SIZE = (
            int(os.getenv('WINDOW_SIZE_WIDTH', 1920)),
            int(os.getenv('WINDOW_SIZE_HEIGHT', 1080))
        )
        self.USER_AGENT = os.getenv('USER_AGENT', 
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        )
        self.CHROME_PROFILE = os.getenv('CHROME_PROFILE')
        self.SELENIUM_HOST = os.getenv('SELENIUM_HOST')

        # Supabase configuration
        self.SUPABASE_URL = os.getenv('SUPABASE_URL')
        self.SUPABASE_KEY = os.getenv('SUPABASE_KEY')

    def validate(self):
        """Validate that all required configuration is present"""
        required_fields = [
            ('LINKEDIN_EMAIL', self.LINKEDIN_EMAIL),
            ('LINKEDIN_PASSWORD', self.LINKEDIN_PASSWORD),
            ('JOB_ALERT_URL', self.JOB_ALERT_URL),
            ('EMAIL_HOST', self.EMAIL_HOST),
            ('EMAIL_USER', self.EMAIL_USER),
            ('EMAIL_PASSWORD', self.EMAIL_PASSWORD),
            ('EMAIL_TO', self.EMAIL_TO)
        ]
        
        missing_fields = [field[0] for field in required_fields if not field[1]]
        
        if missing_fields:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing_fields)}. "
                "Please check your .env file."
            ) 