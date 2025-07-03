import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from pathlib import Path

# ─── 1. Load data safely ────────────────────────────────────────────────────────
BASE    = Path(__file__).parent
DATA_FP = BASE / "data" / "processed" / "monthly_gen_clean.csv"

if not DATA_FP.exists():
    st.error(f"Data file not found: {DATA_FP}")
    st.stop()

df = pd.read_csv(DATA_FP, parse_dates=["date"])

# keep rows that actually have a date
df = df.dropna(subset=["date"]).copy()
if df.empty:
    st.error("Monthly data is empty. Check your cleaning step.")
    st.stop()

# convert to pure Python dates
df["date"] = df["date"].dt.date

# ─── 2. Streamlit page setup ────────────────────────────────────────────────────
st.set_page_config(page_title="US Energy Stability", page_icon="⚡", layout="wide")
st.title("US Electricity Generation & Stability")
st.markdown("Explore how the U.S. electricity mix has evolved over time…")

# ─── 3. Sidebar controls ────────────────────────────────────────────────────────
min_date = df["date"].min() or date.today()
max_date = df["date"].max() or date.today()

with st.sidebar.expander("Settings", expanded=False):
    sources = st.multiselect(
        "Sources to include",
        options=df["source"].unique(),
        default=list(df["source"].unique())
    )
    date_range = st.date_input(
        "Date range",
        value=(min_date, max_date),   # must be tuple of python dates
        min_value=min_date,
        max_value=max_date
    )

# filter dataframe
df = df[
    (df["source"].isin(sources)) &
    (df["date"] >= date_range[0]) &
    (df["date"] <= date_range[1])
]

if df.empty:
    st.warning("No data for the selected filters.")
    st.stop()

# ─── 4. Stacked-area chart ──────────────────────────────────────────────────────
fig_area = px.area(
    df,
    x="date",
    y="TWh",
    color="source",
    labels={"TWh": "Generation (TWh)", "date": "Date", "source": "Source"},
    title="Monthly Generation by Source"
)
st.plotly_chart(fig_area, use_container_width=True)

# ─── 5. Renewables share line chart ─────────────────────────────────────────────
renew = (
    df[df["source"].isin(["Wind", "Solar", "Hydro"])]
      .groupby("date", as_index=False)["share"]
      .sum()
)

fig_line = px.line(
    renew, x="date", y="share",
    labels={"share": "Renewables Share", "date": "Date"},
    title="Share of Renewables Over Time"
)
fig_line.update_yaxes(tickformat="0%")
st.plotly_chart(fig_line, use_container_width=True)

# ─── 6. Footer ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("Built with **Python · Streamlit · Plotly**")
