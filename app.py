import streamlit as st
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import time
import random

# 1. 頁面基本設定
st.set_page_config(page_title="全球美股量化診斷儀", layout="wide")

# 2. 側邊欄參數
st.sidebar.title("🛡️ 量化決策參數")
ticker_input = st.sidebar.text_input("輸入美股代號 (多支用逗號隔開)", "NVDA, AAPL").upper()
ticker_list = [t.strip() for t in ticker_input.split(",") if t.strip()]

ma_fast = st.sidebar.slider("短線趨勢均線", 10, 100, 50)
ma_slow = st.sidebar.slider("長線年線位置", 100, 300, 200)

run_button = st.sidebar.button("🚀 開始量化分析")

# 3. 數據抓取函數 (強化備援)
@st.cache_data(ttl=86400)
def fetch_stock_full_data(symbol):
    time.sleep(random.uniform(1.0, 2.0))
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period="2y", timeout=25)
        if df.empty:
            df = yf.download(symbol, period="2y", progress=False, timeout=25)
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            return df, stock.info
    except:
        return None, None
    return None, None

# 4. 主畫面邏輯
st.title("📈 智能量化診斷儀")

if run_button and ticker_list:
    tab1, tab2 = st.tabs(["📌 深度診斷報告", "📋 多標的快速對比"])

    with tab1:
        target = ticker_list[0]
        with st.spinner(f"正在分析 {target} 並生成建議..."):
            df, info = fetch_stock_full_data(target)
            
            if df is not None and not df.empty:
                # 指標計算
                df['SMA_F'] = ta.sma(df['Close'], length=ma_fast)
                df['SMA_S'] = ta.sma(df['Close'], length=ma_slow)
                df['RSI'] = ta.rsi(df['Close'], length=14)
                
                last = df.iloc[-1]
                p_val = float(last['Close'])
                r_val = float(last['RSI']) if not pd.isna(last['RSI']) else 50.0
                f_val = float(last['SMA_F']) if not pd.isna(last['SMA_F']) else 0.0
                s_val = float(last['SMA_S']) if not pd.isna(last['SMA_S']) else 0.0

                # A. 規模判定邏輯
                mcap = info.get('marketCap', 0)
                if mcap >= 2e11: size_tag = "💎 超大型股 (Mega-Cap)"
                elif mcap >= 1e10: size_tag = "🏢 大型股 (Large-Cap)"
                elif mcap >= 2e9: size_tag = "🧱 中型股 (Mid-Cap)"
                else: size_tag = "🌱 小型股 (Small-Cap)"

                st.subheader(f"🔍 {target} | {info.get('longName', target)}")
                st.markdown(f"**市值規模：** `{size_tag}` | **產業：** `{info.get('sector', 'N/A')}`")

                # B. 操作建議邏輯
                st.divider()
                col_adv1, col_adv2, col_adv3 = st.columns(3)
                
                # 短線建議 (RSI + 股價vs短均)
                with col_adv1:
                    st.write("### ⚡ 短線建議")
                    if r_val > 70: st.warning("過熱：RSI過高，建議分批獲利了結，不宜追高。")
                    elif r_val < 30: st.success("超跌：RSI進入超賣區，具備反彈潛力，可小量試單。")
                    else: st.info("中性：動能穩定，適合觀察短線支撐。")

                # 中線建議 (股價 vs 50MA)
                with col_adv2:
                    st.write("### 🌀 中線建議")
                    if p_val > f_val: st.success("多頭：股價站穩短均線，回測不破可視為加碼點。")
                    else: st.error("弱勢：股價跌破短均線，中線轉趨震盪，建議縮減部位。")

                # 長線建議 (股價 vs 200MA)
                with col_adv3:
                    st.write("### 📜 長線建議")
                    if p_val > s_val: st.success("長多：股價運行於年線之上，適合長期領息或波段持有。")
                    else: st.warning("保守：股價低於年線，長線趨勢尚未反轉，建議觀望。")

                st.divider()

                # C. 數據卡片
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("當前股價", f"${p_val:.2f}")
                c2.metric("RSI 指標", f"{r_val:.1f}")
                c3.metric(f"{ma_fast}MA (短)", f"${f_val:.2f}")
                c4.metric(f"{ma_slow}MA (長)", f"${s_val:.2f}")

                # D. 圖表
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_F'], name='短均', line=dict(color='cyan')), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_S'], name='長均', line=dict(color='magenta')), row=1, col=1)
                fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='量', marker_color='gray', opacity=0.3), row=2, col=1)
                fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("目前無法取得數據，請檢查代號或等候 Yahoo 伺服器解鎖。")

    with tab2:
        st.subheader("📋 快速規模與價格對比")
        summary_data = []
        for t in ticker_list:
            d, i = fetch_stock_full_data(t)
            if d is not None:
                cp = float(d['Close'].iloc[-1])
                mc = i.get('marketCap', 0)
                summary_data.append({
                    "代號": t, 
                    "股價": round(cp, 2), 
                    "市值(B)": round(mc/1e9, 1),
                    "產業": i.get('sector', 'N/A')
                })
        if summary_data:
            st.table(pd.DataFrame(summary_data))
else:
    st.info("💡 請在左側輸入代號並點擊按鈕啟動診斷。")
else:
    st.info("💡 請在左側輸入代號並按下『🚀 開始量化分析』。")
