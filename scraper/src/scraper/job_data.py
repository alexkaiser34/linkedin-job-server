from models import JobRecord as JobData

# If you need additional functionality:
class EnhancedJobData(JobData):
    """Extends JobRecord with scraper-specific functionality"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Add any scraper-specific fields or methods
    
    def to_supabase_format(self):
        """Convert to format expected by Supabase"""
        data = self.to_dict()
        # Transform as needed
        return data 