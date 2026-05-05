import streamlit as st
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import time
import random

# 1. 頁面設定與美化
st.set_page_config(page_title="全球美股量化診斷儀", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    div[data-testid="stMetric"] {
        background-color: #1e2130;
        border: 1px solid #3e4150;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    h1, h2, h3 { color: #deff9a !important; font-family: 'Segoe UI', sans-serif; }
    .stDivider { border-bottom: 2px solid #3e4150; }
    </style>
    """, unsafe_allow_stdio=True)

# 2. 側邊欄：市場監控與排行榜
st.sidebar.title("📊 市場監控")

@st.cache_data(ttl=600)
def get_top_movers():
    # 預設一組高波動熱門標的
    watch_list = ["NVDA", "TSLA", "AMD", "SMCI", "ARM", "COIN", "MARA", "PLTR", "SOXL", "TSM"]
    data = []
    for t in watch_list:
        try:
            s = yf.Ticker(t)
            h = s.history(period="2d")
            if len(h) >= 2:
                change = ((h['Close'].iloc[-1] / h['Close'].iloc[-2]) - 1) * 100
                data.append({"代號": t, "漲跌%": round(change, 2), "股價": round(h['Close'].iloc[-1], 2)})
        except:
            continue
    return pd.DataFrame(data).sort_values(by="漲跌%", ascending=False)

st.sidebar.subheader("今日表現排行榜")
movers_df = get_top_movers()
if not movers_df.empty:
    st.sidebar.table(movers_df.head(10))

st.sidebar.divider()
target = st.sidebar.text_input("🔍 輸入深度診斷代號", "NVDA").upper().strip()

# 3. 數據抓取函數
@st.cache_data(ttl=86400)
def fetch_stock_data(symbol):
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

# 4. 主畫面深度報告
if target:
    st.title(f"🚀 {target} 深度量化診斷")
    
    with st.spinner(f"正在分析 {target}..."):
        df, info = fetch_stock_data(target)
        
        if df is not None and not df.empty:
            # 指標計算
            df['SMA_F'] = ta.sma(df['Close'], length=50)
            df['SMA_S'] = ta.sma(df['Close'], length=200)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            
            last = df.iloc[-1]
            p_val = float(last['Close'])
            r_val = float(last['RSI']) if not pd.isna(last['RSI']) else 50.0
            f_val = float(last['SMA_F']) if not pd.isna(last['SMA_F']) else 0.0
            s_val = float(last['SMA_S']) if not pd.isna(last['SMA_S']) else 0.0

            # 市值規模判定
            mcap = info.get('marketCap', 0)
            if mcap >= 2e11: size_tag = "💎 超大型股"
            elif mcap >= 1e10: size_tag = "🏢 大型股"
            elif mcap >= 2e9: size_tag = "🧱 中型股"
            else: size_tag = "🌱 小型股"
            
            st.markdown(f"**公司全名：** `{info.get('longName', 'N/A')}` | **市值規模：** `{size_tag}` | **產業：** `{info.get('sector', 'N/A')}`")
            st.divider()

            # 指標卡
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("當前股價", f"${p_val:.2f}")
            c2.metric("RSI 動能", f"{r_val:.1f}")
            c3.metric("50MA (季線)", f"${f_val:.2f}")
            c4.metric("200MA (年線)", f"${s_val:.2f}")

            # 診斷建議
            st.write("### 📝 操作建議與位階診斷")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.info("⚡ 短線 (RSI)")
                if r_val > 70: st.warning("過熱：建議分批獲利")
                elif r_val < 30: st.success("超跌：具反彈潛力")
                else: st.write("動能盤整中")
            with col_b:
                st.info("🌀 中線 (50MA)")
                if p_val > f_val: st.success("多頭：股價站穩季線")
                else: st.error("弱勢：股價跌破季線")
            with col_c:
                st.info("📜 長線 (200MA)")
                if p_val > s_val: st.success("長多：趨勢向上")
                else: st.warning("保守：年線之下")

            st.divider()

            # Plotly 圖表
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA_F'], name='50MA', line=dict(color='#00d4ff',
