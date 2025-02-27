import json
import boto3
import openai
import os
from datetime import datetime, timedelta
import traceback
from typing import List, Dict, Any

# Initialize OpenAI client
openai.api_key = os.environ.get('OPENAI_API_KEY')

def lambda_handler(event, context):
    """
    AWS Lambda entry point for job processing
    
    Args:
        event: API Gateway event with payloads
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    # Extract payloads from the request body
    try:
        # For API Gateway integration
        if 'body' in event:
            if isinstance(event['body'], str):
                body = json.loads(event['body'])
            else:
                body = event['body']
            payloads = body.get('payloads', [])
        else:
            # Direct Lambda invocation
            payloads = event.get('payloads', [])
        
        print(f"Received {len(payloads)} payloads for processing")
        
        # Process payloads with AI filtering
        filtered_jobs = filter_jobs_with_ai(payloads)
        
        if not filtered_jobs:
            return generate_api_response(200, {
                'message': 'No jobs matched criteria',
                'filtered_count': 0
            })
        
        # For each filtered job, create a workflow
        workflow_ids = []
        for job in filtered_jobs:
            # Create workflow record in DynamoDB
            workflow_id = create_workflow(job)
            workflow_ids.append(workflow_id)
            
            # Send notification to user
            send_notification(workflow_id, job)
        
        return generate_api_response(200, {
            'message': f'Processed {len(filtered_jobs)} matching jobs',
            'filtered_count': len(filtered_jobs),
            'workflow_ids': workflow_ids
        })
        
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        print(traceback.format_exc())
        
        return generate_api_response(500, {
            'error': 'Internal server error',
            'message': str(e)
        })

def filter_jobs_with_ai(payloads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter jobs using OpenAI API
    
    Args:
        payloads: List of webhook payloads
        
    Returns:
        List of filtered job records
    """
    filtered_jobs = []
    
    for payload in payloads:
        # Skip non-INSERT and non-UPDATE payloads
        if payload['type'] not in ['INSERT', 'UPDATE']:
            continue
            
        # Skip payloads without a record
        if 'record' not in payload or not payload['record']:
            continue
            
        job = payload['record']
        
        # Prepare job data for AI evaluation
        job_text = f"""
        Title: {job.get('title', 'Unknown')}
        Company: {job.get('company', 'Unknown')}
        Location: {job.get('location', 'Unknown')}
        Description: {job.get('description', 'No description')}
        URL: {job.get('url', 'No URL')}
        """
        
        try:
            # Call OpenAI API to evaluate job
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a job filtering assistant. You evaluate job postings to determine if they match specific criteria. Respond with only YES or NO."},
                    {"role": "user", "content": f"Does this job match our criteria for a good opportunity? Consider factors like job title, company reputation, location, and job description. Respond with only YES or NO.\n\n{job_text}"}
                ],
                max_tokens=10
            )
            
            result = response.choices[0].message.content.strip().upper()
            
            print(f"AI evaluation for job {job.get('id')}: {result}")
            
            if result == "YES":
                filtered_jobs.append(job)
                
        except Exception as e:
            print(f"Error calling OpenAI API: {str(e)}")
            print(traceback.format_exc())
            # Skip this job if there's an error with the API call
            continue
    
    return filtered_jobs

def create_workflow(job: Dict[str, Any]) -> str:
    """
    Create a workflow record in DynamoDB
    
    Args:
        job: Job record data
        
    Returns:
        Workflow ID
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['WORKFLOW_TABLE'])
    
    # Generate a unique workflow ID
    workflow_id = f"wf-{job['id']}-{int(datetime.now().timestamp())}"
    
    # Calculate timestamps
    current_time = datetime.now()
    timeout_time = current_time + timedelta(minutes=5)  # 5-minute timeout
    expiration_time = current_time + timedelta(days=7)  # 7-day TTL
    
    # Create workflow item
    workflow_item = {
        'workflow_id': workflow_id,
        'job_id': job['id'],
        'job_data': job,
        'status': 'PENDING_APPROVAL',
        'created_at': current_time.isoformat(),
        'timeout_at': timeout_time.isoformat(),
        'timeout_timestamp': int(timeout_time.timestamp()),
        'expires_at': int(expiration_time.timestamp())
    }
    
    # Save to DynamoDB
    table.put_item(Item=workflow_item)
    
    print(f"Created workflow {workflow_id} for job {job['id']}")
    
    return workflow_id

def send_notification(workflow_id: str, job: Dict[str, Any]):
    """
    Send notification to user about job with approval/rejection links
    
    Args:
        workflow_id: Workflow ID
        job: Job record data
    """
    sns = boto3.client('sns')
    
    api_base_url = os.environ['API_BASE_URL']
    
    # Create approval and rejection URLs
    approve_url = f"{api_base_url}/approve?workflow_id={workflow_id}"
    reject_url = f"{api_base_url}/reject?workflow_id={workflow_id}"
    
    # Prepare message
    job_title = job.get('title', 'Unknown')
    company = job.get('company', 'Unknown')
    location = job.get('location', 'Unknown')
    
    message = f"""
    New job opportunity found!
    
    Title: {job_title}
    Company: {company}
    Location: {location}
    
    Would you like to process this job and generate a detailed analysis?
    
    To APPROVE this job, click here:
    {approve_url}
    
    To REJECT this job, click here:
    {reject_url}
    
    This request will expire in 5 minutes.
    """
    
    # Send SNS notification
    response = sns.publish(
        TopicArn=os.environ['SNS_TOPIC_ARN'],
        Message=message,
        Subject=f"New Job Opportunity: {job_title} at {company}"
    )
    
    print(f"Sent notification for workflow {workflow_id}, MessageId: {response['MessageId']}")

def generate_api_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate API Gateway response
    
    Args:
        status_code: HTTP status code
        body: Response body
        
    Returns:
        API Gateway response object
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps(body)
    }