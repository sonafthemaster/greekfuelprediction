import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
from sklearn.linear_model import LinearRegression
import yfinance as yf
import requests

st.set_page_config(page_title="Fuel Pro Dashboard", layout="wide")

# -----------------------------
# REAL DATA SOURCES
# -----------------------------
def get_rbob_real():
    try:
        data = yf.Ticker("RB=F").history(period="1d")
        return float(data['Close'].iloc[-1])
    except:
        return None

def get_brent():
    try:
        data = yf.Ticker("BZ=F").history(period="1d")
        return float(data['Close'].iloc[-1])
    except:
        return None

def get_fx():
    try:
        res = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
        return float(res.json()["rates"]["EUR"])
    except:
        return None

# -----------------------------
# GREECE PRICE MODEL
# -----------------------------
def calculate_greece_price(oil_price, fx):
    if oil_price is None or fx is None:
        return None

    eur_price = oil_price * fx

    refinery = eur_price / 100
    tax = 0.7
    vat = 0.24

    final = (refinery + tax) * (1 + vat)
    return final

# -----------------------------
# AI MODEL
# -----------------------------
def train_model(df):
    if len(df) < 5:
        return None

    X = np.arange(len(df)).reshape(-1, 1)
    y = df['brent'].values

    model = LinearRegression()
    model.fit(X, y)
    return model

def predict_next(model, df):
    if model is None:
        return None
    return model.predict([[len(df)]])[0]

# -----------------------------
# ALERT SYSTEM
# -----------------------------
def check_alerts(df):
    if len(df) < 2:
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2]

    change = (last['brent'] - prev['brent']) / prev['brent'] * 100

    if change > 2:
        return f"🚨 ALERT: Price Spike +{change:.2f}%"
    elif change < -2:
        return f"⚠️ ALERT: Price Drop {change:.2f}%"
    return None

# -----------------------------
# SESSION STATE
# -----------------------------
if 'data' not in st.session_state:
    st.session_state.data = []

# -----------------------------
# UI HEADER
# -----------------------------
st.title("⛽ Fuel Pro Analytics Dashboard")
st.markdown("Real Data • AI Prediction • Greece Pricing Model")

col1, col2, col3, col4 = st.columns(4)

# -----------------------------
# UPDATE BUTTON
# -----------------------------
if col1.button("🔄 Update Live Data"):
    rbob = get_rbob_real()
    brent = get_brent()
    fx = get_fx()

    gr_price = calculate_greece_price(brent, fx)

    now = datetime.now()

    st.session_state.data.append({
        'time': now,
        'rbob': rbob,
        'brent': brent,
        'fx': fx,
        'greece_price': gr_price
    })

# -----------------------------
# DATAFRAME
# -----------------------------
df = pd.DataFrame(st.session_state.data)

if not df.empty:

    last = df.iloc[-1]

    col1.metric("Brent Oil", f"{last['brent']:.2f}" if last['brent'] else "-")
    col2.metric("RBOB", f"{last['rbob']:.2f}" if last['rbob'] else "-")
    col3.metric("USD/EUR", f"{last['fx']:.3f}" if last['fx'] else "-")
    col4.metric("🇬🇷 Pump Price (€)", f"{last['greece_price']:.3f}" if last['greece_price'] else "-")

    st.subheader("📊 Market Data")
    st.dataframe(df)

    fig = px.line(df, x='time', y=['brent', 'rbob', 'fx'], title="Market Trends")
    st.plotly_chart(fig, use_container_width=True)

    model = train_model(df)
    pred = predict_next(model, df)

    st.subheader("🤖 AI Forecast")
    if pred:
        st.metric("Next Brent Prediction", f"{pred:.2f}")

    alert = check_alerts(df)
    if alert:
        st.error(alert)

else:
    st.info("Press Update to fetch live market data")

st.markdown("---")
st.markdown("Professional Fuel Analytics System")