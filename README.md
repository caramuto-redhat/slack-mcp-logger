# slack-mcp

MCP server for Slack with log monitoring capabilities

## 🚀 Features

### Core Slack Integration
- **Channel Management**: Join channels and retrieve message history
- **Messaging**: Post messages and threaded replies
- **Commands**: Execute Slack slash commands
- **Reactions**: Add emoji reactions to messages
- **Authentication**: Verify identity and permissions

### Log Monitoring & Team Collaboration
- **Server Log Reading**: Access logs from any MCP server or application
- **Automated Alerts**: Post log analysis to Slack channels
- **Team Debugging**: Share logs instantly with team members
- **Multi-Server Monitoring**: Monitor logs from multiple services

## 🏗️ Architecture

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│    User/Team        │───▶│   Pipeline-Toolkit  │───▶│   Slack-MCP-Logger  │
│  (Natural Language) │    │   (AI Orchestrator) │    │   (Slack Specialist)│
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
                                      ▲                          │
                                      │                          ▼
                           ┌─────────────────────┐    ┌─────────────────────┐
                           │   Log Files         │    │    Slack API        │
                           │ • pipeline_bot.log  │    │ • Channels          │
                           │ • testing_farm.log  │    │ • Messages          │
                           │ • application.log   │    │ • Reactions         │
                           │ • error.log         │    │ • Commands          │
                           └─────────────────────┘    └─────────────────────┘
```

### Workflow Example
1. **User**: *"Check recent pipeline logs and alert team if errors found"*
2. **Pipeline-Toolkit AI**: Understands intent, orchestrates actions
3. **Slack-MCP-Logger**: 
   - Reads logs via `get_server_logs()`
   - Posts alerts via `post_message()`
   - Adds reactions via `add_reaction()`
4. **Result**: Team gets notified in Slack with actionable log data

## 🛠️ Built-in Tools

### 1. **Channel Management**
```python
get_channel_history(channel_id: str) -> list[dict]
join_channel(channel_id: str, skip_log: bool = False) -> bool
```

### 2. **Messaging**
```python
post_message(channel_id: str, message: str, thread_ts: str = "", skip_log: bool = False) -> bool
post_command(channel_id: str, command: str, text: str, skip_log: bool = False) -> bool
```

### 3. **Reactions & Interactions**
```python
add_reaction(channel_id: str, message_ts: str, reaction: str) -> bool
```

### 4. **Authentication**
```python
whoami() -> str
```

### 5. **🆕 Log Monitoring**
```python
get_server_logs(log_file_path: str, lines: int = 50) -> str
```

## 📋 Usage Examples

### Log Monitoring & Team Alerts
```python
# Read recent pipeline logs
logs = get_server_logs("logs/pipeline_bot.log", 100)

# Alert team with logs
post_message("C-DEV-TEAM", f"🚨 Pipeline Issues:\n{logs}")

# Mark for urgent attention  
add_reaction("C-DEV-TEAM", message_ts, "rotating_light")
```

### Automated Monitoring Workflow
```python
# Check multiple log sources
pipeline_logs = get_server_logs("logs/pipeline_bot.log", 50)
error_logs = get_server_logs("/var/log/app/error.log", 30)

# Post to different channels based on content
if "ERROR" in pipeline_logs:
    post_message("C-ALERTS", f"⚠️ Pipeline errors:\n{pipeline_logs}")
    
if "CRITICAL" in error_logs:
    post_message("C-INCIDENTS", f"🚨 Critical app errors:\n{error_logs}")
```

### Daily Team Updates
```python
# Morning standup automation
daily_logs = get_server_logs("logs/pipeline_bot.log", 200)
post_message("C-STANDUP", f"☀️ Overnight activity summary:\n{daily_logs}")
```

## 🚀 Running with Podman or Docker

You can run the slack-mcp server in a container using Podman or Docker:

Example configuration for running with Podman:

```json
{
  "mcpServers": {
    "slack": {
      "command": "podman",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e", "SLACK_XOXC_TOKEN",
        "-e", "SLACK_XOXD_TOKEN",
        "-e", "MCP_TRANSPORT",
        "-e", "LOGS_CHANNEL_ID",
        "quay.io/redhat-ai-tools/slack-mcp"
      ],
      "env": {
        "SLACK_XOXC_TOKEN": "xoxc-...",
        "SLACK_XOXD_TOKEN": "xoxd-...",
        "MCP_TRANSPORT": "stdio",
        "LOGS_CHANNEL_ID": "C7000000",
      }
    }
  }
}
```

## 🌐 Running with non-stdio transport

To run the server with a non-stdio transport (such as SSE), set the `MCP_TRANSPORT` environment variable to a value other than `stdio` (e.g., `sse`).

Example configuration to connect to a non-stdio MCP server:

```json
{
  "mcpServers": {
    "slack": {
      "url": "https://slack-mcp.example.com/sse",
      "headers": {
        "X-Slack-Web-Token": "xoxc-...",
        "X-Slack-Cookie-Token": "xoxd-..."
      }
    }
  }
}
```

## 🔐 Authentication

Extract your Slack XOXC and XOXD tokens easily using browser extensions or Selenium automation: https://github.com/maorfr/slack-token-extractor.

## 🔧 Environment Variables

- `SLACK_XOXC_TOKEN`: Slack web token (required)
- `SLACK_XOXD_TOKEN`: Slack cookie token (required) 
- `MCP_TRANSPORT`: Transport mode (`stdio` or `sse`, default: `stdio`)
- `LOGS_CHANNEL_ID`: Channel ID for logging MCP operations (required)
- `LOG_BASE_PATH`: Optional base path for log file access security

## 🤝 Integration with Pipeline-Toolkit

This MCP server works seamlessly with [Pipeline-Toolkit](https://github.com/your-org/pipeline-toolkit) to provide:

- **Natural Language Processing**: Ask questions in plain English
- **Intelligent Tool Selection**: AI chooses the right tools automatically
- **Multi-Server Coordination**: Monitor logs from multiple MCP servers
- **Team Collaboration**: Share insights and alerts through Slack

### Example Integration
```bash
# In Pipeline-Toolkit
"Check recent logs and update the team if there are any errors"

# Results in:
# 1. get_server_logs("logs/pipeline_bot.log", 100)
# 2. AI analysis of log content
# 3. post_message("C-TEAM", error_summary) if issues found
# 4. add_reaction() for team attention
```

## 📊 Use Cases

- **DevOps Monitoring**: Automated log analysis and team alerts
- **Incident Response**: Quick log sharing and team coordination
- **Daily Standups**: Automated activity summaries
- **Build Monitoring**: Pipeline status updates and failure alerts
- **Multi-Service Debugging**: Centralized log access across services
