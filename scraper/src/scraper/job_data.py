from job_assistant_models import JobRecord as JobData

# If you need additional functionality:
class EnhancedJobData(JobData):
    """Extends JobRecord with scraper-specific functionality"""
    
    def __init__(self, job_data=None, **kwargs):
        # Initialize from either a JobData object or keyword arguments
        if job_data is not None:
            # Copy attributes from the provided JobData object
            super().__init__(
                id=getattr(job_data, 'id', None),
                title=getattr(job_data, 'title', ''),
                job_url=getattr(job_data, 'job_url', ''),
                company=getattr(job_data, 'company', ''),
                location=getattr(job_data, 'location', ''),
                posted_time=getattr(job_data, 'posted_time', ''),
                applicants=getattr(job_data, 'applicants', ''),
                description=getattr(job_data, 'description', '')
            )
        else:
            # Initialize with provided keyword arguments
            super().__init__(**kwargs)
    
    def to_supabase_format(self):
        """Convert to format expected by Supabase"""
        data = {
            'title': self.title or '',
            'job_url': self.job_url or '',
            'company': self.company or '',
            'location': self.location or '',
            'posted_time': self.posted_time or '',
            'applicants': self.applicants or '',
            'description': self.description or ''
        }
            
        return data
    
    @classmethod
    def create_empty(cls):
        """Create an empty EnhancedJobData object"""
        return cls(
            title="",
            job_url="",
            company="",
            location="",
            posted_time="",
            applicants="",
            description=""
        ) 