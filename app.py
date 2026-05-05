import streamlit as st
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# 1. 網頁頁面美化與自定義 CSS
st.set_page_config(page_title="KGI量化投資領航員", layout="wide")

st.markdown("""
    <style>
    .reportview-container { background: #0e1117; }
    .stMetric { background-color: #1e2130; border-radius: 12px; padding: 20px; border: 1px solid #3e4150; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .stAlert { border-radius: 10px; border: none; }
    div[data-testid="stExpander"] { border: 1px solid #3e4150; border-radius: 10px; }
    h1, h2, h3 { color: #deff9a !important; font-family: 'Urbanist', sans-serif; }
    </style>
    """, unsafe_allow_stdio=True)

# 2. 側邊欄控制
st.sidebar.title("🛡️ 投資決策系統")
ticker_symbol = st.sidebar.text_input("輸入美股代號", "NVDA").upper()
ma_fast = st.sidebar.slider("短線趨勢 (MA50)", 10, 100, 50)
ma_slow = st.sidebar.slider("長線年線 (MA200)", 100, 300, 200)

# 3. 數據與資訊抓取模組
@st.cache_data(ttl=3600)
def get_full_info(symbol):
    stock = yf.Ticker(symbol)
    df = stock.history(period="2y")
    info = stock.info
    # 攤平多重索引
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df, info

df, info = get_full_info(ticker_symbol)

# 4. 產業與規模邏輯判斷
def classify_stock(info):
    # 產業分類
    sector = info.get('sector', '未知產業')
    industry = info.get('industry', '未知細分行業')
    
    # 市值分類 (美金)
    mcap = info.get('marketCap', 0)
    if mcap >= 200000000000: # 200B+
        size_label = "💎 超大型股 (Mega-Cap)"
    elif mcap >= 10000000000: # 10B - 200B
        size_label = "🏢 大型股 (Large-Cap)"
    elif mcap >= 2000000000:  # 2B - 10B
        size_label = "🧱 中型股 (Mid-Cap)"
    else:
        size_label = "🌱 小型股 (Small-Cap)"
    
    return sector, industry, size_label, mcap

# 5. 主畫面流程
if not df.empty:
    sector, industry, size_label, mcap = classify_stock(info)
    
    # 計算技術指標
    df['SMA_F'] = ta.sma(df['Close'], length=ma_fast)
    df['SMA_S'] = ta.sma(df['Close'], length=ma_slow)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    df['Vol_MA'] = ta.sma(df['Volume'], length=5)
    
    last = df.iloc[-1]
    p, f, s, rsi = float(last['Close']), float(last['SMA_F']), float(last['SMA_S']), float(last['RSI'])
    vol_curr, vol_ma = float(last['Volume']), float(last['Vol_MA'])

    # --- 第一區：基本面與標籤 ---
    st.title(f"🚀 {ticker_symbol} | {info.get('longName', ticker_symbol)}")
    
    tag_col1, tag_col2, tag_col3 = st.columns([1, 1, 2])
    tag_col1.markdown(f"**產業分類：** `{sector}`")
    tag_col2.markdown(f"**市值規模：** `{size_label}`")
    tag_col3.markdown(f"**細分行業：** `{industry}`")
    
    st.divider()

    # --- 第二區：即時數據與情緒看板 ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("當前股價", f"${p:.2f}", f"{((p/df['Close'].iloc[-2])-1)*100:.2f}%")
