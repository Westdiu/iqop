import time
import pandas as pd
import streamlit as st
from iqoptionapi.stable_api import IQ_Option  # pip install iqoptionapi
from ta.trend import SMAIndicator
from ta.momentum import RSIIndicator

# === API CONFIGURATION ===
st.set_page_config(page_title="🤖 IQ Option Robot", layout="wide")

# API Credentials (store in environment variables for security)
EMAIL = st.sidebar.text_input("IQ Option Email", type="default")
PASSWORD = st.sidebar.text_input("IQ Option Password", type="password")
SYMBOL = st.sidebar.selectbox("Asset", ["EURUSD", "GBPUSD", "BTCUSD"])
ACCOUNT_TYPE = st.sidebar.selectbox("Account Type", ["PRACTICE", "REAL"])
INVESTMENT = st.sidebar.number_input("Investment per Trade ($)", min_value=10, value=10)
STOP_LOSS_PERCENT = st.sidebar.number_input("Stop-Loss (%)", min_value=1, max_value=100, value=10)

# Connect to the API
if EMAIL and PASSWORD:
    try:
        api = IQ_Option(EMAIL, PASSWORD)
        api.connect()
        if api.check_connect():
            st.sidebar.success("Connection successful!")
        else:
            st.sidebar.error("Connection error. Check your credentials.")
    except Exception as e:
        st.sidebar.error(f"Connection error: {e}")
else:
    st.sidebar.warning("Enter your IQ Option email and password")

# === TECHNICAL ANALYSIS ===
def analyze_market(symbol, timeframe=60):
    """Fetch market data and calculate indicators."""
    candles = api.get_candles(symbol, timeframe, 100, time.time())
    df = pd.DataFrame(candles)
    df['close'] = df['close'].astype(float)
    
    # Calculate SMA and RSI
    df['sma_short'] = SMAIndicator(close=df['close'], window=10).sma_indicator()
    df['sma_long'] = SMAIndicator(close=df['close'], window=50).sma_indicator()
    df['rsi'] = RSIIndicator(close=df['close'], window=14).rsi()
    
    return df

# === AUTO MODE ===
def auto_mode():
    st.info("Auto mode activated. Monitoring the market...")
    balance = api.get_balance()
    st.success(f"Current Balance: ${balance:.2f}")
    
    while True:
        df = analyze_market(SYMBOL)
        last_row = df.iloc[-1]
        
        # Check Stop-Loss
        current_balance = api.get_balance()
        if (balance - current_balance) / balance * 100 >= STOP_LOSS_PERCENT:
            st.error("Stop-Loss reached! Stopping operations.")
            break
        
        # Trading Logic
        if last_row['sma_short'] > last_row['sma_long'] and last_row['rsi'] < 30:
            st.balloons()
            st.success(f"Buy (Call) at {time.strftime('%H:%M:%S')}")
            api.buy(INVESTMENT, SYMBOL, "call", 1)
        elif last_row['sma_short'] < last_row['sma_long'] and last_row['rsi'] > 70:
            st.balloons()
            st.error(f"Sell (Put) at {time.strftime('%H:%M:%S')}")
            api.buy(INVESTMENT, SYMBOL, "put", 1)
        else:
            st.warning("Waiting for an opportunity...")
        
        time.sleep(60)  # Update every minute

# === MANUAL MODE ===
def manual_mode():
    st.info("Manual mode activated. Analyzing the chart...")
    df = analyze_market(SYMBOL)
    last_row = df.iloc[-1]
    
    # Display analysis
    st.subheader("📊 Market Analysis")
    st.write(f"Last Price: {last_row['close']:.5f}")
    st.write(f"Short SMA (10): {last_row['sma_short']:.5f}")
    st.write(f"Long SMA (50): {last_row['sma_long']:.5f}")
    st.write(f"RSI (14): {last_row['rsi']:.2f}")
    
    # Entry signal
    if last_row['sma_short'] > last_row['sma_long'] and last_row['rsi'] < 30:
        st.success(f"BUY (Call) signal detected for {SYMBOL}!")
    elif last_row['sma_short'] < last_row['sma_long'] and last_row['rsi'] > 70:
        st.error(f"SELL (Put) signal detected for {SYMBOL}!")
    else:
        st.warning("No clear signals at the moment.")

# === USER INTERFACE ===
st.title("🚀 Binary Options Robot (IQ Option)")
st.subheader("Simplified Configuration")

# Choose Mode
mode = st.radio("Choose Mode:", ("Auto Mode", "Manual Mode"))

if mode == "Auto Mode":
    if st.button("▶️ Start Auto Mode"):
        auto_mode()
elif mode == "Manual Mode":
    if st.button("🔍 Analyze Chart"):
        manual_mode()

# Risk Panel
st.subheader("Risk Management")
st.progress(STOP_LOSS_PERCENT / 100)
st.caption(f"Stop-Loss set to {STOP_LOSS_PERCENT}%")

# Trade History
st.subheader("Trade History")
trades = api.get_optioninfo(10)  # Last 10 trades
st.table(trades)