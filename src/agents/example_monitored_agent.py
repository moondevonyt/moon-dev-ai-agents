"""
🌙 Example: How to Add Health Monitoring to Your Agents
This shows how to integrate the health monitor into existing agents
"""

from agent_health_monitor import get_monitor
import time

class ExampleMonitoredAgent:
    """Example agent with health monitoring"""

    def __init__(self):
        self.monitor = get_monitor()
        self.agent_name = "example_agent"

    def run(self):
        """Main agent logic with monitoring"""
        try:
            # Log that agent is starting
            self.monitor.heartbeat(
                agent_name=self.agent_name,
                status="running",
                metadata={"action": "starting_analysis"}
            )

            # Your actual agent logic here
            result = self._do_trading_logic()

            # Log successful completion
            self.monitor.heartbeat(
                agent_name=self.agent_name,
                status="success",
                metadata={
                    "action": "completed",
                    "result": result
                }
            )

            return result

        except Exception as e:
            # Log error
            self.monitor.heartbeat(
                agent_name=self.agent_name,
                status="error",
                metadata={"error": str(e)}
            )
            raise

    def _do_trading_logic(self):
        """Placeholder for actual trading logic"""
        # Example: Check API health
        self._check_api_health()

        # Your logic here
        return {"trades": 0, "analysis": "completed"}

    def _check_api_health(self):
        """Example API health check"""
        import requests
        from time import time as timer

        # Example: Check BirdEye API
        start = timer()
        try:
            response = requests.get("https://public-api.birdeye.so/public/tokenlist", timeout=5)
            response_time = timer() - start

            if response_time > 3:
                status = "slow"
            else:
                status = "up"

            self.monitor.log_api_status(
                api_name="birdeye",
                status=status,
                response_time=response_time
            )
        except Exception as e:
            self.monitor.log_api_status(
                api_name="birdeye",
                status="down",
                error=str(e)
            )


# HOW TO INTEGRATE INTO EXISTING AGENTS:
"""
1. Add import at top of agent file:
   from agent_health_monitor import get_monitor

2. In __init__ or at module level:
   self.monitor = get_monitor()

3. At start of run() method:
   self.monitor.heartbeat(agent_name="my_agent", status="running")

4. After successful execution:
   self.monitor.heartbeat(agent_name="my_agent", status="success")

5. In exception handlers:
   self.monitor.heartbeat(agent_name="my_agent", status="error", metadata={"error": str(e)})

6. For API calls, wrap with timing:
   start = time.time()
   try:
       response = api_call()
       self.monitor.log_api_status("api_name", "up", time.time() - start)
   except:
       self.monitor.log_api_status("api_name", "down", error=str(e))
"""
