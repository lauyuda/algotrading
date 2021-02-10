class AlgoTrading(QCAlgorithm):

    def Initialize(self):
        # Set the cash for backtest
        self.SetCash(100000)
        
        # Start and end dates for backtest
        self.SetStartDate(2017,1,1)
        self.SetEndDate(2020,11,25)
        
        # Add asset and indicators
        self.__macd = dict()
        self.__ema = dict()
        
        # self.equities = ["AAPL", "PG", "AMGN", "EXC", "LULU", "MNST", "TLT", "LQD", "BNDX", "GLD"]
        self.equities = ["ADBE", "PG", "AMD", "NVDA", "LULU", "MSFT", "TSLA", "CDNS", "VGLT", "NEM"]
        
        # Setting weights using MPT
        self.__weight = dict()
        self.__weight["ADBE"] = 0.12
        self.__weight["PG"] = 0.08
        self.__weight["AMD"] = 0.02
        self.__weight["NVDA"] = 0.02
        self.__weight["LULU"] = 0.06
        self.__weight["MSFT"] = 0.11
        self.__weight["TSLA"] = 0.03
        self.__weight["CDNS"] = 0.05
        self.__weight["VGLT"] = 0.47
        self.__weight["NEM"] = 0.02
        
        # Setting parameters for risk management
        self.__highestPrice = dict()
        self.__stopPrice = dict()
        
        for symbol in self.equities:
            self.AddEquity(symbol, Resolution.Daily)
            self.__highestPrice[symbol] = 0
            self.__stopPrice[symbol] = 0
            self.__macd[symbol] = self.MACD(symbol, 12, 26, 9, MovingAverageType.Exponential, Resolution.Daily)
            self.__ema[symbol] = self.EMA(symbol, 200, Resolution.Daily)
            
        self.SetWarmUp(200)
        self.stop = False
        
    def OnData(self, data):
        if self.stop: return
        equities = self.equities
        for symbol in equities:
            # wait for our macd to fully initialize
            if not self.__macd[symbol].IsReady: continue
            if not self.__ema[symbol].IsReady: continue
            
            # define a small tolerance on our checks to avoid bouncing
            tolerance = 0.0025
    
            holdings = self.Portfolio[symbol].Quantity
    
            signalDeltaPercent = (self.__macd[symbol].Current.Value - self.__macd[symbol].Signal.Current.Value)/self.__macd[symbol].Fast.Current.Value
             
            # if our macd is greater than our signal, then let's go long
            if holdings <= 0 and signalDeltaPercent > tolerance:
                #if self.__rsi[symbol].Current.Value < 30:
                #if self.__macd[symbol].Current.Value < tolerance and self.Securities[symbol].Price > self.__ema[symbol].Current.Value: 
                
                # longterm says buy as well
                self.SetHoldings(symbol, self.__weight[symbol])
    
            # if our macd is less than our signal, then let's liquidate
            elif holdings > 0 and signalDeltaPercent < -tolerance:
                if self.__macd[symbol].Current.Value > tolerance and self.Securities[symbol].Price < self.__ema[symbol].Current.Value:
                    self.Liquidate(symbol)
            
            # if price falls below stop price, then let's liquidate        
            elif self.Securities[symbol].Close < self.__stopPrice[symbol]:
                self.__highestPrice[symbol] = self.__stopPrice[symbol]
                self.__stopPrice[symbol] = self.__highestPrice[symbol] * 0.8
                self.Liquidate(symbol)
            
            # setting trailing stop loss    
            if self.Securities[symbol].Close > self.__highestPrice[symbol]:
                self.__highestPrice[symbol] = self.Securities[symbol].Close
                self.__stopPrice[symbol] = self.__highestPrice[symbol] * 0.95
             
            # if price falls way below, then automate message for investor to check portfolio    
            if self.Securities[symbol].Price < 0.9 * self.__stopPrice[symbol]:
                self.Notify.Email("lauyuda@gmail.com", "Securities Warning", 
                                "Possible changing market conditions. Monitor market and re-evaluate your portfolio.")
        
        # if prices fall due to algo fault or case of possible black swan, then stop trading    
        if self.Portfolio.TotalPortfolioValue < 0.85 * 100000:
            self.stop = True
            self.Liquidate()
            self.Notify.Email("lauyuda@gmail.com", "Investment Balance Alert", 
                                "Trading has been stopped. Please look into issue.")