"""
🌙 Moon Dev's Alternative Data Agent
Ingests and normalizes alternative data sources

Implements alternative data collection:
- Social media velocity tracking (Twitter mentions)
- On-chain metrics (transaction velocity, patterns)
- GitHub activity tracking (commits, contributors)
- Data normalization (z-scores, percentiles)
"""

import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from termcolor import cprint

from src.agents.quant.base_quant_agent import BaseQuantAgent
from src.agents.quant.statistical_utils import calculate_zscore
from src.core.models import Event, EventType
from src.config import (
    ALT_DATA_SOCIAL_INTERVAL_SECONDS,
    ALT_DATA_ONCHAIN_INTERVAL_SECONDS,
    ALT_DATA_GITHUB_INTERVAL_SECONDS,
    ALT_DATA_NORMALIZATION_WINDOW_DAYS
)


@dataclass
class AlternativeDataMetric:
    """Alternative data metric."""
    token: str
    source: str  # twitter, github, onchain
    metric_type: str  # mention_velocity, commit_frequency, tx_velocity
    raw_value: float
    z_score: float
    percentile: float
    timestamp: datetime


class AlternativeDataAgent(BaseQuantAgent):
    """Ingests alternative data (social, on-chain, GitHub)."""
    
    def __init__(self):
        super().__init__(
            agent_type="alternative_data",
            subscribed_topics=[]
        )
        
        # Historical data for normalization
        self.metric_history: Dict[str, List[float]] = {}  # metric_key -> values
        
        cprint("✅ Alternative Data Agent initialized", "green")
    
    async def initialize(self):
        """Initialize agent and start collection tasks."""
        await super().initialize()
        
        # Start data collection tasks
        asyncio.create_task(self._social_data_loop())
        asyncio.create_task(self._onchain_data_loop())
        asyncio.create_task(self._github_data_loop())
    
    async def _social_data_loop(self):
        """Collect social media data periodically."""
        while self.is_running:
            await asyncio.sleep(ALT_DATA_SOCIAL_INTERVAL_SECONDS)
            
            try:
                await self._collect_social_data()
            except Exception as e:
                cprint(f"⚠️ Error collecting social data: {str(e)}", "yellow")
    
    async def _onchain_data_loop(self):
        """Collect on-chain data periodically."""
        while self.is_running:
            await asyncio.sleep(ALT_DATA_ONCHAIN_INTERVAL_SECONDS)
            
            try:
                await self._collect_onchain_data()
            except Exception as e:
                cprint(f"⚠️ Error collecting on-chain data: {str(e)}", "yellow")
    
    async def _github_data_loop(self):
        """Collect GitHub data periodically."""
        while self.is_running:
            await asyncio.sleep(ALT_DATA_GITHUB_INTERVAL_SECONDS)
            
            try:
                await self._collect_github_data()
            except Exception as e:
                cprint(f"⚠️ Error collecting GitHub data: {str(e)}", "yellow")
    
    async def _collect_social_data(self):
        """Collect social media velocity data."""
        # TODO: Integrate with Twitter API or existing tweet_agent
        # For now, placeholder implementation
        
        tokens = ["BTC", "ETH", "SOL"]  # Example tokens
        
        for token in tokens:
            # Simulate mention count (replace with actual API call)
            mention_count = np.random.randint(10, 1000)
            
            # Calculate velocity (mentions per hour)
            velocity = mention_count / 1.0  # Per hour
            
            # Normalize and emit
            await self._process_and_emit_metric(
                token=token,
                source="twitter",
                metric_type="mention_velocity",
                raw_value=velocity
            )
    
    async def _collect_onchain_data(self):
        """Collect on-chain metrics."""
        # TODO: Integrate with Solana RPC or existing blockchain data
        # For now, placeholder implementation
        
        tokens = ["BTC", "ETH", "SOL"]
        
        for token in tokens:
            # Simulate transaction velocity (replace with actual RPC call)
            tx_velocity = np.random.randint(100, 10000)
            
            # Normalize and emit
            await self._process_and_emit_metric(
                token=token,
                source="onchain",
                metric_type="tx_velocity",
                raw_value=tx_velocity
            )
    
    async def _collect_github_data(self):
        """Collect GitHub activity data."""
        # TODO: Integrate with GitHub API
        # For now, placeholder implementation
        
        projects = {"BTC": "bitcoin/bitcoin", "ETH": "ethereum/go-ethereum"}
        
        for token, repo in projects.items():
            # Simulate commit frequency (replace with actual API call)
            commit_frequency = np.random.randint(1, 50)
            
            # Normalize and emit
            await self._process_and_emit_metric(
                token=token,
                source="github",
                metric_type="commit_frequency",
                raw_value=commit_frequency
            )
    
    async def _process_and_emit_metric(
        self,
        token: str,
        source: str,
        metric_type: str,
        raw_value: float
    ):
        """Process metric and emit normalized data."""
        metric_key = f"{token}_{source}_{metric_type}"
        
        # Initialize history if needed
        if metric_key not in self.metric_history:
            self.metric_history[metric_key] = []
        
        # Add to history
        self.metric_history[metric_key].append(raw_value)
        
        # Trim old data
        cutoff_days = ALT_DATA_NORMALIZATION_WINDOW_DAYS
        if len(self.metric_history[metric_key]) > cutoff_days * 24:  # Assuming hourly data
            self.metric_history[metric_key] = self.metric_history[metric_key][-cutoff_days * 24:]
        
        # Calculate z-score
        if len(self.metric_history[metric_key]) >= 10:
            mean = np.mean(self.metric_history[metric_key])
            std = np.std(self.metric_history[metric_key])
            z_score = calculate_zscore(raw_value, mean, std)
            
            # Calculate percentile
            percentile = (np.sum(np.array(self.metric_history[metric_key]) <= raw_value) / 
                         len(self.metric_history[metric_key]) * 100)
        else:
            z_score = 0.0
            percentile = 50.0
        
        # Emit event
        await self.emit_event(
            event_type=EventType.DATA_ALTERNATIVE,
            token=token,
            data={
                "source": source,
                "metric_type": metric_type,
                "raw_value": float(raw_value),
                "z_score": float(z_score),
                "percentile": float(percentile),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        cprint(f"📊 {token} {source}.{metric_type}: {raw_value:.0f} (z={z_score:.2f}, p={percentile:.0f})", "cyan")


if __name__ == "__main__":
    agent = AlternativeDataAgent()
    agent.run()
