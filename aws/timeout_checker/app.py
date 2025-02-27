import json
import boto3
import os
from datetime import datetime
import traceback

def lambda_handler(event, context):
    """
    Process timed-out workflows
    
    Args:
        event: CloudWatch scheduled event
        context: Lambda context
        
    Returns:
        Success/failure response
    """
    try:
        print("Starting timeout checker")
        
        # Get current time
        current_time = datetime.now().isoformat()
        
        # Get DynamoDB table
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(os.environ['WORKFLOW_TABLE'])
        
        # Query for timed-out workflows
        response = table.scan(
            FilterExpression="timeout_at < :now AND #status = :status",
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':now': current_time,
                ':status': 'PENDING_APPROVAL'
            }
        )
        
        timed_out_count = 0
        
        for item in response.get('Items', []):
            workflow_id = item['workflow_id']
            job_data = item.get('job_data', {})
            
            print(f"Processing timed-out workflow: {workflow_id}")
            
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
            
            # Send timeout notification
            send_timeout_notification(workflow_id, job_data)
            
            timed_out_count += 1
        
        print(f"Processed {timed_out_count} timed-out workflows")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Processed {timed_out_count} timed-out workflows',
                'processed_count': timed_out_count
            })
        }
        
    except Exception as e:
        print(f"Error processing timed-out workflows: {str(e)}")
        print(traceback.format_exc())
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to process timed-out workflows',
                'message': str(e)
            })
        }

def send_timeout_notification(workflow_id, job_data):
    """
    Send notification that the job approval request has timed out
    
    Args:
        workflow_id: Workflow ID
        job_data: Job data
    """
    sns = boto3.client('sns')
    
    job_title = job_data.get('title', 'Unknown')
    company = job_data.get('company', 'Unknown')
    
    message = f"""
    The approval request for the following job has timed out:
    
    Job: {job_title}
    Company: {company}
    
    No further action will be taken for this job. If you would like to process this job,
    please contact the administrator to reactivate the workflow.
    
    Workflow ID: {workflow_id}
    """
    
    try:
        sns.publish(
            TopicArn=os.environ['SNS_TOPIC_ARN'],
            Message=message,
            Subject=f"Job Request Timed Out: {job_title} at {company}"
        )
        
        print(f"Sent timeout notification for workflow {workflow_id}")
        
    except Exception as e:
        print(f"Error sending timeout notification: {str(e)}")
        # Don't raise exception here to allow processing of other timed-out workflows

def optimize_scan_for_production(table):
    """
    For production use, implement a more efficient scan with pagination
    
    Args:
        table: DynamoDB table resource
        
    Returns:
        List of timed-out workflow items
    """
    current_time = datetime.now().isoformat()
    timed_out_items = []
    
    # Initial scan
    response = table.scan(
        FilterExpression="timeout_at < :now AND #status = :status",
        ExpressionAttributeNames={
            '#status': 'status'
        },
        ExpressionAttributeValues={
            ':now': current_time,
            ':status': 'PENDING_APPROVAL'
        }
    )
    
    # Add items to our list
    timed_out_items.extend(response.get('Items', []))
    
    # Continue scanning if we have more items
    while 'LastEvaluatedKey' in response:
        response = table.scan(
            FilterExpression="timeout_at < :now AND #status = :status",
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':now': current_time,
                ':status': 'PENDING_APPROVAL'
            },
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        
        timed_out_items.extend(response.get('Items', []))
    
    return timed_out_items