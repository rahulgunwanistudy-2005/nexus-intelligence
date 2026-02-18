"""
Nexus Intelligence Dashboard — v2.0
Dark terminal aesthetic. Professional, emoji-free interface.
"""
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Nexus Intelligence", page_icon="N", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');
html,body,[data-testid="stAppViewContainer"]{background:#0a0e17!important;color:#e2e8f0!important;font-family:'IBM Plex Sans',sans-serif!important}
[data-testid="stSidebar"]{background:#0d1220!important;border-right:1px solid #1e2a3a!important}
.nxs-header{display:flex;align-items:baseline;gap:12px;padding-bottom:20px;border-bottom:1px solid #1e2a3a;margin-bottom:24px}
.nxs-logo{font-family:'IBM Plex Mono',monospace;font-size:20px;font-weight:600;color:#00d4aa;letter-spacing:-0.5px}
.nxs-sub{font-size:11px;color:#4a6080;letter-spacing:2px;text-transform:uppercase;font-family:'IBM Plex Mono',monospace}
.nxs-time{margin-left:auto;font-family:'IBM Plex Mono',monospace;font-size:11px;color:#4a6080}
.kpi-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:28px}
.kpi{background:#0d1220;border:1px solid #1e2a3a;border-radius:6px;padding:16px 20px;position:relative;overflow:hidden}
.kpi::before{content:'';position:absolute;top:0;left:0;right:0;height:2px}
.kpi.g::before{background:#00d4aa} .kpi.b::before{background:#3b82f6}
.kpi.a::before{background:#f59e0b} .kpi.p::before{background:#8b5cf6}
.kpi-lbl{font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;color:#4a6080;margin-bottom:8px}
.kpi-val{font-family:'IBM Plex Mono',monospace;font-size:26px;font-weight:600;color:#e2e8f0;line-height:1}
.kpi-val.sm{font-size:14px;padding-top:4px}
.kpi-tag{display:inline-block;margin-top:8px;font-size:10px;font-family:'IBM Plex Mono',monospace;padding:2px 8px;border-radius:20px;background:#1e2a3a;color:#4a6080}
.sec-lbl{font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#4a6080;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid #1e2a3a}
.sb-title{font-family:'IBM Plex Mono',monospace;font-size:14px;font-weight:600;color:#00d4aa;margin-bottom:4px}
.sb-ver{font-family:'IBM Plex Mono',monospace;font-size:10px;color:#4a6080;margin-bottom:20px}
.dot{display:inline-block;width:6px;height:6px;border-radius:50%;margin-right:6px;vertical-align:middle}
.dot.on{background:#00d4aa;box-shadow:0 0 6px #00d4aa} .dot.off{background:#ef4444}
hr{border-color:#1e2a3a!important}
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input{background:#0d1220!important;border:1px solid #1e2a3a!important;color:#e2e8f0!important;font-family:'IBM Plex Mono',monospace!important;border-radius:4px!important}
[data-testid="stTextInput"] input:focus{border-color:#00d4aa!important}
[data-testid="stButton"] button{background:#00d4aa!important;color:#0a0e17!important;border:none!important;font-family:'IBM Plex Mono',monospace!important;font-weight:600!important;font-size:12px!important;letter-spacing:1px!important;border-radius:4px!important}
::-webkit-scrollbar{width:4px;height:4px} ::-webkit-scrollbar-track{background:#0a0e17} ::-webkit-scrollbar-thumb{background:#1e2a3a;border-radius:2px}
</style>
""", unsafe_allow_html=True)

PLOT = dict(
    paper_bgcolor="#0d1220", plot_bgcolor="#0d1220",
    font=dict(family="IBM Plex Mono, monospace", color="#4a6080", size=10),
    margin=dict(t=36,b=24,l=16,r=16),
    xaxis=dict(gridcolor="#1e2a3a",linecolor="#1e2a3a"),
    yaxis=dict(gridcolor="#1e2a3a",linecolor="#1e2a3a"),
    hoverlabel=dict(bgcolor="#0d1220",font_color="#e2e8f0",bordercolor="#1e2a3a"),
)

def api_ok():
    try: return requests.get(f"{API_URL}/health", timeout=3).status_code == 200
    except: return False

# Sidebar
with st.sidebar:
    st.markdown('<div class="sb-title">NEXUS</div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-ver">MARKET INTELLIGENCE v3.0</div>', unsafe_allow_html=True)
    online = api_ok()
    st.markdown(f'<span class="dot {"on" if online else "off"}"></span><span style="font-family:IBM Plex Mono,monospace;font-size:10px;letter-spacing:1.5px;color:#4a6080">{"API CONNECTED" if online else "API OFFLINE"}</span>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown('<div class="sec-lbl">Search Parameters</div>', unsafe_allow_html=True)
    query = st.text_input("PRODUCT", placeholder="e.g. Sony headphones", label_visibility="collapsed")
    st.caption("Enter product name above")
    c1, c2 = st.columns(2)
    with c1: limit = st.number_input("MAX RESULTS", 10, 100, 20, step=10)
    with c2: min_rating = st.slider("MIN RATING", 0.0, 5.0, 3.5, 0.5)
    go_btn = st.button("SCAN MARKET", use_container_width=True)
    st.markdown("---")
    st.markdown(f'<span style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#4a6080">UTC {datetime.utcnow().strftime("%Y-%m-%d %H:%M")}</span>', unsafe_allow_html=True)

# Main
st.markdown(f'<div class="nxs-header"><span class="nxs-logo">NEXUS INTELLIGENCE</span><span class="nxs-sub">Amazon Market Scanner</span><span class="nxs-time">{datetime.utcnow().strftime("UTC %H:%M:%S")}</span></div>', unsafe_allow_html=True)

if not query:
    st.markdown('<p style="color:#4a6080;font-family:IBM Plex Mono,monospace;font-size:13px">Enter a product name in the sidebar to begin market scan.</p>', unsafe_allow_html=True)
    st.stop()

if not (go_btn or query):
    st.stop()

with st.spinner("Scanning market..."):
    try:
        resp = requests.get(f"{API_URL}/api/products",
            params={"query": query, "limit": limit, "min_rating": min_rating}, timeout=300)

        if resp.status_code != 200:
            st.error(f"API error {resp.status_code}: {resp.text[:200]}")
            st.stop()

        data = resp.json()
        products = data.get("products", [])
        if not products:
            st.warning(f"No products matched query. Try a broader search.")
            st.stop()

        df = pd.DataFrame(products)
        df["price"] = pd.to_numeric(df["price"].astype(str).str.replace(r"[^\d.]","",regex=True), errors="coerce").fillna(0)
        df["rating"] = pd.to_numeric(df["rating"].astype(str).str.extract(r"(\d+\.?\d*)")[0], errors="coerce").fillna(0)
        df["title"] = df["title"].astype(str).str.strip().str.replace(r"\s+"," ",regex=True).str.strip('"\'')
        df = df[df["price"] > 0].reset_index(drop=True)
        if df.empty:
            st.warning("All results had invalid prices. Please try again.")
            st.stop()

        df["value_score"] = (df["rating"] / df["price"] * 10000).round(2)
        p_med = df["price"].median()
        best_i = df["value_score"].idxmax()
        best_short = df.loc[best_i, "title"][:28] + "..."
        source = "CACHED" if data.get("cached") else "LIVE SCAN"

        # KPI row
        st.markdown(f"""
        <div class="kpi-grid">
          <div class="kpi g"><div class="kpi-lbl">Products Found</div><div class="kpi-val">{len(df)}</div><div class="kpi-tag">{source}</div></div>
          <div class="kpi b"><div class="kpi-lbl">Avg Price</div><div class="kpi-val">Rs {df['price'].mean():,.0f}</div><div class="kpi-tag">MEDIAN Rs {p_med:,.0f}</div></div>
          <div class="kpi a"><div class="kpi-lbl">Avg Rating</div><div class="kpi-val">{df['rating'].mean():.2f}</div><div class="kpi-tag">MAX {df['rating'].max():.1f}</div></div>
          <div class="kpi p"><div class="kpi-lbl">Best Value</div><div class="kpi-val sm">{best_short}</div><div class="kpi-tag">SCORE {df.loc[best_i,'value_score']}</div></div>
        </div>""", unsafe_allow_html=True)

        # Charts
        st.markdown('<div class="sec-lbl">Market Analytics</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)

        with c1:
            fig = go.Figure(go.Histogram(x=df["price"], nbinsx=20, marker_color="#3b82f6",
                marker_line_color="#0d1220", marker_line_width=1, opacity=0.9))
            fig.update_layout(**PLOT, title=dict(text="PRICE DISTRIBUTION", font_size=10, font_color="#4a6080", x=0))
            fig.update_xaxes(title_text="Price (Rs)", title_font_size=9)
            fig.update_yaxes(title_text="Count", title_font_size=9)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        with c2:
            fig2 = go.Figure(go.Histogram(x=df["rating"], nbinsx=10, marker_color="#00d4aa",
                marker_line_color="#0d1220", marker_line_width=1, opacity=0.9))
            fig2.update_layout(**PLOT, title=dict(text="RATING DISTRIBUTION", font_size=10, font_color="#4a6080", x=0))
            fig2.update_xaxes(title_text="Rating", title_font_size=9)
            fig2.update_yaxes(title_text="Count", title_font_size=9)
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

        with c3:
            fig3 = go.Figure(go.Scatter(
                x=df["price"], y=df["rating"], mode="markers",
                marker=dict(color=df["value_score"],
                    colorscale=[[0,"#1e2a3a"],[0.5,"#3b82f6"],[1,"#00d4aa"]],
                    size=8, opacity=0.9, line=dict(width=0), showscale=False),
                text=df["title"].str[:50],
                hovertemplate="<b>%{text}</b><br>Rs %{x:,.0f}  Rating %{y}<extra></extra>"))
            fig3.add_vline(x=p_med, line_dash="dot", line_color="#1e2a3a")
            fig3.add_hline(y=df["rating"].median(), line_dash="dot", line_color="#1e2a3a")
            fig3.update_layout(**PLOT, title=dict(text="PRICE vs RATING", font_size=10, font_color="#4a6080", x=0))
            fig3.update_xaxes(title_text="Price (Rs)", title_font_size=9)
            fig3.update_yaxes(title_text="Rating", title_font_size=9)
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

        # Table
        st.markdown('<div class="sec-lbl">Product Listings</div>', unsafe_allow_html=True)
        disp = df[["title","price","rating","value_score"]].copy()
        disp.index += 1
        st.dataframe(disp, use_container_width=True, height=420, column_config={
            "title": st.column_config.TextColumn("PRODUCT", width="large"),
            "price": st.column_config.NumberColumn("PRICE", format="Rs %.0f", width="small"),
            "rating": st.column_config.NumberColumn("RATING", format="%.1f", width="small"),
            "value_score": st.column_config.ProgressColumn("VALUE SCORE", format="%.1f",
                min_value=0, max_value=float(df["value_score"].max()), width="medium"),
        })

        # Export
        col_dl, col_info = st.columns([1,3])
        with col_dl:
            st.download_button("EXPORT CSV", data=df.to_csv(index=False),
                file_name=f"nexus_{query.replace(' ','_')}_{datetime.utcnow().strftime('%Y%m%d')}.csv",
                mime="text/csv")
        with col_info:
            st.markdown(f'<p style="color:#4a6080;font-family:IBM Plex Mono,monospace;font-size:10px;margin-top:8px">Scan completed {datetime.utcnow().strftime("%Y-%m-%d %H:%M")} UTC  |  {len(df)} results for "{query}"</p>', unsafe_allow_html=True)

    except requests.Timeout:
        st.error("Scan timed out. First-run scraping takes approximately 45 seconds. Please retry.")
    except Exception as e:
        st.error(f"Error: {e}")

st.markdown('<p style="color:#1e2a3a;font-family:IBM Plex Mono,monospace;font-size:9px;text-align:center;margin-top:40px;letter-spacing:1px">NEXUS INTELLIGENCE | AMAZON DATA | FOR RESEARCH USE ONLY</p>', unsafe_allow_html=True)