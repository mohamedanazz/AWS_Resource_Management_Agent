from openai import OpenAI
import json
import os
from dotenv import load_dotenv
from backend.config.aws_config import AWSConfig
from typing import Dict, Any, List
from backend.config.prompt import SYSTEM_PROMPT, SUMMARY_PROMPT
from datetime import datetime, timedelta

load_dotenv()


class AWSAgenticAgent:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv('DEEPSEEK_API_KEY'),
            base_url="https://api.deepseek.com"
        )
        self.model = "deepseek-flash"
        self.aws_config = AWSConfig()

        # Validate AWS credentials here; DeepSeek is tested on the first request.
        self._test_aws_connection()

    def _test_aws_connection(self):
        """Test AWS credentials; the DeepSeek API is called when a request arrives."""
        print("🔍 Testing AWS connection...")

        # Test AWS connection
        if not self.aws_config.validate_connection():
            raise Exception("AWS connection failed")

        print("AWS connection successful!")
        print("DeepSeek API connection will be tested on first request")

    @staticmethod
    def _build_system_prompt() -> str:
        """Build system prompt for AWS operations."""
        return SYSTEM_PROMPT

    @staticmethod
    def _format_tools() -> List[Dict]:
        """Load tool definitions and convert Anthropic schemas to OpenAI format."""
        json_path = os.path.join(
            os.path.dirname(__file__), "..", "tools", "tools.json"
        )
        with open(json_path, "r", encoding="utf-8") as file:
            raw_tools = json.load(file)

        formatted_tools = []
        for tool in raw_tools:
            # Already in OpenAI/DeepSeek function-tool format.
            if tool.get("type") == "function" and "function" in tool:
                formatted_tools.append(tool)
                continue

            # Convert Anthropic format:
            # {"name": ..., "description": ..., "input_schema": {...}}
            if "name" in tool and "input_schema" in tool:
                formatted_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool["input_schema"],
                    },
                })
                continue

            raise ValueError(
                "Unsupported tool definition in tools.json. Expected OpenAI "
                "function format or Anthropic name/description/input_schema format."
            )

        return formatted_tools

    def _execute_aws_operation(self, operation: str, resource_type: str,
                               identifier: str = None, properties: Dict = None,
                               region: str = "us-east-1") -> Dict[str, Any]:
        """Execute AWS Cloud Control API operation"""

        try:
            session = self.aws_config.get_session()
            cloudcontrol = session.client('cloudcontrol', region_name=region)

            print(f"Executing {operation} on {resource_type}")
            print(f"Properties: {properties}")
            print(f"Region: {region}")

            if operation == "create":
                try:
                    response = cloudcontrol.create_resource(
                        TypeName=resource_type,
                        DesiredState=json.dumps(properties) if properties else "{}"
                    )
                    print(f"AWS Response: {response}")

                    # Check if we actually got a valid response
                    if 'ProgressEvent' not in response:
                        return {
                            "status": "error",
                            "operation": operation,
                            "resource_type": resource_type,
                            "error": "Invalid response from AWS Cloud Control API",
                            "aws_response": str(response)
                        }

                    request_token = response.get('ProgressEvent', {}).get('RequestToken')
                    if not request_token:
                        return {
                            "status": "error",
                            "operation": operation,
                            "resource_type": resource_type,
                            "error": "No request token received from AWS",
                            "aws_response": str(response)
                        }

                    return {
                        "status": "success",
                        "operation": operation,
                        "resource_type": resource_type,
                        "request_token": request_token,
                        "message": f"Creating {resource_type}...",
                        "aws_response": str(response)
                    }

                except Exception as create_error:
                    print(f"Create Resource Error: {create_error}")
                    return {
                        "status": "error",
                        "operation": operation,
                        "resource_type": resource_type,
                        "error": f"Failed to create resource: {str(create_error)}",
                        "aws_error": str(create_error)
                    }

            elif operation == "list":
                try:
                    response = cloudcontrol.list_resources(TypeName=resource_type)
                    print(f"List Response: {response}")

                    resources = response.get('ResourceDescriptions', [])
                    return {
                        "status": "success",
                        "operation": operation,
                        "resource_type": resource_type,
                        "count": len(resources),
                        "resources": [json.loads(r.get('Properties', '{}')) for r in resources[:5]],  # Limit to 5
                        "aws_response": str(response)
                    }

                except Exception as list_error:
                    print(f"List Resources Error: {list_error}")
                    return {
                        "status": "error",
                        "operation": operation,
                        "resource_type": resource_type,
                        "error": f"Failed to list resources: {str(list_error)}",
                        "aws_error": str(list_error)
                    }

            elif operation == "read" and identifier:
                try:
                    response = cloudcontrol.get_resource(
                        TypeName=resource_type,
                        Identifier=identifier
                    )
                    print(f"Read Response: {response}")

                    return {
                        "status": "success",
                        "operation": operation,
                        "resource_type": resource_type,
                        "identifier": identifier,
                        "properties": json.loads(response['ResourceDescription']['Properties']),
                        "aws_response": str(response)
                    }

                except Exception as read_error:
                    print(f"Read Resource Error: {read_error}")
                    return {
                        "status": "error",
                        "operation": operation,
                        "resource_type": resource_type,
                        "identifier": identifier,
                        "error": f"Failed to read resource: {str(read_error)}",
                        "aws_error": str(read_error)
                    }

            else:
                return {
                    "status": "error",
                    "message": f"Operation {operation} not fully implemented in demo"
                }

        except Exception as e:
            print(f"General AWS Operation Error: {e}")
            return {
                "status": "error",
                "operation": operation,
                "resource_type": resource_type,
                "error": f"General AWS operation failed: {str(e)}",
                "aws_error": str(e)
            }

    def _query_cloudwatch_logs(self, function_name: str, hours_back: int = 1) -> Dict[str, Any]:
        """Query CloudWatch Logs for Lambda function errors"""

        try:
            session = self.aws_config.get_session()
            logs_client = session.client('logs')

            # Calculate time range
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours_back)

            # Find log group for the Lambda function
            log_group_name = f"/aws/lambda/{function_name}"

            # Filter for ERROR level logs
            response = logs_client.filter_log_events(
                logGroupName=log_group_name,
                startTime=int(start_time.timestamp() * 1000),
                endTime=int(end_time.timestamp() * 1000),
                filterPattern="ERROR"
            )

            error_logs = []
            for event in response.get('events', []):
                error_logs.append({
                    "timestamp": datetime.fromtimestamp(event['timestamp'] / 1000).isoformat(),
                    "message": event['message'],
                    "logStreamName": event['logStreamName']
                })

            return {
                "status": "success",
                "function_name": function_name,
                "hours_back": hours_back,
                "error_count": len(error_logs),
                "error_logs": error_logs[:10]  # Limit to 10 most recent errors
            }

        except Exception as e:
            return {
                "status": "error",
                "function_name": function_name,
                "error": str(e)
            }

    def _generate_summary(self, tool_name: str, tool_result: Dict[str, Any], user_question: str) -> str:
        """Generate natural language summary from tool results"""

        try:
            summary_prompt = SUMMARY_PROMPT.format(
                tool_name=tool_name,
                tool_result=json.dumps(tool_result, indent=2),
                user_question=user_question
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._build_system_prompt(),
                    },
                    {
                        "role": "user",
                        "content": summary_prompt,
                    },
                ],
                max_tokens=500,
                extra_body={"thinking": {"type": "disabled"}},
            )

            return response.choices[0].message.content or ""

        except Exception as e:
            return f"Summary generation failed: {str(e)}"

    def process_request(self, user_input: str, history: List[Dict] = None) -> str:
        """Process a user request using DeepSeek and AWS tools."""

        if history is None:
            history = []

        messages = [
            {"role": "system", "content": self._build_system_prompt()}
        ]

        # Keep only supported OpenAI-compatible history messages.
        for item in history:
            if item.get("role") in {"user", "assistant", "tool"} and "content" in item:
                messages.append(item)

        messages.append({"role": "user", "content": user_input})

        try:
            tools = self._format_tools()

            for _ in range(5):  # Limit agent iterations
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    max_tokens=2000,
                    extra_body={"thinking": {"type": "disabled"}},
                )

                assistant_message = response.choices[0].message
                tool_calls = assistant_message.tool_calls or []

                # No tool call: return the final answer.
                if not tool_calls:
                    answer = assistant_message.content or ""
                    history.extend([
                        {"role": "user", "content": user_input},
                        {"role": "assistant", "content": answer},
                    ])
                    return answer

                # Preserve the assistant's tool-call message in history.
                messages.append(
                    assistant_message.model_dump(exclude_none=True)
                )

                for tool_call in tool_calls:
                    tool_name = tool_call.function.name

                    try:
                        tool_input = json.loads(
                            tool_call.function.arguments
                        )

                        # Never execute arbitrary tool names.
                        if tool_name == "aws_cloud_control":
                            result = self._execute_aws_operation(
                                **tool_input
                            )
                        elif tool_name == "cloudwatch_logs":
                            result = self._query_cloudwatch_logs(
                                **tool_input
                            )
                        else:
                            result = {
                                "status": "error",
                                "error": "Unknown tool",
                            }

                    except (json.JSONDecodeError, TypeError, ValueError) as e:
                        result = {
                            "status": "error",
                            "error": f"Invalid tool arguments: {e}",
                        }
                    except Exception as e:
                        result = {
                            "status": "error",
                            "error": str(e),
                        }

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, default=str),
                    })

            return "Stopped: maximum tool-call iterations reached."

        except Exception as e:
            print(f"Error processing request: {e}")
            return f"Error processing request: {str(e)}"
