import backtrader as bt
import os
import datetime
import pandas as pd
import numpy as np

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

        self.trades = []  # 记录所有交易
        self.equity_curve = []  # 资产净值曲线
        self.highest_equity = 0  # 最高资产净值
        self.drawdown_start = None  # 回撤开始时间
        self.max_drawdown = 0  # 最大回撤
        self.max_drawdown_duration = 0  # 最大回撤时长
        self.current_drawdown_duration = 0  # 当前回撤时长
        
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
        """记录每笔交易的详细信息"""
        if not trade.isclosed:
            return
        
        # 记录开仓时间、平仓时间、盈亏、手续费等交易信息
        trade_info = {
            'open_dt': trade.open_datetime(),
            'close_dt': trade.close_datetime(), 
            'gross_pnl': trade.pnl,
            'net_pnl': trade.pnlcomm,
            'commission': trade.commission,
            'size': trade.size,
            'direction': 'long' if trade.size > 0 else 'short'
        }
        self.trades.append(trade_info)
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
        
        # 记录每日资产净值
        current_equity = self.broker.getvalue()
        current_dt = self.datas[0].datetime.datetime(0)
        self.equity_curve.append((current_dt, current_equity))
        
        # 计算实时回撤
        self.highest_equity = max(self.highest_equity, current_equity)
        if self.highest_equity > 0:
            current_drawdown = (self.highest_equity - current_equity) / self.highest_equity
        else:
            current_drawdown = 0
        
        # 更新最大回撤
        if current_drawdown > self.max_drawdown:
            self.max_drawdown = current_drawdown
            self.drawdown_start = current_dt
        elif current_drawdown == 0 and self.drawdown_start is not None:
            drawdown_duration = (current_dt - self.drawdown_start).days
            if drawdown_duration > self.max_drawdown_duration:
                self.max_drawdown_duration = drawdown_duration
            self.drawdown_start = None
        
        # 更新当前回撤时长
        if self.drawdown_start is not None:
            self.current_drawdown_duration = (current_dt - self.drawdown_start).days

    def get_performance_metrics(self):
        """计算并返回所有绩效指标"""
        initial_capital = 100000.0
        final_capital = self.broker.getvalue()
        total_return = (final_capital - initial_capital) / initial_capital
        
        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t['net_pnl'] > 0]
        losing_trades = [t for t in self.trades if t['net_pnl'] < 0]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        avg_win = np.mean([t['net_pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['net_pnl'] for t in losing_trades]) if losing_trades else 0
        profit_factor = abs(sum([t['net_pnl'] for t in winning_trades]) / sum([t['net_pnl'] for t in losing_trades])) if losing_trades else float('inf')
        
        if self.equity_curve:
            start_dt = self.equity_curve[0][0]
            end_dt = self.equity_curve[-1][0]
            total_days = (end_dt - start_dt).days
            trading_days = len(self.equity_curve)
            trade_frequency = total_trades / (total_days / 365) if total_days > 0 else 0  # 年交易次数
        else:
            total_days = 0
            trading_days = 0
            trade_frequency = 0
        
        daily_returns = []
        for i in range(1, len(self.equity_curve)):
            prev_equity = self.equity_curve[i-1][1]
            curr_equity = self.equity_curve[i][1]
            daily_return = (curr_equity - prev_equity) / prev_equity
            daily_returns.append(daily_return)
        
        if daily_returns:
            avg_daily_return = np.mean(daily_returns)
            std_daily_return = np.std(daily_returns)
            
            # 夏普比率
            risk_free_rate = 0.02 / 252  # 日无风险利率
            sharpe_ratio = (avg_daily_return - risk_free_rate) / std_daily_return * np.sqrt(252) if std_daily_return != 0 else 0
        else:
            sharpe_ratio = 0
        
        # 回撤
        max_drawdown = self.max_drawdown
        max_drawdown_duration = self.max_drawdown_duration if self.max_drawdown_duration > 0 else self.current_drawdown_duration
        
        #年化收益率
        annual_return = ((1 + total_return) ** (365 / total_days)) - 1 if total_days > 0 else 0
        
        metrics = {
            '初始资金': initial_capital,
            '最终资金': final_capital,
            '总收益率': total_return,
            '年化收益率': annual_return,
            '夏普比率': sharpe_ratio,
            '最大回撤': max_drawdown,
            '最大回撤时长(天)': max_drawdown_duration,
            '总交易次数': total_trades,
            '胜率': win_rate,
            '平均盈利': avg_win,
            '平均亏损': avg_loss,
            '盈利因子': profit_factor,
            '年交易频率': trade_frequency,
            '回测总天数': total_days,
            '交易天数': trading_days
        }
        
        return metrics
