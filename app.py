import streamlit as st
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import time

# 1. 網頁頁面美化設定
st.set_page_config(page_title="KGI量化分析領航員", layout="wide")

st.markdown("""
    <style>
    .stMetric {
        background-color: #1e2130;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #3e4150;
    }
    h1, h2, h3 { color: #deff9a !important; }
    .stAlert { border-radius: 10px; }
    </style>
    """, unsafe_allow_stdio=True)

# 2. 側邊欄：決策參數設定
st.sidebar.title("🛡️ 決策參數設定")
ticker_input = st.sidebar.text_input("輸入代號 (多支請用逗號隔開)", "NVDA, AAPL, TSLA").upper()
ticker_list = [t.strip() for t in ticker_input.split(",") if t.strip()]

ma_fast = st.sidebar.slider("短線趨勢 (MA50)", 10, 100, 50)
ma_slow = st.sidebar.slider("長線年線 (MA200)", 100, 300, 200)

# 啟動按鈕
run_button = st.sidebar.button("🚀 開始量化分析")

# 3. 核心數據抓取函數 (強化避開限流邏輯)
@st.cache_data(ttl=86400) # 快取 24 小時，減少請求頻率
def get_full_stock_data(symbol):
    try:
        stock = yf.Ticker(symbol)
        # 嘗試抓取 2 年數據
        df = stock.history(period="2y", interval="1d", timeout=20)
        
        # 若 history 失敗，嘗試 yf.download 備援
        if df.empty:
            df = yf.download(symbol, period="2y", progress=False)
            
        if df.empty:
            return None, None
            
        # 修正多重索引問題
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        return df, stock.info
    except Exception as e:
        return None, None

# 4. 主畫面邏輯
st.title("📈 KGI量化分析儀：產業與情緒診斷")

if run_button and ticker_list:
    tab1, tab2 = st.tabs(["📌 深度診斷報告", "📋 多標的評分對比"])

    # --- Tab 1: 深度診斷 (顯示清單第一個標的) ---
    with tab1:
        target = ticker_list[0]
        with st.spinner(f'正在分析 {target}，請稍候...'):
            df, info = get_full_stock_data(target)
            
            if df is not None:
                # 市值分類邏輯
                mcap = info.get('marketCap', 0)
                if mcap > 2e11: size = "💎 超大型股"
                elif mcap > 1e10: size = "🏢 大型股"
                elif mcap > 2e9: size = "🧱 中型股"
                else: size = "🌱 小型股"

                # 技術指標計算
                df['SMA_F'] = ta.sma(df['Close'], length=ma_fast)
                df['SMA_S'] = ta.sma(df['Close'], length=ma_slow)
                df['RSI'] = ta.rsi(df['Close'], length=14)
                
                last = df.iloc[-1]
                curr_p = float(last['Close'])
                rsi_v = float(last['RSI']) if not pd.isna(last['RSI']) else 0
                sma_f_v = float(last['SMA_F']) if not pd.isna(last['SMA_F']) else 0
                sma_s_v = float(last['SMA_S']) if not pd.isna(last['SMA_S']) else 0

                st.subheader(f"🔍 {target} 深度報告")
                st.markdown(f"**公司名稱：** `{info.get('longName', 'N/A')}` | **產業：** `{info.get('sector', 'N/A')}` | **規模：** `{size}`")
                
                # 指標卡片
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("當前股價", f"${curr_p:.2f}")
                c2.metric("RSI 動能", f"{rsi_v:.1f}")
                c3.metric(f"{ma_fast}MA", f"${sma_f_v:.2f}")
                c4.metric(f"{ma_slow}MA", f"${sma_s_v:.2f}")

                # 專業 Plotly 圖表
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
                
                # 1. K線
                fig.add_trace(go.Candlestick(
                    x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'
                ), row=1, col=1)
                
                # 2. 短均
                fig.add_trace(go.Scatter(
                    x=df.index, y=df['SMA_F'], name=f'{ma_fast}MA', line=dict(color='cyan', width=1.5)
                ), row=1, col=1)
                
                # 3. 年線
                fig.add_trace(go.Scatter(
                    x=df.index, y=df['SMA_S'], name=f'{ma_slow}MA', line=dict(color='magenta', width=2)
                ), row=1, col=1)
                
                # 4. 成交量
                fig.add_trace(go.Bar(
                    x=df.index, y=df['Volume'], name='成交量', marker_color='gray', opacity=0.4
                ), row=2, col=1)

                fig.update_layout(template="plotly_dark", height=700, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error(f"目前 Yahoo 伺服器繁忙，無法抓取 {target}。請等候 15 分鐘再試，或更換標的。")

    # --- Tab 2: 多標的評分對比 ---
    with tab2:
        st.subheader("📋 綜合量化評分表")
        summary_list = []
        
        with st.spinner('掃描清單標的中...'):
            for t in ticker_list:
                d, i = get_full_stock_data(t)
                if d is not None:
                    p_v = float(d['Close'].iloc[-1])
                    rsi_v = float(ta.rsi(d['Close'], length=14).iloc[-1])
                    ma_s_v = float(ta.sma(d['Close'], length=ma_slow).iloc[-1])
                    
                    score = 0
                    if p_v > ma_s_v: score += 50
                    if 40 < rsi_v < 70: score += 50
                    
                    summary_list.append({
                        "代號": t,
                        "股價": round(p_v, 2),
                        "RSI": round(rsi_v, 1),
                        "產業": i.get('sector', 'N/A'),
                        "量化評分": score,
                        "建議": "🚀 看多" if score >= 100 else "⚖️ 中性" if score >= 50 else "❄️ 弱勢"
                    })
