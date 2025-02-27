import json
import boto3
import openai
import os
from datetime import datetime, timedelta
import traceback
import uuid

# Initialize OpenAI client
openai.api_key = os.environ.get('OPENAI_API_KEY')

def lambda_handler(event, context):
    """
    Generate document for approved job
    
    Args:
        event: Lambda event with workflow_id
        context: Lambda context
        
    Returns:
        Success/failure response
    """
    try:
        # Get workflow ID from event
        workflow_id = event.get('workflow_id')
        
        if not workflow_id:
            print("No workflow ID provided")
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing workflow ID',
                    'message': 'A workflow ID is required'
                })
            }
        
        print(f"Processing document generation for workflow: {workflow_id}")
        
        # Get workflow from DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(os.environ['WORKFLOW_TABLE'])
        
        response = table.get_item(
            Key={
                'workflow_id': workflow_id
            }
        )
        
        if 'Item' not in response:
            print(f"Workflow {workflow_id} not found")
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'error': 'Workflow not found',
                    'message': f'No workflow found with ID: {workflow_id}'
                })
            }
        
        workflow = response['Item']
        
        # Verify workflow is approved
        if workflow.get('status') != 'APPROVED':
            print(f"Workflow {workflow_id} is not approved. Status: {workflow.get('status')}")
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Invalid workflow status',
                    'message': f'Workflow is not approved. Current status: {workflow.get("status")}'
                })
            }
        
        # Get job data
        job = workflow.get('job_data', {})
        
        # Generate document content
        document_content = generate_document_with_ai(job)
        
        # Upload document to S3
        document_url = upload_document_to_s3(workflow_id, job, document_content)
        
        # Update workflow with document URL
        current_time = datetime.now().isoformat()
        
        table.update_item(
            Key={
                'workflow_id': workflow_id
            },
            UpdateExpression="set #status = :status, document_url = :url, updated_at = :time, completed_at = :time",
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':status': 'COMPLETED',
                ':url': document_url,
                ':time': current_time
            }
        )
        
        # Send notification with document link
        send_document_notification(workflow_id, job, document_url)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Document generated successfully',
                'workflow_id': workflow_id,
                'document_url': document_url
            })
        }
        
    except Exception as e:
        print(f"Error generating document: {str(e)}")
        print(traceback.format_exc())
        
        # If we have a workflow ID, update its status to ERROR
        if 'workflow_id' in locals() and workflow_id:
            try:
                table = boto3.resource('dynamodb').Table(os.environ['WORKFLOW_TABLE'])
                
                table.update_item(
                    Key={
                        'workflow_id': workflow_id
                    },
                    UpdateExpression="set #status = :status, error_message = :error, updated_at = :time",
                    ExpressionAttributeNames={
                        '#status': 'status'
                    },
                    ExpressionAttributeValues={
                        ':status': 'ERROR',
                        ':error': str(e),
                        ':time': datetime.now().isoformat()
                    }
                )
            except Exception as update_error:
                print(f"Error updating workflow status: {str(update_error)}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Document generation failed',
                'message': str(e)
            })
        }

