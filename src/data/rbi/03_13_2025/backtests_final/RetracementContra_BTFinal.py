    def buy(self):
        if self.position_exists:
            return

        # Calculate position size based on risk (e.g., stop loss)
        # and other factors, then cap by available capital.
        position_size = min(
            int(round(abs((self.risk_level / 100) * 
                self.equity) / self.data.Close[-1]))),
            int(self.equity // self.data.Close[-1])
        )

        sl = Decimal(str(self.data.Close[-1] - (self.risk_level / 100) *
            abs(self.position_size)))
        tp = Decimal(str(self.data.Close[-1] + (self.take_profit_risk /
                100) * abs(self.position_size)))

        self.position = Position(
            account_name=self.account_name,
            equity=self.equity,
            instrument=self.instrument,
            side=Side.Buy,
            type='Market',
            position_size=position_size,
            sl=sl,
            tp=tp
        )

    def sell(self):