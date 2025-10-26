#!/usr/bin/env python3
"""
Test script for quantitative agent startup
Tests the async initialization and event loop setup
"""

import asyncio
import sys
import os
from termcolor import cprint

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.agents.quant.anomaly_detection_agent import AnomalyDetectionAgent
from src.agents.quant.signal_aggregation_agent import SignalAggregationAgent


async def test_single_agent():
    """Test single agent initialization and startup"""
    cprint("\n🧪 Test 1: Single Agent Initialization", "cyan", attrs=["bold"])
    
    agent = AnomalyDetectionAgent()
    cprint(f"✅ Agent created: {agent.type}", "green")
    
    try:
        # Initialize
        await agent.initialize()
        cprint("✅ Agent initialized successfully", "green")
        
        # Run for 5 seconds
        cprint("⏱️  Running agent for 5 seconds...", "yellow")
        await asyncio.wait_for(agent.run_event_loop(), timeout=5.0)
        
    except asyncio.TimeoutError:
        cprint("✅ Agent ran successfully for 5 seconds", "green")
    except Exception as e:
        cprint(f"❌ Error: {str(e)}", "red")
        raise
    finally:
        await agent.shutdown()
        cprint("✅ Agent shutdown complete", "green")


async def test_multiple_agents():
    """Test multiple agents running concurrently"""
    cprint("\n🧪 Test 2: Multiple Agents Concurrent Execution", "cyan", attrs=["bold"])
    
    agents = [
        AnomalyDetectionAgent(),
        SignalAggregationAgent(),
    ]
    
    cprint(f"✅ Created {len(agents)} agents", "green")
    
    try:
        # Initialize all agents
        for agent in agents:
            await agent.initialize()
            cprint(f"✅ {agent.type} initialized", "green")
        
        # Run all agents concurrently for 5 seconds
        cprint("⏱️  Running all agents concurrently for 5 seconds...", "yellow")
        await asyncio.wait_for(
            asyncio.gather(*[agent.run_event_loop() for agent in agents]),
            timeout=5.0
        )
        
    except asyncio.TimeoutError:
        cprint("✅ All agents ran successfully for 5 seconds", "green")
    except Exception as e:
        cprint(f"❌ Error: {str(e)}", "red")
        raise
    finally:
        # Shutdown all agents
        for agent in agents:
            await agent.shutdown()
        cprint("✅ All agents shutdown complete", "green")


async def test_agent_event_handling():
    """Test agent event handling capabilities"""
    cprint("\n🧪 Test 3: Agent Event Handling", "cyan", attrs=["bold"])
    
    agent = AnomalyDetectionAgent()
    
    try:
        await agent.initialize()
        cprint("✅ Agent initialized", "green")
        
        # Check event handlers are registered
        if agent._event_handlers:
            cprint(f"✅ Event handlers registered: {list(agent._event_handlers.keys())}", "green")
        else:
            cprint("⚠️  No event handlers registered", "yellow")
        
        # Check subscribed topics
        if agent.subscribed_topics:
            cprint(f"✅ Subscribed to topics: {agent.subscribed_topics}", "green")
        else:
            cprint("⚠️  No topics subscribed", "yellow")
        
    except Exception as e:
        cprint(f"❌ Error: {str(e)}", "red")
        raise
    finally:
        await agent.shutdown()


async def main():
    """Run all tests"""
    cprint("\n" + "="*60, "white", attrs=["bold"])
    cprint("🔬 Quantitative Agent Startup Tests", "white", attrs=["bold"])
    cprint("="*60 + "\n", "white", attrs=["bold"])
    
    try:
        # Test 1: Single agent
        await test_single_agent()
        
        # Test 2: Multiple agents
        await test_multiple_agents()
        
        # Test 3: Event handling
        await test_agent_event_handling()
        
        cprint("\n" + "="*60, "green", attrs=["bold"])
        cprint("✅ All tests passed!", "green", attrs=["bold"])
        cprint("="*60 + "\n", "green", attrs=["bold"])
        
    except Exception as e:
        cprint("\n" + "="*60, "red", attrs=["bold"])
        cprint(f"❌ Tests failed: {str(e)}", "red", attrs=["bold"])
        cprint("="*60 + "\n", "red", attrs=["bold"])
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        cprint("\n⚠️  Tests interrupted by user", "yellow")
        sys.exit(0)
