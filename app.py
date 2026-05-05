import streamlit as st
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import time

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
    }
    h1, h2, h3 { color: #deff9a !important; }
    </style>
    """, unsafe_allow_stdio=True)

# 2. 側邊欄：市場監控
st.sidebar.title("📊 市場監控")

@st.cache_data(ttl=600)
def get_top_movers():
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

# 3. 數據抓取
@st.cache_data(ttl=3600)
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

# 4. 主畫面邏輯
if target:
    st.title(f"🚀 {target} 深度量化診斷")
    df, info = fetch_stock_data(target)
    
    if df is not None and not df.empty:
        # 指標計算
        df['SMA_F'] = ta.sma(df['Close'], length=50)
        df['SMA_S'] = ta.sma(df['Close'], length=200)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        last = df.iloc[-1]
        p_v, r_v = float(last['Close']), float(last['RSI']) if not pd.isna(last['RSI']) else 50.0
        f_v = float(last['SMA_F']) if not pd.isna(last['SMA_F']) else 0.0
        s_v = float(last['SMA_S']) if not pd.isna(last['SMA_S']) else 0.0

        # 市值判定
        mcap = info.get('marketCap', 0)
        size = "💎 超大型股" if mcap > 2e11 else "🏢 大型股" if mcap > 1e10 else "🧱 中型股" if mcap > 2e9 else "🌱 小型股"
        st.markdown(f"**公司：** `{info.get('longName', 'N/A')}` | **規模：** `{size}` | **產業：** `{info.get('sector', 'N/A')}`")

        # 指標卡
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("當前股價", f"${p_v:.2f}")
        c2.metric("RSI 動能", f"{r_v:.1f}")
        c3.metric("50MA (季線)", f"${f_v:.2f}")
        c4.metric("200MA (年線)", f"${s_v:.2f}")

        # 操作建議
        st.divider()
        st.write("### 📝 操作建議")
        ca, cb, cc = st.columns(3)
        with ca:
            st.write("⚡ 短線 (RSI)")
            if r_v > 70: st.warning("過熱：建議分批獲利")
            elif r_v < 30: st.success("超跌：具反彈潛力")
            else: st.info("中性：動能盤整")
        with cb:
            st.write("🌀 中線 (50MA)")
            st.success("多頭：站穩季線") if p_v > f_v else st.error("弱勢：跌破季線")
        with cc:
            st.write("📜 長線 (200MA)")
            st.success("長多：趨勢向上") if p_v > s_v else st.warning("保守：年線之下")

        st.divider()

        # 核心繪圖區 (嚴格檢查括號)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
        
        # 1. K線圖
        fig.add_trace(go.)
