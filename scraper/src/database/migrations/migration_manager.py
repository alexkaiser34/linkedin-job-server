import os
from typing import List
from datetime import datetime

class MigrationManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.migrations_dir = os.path.join(os.path.dirname(__file__), 'versions')

    def run_migrations(self):
        """Run all pending migrations in order"""
        try:
            # Ensure migrations table exists
            self._create_migrations_table()
            
            # Get list of applied migrations
            applied = self._get_applied_migrations()
            
            # Get all migration files
            migration_files = self._get_migration_files()
            
            # Run pending migrations
            for migration_file in migration_files:
                version = self._get_version_from_filename(migration_file)
                if version not in applied:
                    print(f"Running migration: {migration_file}")
                    self._run_migration(migration_file)
                    self._record_migration(version)
                    
        except Exception as e:
            print(f"Error running migrations: {str(e)}")
            raise

    def _create_migrations_table(self):
        """Create the migrations tracking table if it doesn't exist"""
        sql = """
        create table if not exists migrations (
            version text primary key,
            applied_at timestamp with time zone default timezone('utc'::text, now())
        );
        """
        # Use rpc to execute raw SQL
        self.db_manager.supabase.rpc('exec_sql', {'query': sql}).execute()

    def _get_applied_migrations(self) -> List[str]:
        """Get list of already applied migration versions"""
        result = self.db_manager.supabase.table('migrations').select('version').execute()
        return [row['version'] for row in result.data]

    def _get_migration_files(self) -> List[str]:
        """Get sorted list of migration files"""
        files = [f for f in os.listdir(self.migrations_dir) if f.endswith('.sql')]
        return sorted(files)

    def _get_version_from_filename(self, filename: str) -> str:
        """Extract version number from migration filename"""
        return filename.split('_')[0]

    def _run_migration(self, migration_file: str):
        """Execute a single migration file"""
        file_path = os.path.join(self.migrations_dir, migration_file)
        with open(file_path, 'r') as f:
            sql = f.read()
        # Use rpc to execute raw SQL
        self.db_manager.supabase.rpc('exec_sql', {'query': sql}).execute()

    def _record_migration(self, version: str):
        """Record that a migration has been applied"""
        self.db_manager.supabase.table('migrations').insert({'version': version}).execute() 