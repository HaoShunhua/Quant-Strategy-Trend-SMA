import backtrader as bt
import os
import datetime
import pandas as pd

class trend_sma(bt.Strategy):
    params = (
        ('maperiod', 15),
        ('dataname', 'testdata'),
    )

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        # print(f'{dt.isoformat()}, {txt}')
        log_line = f'{dt.isoformat()}, {txt}\n'
        with open(self.log_filename, 'a', encoding='utf-8') as f:
            f.write(log_line)

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.sma = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.maperiod)
        
        current_script_path = os.path.abspath(__file__)
        strategies_dir = os.path.dirname(current_script_path)
        project_root = os.path.dirname(strategies_dir)
        backtests_log_dir = os.path.join(project_root, 'backtests', 'logs')
        if not os.path.exists(backtests_log_dir):
            os.makedirs(backtests_log_dir)
        self.log_filename = os.path.join(backtests_log_dir, f'log_sma_{self.params.dataname}.txt')
        with open(self.log_filename, 'w', encoding='utf-8') as f:
            f.write('Date, Log Content\n')
        
        bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)
        bt.indicators.WeightedMovingAverage(self.datas[0], period=25).subplot = True
        bt.indicators.StochasticSlow(self.datas[0])
        bt.indicators.MACDHisto(self.datas[0])
        rsi = bt.indicators.RSI(self.datas[0])
        bt.indicators.SmoothedMovingAverage(rsi, period=10)
        bt.indicators.ATR(self.datas[0]).plot = False

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm {order.executed.comm:.2f}')
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm {order.executed.comm:.2f}')

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed: # 交易未完成
            return

        self.log(f'OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}')

    def next(self):
        self.log(f'Close, {self.dataclose[0]:.2f}')

        if self.order:
            return
        
        if not self.position: # 没有持仓
            if self.dataclose[0] > self.sma[0]: # 移动平均线突破
                self.log(f'BUY CREATE, {self.dataclose[0]:.2f}')
                self.order = self.buy()
        else:
            if self.dataclose[0] < self.sma[0]: # 移动平均线下穿
                self.log(f'SELL CREATE, {self.dataclose[0]:.2f}')
                self.order = self.sell()