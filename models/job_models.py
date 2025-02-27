from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Literal
from datetime import datetime
import json

@dataclass
class JobRecord:
    """
    Represents a job record shared across all components of the application
    """
    id: str
    job_url: str
    title: str
    company: str
    location: Optional[str] = None
    posted_time: Optional[str] = None
    applicants: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def create_empty(cls):
        """Create an empty job data object with default values"""
        return cls(
            id="",
            job_url="Not available",
            title="Not available",
            company="Not available",
            location="Not available",
            posted_time="Not available",
            applicants="Not available",
            description="Not available"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = {k: v for k, v in self.__dict__.items()}
        # Convert datetime objects to ISO format strings
        if self.created_at:
            result['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            result['updated_at'] = self.updated_at.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobRecord':
        """Create from dictionary"""
        # Handle datetime fields
        if 'created_at' in data and data['created_at'] and isinstance(data['created_at'], str):
            try:
                data = data.copy()  # Create a copy to avoid modifying the original
                data['created_at'] = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                data['created_at'] = None
                
        if 'updated_at' in data and data['updated_at'] and isinstance(data['updated_at'], str):
            try:
                data = data.copy() if 'created_at' not in data else data  # Create a copy if not already done
                data['updated_at'] = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                data['updated_at'] = None
                
        return cls(**data)

@dataclass
class WebhookPayload:
    """
    Represents a webhook payload from Supabase
    """
    type: Literal["INSERT", "UPDATE", "DELETE"]
    table: str
    schema: str
    record: Optional[JobRecord] = None
    old_record: Optional[JobRecord] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'type': self.type,
            'table': self.table,
            'schema': self.schema,
            'record': self.record.to_dict() if self.record else None,
            'old_record': self.old_record.to_dict() if self.old_record else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebhookPayload':
        """Create from dictionary"""
        record = JobRecord.from_dict(data['record']) if 'record' in data and data['record'] else None
        old_record = JobRecord.from_dict(data['old_record']) if 'old_record' in data and data['old_record'] else None
        
        return cls(
            type=data['type'],
            table=data['table'],
            schema=data['schema'],
            record=record,
            old_record=old_record
        )

@dataclass
class Workflow:
    """
    Represents a workflow state for AWS Lambda functions
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {k: v for k, v in self.__dict__.items()}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Workflow':
        """Create from dictionary"""
        return cls(**data)