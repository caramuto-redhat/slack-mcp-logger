import os
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import re
from pathlib import Path

SLACK_API_BASE = "https://slack.com/api"
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
LOGS_CHANNEL_ID = os.environ["LOGS_CHANNEL_ID"]

mcp = FastMCP(
    "slack", settings={"host": "127.0.0.1" if MCP_TRANSPORT == "stdio" else "0.0.0.0"}
)


async def make_request(
    url: str, payload: dict[str, Any] | None = None
) -> dict[str, Any] | None:
    if MCP_TRANSPORT == "stdio":
        xoxc_token = os.environ["SLACK_XOXC_TOKEN"]
        xoxd_token = os.environ["SLACK_XOXD_TOKEN"]
        user_agent = "MCP-Server/1.0"
    else:
        request_headers = mcp.get_context().request_context.request.headers
        xoxc_token = request_headers["X-Slack-Web-Token"]
        xoxd_token = request_headers["X-Slack-Cookie-Token"]
        user_agent = request_headers.get("User-Agent", "MCP-Server/1.0")

    headers = {
        "Authorization": f"Bearer {xoxc_token}",
        "Content-Type": "application/json",
        "User-Agent": user_agent,
    }

    cookies = {"d": xoxd_token}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url, headers=headers, cookies=cookies, json=payload, timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(e)
            return None


async def log_to_slack(message: str):
    await post_message(LOGS_CHANNEL_ID, message, skip_log=True)


# Validate and convert thread_ts if needed
def convert_thread_ts(ts: str) -> str:
    # If ts is already in the correct format, return as is
    if re.match(r"^\d+\.\d+$", ts):
        return ts
    # If ts is a long integer string (from Slack URL), convert it
    if re.match(r"^\d{16}$", ts):
        return f"{ts[:10]}.{ts[10:]}"
    return ""


@mcp.tool()
async def get_server_logs(log_file_path: str, lines: int = 50) -> str:
    """Read recent logs from MCP server log files.
    
    Args:
        log_file_path: Path to log file (e.g., 'logs/pipeline_bot.log')
        lines: Number of recent lines to read (default: 50)
    
    Returns:
        String containing the recent log lines
    """
    await log_to_slack(f"Reading {lines} lines from log file: {log_file_path}")
    
    try:
        # Security: Resolve path and ensure it's within allowed directories
        log_path = Path(log_file_path).resolve()
        
        # Optional: Restrict to specific directories (uncomment if needed)
        # allowed_dirs = [Path("logs").resolve(), Path("/var/log").resolve()]
        # if not any(str(log_path).startswith(str(allowed_dir)) for allowed_dir in allowed_dirs):
        #     return f"Error: Access denied to {log_file_path}"
        
        if not log_path.exists():
            return f"Error: Log file not found: {log_file_path}"
        
        if not log_path.is_file():
            return f"Error: Path is not a file: {log_file_path}"
        
        # Read the last N lines efficiently
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as file:
            # For large files, read from end
            if log_path.stat().st_size > 1024 * 1024:  # 1MB
                # Use tail-like approach for large files
                file.seek(0, 2)  # Go to end
                file_size = file.tell()
                
                # Estimate bytes to read (roughly 100 chars per line)
                bytes_to_read = min(lines * 100, file_size)
                file.seek(max(0, file_size - bytes_to_read))
                
                # Read and split into lines
                content = file.read()
                all_lines = content.split('\n')
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            else:
                # For small files, read all and take last N lines
                all_lines = file.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        # Clean up lines and format
        cleaned_lines = [line.rstrip() for line in recent_lines if line.strip()]
        
        if not cleaned_lines:
            return f"Log file is empty: {log_file_path}"
        
        # Format with metadata
        result = f"📄 **{log_file_path}** (last {len(cleaned_lines)} lines):\n"
        result += "```\n"
        result += "\n".join(cleaned_lines)
        result += "\n```"
        
        return result
        
    except PermissionError:
        return f"Error: Permission denied reading {log_file_path}"
    except Exception as e:
        return f"Error reading log file: {str(e)}"


@mcp.tool()
async def get_channel_history(channel_id: str) -> list[dict[str, Any]]:
    """Get the history of a channel."""
    await log_to_slack(f"Getting history of channel <#{channel_id}>")
    url = f"{SLACK_API_BASE}/conversations.history"
    payload = {"channel": channel_id}
    data = await make_request(url, payload=payload)
    if data and data.get("ok"):
        return data.get("messages", [])


@mcp.tool()
async def post_message(
    channel_id: str, message: str, thread_ts: str = "", skip_log: bool = False
) -> bool:
    """Post a message to a channel."""
    if not skip_log:
        await log_to_slack(f"Posting message to channel <#{channel_id}>: {message}")
    await join_channel(channel_id, skip_log=skip_log)
    url = f"{SLACK_API_BASE}/chat.postMessage"
    payload = {"channel": channel_id, "text": message}
    if thread_ts:
        payload["thread_ts"] = convert_thread_ts(thread_ts)
    data = await make_request(url, payload=payload)
    return data.get("ok")


@mcp.tool()
async def post_command(
    channel_id: str, command: str, text: str, skip_log: bool = False
) -> bool:
    """Post a command to a channel."""
    if not skip_log:
        await log_to_slack(
            f"Posting command to channel <#{channel_id}>: {command} {text}"
        )
    await join_channel(channel_id, skip_log=skip_log)
    url = f"{SLACK_API_BASE}/chat.command"
    payload = {"channel": channel_id, "command": command, "text": text}
    data = await make_request(url, payload=payload)
    return data.get("ok")


@mcp.tool()
async def add_reaction(channel_id: str, message_ts: str, reaction: str) -> bool:
    """Add a reaction to a message."""
    await log_to_slack(
        f"Adding reaction to message {message_ts} in channel <#{channel_id}>: :{reaction}:"
    )
    url = f"{SLACK_API_BASE}/reactions.add"
    payload = {"channel": channel_id, "name": reaction, "timestamp": convert_thread_ts(message_ts)}
    data = await make_request(url, payload=payload)
    return data.get("ok")


@mcp.tool()
async def whoami() -> str:
    """Checks authentication & identity."""
    await log_to_slack("Checking authentication & identity")
    url = f"{SLACK_API_BASE}/auth.test"
    data = await make_request(url)
    return data.get("user")


@mcp.tool()
async def join_channel(channel_id: str, skip_log: bool = False) -> bool:
    """Join a channel."""
    if not skip_log:
        await log_to_slack(f"Joining channel <#{channel_id}>")
    url = f"{SLACK_API_BASE}/conversations.join"
    payload = {"channel": channel_id}
    data = await make_request(url, payload=payload)
    return data.get("ok")


if __name__ == "__main__":
    mcp.run(transport=MCP_TRANSPORT)
