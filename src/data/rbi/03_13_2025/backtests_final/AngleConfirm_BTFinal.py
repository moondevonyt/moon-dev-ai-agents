import pandas as pd
import numpy as np
from talib import GANNAAngLine, MA_Type as MA_TYPE

class AngleConfirm:
    """
    A trend-based trading strategy using William D. Gann's angular analysis combined with 5-period SMA for confirmation.
    """
    
    def __init__(self):
        self.risk_percent = 2
        self.stop_loss_pct = 0.5
        self.rr_ratio = 2

    def on_data(self, data):
        """Prepare indicators and store them."""
        # Create Gann Angle Lines
        high, low = data['high'], data['low']
        gann_lines = {
            MA_TYPE.SMA: [self.risk_percent],
            MA_TYPE.EWMA: [5]
        }
        
        self.add_indicator(GANNAAngLine(high, low), name="gann_angle")
        for indicator_name, parameters in gann_lines.items():
            self.add_indicator(MA_Type(high, parameters), name=f"ma_{indicator_name}")

    def on_bar(self):
        """Check conditions and generate trades."""
        data = self.data.current
        if len(data) < 60:  # Not enough historical bars for confirmation (adjust as needed)
            return

        # Get latest values from indicators
        last_gann_angle = self.get_indicator_value("gann_angle")
        last_ma_ewma = [self.get_indicator_value(f"ma_{p}") for p in [5]]
        
        # Check trend confirmation using 5-period SMA
        if (last_ma_ewma[0] > last_ma_ewma[1] and 
            ((data['high'][-2] + data['low'][-2]) / 2) > last_gann_angle[-1]):
            
            # Long entry condition
            if last_ma_ewma[0] > last_gann_angle[-1]:
                position = self.position.current
                if not position:
                    size = (self.risk_percent * 2) / ((last_ma_ewma[0] - last_gann_angle[-1]) * 
                            np.diff(data['high'][-5:]).max())
                    trade = self.marketorder(data['close'][-1], 'long', size=size)
                    self.position.add(trade)

                # Short entry condition
            elif last_ma_ewma[1] > last_gann_angle[-1]:
                position = self.position.current
                if not position:
                    size = (self.risk_percent * 2) / ((last_ma_ewma[1] - last_gann_angle[-1]) *
                            np.diff(data['low'][-5:]).max())
                    trade = self.marketorder(data['close'][-1], 'short', size=size)
                    self.position.add(trade)

        # Close positions if conditions are not met
        else:
            for pos in self.position.current:
                self.position.close(pos, 'exiting')

    def on_exit(self):
        """Clean up after exiting trades."""
        self.position.clear()