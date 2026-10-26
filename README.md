# Agentic AWS Demo 🤖

An AI-powered AWS infrastructure management system that allows you to manage cloud resources through natural language conversations. Built with Claude AI, FastAPI, and Streamlit.

## 🌟 Features

- **Natural Language Interface**: Manage AWS resources using plain English
- **AI-Powered Tool Selection**: Claude automatically chooses the right AWS operations
- **Real AWS Integration**: Actually creates and manages AWS resources
- **Intelligent Responses**: Get both technical data and human explanations
- **CloudWatch Monitoring**: Query logs and debug Lambda functions
- **Conversational AI**: Context-aware conversations with memory

## 🏗️ Architecture

```
User (Streamlit) → FastAPI → AI Agent (Claude) → AWS APIs → Response
```

### Components:
- **Frontend**: Streamlit chat interface (`frontend/`)
- **Backend**: FastAPI server with CORS (`backend/api/`)
- **AI Agent**: Claude Haiku with function calling (`backend/core/`)
- **AWS Integration**: Cloud Control API + CloudWatch Logs

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- AWS Account with appropriate permissions
- Deepseek API key

### 1. Download the Zip File

```bash
cd AWS_Resource_Management_Agent
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Mac: source venv/bin/activate  

# On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. AWS Account Setup

#### Step 4.1 — Create an IAM User

1. Sign in to the [AWS Management Console](https://console.aws.amazon.com/)
2. Navigate to **IAM** → **Users** → **Create user**
3. Enter a username (e.g., `agentic-aws-demo-user`)
4. Leave "Provide user access to the AWS Management Console" **unchecked** (programmatic access only)
5. Click **Next**

#### Step 4.2 — Create an IAM Policy

1. In a new tab, go to **IAM** → **Policies** → **Create policy**
2. Click the **JSON** tab and replace the default content with the following:

```json
{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Sid": "VisualEditor0",
			"Effect": "Allow",
			"Action": [
				"cloudformation:ListResources",
				"cloudformation:DeleteResource",
				"cloudformation:GetResource",
				"logs:DescribeLogGroups",
				"cloudformation:UpdateResource",
				"s3:ListAllMyBuckets",
				"cloudformation:GetResourceRequestStatus",
				"cloudformation:ListResourceRequests",
				"cloudformation:CreateResource",
				"s3:CreateBucket",
				"s3:ListBucket",
				"logs:FilterLogEvents"
			],
			"Resource": "*"
		}
	]
}
```

3. Click **Next**, give the policy a name (e.g., `AgenticAWSDemoPolicy`), then click **Create policy**

#### Step 4.3 — Attach the Policy to the User

1. Return to the **IAM → Users** tab and select your new user
2. Click **Add permissions** → **Attach policies directly**
3. Search for `AgenticAWSDemoPolicy`, select it, and click **Next** → **Add permissions**

#### Step 4.4 — Generate Access Keys

1. On the user page, go to the **Security credentials** tab
2. Scroll to **Access keys** → **Create access key**
3. Select **Local code** as the use case and click **Next** → **Create access key**
4. **Copy or download the CSV** — the Secret Access Key is only shown once
5. You will use these values in the `.env` file in the next step

---

### 5. Environment Setup

Create a `.env` file in the project root and add the following variables.
#### Important: Never share this .env file to anyone and never commit this to your git repository. It will leak your credentials.

#### Create Anthropic API Key here - https://platform.claude.com/settings/keys


```bash
# Deepseek API Key
DEEPSEEK_API_KEY= PASTE_YOUR_DEEPSEEK_KEY

# AWS Credentials (for demo purposes)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=ap-south-1

# Optional: AWS Role ARN for better security
# AWS_ROLE_ARN=arn:aws:iam::ACCOUNT:role/ROLE_NAME
```

### 6. Run the Application

#### Start the Backend (FastAPI):
```bash
python3 -m uvicorn backend.api.main:app --reload --port 8000
```

#### Start the Frontend (Streamlit):
```bash
streamlit run frontend/chat.py --server.port 8501
```

### 7. Access the Application

Open your browser and go to: `http://localhost:8501`

