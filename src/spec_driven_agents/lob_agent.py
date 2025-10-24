"""
LOB (Limit Order Book) Agent

This agent is responsible for managing trade-level risk by analyzing the Limit Order Book.
"""

from src.nice_funcs_hyperliquid import ask_bid

class LOBAgent:
    def __init__(self):
        pass

    def get_order_book(self, symbol):
        """
        Fetches the Limit Order Book for a given symbol.
        """
        ask, bid, l2_data = ask_bid(symbol)
        return l2_data

    def analyze_order_book_imbalance(self, order_book):
        """
        Analyzes the order book to identify imbalances.
        """
        bids = order_book[0]
        asks = order_book[1]

        total_bid_volume = sum([float(bid['n']) for bid in bids])
        total_ask_volume = sum([float(ask['n']) for ask in asks])

        if total_bid_volume == 0:
            return 0

        imbalance = (total_bid_volume - total_ask_volume) / total_bid_volume
        return imbalance

    def run(self, symbol):
        """
        Fetches and analyzes the order book for a given symbol.
        """
        order_book = self.get_order_book(symbol)
        imbalance = self.analyze_order_book_imbalance(order_book)
        return imbalance
