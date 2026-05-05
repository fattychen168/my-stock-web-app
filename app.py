import streamlit as st
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

# 1. 頁面設定
st.set_page_config(page_title="KGI量化診斷器", layout="wide")

# 2. 側邊欄控制
st.sidebar.title("🛡️ 參數設定")
ticker_input = st.sidebar.text_input("輸入代號 (例如: NVDA, AAPL)", "NVDA").upper()
ticker_list = [t.strip() for t in ticker_input.split(",") if t.strip()]

ma_fast = st.sidebar.slider("短線均線 (MA50)", 10, 100, 50)
ma_slow = st.sidebar.slider("長線均線 (MA200)", 100, 300, 200)

run_button = st.sidebar.button("🚀 開始量化分析")

# 3. 數據抓取函數 (加入多重備援)
@st.cache_data(ttl=86400)
def fetch_data(symbol):
    df = pd.DataFrame()
    info = {}
    try:
        # 方法 A: Ticker 物件 (可拿產業資訊)
        stock = yf.Ticker(symbol)
        df = stock.history(period="2y", timeout=20)
        info = stock.info
        
        # 方法 B: 若 A 失敗，改用 download
        if df.empty:
            df = yf.download(symbol, period="2y", progress=False)
            
        if not df.empty:
            # 修正多重索引
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            return df, info
    except Exception as e:
        st.error(f"數據源抓取失敗 ({symbol}): {str(e)}")
    return None, None

# 4. 主畫面
st.title("📈 KGI量化分析儀")

if run_button and ticker_list:
    # 建立分頁
    tab1, tab2 = st.tabs(["📌 深度診斷報告", "📋 多標的對比表"])

    # --- Tab 1: 深度報告 ---
    with tab1:
        target = ticker_list[0]
        with st.spinner(f'正在分析 {target}...'):
            df, info = fetch_data(target)
            
            if df is not None and not df.empty:
                # 指標計算
                df['SMA_F'] = ta.sma(df['Close'], length=ma_fast)
                df['SMA_S'] = ta.sma(df['Close'], length=ma_slow)
                df['RSI'] = ta.rsi(df['Close'], length=14)
                
                # 數據清洗 (確保是純數字)
                last_row = df.iloc[-1].to_dict()
                
                def to_num(val):
                    if isinstance(val, (int, float, np.number)):
                        return float(val)
                    return 0.0

                p = to_num(last_row.get('Close', 0))
                r = to_num(last_row.get('RSI', 0))
                f = to_num(last_row.get('SMA_F', 0))
                s = to_num(last_row.get('SMA_S', 0))

                st.subheader(f"🔍 {target} 報告結果")
                st.write(f"**產業:** {info.get('sector', 'N/A')} | **市值:** ${info.get('marketCap', 0)/1e9:.1f}B")
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("當前股價", f"${p:.2f}")
                c2.metric("RSI 動能", f"{r:.1f}")
                c3.metric(f"{ma_fast}MA", f"${f:.2f}")
                c4.metric(f"{ma_slow}MA", f"${s:.2f}")
                
                # 繪圖
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_F'], name='短均', line=dict(color='cyan')), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_S'], name='年線', line=dict(color='magenta')), row=1, col=1)
                fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='成交量', marker_color='gray', opacity=0.3), row=2, col=1)
                fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"目前無法連線至 Yahoo Finance 獲取 {target}。請稍後再試。")

    # --- Tab 2: 對比表 ---
    with tab2:
        st.subheader("📋 快速對比清單")
        results = []
        for t in ticker_list:
            d, i = fetch_data(t)
            if d is not None:
                curr = float(d['Close'].iloc[-1])
                results.append({"代號": t, "股價": round(curr, 2), "產業": i.get('sector', 'N/A')})
        if results:
            st.table(pd.DataFrame(results))

else:
    st.info("💡 請在左側輸入代號並按下『🚀 開始量化分析』。若一直沒反應，可能是 Yahoo 伺服器暫時限流。")
