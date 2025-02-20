import os
from supabase import create_client
from typing import List
from ..scraper.job_data import JobData
from .migrations.migration_manager import MigrationManager

class DatabaseManager:
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase = create_client(supabase_url, supabase_key)
        self.migration_manager = MigrationManager(self)

    def initialize_database(self):
        """Initialize database and run any pending migrations"""
        try:
            print("Running database migrations...")
            self.migration_manager.run_migrations()
            
            # Call delete_old_jobs function after migrations
            print("Cleaning up old jobs...")
            self.supabase.rpc('delete_old_jobs').execute()
            
            print("Database initialization complete")
        except Exception as e:
            print(f"Error initializing database: {str(e)}")
            raise

    def upsert_jobs(self, jobs: List[JobData]):
        """
        Upsert job data into Supabase database.
        Uses job_url as the unique identifier.
        """
        try:
            # Convert jobs to list of dictionaries and remove duplicates
            job_dicts = []
            seen = set()
            for job in jobs:
                if job.job_url not in seen and job.job_url != "Not available":
                    seen.add(job.job_url)
                    job_dicts.append(job.__dict__)
            
            if not job_dicts:
                return
            
            # Upsert the jobs into the 'jobs' table
            result = self.supabase.table('jobs').upsert(
                job_dicts,
                on_conflict='job_url'  # Use job_url for conflict resolution
            ).execute()
            
            print(f"Successfully upserted {len(job_dicts)} jobs to database")
            return result
            
        except Exception as e:
            print(f"Error upserting jobs to database: {str(e)}")
            raise

    def get_job_count(self) -> int:
        """Get the total number of jobs in the database"""
        try:
            result = self.supabase.table('jobs').select('count', count='exact').execute()
            return result.count
        except Exception as e:
            print(f"Error getting job count: {str(e)}")
            return 0