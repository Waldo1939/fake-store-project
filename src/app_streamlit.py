import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from pathlib import Path
import numpy as np
import altair as alt

# -------------------------
# Helpers
# -------------------------
def make_sparkline(df_spark, color="#1f77b4", height=60, stroke_width=1.5):
    # Devuelve un chart Altair o None si df vacío
    if df_spark.empty:
        return None
    chart = (
        alt.Chart(df_spark)
        .mark_line(interpolate='monotone', point=False, strokeWidth=stroke_width)
        .encode(
            x=alt.X("x:Q", axis=None),
            y=alt.Y("y:Q", axis=None),
            color=alt.value(color)
        )
        .properties(height=height)
        .configure_view(stroke=None)
    )
    return chart

# -------------------------
# Load data
# -------------------------
DB = Path("data") / "fake_store.db"

@st.cache_data
def load_data():
    engine = create_engine(f"sqlite:///{DB}")
    return pd.read_sql("select * from products", engine)

st.title("Fake Store — Product Insights")

if not DB.exists():
    st.warning(
        "No se encontró la DB. Corre primero: python -m src.extract ; python -m src.transform ; python -m src.load"
    )
    st.stop()  # corta la ejecución si no hay DB

# Cargar dataframe (cacheado)
df = load_data()

# -------------------------
# Sidebar filters (necesitan df)
# -------------------------
st.sidebar.title("Filtros")

# 1) Categoría (multiselect)
all_categories = sorted(df['category_name'].dropna().unique().tolist())
selected_categories = st.sidebar.multiselect(
    "Categoría", options=all_categories, default=all_categories
)

# 2) Rango de precios (slider)
min_price = float(df['price'].min())
max_price = float(df['price'].max())
price_range = st.sidebar.slider(
    "Rango de precio", min_value=min_price, max_value=max_price, value=(min_price, max_price)
)

# 3) Buscador por texto (input)
search_text = st.sidebar.text_input("Buscar producto (por título)")

# -------------------------
# Aplicar filtros al DataFrame
# -------------------------
min_sel, max_sel = price_range  # price_range viene del slider

# 1) filtro por categoría
if selected_categories:
    cond_cat = df['category_name'].isin(selected_categories)
else:
    cond_cat = pd.Series([True] * len(df), index=df.index)

# 2) filtro por rango de precio
cond_price = df['price'].between(min_sel, max_sel)

# 3) filtro por búsqueda de texto (partial match, case-insensitive)
if search_text and search_text.strip() != "":
    cond_text = df['title'].str.contains(search_text, case=False, na=False)
else:
    cond_text = pd.Series([True] * len(df), index=df.index)

# 4) combinar condiciones
filtered_df = df[cond_cat & cond_price & cond_text].copy()

# -------------------------
# Header + KPIs (ahora que tenemos filtered_df)
# -------------------------
st.header("Visión general filtrada")

# Métricas clave
n_products = len(filtered_df)
avg_price = filtered_df['price'].mean() if n_products else 0
median_price = filtered_df['price'].median() if n_products else 0

# IQR outliers
if n_products:
    Q1 = filtered_df['price'].quantile(0.25)
    Q3 = filtered_df['price'].quantile(0.75)
    IQR = Q3 - Q1
    outliers_mask = (filtered_df['price'] < Q1 - 1.5 * IQR) | (filtered_df['price'] > Q3 + 1.5 * IQR)
    pct_outliers = outliers_mask.sum() / n_products * 100
else:
    pct_outliers = 0

# -------------------------
# Preparar datos para sparklines
# -------------------------
n_points = 40  # cuántos puntos queremos en cada sparkline

# Sparkline 1 & 2 (prices ordered) - para Avg y Median visual
prices_sorted = filtered_df['price'].sort_values().reset_index(drop=True)
if len(prices_sorted) == 0:
    spark_prices = np.array([])
else:
    if len(prices_sorted) <= n_points:
        spark_prices = prices_sorted.values
    else:
        idxs = np.linspace(0, len(prices_sorted) - 1, n_points).astype(int)
        spark_prices = prices_sorted.iloc[idxs].values

# Sparkline 3 (histogram normalized) - para forma / outliers
if len(filtered_df) == 0:
    spark_hist = np.array([])
    bin_centers = np.array([])
else:
    min_p = float(filtered_df['price'].min())
    max_p = float(filtered_df['price'].max())
    hist_counts, bin_edges = np.histogram(filtered_df['price'], bins=20, range=(min_p, max_p))
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    if hist_counts.max() > 0:
        spark_hist = hist_counts / hist_counts.max()
    else:
        spark_hist = hist_counts

# DataFrame para spark_prices (x: índice, y: price)
if spark_prices.size > 0:
    df_spark_prices = pd.DataFrame({"x": np.arange(len(spark_prices)), "y": spark_prices})
else:
    df_spark_prices = pd.DataFrame({"x": [], "y": []})

# DataFrame para spark_hist (x: bin center, y: normalized count)
if len(bin_centers) == 0:
    df_spark_hist = pd.DataFrame({"x": [], "y": []})
else:
    df_spark_hist = pd.DataFrame({"x": bin_centers, "y": spark_hist})

# -------------------------
# Mostrar KPIs + Sparklines (4 columnas)
# -------------------------
cols = st.columns(4)

# Col 0: Total Productos
with cols[0]:
    st.metric("Productos", n_products)
    chart0 = make_sparkline(df_spark_prices, color="#1f77b4")
    if chart0:
        st.altair_chart(chart0, use_container_width=True)

# Col 1: Precio promedio
with cols[1]:
    st.metric("Precio promedio", f"${avg_price:.2f}" if n_products else "—")
    chart1 = make_sparkline(df_spark_prices, color="#2ca02c")
    if chart1:
        st.altair_chart(chart1, use_container_width=True)

# Col 2: Precio mediano
with cols[2]:
    st.metric("Mediana", f"${median_price:.2f}" if n_products else "—")
    chart2 = make_sparkline(df_spark_prices, color="#ff7f0e")
    if chart2:
        st.altair_chart(chart2, use_container_width=True)

# Col 3: % Outliers (usa histograma normalizado)
with cols[3]:
    st.metric("% Outliers", f"{pct_outliers:.1f}%" if n_products else "—")
    chart3 = make_sparkline(df_spark_hist, color="#d62728")
    if chart3:
        st.altair_chart(chart3, use_container_width=True)

# -------------------------
# Resultados: tabla y gráfico principal
# -------------------------
st.subheader("Resultados (primera vista)")
st.dataframe(filtered_df.reset_index(drop=True).head(50))

st.subheader("Precio promedio por categoría")
st.bar_chart(filtered_df.groupby("category_name")["price"].mean())
