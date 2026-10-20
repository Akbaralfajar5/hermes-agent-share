#!/usr/bin/env python3
"""Generate multi-panel candlestick chart with EMA, RSI, MACD.

Usage: python3 generate_chart.py PENDLEUSDT 1d 60
       python3 generate_chart.py BTCUSDT 4h 100

Outputs: /tmp/<SYMBOL>_chart.png
Requires: pip install plotly kaleido numpy
          python3 -c "import kaleido; kaleido.get_chrome_sync()"  # first time only
"""
import sys, json, urllib.request
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

def fetch_ohlc(symbol, interval="1d", limit=60):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read())

def calc_ema(data, period):
    k = 2 / (period + 1)
    ema = [data[0]]
    for d in data[1:]:
        ema.append(d * k + ema[-1] * (1 - k))
    return np.array(ema)

def calc_rsi(closes, period=14):
    rsi_vals = np.full(len(closes), np.nan)
    deltas = np.diff(closes)
    for i in range(period, len(closes)):
        gains = [d for d in deltas[i-period:i] if d > 0]
        losses = [-d for d in deltas[i-period:i] if d < 0]
        avg_g = sum(gains)/period if gains else 0
        avg_l = sum(losses)/period if losses else 0.001
        rs = avg_g / avg_l
        rsi_vals[i] = 100 - (100 / (1 + rs))
    return rsi_vals

def main():
    symbol = sys.argv[1] if len(sys.argv) > 1 else "BTCUSDT"
    interval = sys.argv[2] if len(sys.argv) > 2 else "1d"
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    
    name = symbol.replace("USDT", "").replace("BUSD", "")
    
    data = fetch_ohlc(symbol, interval, limit)
    dates = [datetime.fromtimestamp(d[0]/1000) for d in data]
    closes = np.array([float(d[4]) for d in data])
    opens = np.array([float(d[1]) for d in data])
    highs = np.array([float(d[2]) for d in data])
    lows = np.array([float(d[3]) for d in data])
    
    ema7 = calc_ema(closes, 7)
    ema21 = calc_ema(closes, 21)
    rsi = calc_rsi(closes, 14)
    macd_line = calc_ema(closes, 12) - calc_ema(closes, 26)
    signal = calc_ema(list(macd_line), 9)
    hist = macd_line - signal
    
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
        row_heights=[0.55, 0.22, 0.23], vertical_spacing=0.04,
        subplot_titles=[f'{name}/USDT {interval.upper()}', 'RSI(14)', 'MACD'])
    
    fig.add_trace(go.Candlestick(x=dates, open=opens, high=highs, low=lows, close=closes, name='Price'), row=1, col=1)
    fig.add_trace(go.Scatter(x=dates, y=ema7, name='EMA7', line=dict(color='cyan', width=1.2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=dates, y=ema21, name='EMA21', line=dict(color='orange', width=1.2)), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=dates, y=rsi, name='RSI', line=dict(color='#AB47BC', width=1.5)), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=2, col=1)
    
    colors = ['#26A69A' if h >= 0 else '#EF5350' for h in hist]
    fig.add_trace(go.Bar(x=dates, y=hist, name='Hist', marker_color=colors), row=3, col=1)
    fig.add_trace(go.Scatter(x=dates, y=macd_line, name='MACD', line=dict(color='#42A5F5', width=1)), row=3, col=1)
    fig.add_trace(go.Scatter(x=dates, y=signal, name='Signal', line=dict(color='#EF5350', width=1)), row=3, col=1)
    
    fig.update_layout(template='plotly_dark', height=700, showlegend=True, xaxis_rangeslider_visible=False)
    
    filepath = f'/tmp/{name}_chart.png'
    fig.write_image(filepath, width=1200, height=700, scale=2)
    print(f"OK {filepath}")

if __name__ == "__main__":
    main()
