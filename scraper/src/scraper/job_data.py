from dataclasses import dataclass
from datetime import datetime

@dataclass
class JobData:
    """Data class to store job information"""
    title: str
    job_url: str
    company: str
    location: str
    posted_time: str
    applicants: str
    description: str
    error: str = None

    @classmethod
    def create_empty(cls):
        """Create an empty job data object with default values"""
        return cls(
            title="Not available",
            job_url="Not available",
            company="Not available",
            location="Not available",
            posted_time="Not available",
            applicants="Not available",
            description="Not available"
        ) 