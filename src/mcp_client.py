"""
🌙 BB1151's MCP Client - Minimal Python Client for MCP Servers
Connects to MCP servers (like Smithery deep-research) via JSON-RPC over STDIN/STDOUT
"""
import json
import subprocess
import threading
import uuid
from queue import Queue, Empty
from typing import Dict, List, Optional, Any

class MCPClient:
    """Lightweight MCP client that communicates with MCP servers via JSON-RPC"""
    
    def __init__(self, command: str, args: List[str], timeout: int = 10, env: Optional[Dict[str, str]] = None):
        """
        Initialize MCP client and start the server process
        
        Args:
            command: Command to run (e.g., "npx")
            args: Arguments for the command (e.g., ["-y", "mcp-deep-research@latest"])
            timeout: Default timeout for RPC calls in seconds
            env: Environment variables to pass to the server process
        """
        self.timeout = timeout
        self.proc = None
        self._out_queue = Queue()
        self._reader_thread = None
        
        try:
            # Prepare environment variables
            import os
            process_env = os.environ.copy()
            if env:
                process_env.update(env)
            
            # Start the MCP server process
            self.proc = subprocess.Popen(
                [command, *args],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=process_env
            )
            
            # Start reader thread
            self._reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
            self._reader_thread.start()
            
            # Fetch available tools
            self.tools = self.list_tools()
            
        except Exception as e:
            self.close()
            raise RuntimeError(f"Failed to initialize MCP client: {e}")
    
    def _reader_loop(self):
        """Background thread that reads stdout from MCP server"""
        try:
            for line in self.proc.stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                    self._out_queue.put(msg)
                except json.JSONDecodeError:
                    # Ignore non-JSON output (e.g., server logs)
                    pass
        except Exception:
            pass
    
    def _rpc(self, method: str, params: Dict) -> Any:
        """
        Make a JSON-RPC call to the MCP server
        
        Args:
            method: RPC method name (e.g., "tools/list")
            params: Method parameters as dict
            
        Returns:
            Result from the server
        """
        if not self.proc or self.proc.poll() is not None:
            raise RuntimeError("MCP server process is not running")
        
        req_id = str(uuid.uuid4())
        payload = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params
        }
        
        try:
            # Send request
            self.proc.stdin.write(json.dumps(payload) + "\n")
            self.proc.stdin.flush()
            
            # Wait for matching response
            while True:
                try:
                    msg = self._out_queue.get(timeout=self.timeout)
                except Empty:
                    raise TimeoutError(f"MCP call timeout for {method}")
                
                if msg.get("id") == req_id:
                    if "error" in msg:
                        raise RuntimeError(f"MCP error: {msg['error']}")
                    return msg.get("result")
                    
        except BrokenPipeError:
            raise RuntimeError("MCP server connection broken")
    
    def list_tools(self) -> Dict:
        """
        List available tools from the MCP server
        
        Returns:
            Dict with 'tools' key containing list of tool definitions
        """
        return self._rpc("tools/list", {})
    
    def call_tool(self, tool_name: str, arguments: Dict) -> Any:
        """
        Call a specific tool on the MCP server
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments as dict
            
        Returns:
            Tool result
        """
        return self._rpc("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
    
    def get_tool_names(self) -> List[str]:
        """Get list of available tool names"""
        tools = self.tools.get("tools", [])
        return [t.get("name", "") for t in tools]
    
    def find_tool(self, keywords: List[str]) -> Optional[str]:
        """
        Find first tool matching any of the keywords
        
        Args:
            keywords: List of keywords to search for (case-insensitive)
            
        Returns:
            Tool name or None if not found
        """
        for tool in self.tools.get("tools", []):
            tool_name = tool.get("name", "").lower()
            for keyword in keywords:
                if keyword.lower() in tool_name:
                    return tool.get("name")
        return None
    
    def close(self):
        """Close the MCP server process"""
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=2)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass
            finally:
                self.proc = None


# Example usage
if __name__ == "__main__":
    # Example: Connect to Smithery deep-research
    client = MCPClient(
        command="npx",
        args=[
            "-y",
            "@smithery/cli@latest",
            "run",
            "@baranwang/mcp-deep-research"
            # Add --key and --profile if needed
        ]
    )
    
    print("Available tools:", client.get_tool_names())
    
    # Find and call research tool
    research_tool = client.find_tool(["research", "search"])
    if research_tool:
        result = client.call_tool(research_tool, {
            "query": "latest crypto market trends"
        })
        print("Result:", result)
    
    client.close()
