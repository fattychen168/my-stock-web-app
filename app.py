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

run_button = st.sidebar.button("🚀 開始量化分析")

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
st.title("📈 KGI量化分析儀：產業、規模與情緒診斷")

if run_button:
    tab1, tab2 = st.tabs(["📌 深度診斷報告", "📋 多標的評分對比"])

    with tab1:
        if ticker_list:
            target = ticker_list[0] 
            df, info = get_full_stock_data(target)
            
            if df is not None:
                st.subheader(f"🔍 {target} 詳細診斷")
                
                # 計算技術指標
                df['SMA_F'] = ta.sma(df['Close'], length=ma_fast)
                df['SMA_S'] = ta.sma(df['Close'], length=ma_slow)
                df['RSI'] = ta.rsi(df['Close'], length=14)
                
                last_row = df.iloc[-1]
                curr_p = float(last_row['Close'])
                rsi_v = float(last_row['RSI'])
                sma_f_v = float(last_row['SMA_F']) if not pd.isna(last_row['SMA_F']) else 0
                sma_s_v = float(last_row['SMA_S']) if not pd.isna(last_row['SMA_S']) else 0

                # 產業資訊
                mcap = info.get('marketCap', 0)
                st.markdown(f"**產業：** `{info.get('sector', 'N/A')}` | **市值：** `${mcap/1e9:.1f}B`")
                
                # 數據指標
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("當前股價", f"${curr_p:.2f}")
                c2.metric("RSI 動能", f"{rsi_v:.1f}")
                c3.metric(f"{ma_fast}MA", f"${sma_f_v:.2f}")
                c4.metric(f"{ma_slow}MA", f"${sma_s_v:.2f}")
                
                # --- 核心繪圖區 (嚴格檢查括號) ---
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
                
                # K線圖
                fig.add_trace(go.Candlestick(
                    x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'
                ), row=1, col=1)
                
                # 短均線
                fig.add_trace(go.Scatter(
                    x=df.index, y=df['SMA_F'], name='短均', line=dict(color='cyan', width=1)
                ), row=1, col=1)
                
                # 長均線
                fig.add_trace(go.Scatter(
                    x=df.index, y=df['SMA_S'], name='年線', line=dict(color='magenta', width=2)
                ), row=1, col=1)
                
                # 成交量
                fig.add_trace(go.Bar(
                    x=df.index, y=df['Volume'], name='成交量', marker_color='gray', opacity=0.4
                ), row=2, col=1)
                
                fig.update_layout(template="plotly_dark", height=700, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("請在側邊欄輸入正確代號。")

    with tab2:
        st.subheader("📋 綜合量化評分表")
        summary_list = []
        for t in ticker_list:
            d, i = get_full_stock_data(t)
            if d is not None:
                p_v = float(d['Close'].iloc[-1])
                r_v = float(ta.rsi(d['Close'], length=14).iloc[-1])
                score = 100 if p_v > float(ta.sma(d['Close'], length=ma_slow).iloc[-1]) else 50
                summary_list.append({"代號": t, "股價": round(p_v, 2), "RSI": round(r_v, 1), "總分": score})
        
        if summary_list:
            st.dataframe(pd.DataFrame(summary_list), use_container_width=True)
else:
    st.info("👋 歡迎！請在左側輸入代號並按下『🚀 開始量化分析』。")
