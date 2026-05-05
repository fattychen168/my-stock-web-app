import streamlit as st
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import time
import random

# 1. 頁面基本設定
st.set_page_config(page_title="全球美股量化診斷儀", layout="wide")

# 2. 側邊欄參數
st.sidebar.title("🛡️ 量化決策參數")
ticker_input = st.sidebar.text_input("輸入美股代號 (多支用逗號隔開)", "NVDA, AAPL").upper()
ticker_list = [t.strip() for t in ticker_input.split(",") if t.strip()]

ma_fast = st.sidebar.slider("短線趨勢均線", 10, 100, 50)
ma_slow = st.sidebar.slider("長線年線位置", 100, 300, 200)

run_button = st.sidebar.button("🚀 開始量化分析")

# 3. 數據抓取函數
@st.cache_data(ttl=86400)
def fetch_stock_data(symbol):
    time.sleep(random.uniform(0.5, 1.5))
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period="2y", timeout=25)
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
        with st.spinner(f"正在分析 {target}..."):
            df, info = fetch_stock_data(target)
            if df is not None and not df.empty:
                # 指標計算
                df['SMA_F'] = ta.sma(df['Close'], length=ma_fast)
                df['SMA_S'] = ta.sma(df['Close'], length=ma_slow)
                df['RSI'] = ta.rsi(df['Close'], length=14)
                
                last = df.iloc[-1]
                p_val = float(last['Close'])
                r_val = float(last['RSI']) if not pd.isna(last['RSI']) else 0.0
                f_val = float(last['SMA_F']) if not pd.isna(last['SMA_F']) else 0.0
                s_val = float(last['SMA_S']) if not pd.isna(last['SMA_S']) else 0.0

                st.subheader(f"🔍 {target} 診斷報告")
                st.write(f"公司: {info.get('longName', 'N/A')} | 產業: {info.get('sector', 'N/A')}")

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("當前股價", f"${p_val:.2f}")
                col2.metric("RSI動能", f"{r_val:.1f}")
                col3.metric(f"{ma_fast}MA", f"${f_val:.2f}")
                col4.metric(f"{ma_slow}MA", f"${s_val:.2f}")

                # 繪圖區 (採緊湊寫法避免括號錯誤)
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
                
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_F'], name='短均', line=dict(color='cyan')), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_S'], name='年線', line=dict(color='magenta')), row=1, col=1)
                fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='量', marker_color='gray', opacity=0.3), row=2, col=1)
                
                fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("無法取得數據，請確認代號正確或稍後再試。")

    with tab2:
        st.subheader("📋 快速對比")
        summary_data = []
        for t in ticker_list:
            d, _ = fetch_stock_data(t)
            if d is not None:
                cp = float(d['Close'].iloc[-1])
                summary_data.append({"代號": t, "價格": round(cp, 2)})
        
        if summary_data:
            st.table(pd.DataFrame(summary_data))

else:
    st.info("💡 請在左側輸入代號並按下『🚀 開始量化分析』。")
