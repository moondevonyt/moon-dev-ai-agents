"""
Tick Data Collector

This script connects to the HyperLiquid WebSocket API to collect real-time tick data.
"""

import websocket
import json
import threading

class TickCollector:
    def __init__(self, symbol):
        self.symbol = symbol
        self.ws = None
        self.latest_tick = None
        self.is_connected = False
        websocket.enableTrace(True)

    def on_message(self, ws, message):
        self.latest_tick = json.loads(message)
        print(f"New tick received: {self.latest_tick}")

    def on_error(self, ws, error):
        print(f"WebSocket Error: {error}")
        self.is_connected = False

    def on_close(self, ws, close_status_code, close_msg):
        print("### WebSocket closed ###")
        self.is_connected = False

    def on_open(self, ws):
        print("### WebSocket opened ###")
        self.is_connected = True
        self.ws.send(json.dumps({
            "method": "subscribe",
            "subscription": {"type": "trades", "coin": self.symbol}
        }))

    def start(self):
        """Starts the WebSocket connection in a new thread."""
        self.ws = websocket.WebSocketApp("wss://api.hyperliquid.xyz/ws",
                                      on_message=self.on_message,
                                      on_error=self.on_error,
                                      on_close=self.on_close)
        self.ws.on_open = self.on_open

        # Run the WebSocket in a separate thread to avoid blocking
        wst = threading.Thread(target=self.ws.run_forever)
        wst.daemon = True
        wst.start()

    def get_latest_tick(self):
        """Returns the latest tick received from the WebSocket."""
        return self.latest_tick

    def stop(self):
        """Closes the WebSocket connection."""
        if self.ws:
            self.ws.close()
            self.is_connected = False
            print("WebSocket connection closed.")

if __name__ == "__main__":
    # Example usage
    collector = TickCollector(symbol='BTC')
    collector.start()

    # Keep the main thread alive to see the ticks coming in
    try:
        while True:
            pass
    except KeyboardInterrupt:
        collector.stop()
