import streamlit as st
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import time

# 1. 頁面基礎設定
st.set_page_config(page_title="全球美股量化診斷儀", layout="wide")

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
                data.append({"代號": t, "漲跌%": round(float(change), 2), "股價": round(float(h['Close'].iloc[-1]), 2)})
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
st.title("📈 智能量化診斷儀")

if target:
    df, info = fetch_stock_data(target)
    
    if df is not None and not df.empty:
        # 指標計算
        df['SMA_F'] = ta.sma(df['Close'], length=50)
        df['SMA_S'] = ta.sma(df['Close'], length=200)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        last = df.iloc[-1]
        
        # 安全數值轉換函數
        def safe_float(val):
            try:
                v = val.item() if hasattr(val, 'item') else val
                return float(v) if not pd.isna(v) else 0.0
            except:
                return 0.0

        # 統一變數命名，避免 NameError
        p_v = safe_float(last['Close'])
        r_v = safe_float(last['RSI'])
        f_v = safe_float(last['SMA_F'])
        s_v = safe_float(last['SMA_S'])

        # 市值判定
        mcap = info.get('marketCap', 0)
        size = "💎 超大型股" if mcap > 2e11 else "🏢 大型股" if mcap > 1e10 else "🧱 中型股" if mcap > 2e9 else "🌱 小型股"
        st.write(f"**公司：** {info.get('longName', 'N/A')} | **規模：** {size} | **產業：** {info.get('sector', 'N/A')}")

        # 指標卡
        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("當前股價", f"${p_v:.2f}")
        c2.metric("RSI 動能", f"{r_v:.1f}")
        c3.metric("50MA (季線)", f"${f_v:.2f}")
        c4.metric("200MA (年線)", f"${s_v:.2f}")

        # 操作建議 (修正 NameError 的位置)
        st.divider()
        st.write("### 📝 操作建議")
        ca, cb, cc = st.columns(3)
        with ca:
            st.info("⚡ 短線 (RSI)")
            if r_v > 70: st.warning("過熱：建議分批獲利")
            elif r_v < 30: st.success("超跌：具反彈潛力")
            else: st.write("動能盤整中")
        with cb:
            st.info("🌀 中線 (50MA)")
            if p_v > f_v: st.success("多頭：站穩季線")
            else: st.error("弱勢：跌破季線")
        with cc:
            st.info("📜 長線 (200MA)")
            if p_v > s_v: st.success("長多：趨勢向上")
            else: st.warning("保守：年線之下")

        st.divider()

        # 繪圖
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_F'], name='50MA', line=dict(color='#00d4ff')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_S'], name='200MA', line=dict(color='#ff00ff')), row=1, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='量', marker_color='#4e5d6c', opacity=0.5), row=2, col=1)
        fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("暫時無法取得數據，請確認代號或等候冷卻期。")
else:
    st.info("👈 請在左側輸入代號開始分析。")