def generate_document_with_ai(job):
    """
    Generate document content using OpenAI
    
    Args:
        job: Job data
        
    Returns:
        Generated document content as HTML
    """
    job_title = job.get('title', 'Unknown')
    company = job.get('company', 'Unknown')
    location = job.get('location', 'Unknown')
    description = job.get('description', 'No description provided')
    url = job.get('url', '#')
    
    # Prepare job data for AI
    job_text = f"""
    Title: {job_title}
    Company: {company}
    Location: {location}
    Description: {description}
    URL: {url}
    """
    
    # Call OpenAI API to generate document
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": """You are an expert job analyst. Your task is to create a detailed analysis of a job posting in HTML format.
                Include the following sections:
                1. Job Overview
                2. Company Analysis
                3. Key Responsibilities
                4. Required Skills & Qualifications
                5. Potential Interview Questions
                6. Salary Insights (if possible)
                7. Application Strategy
                
                Format the output as clean, well-structured HTML with appropriate headings, paragraphs, and lists.
                Use a professional tone and provide actionable insights."""},
                {"role": "user", "content": f"Please analyze this job posting and create a detailed report:\n\n{job_text}"}
            ],
            max_tokens=4000,
            temperature=0.7
        )
        
        # Extract the generated content
        document_content = response.choices[0].message.content.strip()
        
        # Wrap in full HTML document if not already
        if not document_content.startswith('<!DOCTYPE html>') and not document_content.startswith('<html>'):
            document_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job Analysis: {job_title} at {company}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #2980b9;
            margin-top: 30px;
        }}
        h3 {{
            color: #3498db;
        }}
        .job-header {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        ul, ol {{
            padding-left: 20px;
        }}
        .highlight {{
            background-color: #e8f4fc;
            padding: 10px;
            border-left: 4px solid #3498db;
            margin: 15px 0;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            font-size: 0.9em;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <div class="job-header">
        <h1>Job Analysis: {job_title}</h1>
        <p><strong>Company:</strong> {company}</p>
        <p><strong>Location:</strong> {location}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
    </div>
    
    {document_content}
    
    <div class="footer">
        <p>This analysis was generated automatically and should be used as a reference only.</p>
        <p>Original job posting: <a href="{url}" target="_blank">{job_title} at {company}</a></p>
    </div>
</body>
</html>"""
        
        return document_content
        
    except Exception as e:
        print(f"Error calling OpenAI API: {str(e)}")
        raise Exception(f"Failed to generate document content: {str(e)}")

def upload_document_to_s3(workflow_id, job, document_content):
    """
    Upload document to S3 bucket
    
    Args:
        workflow_id: Workflow ID
        job: Job data
        document_content: Document content as HTML
        
    Returns:
        S3 URL for the uploaded document
    """
    s3 = boto3.client('s3')
    bucket_name = os.environ['DOCUMENT_BUCKET']
    
    # Generate a unique filename
    job_title = job.get('title', 'Unknown').replace(' ', '_')
    company = job.get('company', 'Unknown').replace(' ', '_')
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    
    filename = f"{job_title}_{company}_{timestamp}_{unique_id}.html"
    
    # Upload to S3
    try:
        s3.put_object(
            Bucket=bucket_name,
            Key=filename,
            Body=document_content,
            ContentType='text/html',
            Metadata={
                'workflow_id': workflow_id,
                'job_id': job.get('id', 'unknown'),
                'job_title': job.get('title', 'Unknown'),
                'company': job.get('company', 'Unknown')
            }
        )
        
        # Generate a pre-signed URL that expires in 7 days
        url = s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket_name,
                'Key': filename
            },
            ExpiresIn=604800  # 7 days in seconds
        )
        
        return url
        
    except Exception as e:
        print(f"Error uploading to S3: {str(e)}")
        raise Exception(f"Failed to upload document to S3: {str(e)}")

def send_document_notification(workflow_id, job, document_url):
    """
    Send notification with document link
    
    Args:
        workflow_id: Workflow ID
        job: Job data
        document_url: URL to the generated document
    """
    sns = boto3.client('sns')
    
    job_title = job.get('title', 'Unknown')
    company = job.get('company', 'Unknown')
    
    message = f"""
    Your job analysis document is ready!
    
    Job: {job_title} at {company}
    
    You can view your document here:
    {document_url}
    
    This link will expire in 7 days.
    """
    
    try:
        sns.publish(
            TopicArn=os.environ['SNS_TOPIC_ARN'],
            Message=message,
            Subject=f"Job Analysis Ready: {job_title} at {company}"
        )
        
        print(f"Sent document notification for workflow {workflow_id}")
        
    except Exception as e:
        print(f"Error sending notification: {str(e)}")
        # Don't raise exception here, as the document was still generated successfully