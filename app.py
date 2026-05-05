import streamlit as st
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import time
import random

# 1. 網頁頁面基礎設定
st.set_page_config(page_title="全球美股量化診斷儀", layout="wide")

# 2. 側邊欄控制與參數
st.sidebar.title("🛡️ 量化決策參數")
ticker_input = st.sidebar.text_input("輸入美股代號 (多支請用逗號隔開)", "NVDA, AAPL").upper()
ticker_list = [t.strip() for t in ticker_input.split(",") if t.strip()]

ma_fast = st.sidebar.slider("短線趨勢均線", 10, 100, 50)
ma_slow = st.sidebar.slider("長線年線位置", 100, 300, 200)

run_button = st.sidebar.button("🚀 開始量化分析")

# 3. 數據抓取函數 (加強緩存與錯誤處理)
@st.cache_data(ttl=86400)
def fetch_stock_data(symbol):
    time.sleep(random.uniform(0.5, 1.5))
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period="2y", timeout=25)
        
        # 備援路徑
        if df.empty:
            df = yf.download(symbol, period="2y", progress=False, timeout=25)
            
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            return df, stock.info
    except:
        return None, None
    return None, None

# 4. 主畫面邏輯
st.title("📈 智能量化診斷儀")

if run_button and ticker_list:
    tab1, tab2 = st.tabs(["📌 深度診斷報告", "📋 多標的快速對比"])

    with tab1:
        target = ticker_list[0]
        with st.spinner(f'正在分析 {target}...'):
            df, info = fetch_stock_data(target)
            
            if df is not None and not df.empty:
                # 指標計算
                df['SMA_F'] = ta.sma(df['Close'], length=ma_fast)
                df['SMA_S'] = ta.sma(df['Close'], length=ma_slow)
                df['RSI'] = ta.rsi(df['Close'], length=14)
                
                # 強制轉換純數值，防止 TypeError
                last = df.iloc[-1]
                def safe_val(key):
                    v = last.get(key, 0)
                    return float(v) if not pd.isna(v) else 0.0

                p_val = safe_val('Close')
                r_val = safe_val('RSI')
                f_val = safe_val('SMA_F')
                s_val = safe_val('SMA_S')

                st.subheader(f"🔍 {target} 診斷報告")
                st.write(f"**公司:** {info.get('longName', 'N/A')} | **產業:** {info.get('sector', 'N/A')}")

                # 指標卡片
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("當前股價", f"${p_val:.2f}")
                c2.metric("RSI動能", f"{r_val:.1f}")
                c3.metric(f"{ma_fast}MA", f"${f_val:.2f}")
                c4.metric(f"{ma_slow}MA", f"${s_val:.2f}")

                # Plotly 圖表
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_F'], name='短均', line=dict(color='cyan')), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_S'], name='年線', line=dict(color='magenta')), row=1, col=1)
                fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='量', marker_color='gray', opacity=0.3), row=2, col=1)
                fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error(f"無法取得 {target} 的數據，請確認代號或稍後再試。")

    with tab2:
        st.subheader("📋 快速對比")
        summary = []
        for t in ticker_list:
            d, _ = fetch_stock_data(t)
            if d is not None:
                cp = float(d['Close'].iloc[-1])
                summary.append({"代
