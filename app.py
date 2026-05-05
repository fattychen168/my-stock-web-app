import streamlit as st
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go
import pandas as pd

# 1. 網頁基本設定：讓外觀更專業
st.set_page_config(page_title="KGI量化美股分析儀", layout="wide", initial_sidebar_state="expanded")

# 加入自訂 CSS 讓字體更好看
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e4150; }
    </style>
    """, unsafe_allow_stdio=True)

# 2. 側邊欄控制區
st.sidebar.title("🛠 系統設定")
ticker_symbol = st.sidebar.text_input("輸入股票代號", "NVDA").upper()
ma_fast = st.sidebar.number_input("短線均線 (例如 50)", value=50)
ma_slow = st.sidebar.number_input("長線均線 (例如 200)", value=200)

# 3. 數據抓取模組
@st.cache_data(ttl=3600) # 快取 1 小時
def get_stock_data(symbol):
    try:
        df = yf.download(symbol, period="2y") # 抓兩年數據以便計算長均線
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except:
        return pd.DataFrame()

df = get_stock_data(ticker_symbol)

# 4. 主畫面邏輯
if not df.empty:
    # --- 計算技術指標 ---
    df['SMA_Fast'] = ta.sma(df['Close'], length=ma_fast)
    df['SMA_Slow'] = ta.sma(df['Close'], length=ma_slow)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    
    # 取得最新數值
    last = df.iloc[-1]
    price = float(last['Close'])
    fast_val = float(last['SMA_Fast'])
    slow_val = float(last['SMA_Slow'])
    rsi_val = float(last['RSI'])
    
    # --- 第一區：指標儀表板 ---
    st.title(f"📊 {ticker_symbol} 即時量化報告")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("當前股價", f"${price:.2f}")
    c2.metric(f"{ma_fast}MA (短線)", f"${fast_val:.2f}")
    c3.metric(f"{ma_slow}MA (長線)", f"${slow_val:.2f}")
    c4.metric("RSI 強度", f"{rsi_val:.1f}")

    # --- 第二區：自動篩選邏輯與訊號 ---
    st.divider()
    col_info, col_signal = st.columns([2, 1])
    
    with col_info:
        st.subheader("💡 智慧診斷")
        # 邏輯判斷
        is_bullish = price > slow_val
        is_golden_cross = fast_val > slow_val
        is_overbought = rsi_val > 70
        is_oversold = rsi_val < 30
        
        # 顯示條件清單
        st.write(f"1. 股價是否站上年線：{'✅ 是' if is_bullish else '❌ 否'}")
        st.write(f"2. 均線是否形成多頭排列：{'✅ 是' if is_golden_cross else '❌ 否'}")
        st.write(f"3. RSI 狀態：{'🔥 超買 (過熱)' if is_overbought else '❄️ 超賣 (過冷)' if is_oversold else '⚖️ 中性'}")

    with col_signal:
        st.subheader("🚩 操作建議")
        if is_bullish and is_golden_cross and not is_overbought:
            st.success("🎯 強烈建議：趨勢多頭，且尚未過熱，適合關注。")
        elif not is_bullish:
            st.error("📉 觀望：目前處於空頭趨勢，建議耐心等待。")
        else:
            st.info("⌛ 中性：趨勢不明或處於盤整，建議分批佈局。")

    # --- 第三區：互動 K 線圖 ---
    st.divider()
    fig = go.Figure()
    # K 線
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                                low=df['Low'], close=df['Close'], name='K線'))
    # 均線
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_Fast'], name=f'{ma_fast}MA', line=dict(color='#00ff00', width=1.5)))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_Slow'], name=f'{ma_slow}MA', line=dict(color='#ff0000', width=2)))
    
    fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False,
                      margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, use_container_width=True)

    # --- 第四區：數據明細 ---
    with st.expander("查看原始數據明細"):
        st.write(df.tail(10))

else:
