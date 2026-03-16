import backtrader as bt
import os
import datetime
import pandas as pd
import sys
import matplotlib.pyplot as plt
# 导入策略
current_backtest_path = os.path.abspath(__file__)
backtests_dir = os.path.dirname(current_backtest_path)
project_root = os.path.dirname(backtests_dir)
strategies_dir = os.path.join(project_root, 'strategies')
sys.path.append(strategies_dir)
from Trend_SMA import trend_sma

os.chdir(project_root)
plt.switch_backend('Agg')  # 非交互式后端（只保存图片，不弹出窗口）
plt.rcParams["figure.max_open_warning"] = 0  # 关闭窗口过多警告
plt.rcParams['font.sans-serif'] = ['SimHei']  # 解决中文乱码（如果文件名/标题有中文）
plt.rcParams['axes.unicode_minus'] = False    # 解决负号显示问题

# 创建figs文件夹（backtests/figs）
figs_dir = os.path.join(backtests_dir, 'figs')
if not os.path.exists(figs_dir):
    os.makedirs(figs_dir)

if __name__ == '__main__':
    datanames = ['SPY', '510050.SS','510300.SS', '510500.SS']
    for dataname in datanames:
        cerebro = bt.Cerebro()
        df = pd.read_csv(f'data/processed/{dataname}_2014_2024_clhov.csv', parse_dates=['datetime'], index_col='datetime')
        data = bt.feeds.PandasData(dataname=df)
        cerebro.adddata(data)
        cerebro.addstrategy(trend_sma, dataname=dataname)
        cerebro.broker.setcash(100000.0)
        cerebro.broker.setcommission(commission=0.001)
        cerebro.addsizer(bt.sizers.PercentSizer, percents=10) # 每次交易10%的资金
        print(f'========== 回测 {dataname} ==========')
        print(f'初始资金: {cerebro.broker.getvalue():.2f}')
        cerebro.run()
        final_value = cerebro.broker.getvalue()
        profit = final_value - 100000
        print(f'最终资金: {final_value:.2f}')
        print(f'盈亏金额: {profit:.2f}')
        print(f'盈亏比例: {profit/100000*100:.2f}%')
        log_path = os.path.join(backtests_dir, 'logs', f'log_sma_{dataname}.txt')
        print(f'日志路径: {log_path}')
        
        fig = cerebro.plot(
            numfigs=1,
            title=f'回测结果 - {dataname}',
            style='candlestick',
        )[0][0]
        
        fig_filename = f'{dataname}_sma_backtest.png'
        fig_path = os.path.join(figs_dir, fig_filename)
        
        # 保存图片
        fig.savefig(
            fig_path,
            dpi=300,
            bbox_inches='tight'
        )
        plt.close(fig)
        
        print(f'图片已保存到: {fig_path}\n')

print('========== 所有回测完成 ==========')
print(f'所有图片保存在: {figs_dir}')
print(f'所有日志保存在: {os.path.join(backtests_dir, "logs")}')
# 最后保持所有窗口不关闭
plt.show()