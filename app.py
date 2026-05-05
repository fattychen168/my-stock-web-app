import streamlit as st
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go
import pandas as pd

# 1. 網頁基本設定
st.set_page_config(page_title="美股自動分析儀表板", layout="wide")

# 2. 側邊欄設定
st.sidebar.header("🔍 投資參數")
ticker_input = st.sidebar.text_input("輸入美股代號", "NVDA").upper()
ma_days = st.sidebar.slider("均線天數 (SMA)", 50, 250, 200)

st.title(f"📈 {ticker_input} 技術面分析儀表板")

# 3. 抓取數據 (加入快取避免重複讀取)
@st.cache_data
def load_data(symbol):
    df = yf.download(symbol, period="1y")
    # 關鍵修正：處理 yfinance 新版本的多重索引問題
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

# 執行抓取
df = load_data(ticker_input)

# 4. 判斷數據是否成功抓取
if not df.empty and len(df) > ma_days:
    # 計算指標
    df['SMA'] = ta.sma(df['Close'], length=ma_length if 'ma_length' in locals() else ma_days)
    df['RSI'] = ta.rsi(df['Close'], length=14)

    # 取得最新一筆數據並強制轉為數值
    latest_data = df.iloc[-1]
    curr_price = float(latest_data['Close'])
    sma_price = float(latest_data['SMA'])
    rsi_val = float(latest_data['RSI'])

    # 5. 顯示數據指標卡片
    col1, col2, col3 = st.columns(3)
    col1.metric("當前股價", f"${curr_price:.2f}")
    col2.metric(f"{ma_days}日均線", f"${sma_price:.2f}")
    col3.metric("RSI (14)", f"{rsi_val:.1f}")

    # 6. 趨勢診斷
    if curr_price > sma_price:
        st.success(f"✅ 多頭趨勢：{ticker_input} 股價站於均線之上。")
    else:
        st.warning(f"⚠️ 空頭趨勢：{ticker_input} 股價低於均線。")

    # 7. 繪製互動 K 線圖
    fig = go.Figure()
    # K 線
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'],
        name="K線"
    ))
    # 均線
    fig.add_trace(go.Scatter(
        x=df.index, y=df['SMA'],
        name=f"{ma_days}MA",
        line=dict(color='orange', width=2)
    ))

    fig.update_layout(
        title=f"{ticker_input} 歷史走勢與 {ma_days} 均線",
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        height=600
    )
    st.plotly_chart(fig, use_container_width=True)

else:
    st.error(f"無法取得 {ticker_input} 的數據。請確認代號是否正確，或增加數據長度。")
