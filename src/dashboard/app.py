import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import sys
import os

# --- 1. CONFIGURATION & SETUP ---
# Add project root to path so we can import utils if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Nexus Intelligence", layout="wide")

st.title("⚡ Nexus Market Intelligence")
st.markdown("### Real-time AI Analysis of E-Commerce Trends")

# --- 2. SIDEBAR CONTROLS ---
st.sidebar.header("Filter Options")
search_term = st.sidebar.text_input("Search Product", "Headphone")
min_rating = st.sidebar.slider("Minimum Rating", 0.0, 5.0, 3.5)

# --- 3. FETCH DATA ---
df = pd.DataFrame() # Initialize empty dataframe
try:
    response = requests.get(f"{API_URL}/products/search", params={"query": search_term, "min_rating": min_rating})
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
    else:
        # If API is up but returns error (e.g. database empty)
        pass 
except Exception as e:
    st.error(f"⚠️ API connection failed. Is the server running? Error: {e}")
    st.info("Run 'uvicorn src.api.main:app --reload' in a separate terminal.")

# --- 4. MAIN DASHBOARD LOGIC ---
if not df.empty:
    # Metrics Row
    col1, col2, col3 = st.columns(3)
    col1.metric("Products Found", len(df))
    # Handle price display safely
    avg_price = df['price'].mean() if 'price' in df.columns else 0
    col2.metric("Avg Price", f"₹{avg_price:.0f}")
    
    avg_rating = df['rating'].mean() if 'rating' in df.columns else 0
    col3.metric("Avg Rating", f"{avg_rating:.1f} ⭐")

    # AI Insights Table
    st.subheader("🤖 GenAI Analysis")
    # Check if AI columns exist, otherwise fill with defaults
    if 'audience' not in df.columns:
        df['audience'] = "Pending"
    if 'value_prop' not in df.columns:
        df['value_prop'] = "Pending"

    st.dataframe(
        df[['title', 'price', 'rating', 'audience', 'value_prop']],
        use_container_width=True,
        hide_index=True
    )

    # Chart
    st.subheader("💰 Price vs Rating Landscape")
    if 'price' in df.columns and 'rating' in df.columns:
        fig = px.scatter(
            df, x="price", y="rating", 
            size="price", hover_name="title",
            color="rating", color_continuous_scale="RdBu"
        )
        st.plotly_chart(fig, use_container_width=True)

# --- 5. "NO RESULTS" LOGIC (TRIGGER SCRAPER) ---
else:
    if search_term:
        st.warning(f"No cached data found for '{search_term}'.")
        
        st.markdown(f"### 🚀 Launch Live Scraper?")
        st.write(f"Nexus can scrape Amazon India in real-time for **'{search_term}'**.")
        
        if st.button(f"Scrape '{search_term}' Now"):
            with st.spinner("Initializing Autonomous Agent... (This takes ~15 seconds)"):
                try:
                    # Call the Ingest Endpoint
                    res = requests.post(f"{API_URL}/ingest/live", params={"search_term": search_term})
                    
                    if res.status_code == 200:
                        data = res.json()
                        st.success(f"Success! {data['message']}")
                        st.rerun() # Refresh page to show new data
                    else:
                        st.error(f"Scraping Failed: {res.text}")
                except Exception as e:
                    st.error(f"Error triggering scraper: {e}")

# --- 6. LIVE LAB ---
st.divider()
st.subheader("🧪 Live Lab: Test a New Product")
with st.form("ai_lab"):
    new_product = st.text_input("Product Title", "Sony WH-1000XM6 Noise Cancelling")
    new_price = st.number_input("Price (₹)", 25000)
    submitted = st.form_submit_button("Analyze with Gemini")
    
    if submitted:
        with st.spinner("Consulting Gemini 2.0..."):
            try:
                res = requests.get(f"{API_URL}/intelligence/live-analyze", params={"product_name": new_product, "price": new_price})
                if res.status_code == 200:
                    st.json(res.json())
                else:
                    st.error("Analysis Failed")
            except Exception as e:
                st.error(f"Connection Error: {e}")