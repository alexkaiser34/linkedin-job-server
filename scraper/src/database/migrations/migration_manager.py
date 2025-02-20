import os
from typing import List
from datetime import datetime
import re

class MigrationManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.migrations_dir = os.path.join(os.path.dirname(__file__), 'versions')

    def run_migrations(self):
        """Run all pending migrations in order"""
        try:
            # Ensure migrations table exists
            self._create_migrations_table()
            
            # Get dictionary of applied migrations and their content
            applied = self._get_applied_migrations()
            
            # Get all migration files
            migration_files = self._get_migration_files()
            
            # Run pending migrations
            for migration_file in migration_files:
                version = self._get_version_from_filename(migration_file)
                
                # Read the current file content
                with open(os.path.join(self.migrations_dir, migration_file), 'r') as f:
                    current_content = f.read()
                
                # Check if migration needs to be applied or rerun
                if version not in applied:
                    print(f"Running new migration: {migration_file}")
                    self._run_migration(migration_file)
                    self._record_migration(version, current_content)
                elif current_content != applied[version]:
                    print(f"Rerunning modified migration: {migration_file}")
                    self._run_migration(migration_file)
                    self._record_migration(version, current_content)
                
        except Exception as e:
            print(f"Error running migrations: {str(e)}")
            raise

    def _create_migrations_table(self):
        """Create the migrations tracking table if it doesn't exist"""
        sql = """
        create table if not exists migrations (
            version text primary key,
            applied_at timestamp with time zone default timezone('utc'::text, now()),
            content text not null
        );
        """
        self.db_manager.supabase.rpc('exec_sql', {'query': sql}).execute()

    def _get_applied_migrations(self) -> dict:
        """Get dictionary of applied migration versions and their content"""
        result = self.db_manager.supabase.table('migrations').select('version, content').execute()
        return {row['version']: row['content'] for row in result.data}

    def _get_migration_files(self) -> List[str]:
        """Get sorted list of migration files"""
        files = [f for f in os.listdir(self.migrations_dir) if f.endswith('.sql')]
        return sorted(files)

    def _get_version_from_filename(self, filename: str) -> str:
        """Extract version number from migration filename"""
        return filename.split('_')[0]

    def _split_sql_statements(self, sql: str) -> list:
        """Split SQL into statements while preserving dollar-quoted blocks and DO blocks"""
        statements = []
        current_statement = []
        in_quotes = False
        quote_char = None
        in_dollar_quote = False
        dollar_quote_tag = None
        in_do_block = False
        nested_level = 0
        
        # Split into lines while preserving newlines
        lines = sql.splitlines(True)
        
        for line in lines:
            i = 0
            while i < len(line):
                # Check for DO block start
                if not in_quotes and not in_dollar_quote and line[i:].strip().upper().startswith('DO'):
                    in_do_block = True
                
                # Handle dollar quotes
                if line[i:i+1] == '$':
                    # Look for the end of the dollar quote tag
                    end_tag = line.find('$', i+1)
                    if end_tag != -1:
                        tag = line[i:end_tag+1]
                        if not in_dollar_quote:
                            in_dollar_quote = True
                            dollar_quote_tag = tag
                        elif tag == dollar_quote_tag:
                            in_dollar_quote = False
                            dollar_quote_tag = None
                        i = end_tag
                
                # Handle regular quotes when not in dollar quotes
                elif not in_dollar_quote and line[i] in ["'", '"']:
                    if not in_quotes:
                        in_quotes = True
                        quote_char = line[i]
                    elif line[i] == quote_char:
                        in_quotes = False
                        quote_char = None
                
                # Track nested blocks
                elif not in_quotes and not in_dollar_quote:
                    if line[i:].strip().startswith('begin'):
                        nested_level += 1
                    elif line[i:].strip().startswith('end'):
                        nested_level -= 1
                        if nested_level == 0:
                            in_do_block = False
                
                # Handle semicolons when not in any quotes and not in a DO block
                elif (line[i] == ';' and 
                      not in_quotes and 
                      not in_dollar_quote and 
                      not in_do_block):
                    current_statement.append(line[:i+1])
                    statements.append(''.join(current_statement))
                    current_statement = []
                    line = line[i+1:]
                    i = 0
                    continue
                
                i += 1
            
            if line:
                current_statement.append(line)
        
        # Add any remaining statement
        if current_statement:
            statements.append(''.join(current_statement))
        
        return [stmt.strip() for stmt in statements if stmt.strip()]

    def _run_migration(self, migration_file: str):
        """Execute a single migration file"""
        file_path = os.path.join(self.migrations_dir, migration_file)
        with open(file_path, 'r') as f:
            sql = f.read()
            
        # Split SQL into separate statements, preserving DO blocks and dollar quotes
        statements = self._split_sql_statements(sql)
        
        # Execute each statement separately
        for statement in statements:
            try:
                self.db_manager.supabase.rpc('exec_sql', {'query': statement}).execute()
            except Exception as e:
                print(f"Error executing SQL statement: {str(e)}")
                print(f"Failed statement: {statement}")
                raise

    def _record_migration(self, version: str, content: str):
        """Record that a migration has been applied"""
        self.db_manager.supabase.table('migrations').upsert({
            'version': version,
            'content': content,
            'applied_at': 'now()'
        }).execute() 