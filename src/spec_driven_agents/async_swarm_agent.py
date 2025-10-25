"""
Asynchronous Swarm Agent

This agent is responsible for querying multiple AI models asynchronously.
"""

import asyncio
import aiohttp

class AsyncSwarmAgent:
    def __init__(self, model_urls):
        self.model_urls = model_urls

    async def fetch(self, session, url, prompt):
        """
        Fetches a response from a single AI model.
        """
        async with session.post(url, json={'prompt': prompt}) as response:
            return await response.json()

    async def query(self, prompt):
        """
        Queries all AI models asynchronously and returns their responses.
        """
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch(session, url, prompt) for url in self.model_urls]
            responses = await asyncio.gather(*tasks)
            return responses
