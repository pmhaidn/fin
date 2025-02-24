import streamlit as st
import pandas as pd
import numpy as np
import requests
import ta
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Cấu hình trang
st.set_page_config(page_title="Crypto Technical Analysis", layout="wide")
st.title("Phân tích Kỹ thuật Thị trường Crypto")

# Hàm lấy dữ liệu từ OKX API
def get_okx_data(symbol, interval, limit=100):
    base_url = "https://www.okx.com"
    endpoint = f"/api/v5/market/candles"
    url = f"{base_url}{endpoint}?instId={symbol}&bar={interval}&limit={limit}"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()['data']
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote', 'confirm'])
        
        # Chuyển đổi kiểu dữ liệu
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(float), unit='ms')
        return df.sort_values('timestamp')
    return None

# Hàm tính toán các chỉ báo kỹ thuật
def calculate_indicators(df):
    # RSI
    df['RSI'] = ta.momentum.RSIIndicator(df['close']).rsi()
    
    # MACD
    macd = ta.trend.MACD(df['close'])
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    
    # Bollinger Bands
    bollinger = ta.volatility.BollingerBands(df['close'])
    df['BB_High'] = bollinger.bollinger_hband()
    df['BB_Low'] = bollinger.bollinger_lband()
    df['BB_Mid'] = bollinger.bollinger_mavg()
    
    # Stochastic Oscillator
    stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
    df['Stoch_K'] = stoch.stoch()
    df['Stoch_D'] = stoch.stoch_signal()
    
    return df

# Hàm phân tích xu hướng và đưa ra khuyến nghị
def analyze_trend(df):
    last_close = df['close'].iloc[-1]
    rsi = df['RSI'].iloc[-1]
    stoch_k = df['Stoch_K'].iloc[-1]
    stoch_d = df['Stoch_D'].iloc[-1]
    macd = df['MACD'].iloc[-1]
    macd_signal = df['MACD_Signal'].iloc[-1]
    bb_high = df['BB_High'].iloc[-1]
    bb_low = df['BB_Low'].iloc[-1]
    
    signals = []
    
    # Phân tích RSI
    if rsi > 70:
        signals.append("RSI cho thấy vùng quá mua")
    elif rsi < 30:
        signals.append("RSI cho thấy vùng quá bán")
        
    # Phân tích Stochastic
    if stoch_k > 80 and stoch_d > 80:
        signals.append("Stochastic cho thấy vùng quá mua")
    elif stoch_k < 20 and stoch_d < 20:
        signals.append("Stochastic cho thấy vùng quá bán")
        
    # Phân tích MACD
    if macd > macd_signal:
        signals.append("MACD cho tín hiệu tích cực")
    else:
        signals.append("MACD cho tín hiệu tiêu cực")
        
    # Phân tích Bollinger Bands
    if last_close > bb_high:
        signals.append("Giá đang ở vùng quá mua theo Bollinger Bands")
    elif last_close < bb_low:
        signals.append("Giá đang ở vùng quá bán theo Bollinger Bands")
        
    # Xác định xu hướng tổng thể
    bullish_signals = len([s for s in signals if "quá bán" in s or "tích cực" in s])
    bearish_signals = len([s for s in signals if "quá mua" in s or "tiêu cực" in s])
    
    if bullish_signals > bearish_signals:
        trend = "TĂNG 📈"
    elif bearish_signals > bullish_signals:
        trend = "GIẢM 📉"
    else:
        trend = "ĐANG TÍCH LŨY ↔️"
        
    return trend, signals

# Sidebar cho cấu hình
st.sidebar.header("Cấu hình")

# Danh sách các cặp giao dịch phổ biến
trading_pairs = [
    "PI-USDT", "BTC-USDT", "ETH-USDT", "BNB-USDT", "XRP-USDT", "SOL-USDT",
    "ADA-USDT", "AVAX-USDT", "MATIC-USDT", "LINK-USDT", "DOT-USDT"
]

# Widget chọn cặp giao dịch
selected_pair = st.sidebar.selectbox(
    "Chọn cặp giao dịch",
    trading_pairs
)

# Widget chọn khung thời gian
timeframes = {
    "1 phút": "1m",
    "5 phút": "5m",
    "15 phút": "15m",
    "30 phút": "30m",
    "1 giờ": "1H",
    "4 giờ": "4H",
    "1 ngày": "1D"
}

selected_timeframe = st.sidebar.selectbox(
    "Chọn khung thời gian",
    list(timeframes.keys())
)

# Lấy và xử lý dữ liệu
df = get_okx_data(selected_pair, timeframes[selected_timeframe])

if df is not None:
    df = calculate_indicators(df)
    trend, signals = analyze_trend(df)
    
    # Hiển thị xu hướng và tín hiệu
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Xu hướng hiện tại")
        st.markdown(f"## {trend}")
        
    with col2:
        st.subheader("Các tín hiệu kỹ thuật")
        for signal in signals:
            st.write(f"• {signal}")
            
    # Vẽ biểu đồ giá và các chỉ báo
    fig = go.Figure()
    
    # Thêm nến
    fig.add_trace(go.Candlestick(
        x=df['timestamp'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='Giá'
    ))
    
    # Thêm Bollinger Bands
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['BB_High'],
        name='BB Upper',
        line=dict(color='gray', dash='dash')
    ))
    
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['BB_Low'],
        name='BB Lower',
        line=dict(color='gray', dash='dash'),
        fill='tonexty'
    ))
    
    fig.update_layout(
        title=f'Biểu đồ giá {selected_pair}',
        yaxis_title='Giá',
        xaxis_title='Thời gian',
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Vẽ các chỉ báo phụ
    col1, col2 = st.columns(2)
    
    with col1:
        # RSI
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['RSI'],
            name='RSI'
        ))
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
        fig_rsi.update_layout(title='RSI', height=300)
        st.plotly_chart(fig_rsi, use_container_width=True)
        
    with col2:
        # Stochastic
        fig_stoch = go.Figure()
        fig_stoch.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['Stoch_K'],
            name='Stoch %K'
        ))
        fig_stoch.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['Stoch_D'],
            name='Stoch %D'
        ))
        fig_stoch.add_hline(y=80, line_dash="dash", line_color="red")
        fig_stoch.add_hline(y=20, line_dash="dash", line_color="green")
        fig_stoch.update_layout(title='Stochastic Oscillator', height=300)
        st.plotly_chart(fig_stoch, use_container_width=True)
    
    # MACD
    fig_macd = go.Figure()
    fig_macd.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['MACD'],
        name='MACD'
    ))
    fig_macd.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['MACD_Signal'],
        name='Signal'
    ))
    fig_macd.update_layout(title='MACD', height=300)
    st.plotly_chart(fig_macd, use_container_width=True)
    
else:
    st.error("Không thể lấy dữ liệu từ OKX API. Vui lòng thử lại sau.")