import streamlit as st
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# 1. 網頁頁面美化設定
st.set_page_config(page_title="KGI量化情緒分析儀", layout="wide")
st.markdown("""<style>.stMetric { background-color: #1e2130; border-radius: 10px; padding: 15px; border: 1px solid #3e4150; }</style>""", unsafe_allow_stdio=True)

# 2. 側邊欄控制
st.sidebar.title("📊 參數設定")
ticker_symbol = st.sidebar.text_input("輸入股票代號", "NVDA").upper()
ma_fast = st.sidebar.slider("短線均線", 10, 100, 50)
ma_slow = st.sidebar.slider("長線年線", 100, 300, 200)

# 3. 數據抓取
@st.cache_data(ttl=3600)
def get_data(symbol):
    df = yf.download(symbol, period="2y")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

df = get_data(ticker_symbol)

if not df.empty:
    # --- 指標計算 ---
    df['SMA_F'] = ta.sma(df['Close'], length=ma_fast)
    df['SMA_S'] = ta.sma(df['Close'], length=ma_slow)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    # 增加交易量指標：5日平均成交量
    df['Vol_MA5'] = ta.sma(df['Volume'], length=5)
    
    last = df.iloc[-1]
    prev = df.iloc[-2]
    p, f, s, rsi = float(last['Close']), float(last['SMA_F']), float(last['SMA_S']), float(last['RSI'])
    vol_curr = float(last['Volume'])
    vol_ma5 = float(last['Vol_MA5'])

    # --- 核心邏輯：加權評分 (加入成交量與情緒) ---
    score = 0
    signals = []

    # A. 趨勢與成交量 (40%)
    if p > s and f > s: 
        score += 20
        signals.append("🟢 長線多頭：股價在年線之上且均線交叉。")
    
    if vol_curr > vol_ma5 * 1.5:
        score += 20
        signals.append("🔥 成交量爆發：當前買氣極強，資金進場。")
    elif vol_curr < vol_ma5 * 0.7:
        score -= 10
        signals.append("⚪ 成交量萎縮：買盤力道不足，小心量價背離。")

    # B. 投資人情緒溫度 (30%)
    # 利用乖離率 (Bias) 與 RSI 判定
    bias = (p - f) / f * 100
    if 30 < rsi < 65:
        score += 30
        sentiment = "理性樂觀"
        signals.append(f"⚖️ 情緒穩定：RSI ({rsi:.1f}) 處於健康區間。")
    elif rsi >= 75:
        score -= 20
        sentiment = "極度狂熱"
        signals.append("🔴 市場過熱：情緒指標進入超買區，隨時可能反轉。")
    elif rsi <= 25:
        score += 20 # 逆向思考
        sentiment = "極度恐慌"
        signals.append("🔵 恐慌買點：市場過度悲觀，通常是撿便宜的好時機。")
    else:
        score += 10
        sentiment = "觀望中"

    # C. 買點位階 (30%)
    if -2 < bias < 3:
        score += 30
        signals.append("✅ 完美買點：價格回測支撐位。")

    # --- 介面呈現 ---
    st.title(f"🚀 {ticker_symbol} 情緒與量化診斷報告")
    
    # 儀表板
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("當前股價", f"${
