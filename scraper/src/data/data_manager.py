import csv
from datetime import datetime
from typing import List
from ..scraper.job_data import JobData

class DataManager:
    def __init__(self):
        self.jobs: List[JobData] = []

    def add_job(self, job: JobData):
        """Add a job to the collection"""
        self.jobs.append(job)

    def save_to_csv(self, filename=None):
        """Save jobs to CSV file"""
        if filename is None:
            filename = f"linkedin_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        fieldnames = ['title', 'job_url', 'company', 'location', 'posted_time', 
                     'applicants', 'description']
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for job in self.jobs:
                    writer.writerow(job.__dict__)
            print(f"\nJob details successfully saved to {filename}")
        except Exception as e:
            print(f"Error saving to CSV: {str(e)}") 