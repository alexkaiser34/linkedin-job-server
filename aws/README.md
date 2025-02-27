# AWS Lambda Functions for Job Application Assistant

This directory contains AWS Lambda functions that power the AI workflow for processing job postings, generating tailored documents, and managing user interactions.

## Lambda Functions

### 1. Job Processor (`job_processor/`)

This function processes incoming job data from the webhook API and uses AI to determine if a job is a good match.

- **Handler**: `app.lambda_handler`
- **Key Features**:
  - Filters jobs using OpenAI GPT-4
  - Creates workflow records in DynamoDB
  - Sends notifications to users via SNS
  - Exposes an API endpoint for job processing

### 2. User Response Handler (`user_response/`)

Handles user responses (approve/reject) for job processing requests.

- **Handler**: `app.lambda_handler`
- **Key Features**:
  - Processes approval/rejection actions
  - Updates workflow status in DynamoDB
  - Triggers document generation for approved jobs
  - Returns HTML responses to users

### 3. Document Generator (`document_generator/`)

Generates tailored documents (resumes, cover letters) for approved jobs.

- **Handler**: `app.lambda_handler`
- **Key Features**:
  - Uses OpenAI GPT-4 to analyze job descriptions
  - Creates detailed HTML documents
  - Uploads documents to S3
  - Sends notifications with document links

### 4. Timeout Checker (`timeout_checker/`)

Monitors and processes workflows that have timed out.

- **Handler**: `app.lambda_handler`
- **Key Features**:
  - Runs on a scheduled basis (every minute)
  - Identifies timed-out approval requests
  - Updates workflow status
  - Sends timeout notifications

## Shared Components

- **Models** (`shared/models.py`): Data classes for job records, webhook payloads, and workflows
- **Utils** (`shared/utils.py`): Utility functions for DynamoDB, SNS, and API responses

## Deployment Instructions

This project uses AWS SAM (Serverless Application Model) for deployment.

### Prerequisites

1. Install AWS SAM CLI: [Installation Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
2. Configure AWS credentials: [AWS CLI Configuration](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html)
3. OpenAI API key

### Deployment Steps

1. **Build the application**:
   ```bash
   sam build
   ```

2. **Deploy the application**:
   ```bash
   sam deploy --guided
   ```
   
   During the guided deployment, you'll be prompted for:
   - Stack name (e.g., `job-application-assistant`)
   - AWS Region
   - Environment parameter (`dev` or `prod`)
   - OpenAI API key
   - Confirmation of IAM role creation
   - Deployment confirmation

3. **Note the outputs**:
   After deployment completes, note the API endpoints and SNS topic ARN for configuration.

### Updating the Application

To update the application after making changes:

```bash
sam build && sam deploy
```

### Testing Locally

You can test functions locally using SAM CLI:

1. Invoke Job processor with test event:

```bash
sam local invoke JobProcessorFunction --event events/event.json
```

2. Start local api for testing:

```bash
sam local start-api
```

## Environment Variables

The following environment variables are used across the functions:

- `WORKFLOW_TABLE`: DynamoDB table for workflow state
- `DOCUMENT_BUCKET`: S3 bucket for generated documents
- `SNS_TOPIC_ARN`: ARN for the SNS notification topic
- `OPENAI_API_KEY`: OpenAI API key
- `API_BASE_URL`: Base URL for the API Gateway
- `DOCUMENT_GENERATOR_FUNCTION`: ARN of the document generator function

These are automatically set during deployment via the SAM template.

