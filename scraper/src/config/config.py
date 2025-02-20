import os
from dotenv import load_dotenv

class Config:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
        
        # LinkedIn credentials
        self.LINKEDIN_EMAIL = os.getenv('LINKEDIN_EMAIL')
        self.LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD')
        
        # Job search URL
        self.JOB_ALERT_URL = os.getenv('JOB_ALERT_URL')
        
        # Maximum number of jobs to process
        try:
            self.MAX_JOBS = int(os.getenv('MAX_PROCESS_JOBS'))
        except (TypeError, ValueError):
            print("Warning: Invalid MAX_JOBS value in .env, defaulting to 50")
            self.MAX_JOBS = 50
        
        # Selenium configuration
        self.WINDOW_SIZE = (
            int(os.getenv('WINDOW_SIZE_WIDTH', 1920)),
            int(os.getenv('WINDOW_SIZE_HEIGHT', 1080))
        )
        self.USER_AGENT = os.getenv('USER_AGENT', 
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        )
        self.CHROME_PROFILE = os.getenv('CHROME_PROFILE', 'chrome_profile')

        # Supabase configuration
        self.SUPABASE_URL = os.getenv('SUPABASE_URL')
        self.SUPABASE_KEY = os.getenv('SUPABASE_KEY')

    def validate(self):
        """Validate that all required configuration is present"""
        required_fields = [
            ('LINKEDIN_EMAIL', self.LINKEDIN_EMAIL),
            ('LINKEDIN_PASSWORD', self.LINKEDIN_PASSWORD),
            ('JOB_ALERT_URL', self.JOB_ALERT_URL)
        ]
        
        missing_fields = [field[0] for field in required_fields if not field[1]]
        
        if missing_fields:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing_fields)}. "
                "Please check your .env file."
            ) 