## 💬 Usage Examples

### Resource Creation

```
User: "Create an S3 bucket for my photos"
AI: I'll create an S3 bucket for your photos. What would you like to name it?

User: "my-photo-bucket-2024"
AI: [Creates bucket] ✅ Successfully created S3 bucket 'my-photo-bucket-2024'
```
### Resource Listing

```
User: "Show me all my S3 buckets"
AI: [Lists resources] You have 5 S3 buckets:
- my-photo-bucket-2024
- data-backup-bucket
- static-website-assets
- ...
```

### Monitoring & Debugging

```
User: "Check for errors in my lambda function 'user-authentication'"
AI: [Queries CloudWatch Logs] Found 3 errors in the last hour:
- Authentication failed for user 'john@example.com'
- Invalid token format detected
- Database connection timeout
```

## 🛠️ Available Tools

### 1. AWS Cloud Control API
- **Create resources**: S3 buckets, EC2 instances, Lambda functions
- **List resources**: View existing infrastructure
- **Read resources**: Get detailed resource information
- **Update/Delete**: Modify or remove resources

### 2. CloudWatch Logs
- **Query error logs**: Find issues in Lambda functions
- **Time-based filtering**: Search logs by time range
- **Error analysis**: Get detailed error information

## 🔧 Configuration

### Tool Definitions
Tools are defined in `backend/tools/tools.json`:
- `aws_cloud_control`: Infrastructure management operations
- `cloudwatch_logs`: Log querying and monitoring

### System Prompts
AI behavior is controlled by prompts in `backend/config/prompt.py`:
- Parameter validation rules
- Error handling instructions
- Response formatting guidelines

## 🚨 Troubleshooting

### Common Issues

#### 1. Deepseek API Overloaded (Error 529)
```
Error: Overloaded
```
**Solution**: Restart the app. Context Window size might have exceeded (Need to be managed for production).

#### 2. AWS Connection Failed
```
Error: AWS connection failed
```
**Solutions**:
- Check your AWS credentials in `.env`
- Verify AWS permissions
- Ensure AWS region is correct

#### 3. Resource Not Created
```
Status: success, but no resource in AWS
```
**Cause**: Cloud Control API is asynchronous
**Solution**: Check resource status and the error details using the request token that was returned by the AWS API. 
```bash
aws cloudcontrol get-resource-request-status --request-token YOUR_TOKEN
```

### Debug Mode

Enable detailed logging by checking the console output:
- AWS API calls and responses
- AI tool selection process
- Error details and stack traces

## 🔒 Security Considerations

### Current Setup (Demo)
- Uses AWS access keys (not recommended for production)
- Basic authentication

### Production Recommendations
1. **Use IAM Roles** instead of access keys
2. **Implement AWS SSO** for user authentication
3. **Use least privilege** permissions
4. **Enable CloudTrail** for audit logging
5. **Implement proper error handling** and logging

### Role-Based Access Example
```python
# Instead of access keys, use role assumption
sts_client = boto3.client('sts')
assumed_role = sts_client.assume_role(
    RoleArn='arn:aws:iam::ACCOUNT:role/DemoRole',
    RoleSessionName='AgenticAIDemo'
)
```

## 📁 Project Structure

```
AWS_AIagent/
├── frontend/
│   └── chat.py               # Streamlit chat interface
├── backend/
│   ├── api/
│   │   └── main.py           # FastAPI server and route definitions
│   ├── config/
│   │   ├── aws_config.py     # AWS credentials and boto3 session setup
│   │   └── prompt.py         # AI system prompts and summary prompts
│   ├── core/
│   │   ├── aws_agent.py      # AI agent logic — Claude API calls and AWS execution
│   │   └── processor.py      # Bridge between API layer and agent
│   └── tools/
│       └── tools.json        # Tool definitions exposed to Claude
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (never commit this)
└── README.md                 # This file
```


## 🔮 Future Enhancements

- **Additional AWS services** (RDS, ECS, etc.)
- **Cost management** tools
- **Infrastructure templates**
- **Multi-account support**
- **Enhanced security** features
- **Real-time monitoring** dashboard

---
