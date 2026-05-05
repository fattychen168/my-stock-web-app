import streamlit as st
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go

st.set_page_config(page_title="美股分析", layout="wide")

# 增加進度條提示
with st.spinner('數據讀取中，請稍候...'):
    st.title("🍎 美股技術面分析系統")
    
    ticker = st.sidebar.text_input("輸入股票代號", "AAPL")
    
    # 確保代號是大寫
    ticker = ticker.upper()
    
    # 抓取數據
    df = yf.download(ticker, period="1y")

    if not df.empty:
        # 計算指標
        df['SMA200'] = ta.sma(df['Close'], length=200)
        
        # 指標看板
        curr_price = df['Close'].iloc[-1]
        st.metric(f"{ticker} 當前股價", f"${curr_price:.2f}")

        # 畫圖
        fig = go.Figure(data=[go.Candlestick(x=df.index,
                    open=df['Open'], high=df['High'],
                    low=df['Low'], close=df['Close'])])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error(f"目前無法取得 {ticker} 的數據，請檢查代號或稍後再試。")
