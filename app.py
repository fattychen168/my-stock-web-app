import streamlit as st
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# 1. 網頁頁面設定
st.set_page_config(page_title="KGI量化分析領航員", layout="wide")

# 2. 側邊欄參數設定
st.sidebar.title("🛡️ 決策參數設定")
ticker_input = st.sidebar.text_input("輸入代號 (多支請用逗號隔開)", "NVDA, AAPL, TSLA").upper()
ticker_list = [t.strip() for t in ticker_input.split(",") if t.strip()]

ma_fast = st.sidebar.slider("短線趨勢 (MA50)", 10, 100, 50)
ma_slow = st.sidebar.slider("長線年線 (MA200)", 100, 300, 200)

# 3. 數據抓取函數
@st.cache_data(ttl=3600)
def get_full_stock_data(symbol):
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period="2y")
        if df.empty:
            return None, None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df, stock.info
    except:
        return None, None

# 4. 主畫面標題
st.title("🚀 KGI量化分析儀：產業、規模與情緒診斷")

tab1, tab2 = st.tabs(["📌 單個深度診斷", "📋 多標的評分對比"])

# --- Tab 1: 單個深度診斷 ---
with tab1:
    if ticker_list:
        selected_ticker = st.selectbox("選擇要查看的標的", ticker_list)
        df, info = get_full_stock_data(selected_ticker)
        
        if df is not None:
            # 市值分類
            mcap = info.get('marketCap', 0)
            size = "💎 超大型" if mcap > 2e11 else "🏢 大型" if mcap > 1e10 else "🧱 中型" if mcap > 2e9 else "🌱 小型"
            
            # 指標計算
            df['SMA_F'] = ta.sma(df['Close'], length=ma_fast)
            df['SMA_S'] = ta.sma(df['Close'], length=ma_slow)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            
            last_row = df.iloc[-1]
            curr_p = float(last_row['Close'])
            rsi_v = float(last_row['RSI'])
            sma_f_v = float(last_row['SMA_F']) if not pd.isna(last_row['SMA_F']) else 0
            sma_s_v = float(last_row['SMA_S']) if not pd.isna(last_row['SMA_S']) else 0

            st.markdown(f"**產業：** `{info.get('sector', 'N/A')}` | **行業：** `{info.get('industry', 'N/A')}` | **市值：** `{size} (${mcap/1e9:.1f}B)`")
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("當前股價", f"${curr_p:.2f}")
            c2.metric("RSI 動能", f"{rsi_v:.1f}")
            c3.metric(f"{ma_fast}MA", f"${sma_f_v:.2f}")
            c4.metric(f"{ma_slow}MA", f"${sma_s_v:.2f}")
            
            # 圖表
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA_F'], name='短均', line=dict(color='cyan', width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA_S'], name='年線', line=dict(color='magenta', width=2)), row=1, col=1)
            fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='成交量', marker_color='gray', opacity=0.4), row=2, col=1)
            fig.update_layout(template="plotly_dark", height=700, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig, use_container_width=True)

# --- Tab 2: 多標的評分對比 (修正括號問題) ---
with tab2:
    st.subheader("📋 綜合量化評分表")
    summary_list = []
    
    if ticker_list:
        with st.spinner('正在分析清單中...'):
            for t in ticker_list:
                d, i = get_full_stock_data(t)
                if d is not None:
                    p_val = float(d['Close'].iloc[-1])
                    rsi_series = ta.rsi(d['Close'], length=14)
                    rsi_val = float(rsi_series.iloc[-1]) if not rsi_series.empty else 0
                    ma_s_series = ta.sma(d['Close'], length=ma_slow)
                    ma_s_val = float(ma_s_series.iloc[-1]) if not ma_s_series.empty else 0
                    
                    # 評分邏輯
                    score
