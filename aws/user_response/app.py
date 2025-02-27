import json
import boto3
import os
from datetime import datetime
import traceback

def lambda_handler(event, context):
    """
    Handle user response (approve/reject)
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        HTML response for the user
    """
    try:
        # Get workflow ID from query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        workflow_id = query_params.get('workflow_id')
        
        # Determine if this is an approval or rejection
        path = event.get('path', '')
        is_approval = '/approve' in path
        
        if not workflow_id:
            return generate_html_response(400, 
                '<html><body><h1>Error</h1><p>Missing workflow ID</p></body></html>'
            )
        
        # Get workflow from DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(os.environ['WORKFLOW_TABLE'])
        
        try:
            response = table.get_item(
                Key={
                    'workflow_id': workflow_id
                }
            )
        except Exception as e:
            print(f"Database error: {str(e)}")
            print(traceback.format_exc())
            return generate_html_response(500, 
                f'<html><body><h1>Error</h1><p>Database error: {str(e)}</p></body></html>'
            )
        
        if 'Item' not in response:
            return generate_html_response(404, 
                '<html><body><h1>Not Found</h1><p>Workflow not found or has expired</p></body></html>'
            )
        
        workflow = response['Item']
        job = workflow.get('job_data', {})
        job_title = job.get('title', 'Unknown')
        company = job.get('company', 'Unknown')
        
        # Check if workflow is still pending
        if workflow.get('status') != 'PENDING_APPROVAL':
            current_status = workflow.get('status', 'UNKNOWN')
            
            if current_status == 'APPROVED':
                return generate_html_response(400, 
                    '<html><body><h1>Already Processed</h1><p>This job has already been approved and is being processed.</p></body></html>'
                )
            elif current_status == 'REJECTED':
                return generate_html_response(400, 
                    '<html><body><h1>Already Processed</h1><p>This job has already been rejected.</p></body></html>'
                )
            elif current_status == 'TIMED_OUT':
                return generate_html_response(400, 
                    '<html><body><h1>Request Expired</h1><p>This job approval request has timed out.</p></body></html>'
                )
            else:
                return generate_html_response(400, 
                    f'<html><body><h1>Already Processed</h1><p>This job is in status: {current_status}</p></body></html>'
                )
        
        # Check if the request has timed out
        current_time = datetime.now().isoformat()
        timeout_at = workflow.get('timeout_at', '')
        
        if timeout_at and timeout_at < current_time:
            # Update workflow status to TIMED_OUT
            table.update_item(
                Key={
                    'workflow_id': workflow_id
                },
                UpdateExpression="set #status = :status, updated_at = :time",
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':status': 'TIMED_OUT',
                    ':time': current_time
                }
            )
            
            return generate_html_response(400, 
                '<html><body><h1>Request Expired</h1><p>This job approval request has timed out.</p></body></html>'
            )
        
        if is_approval:
            # Update workflow status
            table.update_item(
                Key={
                    'workflow_id': workflow_id
                },
                UpdateExpression="set #status = :status, updated_at = :time",
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':status': 'APPROVED',
                    ':time': current_time
                }
            )
            
            # Trigger document generation
            lambda_client = boto3.client('lambda')
            
            try:
                lambda_client.invoke(
                    FunctionName=os.environ['DOCUMENT_GENERATOR_FUNCTION'],
                    InvocationType='Event',  # Asynchronous invocation
                    Payload=json.dumps({
                        'workflow_id': workflow_id
                    })
                )
                
                print(f"Triggered document generation for workflow {workflow_id}")
                
            except Exception as e:
                print(f"Error invoking document generator: {str(e)}")
                print(traceback.format_exc())
                # Continue anyway, as we've already updated the status
            
            # Return success page with styling
            return generate_html_response(200, f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Job Approved</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    h1 {{
                        color: #2c7c3e;
                        border-bottom: 2px solid #2c7c3e;
                        padding-bottom: 10px;
                    }}
                    .job-info {{
                        background-color: #f5f5f5;
                        padding: 15px;
                        border-radius: 5px;
                        margin: 20px 0;
                    }}
                    .success-message {{
                        background-color: #e8f5e9;
                        border-left: 4px solid #2c7c3e;
                        padding: 10px 15px;
                        margin: 20px 0;
                    }}
                </style>
            </head>
            <body>
                <h1>Job Approved</h1>
                
                <div class="job-info">
                    <p><strong>Job Title:</strong> {job_title}</p>
                    <p><strong>Company:</strong> {company}</p>
                </div>
                
                <div class="success-message">
                    <p>You have successfully approved this job. We will now generate a detailed analysis document.</p>
                    <p>You will receive a notification when the document is ready.</p>
                </div>
                
                <p>Thank you for your response!</p>
            </body>
            </html>
            ''')
        else:
            # Update workflow status for rejection
            table.update_item(
                Key={
                    'workflow_id': workflow_id
                },
                UpdateExpression="set #status = :status, updated_at = :time",
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':status': 'REJECTED',
                    ':time': current_time
                }
            )
            
            # Return rejection page with styling
            return generate_html_response(200, f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Job Rejected</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    h1 {{
                        color: #c62828;
                        border-bottom: 2px solid #c62828;
                        padding-bottom: 10px;
                    }}
                    .job-info {{
                        background-color: #f5f5f5;
                        padding: 15px;
                        border-radius: 5px;
                        margin: 20px 0;
                    }}
                    .reject-message {{
                        background-color: #ffebee;
                        border-left: 4px solid #c62828;
                        padding: 10px 15px;
                        margin: 20px 0;
                    }}
                </style>
            </head>
            <body>
                <h1>Job Rejected</h1>
                
                <div class="job-info">
                    <p><strong>Job Title:</strong> {job_title}</p>
                    <p><strong>Company:</strong> {company}</p>
                </div>
                
                <div class="reject-message">
                    <p>You have rejected this job. No further action will be taken.</p>
                </div>
                
                <p>Thank you for your response!</p>
            </body>
            </html>
            ''')
            
    except Exception as e:
        print(f"Unhandled error: {str(e)}")
        print(traceback.format_exc())
        
        return generate_html_response(500, f'''
        <html>
            <body>
                <h1>Error</h1>
                <p>An unexpected error occurred: {str(e)}</p>
            </body>
        </html>
        ''')

def generate_html_response(status_code: int, html_content: str) -> dict:
    """
    Generate HTML response for API Gateway
    
    Args:
        status_code: HTTP status code
        html_content: HTML content
        
    Returns:
        API Gateway response object
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'text/html',
            'Access-Control-Allow-Origin': '*'
        },
        'body': html_content
    }