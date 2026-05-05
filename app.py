import streamlit as st
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import time
import random

# 1. 網頁頁面基礎設定
st.set_page_config(page_title="全球美股量化診斷儀", layout="wide")

# 自定義 CSS 美化
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

# 2. 側邊欄控制與參數
st.sidebar.title("🛡️ 量化決策參數")
ticker_input = st.sidebar.text_input("輸入美股代號 (多支請用逗號隔開)", "NVDA, AAPL").upper()
ticker_list = [t.strip() for t in ticker_input.split(",") if t.strip()]

ma_fast = st.sidebar.slider("短線趨勢均線", 10, 100, 50)
ma_slow = st.sidebar.slider("長線年線位置", 100, 300, 200)

# 核心啟動按鈕
run_button = st.sidebar.button("🚀 開始量化分析")

# 3. 強化的數據抓取函數 (避開限流與處理錯誤)
@st.cache_data(ttl=86400) # 快取 24 小時，避免頻繁請求被封鎖 IP
def fetch_stock_data(symbol):
    # 加入微小隨機延遲，模擬人類行為
    time.sleep(random.uniform(0.5, 1.5))
    df = pd.DataFrame()
    info = {}
    try:
        stock = yf.Ticker(symbol)
        # 優先嘗試 history 模式
        df = stock.history(period="2y", timeout=25)
        info = stock.info
        
        # 備援：若 history 為空，嘗試 download 模式
        if df.empty:
            df = yf.download(symbol, period="2y", progress=False, timeout=25)
            
        if not df.empty:
            # 處理多重索引問題 (yfinance 升級後的常見 Bug)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            return df, info
    except Exception as e:
        if "Too Many Requests" in str(e):
            st.error(f"⚠️ Yahoo 伺服器目前對此 IP 限流。請等待 15 分鐘冷卻期。")
        else:
            st.error(f"數據抓取錯誤 ({symbol}): {str(e)}")
    return None, None

# 4. 主畫面邏輯
st.title("📈 智能量化診斷：產業、規模與情緒分析")

if run_button and ticker_list:
    tab1, tab2 = st.tabs(["📌 深度診斷報告", "📋 多標的快速對比"])

    # --- Tab 1: 深度報告 ---
    with tab1:
        target = ticker_list[0] # 預設分析清單中第一個標的
        with st.spinner(f'正在分析 {target} 資料中...'):
            df, info = fetch_stock_data(target)
            
            if df is not None and not df.empty:
                # 計算技術指標
                df['SMA_F'] = ta.sma(df['Close'], length=ma_fast)
                df['SMA_S'] = ta.sma(df['Close'], length=ma_slow)
                df['RSI'] = ta.rsi(df['Close'], length=14)
                
                # 數據類型安全轉換 (解決 TypeError)
                last = df.iloc[-1]
                def get_val(key):
                    val = last.get(key, 0)
                    return float(val.item()) if hasattr(val, 'item') else float(val)

                p_val = get_val('Close')
                r_val = get_val('RSI')
                f
