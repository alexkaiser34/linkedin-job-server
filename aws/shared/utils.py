import json
import boto3
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import time
import openai

def format_timestamp(dt: datetime) -> str:
    """Format datetime as ISO string"""
    return dt.isoformat()

def create_workflow_id(job_id: str) -> str:
    """Create a unique workflow ID"""
    timestamp = int(datetime.now().timestamp())
    return f"wf-{job_id}-{timestamp}"

def get_dynamodb_table():
    """Get DynamoDB table resource"""
    dynamodb = boto3.resource('dynamodb')
    table_name = os.environ['WORKFLOW_TABLE']
    return dynamodb.Table(table_name)

def send_sns_notification(topic_arn: str, subject: str, message: str):
    """Send SNS notification"""
    sns = boto3.client('sns')
    
    response = sns.publish(
        TopicArn=topic_arn,
        Subject=subject,
        Message=message
    )
    
    return response

def generate_api_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Generate API Gateway response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps(body)
    }

def generate_html_response(status_code: int, html_content: str) -> Dict[str, Any]:
    """Generate HTML response for API Gateway"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'text/html',
            'Access-Control-Allow-Origin': '*'
        },
        'body': html_content
    }

def get_workflow(workflow_id: str) -> Optional[Dict[str, Any]]:
    """
    Get workflow from DynamoDB
    
    Args:
        workflow_id: Workflow ID
        
    Returns:
        Workflow item or None if not found
    """
    table = get_dynamodb_table()
    
    response = table.get_item(
        Key={
            'workflow_id': workflow_id
        }
    )
    
    return response.get('Item')

def update_workflow_status(workflow_id: str, status: str, additional_attrs: Dict[str, Any] = None):
    """
    Update workflow status in DynamoDB
    
    Args:
        workflow_id: Workflow ID
        status: New status
        additional_attrs: Additional attributes to update
    """
    table = get_dynamodb_table()
    current_time = datetime.now().isoformat()
    
    update_expression = "set #status = :status, updated_at = :time"
    expression_attr_values = {
        ':status': status,
        ':time': current_time
    }
    
    # Add additional attributes
    if additional_attrs:
        for key, value in additional_attrs.items():
            update_expression += f", {key} = :{key.replace('_', '')}"
            expression_attr_values[f":{key.replace('_', '')}"] = value
    
    table.update_item(
        Key={
            'workflow_id': workflow_id
        },
        UpdateExpression=update_expression,
        ExpressionAttributeNames={
            '#status': 'status'
        },
        ExpressionAttributeValues=expression_attr_values
    )

def call_openai_with_retry(messages, max_retries=3, backoff_factor=2):
    """
    Call OpenAI API with retry logic
    
    Args:
        messages: Messages for the API call
        max_retries: Maximum number of retries
        backoff_factor: Backoff factor for exponential backoff
        
    Returns:
        API response
    """
    retries = 0
    last_exception = None
    
    while retries <= max_retries:
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=messages,
                max_tokens=4000,
                temperature=0.7
            )
            return response
        except Exception as e:
            last_exception = e
            retries += 1
            
            if retries <= max_retries:
                # Exponential backoff
                sleep_time = backoff_factor ** retries
                print(f"OpenAI API call failed. Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                print(f"OpenAI API call failed after {max_retries} retries")
                raise last_exception