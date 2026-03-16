import os
import pandas as pd
os.chdir(os.path.dirname(os.path.abspath(__file__)))
# 处理data/raw/下的csv文件，检查缺失值并进行填充
for filename in os.listdir('../raw/'):
    if filename.endswith('.csv'):
        df = pd.read_csv(f'../raw/{filename}')
        print(f'{filename}缺失情况:')
        for col in df.columns:
            missing_count = df[col].isnull().sum()
            if missing_count:
                print(f'{col}: {missing_count}')
                df.fillna(method='ffill', inplace=True)
        if df.isnull().sum().sum() == 0:
            print('无缺失值')
        # 更改列名
        df.rename(columns={'Date': 'datetime', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'}, inplace=True)
        df = df
        # 存储到当前文件夹下
        df.to_csv(f'{filename}', index=False)
