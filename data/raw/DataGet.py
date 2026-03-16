import os
import yfinance as yf
os.chdir(os.path.dirname(os.path.abspath(__file__)))
# 需美国ip，并设置http和https代理，否则yfinance下载数据会失败
proxy = 'http://127.0.0.1:7890'
os.environ['HTTP_PROXY'] = proxy
os.environ['HTTPS_PROXY'] = proxy
# 沪深300、上证50、中证500,标普500ETF
tickers = ['510300.SS', '510050.SS', '510500.SS','SPY']
start_date = '2014-01-01'
end_date = '2024-06-30'
for ticker in tickers:
    data = yf.download(ticker, start=start_date, end=end_date, multi_level_index=False)
    data.to_csv(f'{ticker}_2014_2024_clhov.csv')