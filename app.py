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

# 加入按鈕
run_button = st.sidebar.button("🚀 開始量化分析")

# 3. 數據抓取函數 (加強錯誤回報)
@st.cache_data(ttl=3600)
def get_full_stock_data(symbol):
    try:
        stock = yf.Ticker(symbol)
        # 抓取 2 年數據
        df = stock.history(period="2y")
        if df.empty:
            return None, None
        # 修正多重索引
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df, stock.info
    except Exception as e:
        st.error(f"抓取 {symbol} 時發生錯誤: {e}")
        return None, None

# 4. 主畫面標題
st.title("📈 KGI量化分析儀")

# --- 判斷按鈕點擊後的邏輯 ---
if run_button and ticker_list:
    # 建立分頁
    tab1, tab2 = st.tabs(["📌 深度診斷報告", "📋 多標的評分對比"])

    # --- Tab 1: 深度診斷 ---
    with tab1:
        target = ticker_list[0]
        with st.spinner(f'正在分析 {target}...'):
            df, info = get_full_stock_data(target)
            
            if df is not None:
                st.subheader(f"🔍 {target} 詳細診斷")
                
                # 計算指標
                df['SMA_F'] = ta.sma(df['Close'], length=ma_fast)
                df['SMA_S'] = ta.sma(df['Close'], length=ma_slow)
                df['RSI'] = ta.rsi(df['Close'], length=14)
                
                last_row = df.iloc[-1]
                curr_p = float(last_row['Close'])
                rsi_v = float(last_row['RSI']) if not pd.isna(last_row['RSI']) else 0
                
                # 安全獲取均線值
                sma_f_v = float(last_row['SMA_F']) if 'SMA_F' in last_row and not pd.isna(last_row['SMA_F']) else 0
                sma_s_v = float(last_row['SMA_S']) if 'SMA_S' in last_row and not pd.isna(last_row['SMA_S']) else 0

                # 產業與數據顯示
                st.write(f"**公司全名:** {info.get('longName', 'N/A')} | **產業:** {info.get('sector', 'N/A')}")
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("當前股價", f"${curr_p:.2f}")
                c2.metric("RSI 動能", f"{rsi_v:.1f}")
                c3.metric(f"{ma_fast}MA", f"${sma_f_v:.2f}")
                c4.metric(f"{ma_slow}MA", f"${sma_s_v:.2f}")
                
                # 圖表繪製
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
                
                fig.add_trace(go.Candlestick(
                    x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'
                ), row=1, col=1)
                
                fig.add_trace(go.Scatter(
                    x=df.index, y=df['SMA_F'], name='短均', line=dict(color='cyan', width=1.5)
                ), row=1, col=1)
                
                fig.add_trace(go.Scatter(
                    x=df.index, y=df['SMA_S'], name='年線', line=dict(color='magenta', width=2)
                ), row=1, col=1)
                
                fig.add_trace(go.Bar(
                    x=df.index, y=df['Volume'], name='成交量', marker_color='gray', opacity=0.4
                ), row=2, col=1)
                
                fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error(f"無法取得 {target} 的數據，請確認代號或 API 狀態。")

    # --- Tab 2: 多標的對比 ---
    with tab2:
        st.subheader("📋 綜合評分對比")
        summary_list = []
        for t in ticker_list:
            d, i = get_full_stock_data(t)
            if d is not None:
                p_v = float(d['Close'].iloc[-1])
                # 計算簡易分數
                ma200_series = ta.sma(d['Close'], length=200)
                ma200_val = float(ma200_series.iloc[-1]) if not ma200_series.empty else 0
                score = 100 if p_v > ma200_val else 50
                summary_list.append({"代號": t, "股價": round(p_v, 2), "產業": i.get('sector', 'N/A'), "量化分數": score})
        
        if summary_list:
            st.table(pd.DataFrame(summary_list))

elif not ticker_list:
    st.warning("👈 請在左側輸入股票代號。")
else:
    st.info("💡 設定完成後，請點擊左側的『🚀 開始量化分析』產生報告。")
