from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime

@dataclass
class JobRecord:
    """
    Represents a job record
    """
    id: str
    created_at: str
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None

@dataclass
class WebhookPayload:
    """
    Represents a webhook payload
    """
    type: str
    table: str
    schema: str
    record: Optional[JobRecord] = None
    old_record: Optional[JobRecord] = None

@dataclass
class Workflow:
    """
    Represents a workflow state
    """
    workflow_id: str
    job_id: str
    job_data: Dict[str, Any]
    status: str
    created_at: str
    timeout_at: str
    timeout_timestamp: int
    expires_at: int
    updated_at: Optional[str] = None
    document_url: Optional[str] = None
    completed_at: Optional[str] = None