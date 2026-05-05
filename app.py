import streamlit as st
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go
import pandas as pd

# 1. 網頁基本設定
st.set_page_config(page_title="KGI量化交易診斷器", layout="wide")

# 2. 側邊欄：進階參數設定
st.sidebar.title("🛠 量化參數設定")
ticker_symbol = st.sidebar.text_input("輸入股票代號", "NVDA").upper()
ma_fast = st.sidebar.slider("短線均線 (MA50)", 10, 100, 50)
ma_slow = st.sidebar.slider("長線年線 (MA200)", 100, 300, 200)

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
    
    last = df.iloc[-1]
    p = float(last['Close'])
    f = float(last['SMA_F'])
    s = float(last['SMA_S'])
    rsi = float(last['RSI'])

    # --- 核心邏輯：加權評分系統 ---
    score = 0
    reasons = []

    # 1. 趨勢分 (40分)
    if p > s: 
        score += 25
        reasons.append("✅ 股價位於年線之上 (長線多頭)")
    if f > s: 
        score += 15
        reasons.append("✅ 均線黃金交叉 (多頭排列)")

    # 2. 動能分 (30分)
    if 40 <= rsi <= 60:
        score += 30
        reasons.append("✅ RSI 位處中性偏強區，具備上攻空間")
    elif rsi < 40:
        score += 15
        reasons.append("⚠️ RSI 較低，雖有反彈機會但動能偏弱")
    else:
        reasons.append("❌ RSI 過熱，回檔風險高")

    # 3. 位階分 (30分)
    dist_to_ma = (p - f) / f
    if -0.02 <= dist_to_ma <= 0.05: # 股價離短均線很近，代表支撐力強
        score += 30
        reasons.append("✅ 股價回測支撐位，為理想買點")
    elif dist_to_ma > 0.15:
        reasons.append("❌ 乖離率過大，不宜追高")
    else:
        score += 10

    # --- 顯示介面 ---
    st.title(f"🚀 {ticker_symbol} 量化診斷報告")
    
    # 推薦程度儀表板
    col_score, col_advice = st.columns([1, 2])
    
    with col_score:
        st.subheader("🔥 推薦程度")
        if score >= 80:
            st.write(f"## ⭐⭐⭐⭐⭐")
            st.success(f"評分：{score} / 100\n\n**強烈建議買入**")
        elif 60 <= score < 80:
            st.write(f"## ⭐⭐⭐⭐")
            st.info(f"評分：{score} / 100\n\n**分批佈局**")
        elif 40 <= score < 60:
            st.write(f"## ⭐⭐⭐")
            st.warning(f"評分：{score} / 100\n\n**中性觀望**")
        else:
            st.write(f"## ⭐")
            st.error(f"評分：{score} / 100\n\n**暫不進場**")

    with col_advice:
        st.subheader("📝 買點與建議原因")
        for r in reasons:
            st.write(r)

    # 圖表
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_F'], name='短均線', line=dict(color='cyan')))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_S'], name='長年線', line=dict(color='magenta')))
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=500)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("無法分析該標的。")
