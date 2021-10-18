import numpy as np
import pandas as pd
import yfinance as yf 
from pandas_datareader import data as pdr
import matplotlib.pyplot as plt
from collections import defaultdict
yf.pdr_override() 

class Backtester:
    """
    buy_signal_func should work on only closing data and window of some length and return 1/0 or True/False
    
    sell_signal_func works on window, curr_price and buy_price
    return 1/0 or True/False
    """
    def __init__(self, buy_signal_func, sell_signal_func):
        self.buy_signal_func = buy_signal_func
        self.sell_signal_func = sell_signal_func     
        self.hist_data = None
        self.signals = None
        self.tickers = None
        
    
    def mount_data(self, raw_data):
        """
        Args:
            raw_data ([type]): [raw_data should be dataframe or be able to load as df using pd.DataFrame(raw_data)]
        """
        if type(raw_data) == pd.DataFrame:
           self. hist_data = raw_data
        else:
            self.hist_data = pd.DataFrame(raw_data)
        self.tickers = self.hist_data.columns
    
    def load_data_from_file(self, path):
        if path.endswith('.csv'):
            self.hist_data = pd.read_csv(path)
        elif path.endswith('.pkl'):
            self.hist_data = pd.read_pkl(path)
        self.tickers= self.hist_data.columns


    def download_data(self,tickers, period):
        """
        Args:
            tickers ([type]): [list of tickers to be looked at]
            period ([type]): [(start_date, end_date) as 'yyyy-mm-dd']
        """
        self.hist_data =  pdr.get_data_yahoo(tickers=tickers,start=period[0],end=period[1])["Adj Close"]
        self.tickers = tickers

    def save_data(self, filename, format):
        if format in ["pickle" ,"pkl", ".pkl"]:
            path = filename +".pkl"
            self.hist_data.to_pickle(path)
        elif format in ["csv" , "CSV", ".csv"]:
            path = filename + ".csv"
            self.hist_data.to_csv(path)
        
        return path            
                

    def apply_buy_func(self, window=10):
        """[applies user function to each window in data, saves result.]

        Args:
            window ([int]): [leangth of each window ]
        """
        applicable = lambda x : self.buy_signal_func(x)
        df_signals = self.hist_data.rolling(window).apply(applicable).dropna()
        self.signals = df_signals

    
    def simulate_trading(self):
        if self.signals is None:
            self.apply_buy_func(window=10)
            print(self.signals.sum())
            
        buy_dict = defaultdict(list)
       
        held = []
        sell_dict = defaultdict(list)
        for date in self.signals.index:
            for tick in self.signals.columns:
                curr_price = self.hist_data[tick][date]
                buy = self.signals[tick][date]
                holds = tick in held
                if buy and not holds:
                    buy_dict[tick].append({"price":curr_price,
                                           "date":date})
                    held.append(tick)
                    continue
                elif holds:
                    if self.sell_signal_func(buy_dict[tick][-1]["price"],curr_price):
                        sell_dict[tick].append({"price":curr_price,
                                                "date":date})
                        held.remove(tick)
        
        ##sell everything
        for tick in held:
            last_date = self.hist_data.index[-1]
            last_price = self.hist_data[tick][last_date]
            sell_dict[tick].append({"price":last_price,
                                                "date":last_price})
            
        return dict(buy_dict), dict(sell_dict)
    
    def calculate_returns(self,buy_dict,sell_dict):
        results = {}
        all_returns=[]
        
        for tick in self.tickers:
            
            buy_prices = [b["price"] for b in buy_dict.get(tick,[])]
            sell_prices = [s["price"] for s in sell_dict.get(tick,[])]
            if buy_prices is None:
                ret = 0
            else:
                ret = (np.sum(sell_prices) / np.sum(buy_prices)) -1 
            all_returns.append(ret)
            
            num_trades = len(sell_prices)
            
            results[tick] = {
                "returns":ret,
                "num_trades":num_trades
                }
       
        return results







if __name__ == "__main__":
    def buy_func_placeholder(window):
        return np.max(window)>1.5*window[-1]
    def sell_func_placeholder(buy_price, curr_price):
        return curr_price > 1.05*buy_price or curr_price < .95*buy_price
    my_backtester = Backtester(buy_func_placeholder,sell_func_placeholder)
    my_backtester.download_data(tickers=["MSFT","AAPL","V", "XOM"], period = ("2016-01-01","2020-01-01"))
    print(my_backtester.hist_data.head())
    
    buy_dict, sell_dict = my_backtester.simulate_trading()
    res = my_backtester.calculate_returns(buy_dict, sell_dict)
    print(res)
    