from dataclasses import dataclass
from typing import Optional, Dict, Any, Literal, List
from datetime import datetime
import threading
import time
from collections import deque
import copy
from job_assistant_models import JobRecord, WebhookPayload

class SupabaseWebhookService:
    """Service for handling Supabase webhooks with batching capability"""
    
    def __init__(self, quiet_period=10):
        """
        Initialize the webhook service
        
        Args:
            quiet_period: Time in seconds to wait with no new webhooks before processing
        """
        self.webhook_queue = deque()
        self.queue_lock = threading.Lock()
        self.processing_thread = None
        self.quiet_period = quiet_period
        self.last_webhook_time = None
        self.quiet_timer = None
    
    def parse_job_record(self, record_data: Dict[str, Any]) -> Optional[JobRecord]:
        """
        Parse a record dictionary into a JobRecord object
        
        Args:
            record_data: Dictionary containing job record data
            
        Returns:
            JobRecord object or None if parsing fails
        """
        if not record_data:
            return None
            
        # Convert string timestamps to datetime objects if they exist
        created_at = None
        if 'created_at' in record_data and record_data['created_at']:
            try:
                created_at = datetime.fromisoformat(record_data['created_at'].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                pass
                
        updated_at = None
        if 'updated_at' in record_data and record_data['updated_at']:
            try:
                updated_at = datetime.fromisoformat(record_data['updated_at'].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                pass
        
        return JobRecord(
            id=record_data.get('id', ''),
            job_url=record_data.get('job_url', ''),
            title=record_data.get('title', ''),
            company=record_data.get('company', ''),
            location=record_data.get('location'),
            posted_time=record_data.get('posted_time'),
            applicants=record_data.get('applicants'),
            description=record_data.get('description'),
            created_at=created_at,
            updated_at=updated_at
        )
    
    def process_job_batch(self, payloads: List[WebhookPayload]):
        """
        Process a batch of job payloads
        This is the main async function that will be called with all collected payloads
        
        Args:
            payloads: List of parsed webhook payloads
        """
        try:
            print(f"Starting batch processing of {len(payloads)} job payloads")
            
            # Group payloads by type for easier processing
            inserts = [p for p in payloads if p.type == 'INSERT']
            updates = [p for p in payloads if p.type == 'UPDATE']
            
            print(f"Batch contains: {len(inserts)} inserts, {len(updates)} updates")
            
            # Process inserts
            if inserts:
                print("Processing INSERT payloads:")
                for payload in inserts:
                    print(f"  - New job: {payload.record.title} at {payload.record.company}")
                    # Add your business logic for handling new jobs here
            
            # Process updates
            if updates:
                print("Processing UPDATE payloads:")
                for payload in updates:
                    print(f"  - Updated job: {payload.record.title} at {payload.record.company}")
                    # Add your business logic for handling updated jobs here
            
            # Simulate some processing time
            # start of our AI workflow
            # call here the AI workflow
            print(f"Batch processing completed for {len(payloads)} job payloads")
            
        except Exception as e:
            import traceback
            print(f"Error in batch processing: {str(e)}")
            print(traceback.format_exc())
    
    def start_quiet_timer(self):
        """
        Start or restart a timer that will process the queue after the quiet period
        if no new webhooks arrive during that time
        """
        # Cancel any existing timer
        if self.quiet_timer:
            self.quiet_timer.cancel()
        
        # Create a new timer
        self.quiet_timer = threading.Timer(
            self.quiet_period, 
            self.process_queue_after_quiet_period
        )
        self.quiet_timer.daemon = True
        self.quiet_timer.start()
        
        print(f"Started quiet period timer for {self.quiet_period} seconds")
    
    def process_queue_after_quiet_period(self):
        """
        Process the queue after the quiet period has elapsed
        This is called by the timer
        """
        print("Quiet period elapsed, checking if processing is needed")
        
        with self.queue_lock:
            # Only process if there are items and no processing is happening
            if self.webhook_queue and (self.processing_thread is None or not self.processing_thread.is_alive()):
                # Create a copy of the queue for processing
                payloads_to_process = list(self.webhook_queue)
                self.webhook_queue.clear()
                
                # Reset the last webhook time
                self.last_webhook_time = None
                
                # Start processing in a new thread
                self.processing_thread = threading.Thread(
                    target=self.process_job_batch,
                    args=(payloads_to_process,)
                )
                self.processing_thread.daemon = True
                self.processing_thread.start()
                
                print(f"Started batch processing thread with {len(payloads_to_process)} items after quiet period")
            else:
                print("No processing needed or processing already in progress")
    
    def process_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process webhook data from Supabase when jobs table changes
        
        Args:
            data: The webhook payload from Supabase
            
        Returns:
            dict: Response with processing results
        """
        try:
            # Print the raw data for debugging
            print(f"Received webhook data: {data}")
            
            # Validate that this is a Supabase webhook payload
            if not all(key in data for key in ['type', 'table', 'schema']):
                return {
                    "success": False,
                    "message": "Invalid webhook payload format",
                    "data": data
                }
                
            # Parse the webhook payload
            webhook_type = data['type']
            table_name = data['table']
            schema_name = data['schema']
            
            # Parse record and old_record based on webhook type
            record = None
            old_record = None
            
            if webhook_type in ['INSERT', 'UPDATE'] and 'record' in data:
                record = self.parse_job_record(data['record'])
                
            if webhook_type in ['UPDATE', 'DELETE'] and 'old_record' in data:
                old_record = self.parse_job_record(data['old_record'])
                
            # Create the parsed payload object
            payload = WebhookPayload(
                type=webhook_type,
                table=table_name,
                schema=schema_name,
                record=record,
                old_record=old_record
            )
            
            # Update the last webhook time and add to queue
            current_time = time.time()
            
            with self.queue_lock:
                self.last_webhook_time = current_time
                self.webhook_queue.append(payload)
                queue_size = len(self.webhook_queue)
            
            print(f"Added payload to queue. Queue size is now {queue_size}")
            
            # Start or restart the quiet period timer
            self.start_quiet_timer()
            
            # Return success response
            return {
                "success": True,
                "message": f"Processed {webhook_type} event for {table_name}",
                "data": {
                    "type": webhook_type,
                    "table": table_name,
                    "schema": schema_name,
                    "record": record.__dict__ if record else None,
                    "old_record": old_record.__dict__ if old_record else None,
                    "queue_size": queue_size,
                    "quiet_period_started": True
                }
            }
                
        except Exception as e:
            # Log the error for debugging
            import traceback
            print(f"Error processing webhook: {str(e)}")
            print(traceback.format_exc())
            
            # Return error response
            return {
                "success": False,
                "error": str(e)
            }

# Create a singleton instance of the service
webhook_service = SupabaseWebhookService(quiet_period=10)

# Function to maintain backward compatibility with existing code
def process_supabase_webhook(data: Dict[str, Any]) -> Dict[str, Any]:
    """Wrapper function to maintain backward compatibility"""
    return webhook_service.process_webhook(data) 