import streamlit as st
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# 1. 網頁頁面設定
st.set_page_config(page_title="KGI量化分析領航員", layout="wide")

# 2. 安全美化：使用 st.markdown 的安全寫法
st.markdown("""
    <style>
    .stMetric {
        background-color: #1e2130;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #3e4150;
    }
    h1, h2, h3 { color: #deff9a !important; }
    </style>
    """, unsafe_allow_stdio=True)

# 3. 側邊欄控制
st.sidebar.title("🛡️ 決策參數")
# 支援多標的輸入，用逗號隔開
ticker_input = st.sidebar.text_input("輸入股票代號 (多支請用逗號隔開)", "NVDA, AAPL, TSLA").upper()
ticker_list = [t.strip() for t in ticker_input.split(",")]

ma_fast = st.sidebar.slider("短線趨勢 (MA50)", 10, 100, 50)
ma_slow = st.sidebar.slider("長線年線 (MA200)", 100, 300, 200)

# 4. 數據抓取函數 (含產業資訊)
@st.cache_data(ttl=3600)
def get_stock_all_info(symbol):
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period="2y")
        if df.empty: return None, None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df, stock.info
    except:
        return None, None

# 5. 主程式邏輯
st.title("🚀 KGI量化分析儀：產業與情緒診斷")

# 建立多分頁，第一頁看詳細分析，第二頁看清單對比
tab1, tab2 = st.tabs(["📌 單個深度診斷", "📋 多標的對比表"])

with tab1:
    selected_ticker = st.selectbox("選擇要查看的標的", ticker_list)
    df, info = get_stock_all_info(selected_ticker)
    
    if df is not None:
        # 分類邏輯
        mcap = info.get('marketCap', 0)
        size = "💎 超大型" if mcap > 2e11 else "🏢 大型" if mcap > 1e10 else "🧱 中型" if mcap > 2e9 else "🌱 小型"
        
        # 指標計算
        df['SMA_F'] = ta.sma(df['Close'], length=ma_fast)
        df['SMA_S'] = ta.sma(df['Close'], length=ma_slow)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        last = df.iloc[-1]
        p = float(last['Close'])
        rsi = float(last['RSI'])
        
        # 顯示產業資訊
        st.markdown(f"**產業：** `{info.get('sector', 'N/A')}` | **行業：** `{info.get('industry', 'N/A')}` | **市值：** `{size}股 (${mcap/1e9:.1f}B)`")
        
        # 數據卡片
        c1, c2, c3 = st.columns(3)
        c1.metric("當前股價", f"${p:.2f}")
        c2.metric("RSI 動能", f"{rsi:.1f}")
        c3.metric("52週高點", f"${info.get('fiftyTwoWeekHigh', 0):.2f}")
        
        # 繪圖
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_F'], name='短均', line=dict(color='cyan')), row=1, col=1)
        fig.add_trace(go.
                      
