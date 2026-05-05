import streamlit as st
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import time

# 1. 頁面美化設定
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

# 2. 側邊欄設計
st.sidebar.title("📊 市場監控")

# 獲取熱門股漲幅榜 (示範清單：科技股與權值股)
@st.cache_data(ttl=600)
def get_top_movers():
    # 這裡預設一組觀察名單，模擬市場掃描
    watch_list = ["NVDA", "AAPL", "TSLA", "AMD", "MSFT", "GOOGL", "META", "AVGO", "SMCI", "ARM", "NFLX", "COIN"]
    data = []
    for t in watch_list:
        try:
            s = yf.Ticker(t)
            # 抓取最近兩天數據計算漲跌幅
            h = s.history(period="2d")
            if len(h) >= 2:
                change = ((h['Close'].iloc[-1] / h['Close'].iloc[-2]) - 1) * 100
                data.append({"代號": t, "漲跌": round(change, 2), "現價": round(h['Close'].iloc[-1], 2)})
        except:
            continue
    df = pd.DataFrame(data).sort_values(by="漲跌", ascending=False)
    return df

st.sidebar.subheader("今日表現排行榜")
top_df = get_top_movers()
st.sidebar.table(top_df.head(10))

st.sidebar.divider()
target = st.sidebar.text_input("🔍 輸入深度診斷代號", "NVDA").upper().strip()

# 3. 數據抓取函數
@st.cache_data(ttl=3600)
def fetch_data(symbol):
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period="2y", timeout=20)
        if df.empty:
            df = yf.download(symbol, period="2y", progress=False)
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
    df, info = fetch_data(target)
    
    if df is not None and not df.empty:
        # 指標計算
        df['SMA_F'] = ta.sma(df['Close'], length=50)
        df['SMA_S'] = ta.sma(df['Close'], length=200)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        last = df.iloc[-1]
        p_val, r_val = float(last['Close']), float(last['RSI'])
        f_val, s_val = float(last['SMA_F']), float(last['SMA_S'])

        # 市值規模判定
        mcap = info.get('marketCap', 0)
        size = "💎 超大型股" if mcap > 2e11 else "🏢 大型股" if mcap > 1e10 else "🧱 中型股" if mcap > 2e9 else "🌱 小型股"
        
        st.markdown(f"**公司：** `{info.get('longName', 'N/A')}` | **規模：** `{size}` | **產業：** `{info.get('sector', 'N/A')}`")
        
        # 指標卡
        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("當前股價", f"${p_val:.2f}")
        c2.metric("RSI 動能", f"{r_val:.1f}")
        c3.metric("50MA (季線)", f"${f_val:.2f}")
        c4.metric("200MA (年線)", f"${s_val:.2f}")

        # 操作建議
        st.divider()
        st.write("### 📝 操作建議")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.write("#### ⚡ 短線 (RSI)")
            if r_val > 70: st.warning("過熱：不宜追高")
            elif r_val < 30: st.success("超跌：具反彈潛力")
            else: st.info("中性：動能盤整")
        with col_b:
            st.write("#### 🌀
