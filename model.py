import numpy as np
import pandas as pd
import yfinance as yf
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler
import warnings
warnings.filterwarnings('ignore')


class LSTMModel(nn.Module):
    def __init__(self):
        super(LSTMModel, self).__init__()
        self.lstm1 = nn.LSTM(1, 50, batch_first=True, num_layers=2, dropout=0.2)
        self.fc1   = nn.Linear(50, 25)
        self.fc2   = nn.Linear(25, 1)
        self.relu  = nn.ReLU()

    def forward(self, x):
        out, _ = self.lstm1(x)
        out = self.relu(self.fc1(out[:, -1, :]))
        return self.fc2(out)


def predict_stock(ticker: str, future_days: int = 30) -> dict:
    try:
        df = yf.download(ticker, period='2y', progress=False)
        if df.empty:
            return {'error': f'No data found for ticker "{ticker}"'}
    except Exception as e:
        return {'error': str(e)}

    prices = df['Close'].values.reshape(-1, 1)
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(prices)

    SEQ_LEN = 60
    X, y = [], []
    for i in range(SEQ_LEN, len(scaled)):
        X.append(scaled[i - SEQ_LEN:i, 0])
        y.append(scaled[i, 0])

    X = np.array(X)
    y = np.array(y)

    split = int(len(X) * 0.8)
    X_train = torch.tensor(X[:split].reshape(-1, SEQ_LEN, 1), dtype=torch.float32)
    y_train = torch.tensor(y[:split].reshape(-1, 1),           dtype=torch.float32)

    model     = LSTMModel()
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    model.train()
    for epoch in range(20):
        optimizer.zero_grad()
        output = model(X_train)
        loss   = criterion(output, y_train)
        loss.backward()
        optimizer.step()

    model.eval()
    with torch.no_grad():
        X_test      = torch.tensor(X[split:].reshape(-1, SEQ_LEN, 1), dtype=torch.float32)
        pred_scaled = model(X_test).numpy()

    predicted_prices = scaler.inverse_transform(pred_scaled).flatten().tolist()
    actual_prices    = prices[split + SEQ_LEN:].flatten().tolist()
    test_dates       = df.index[split + SEQ_LEN:].strftime('%Y-%m-%d').tolist()

    # Future forecast
    last_seq = scaled[-SEQ_LEN:].reshape(1, SEQ_LEN, 1)
    future   = []
    seq      = last_seq.copy()
    model.eval()
    with torch.no_grad():
        for _ in range(future_days):
            inp = torch.tensor(seq, dtype=torch.float32)
            p   = model(inp).item()
            future.append(p)
            seq = np.append(seq[:, 1:, :], [[[p]]], axis=1)

    future_prices = scaler.inverse_transform(
        np.array(future).reshape(-1, 1)
    ).flatten().tolist()

    last_date    = pd.Timestamp(df.index[-1])
    future_dates = pd.bdate_range(
        start=last_date + pd.Timedelta(days=1), periods=future_days
    ).strftime('%Y-%m-%d').tolist()

    return {
        'ticker':           ticker,
        'historical_dates': test_dates,
        'actual_prices':    actual_prices,
        'predicted_prices': predicted_prices,
        'future_dates':     future_dates,
        'future_prices':    future_prices,
        'current_price':    round(float(prices[-1][0]), 2),
        'predicted_next':   round(future_prices[0], 2),
    }