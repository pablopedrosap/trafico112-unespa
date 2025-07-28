import pandas as pd
from haversine import haversine
import streamlit as st
import pgeocode
import re

# ── 1. Cargar lista de centros ──────────────────────────────────────────────
df = pd.read_csv("centros_unespa_geo.csv")
df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
df = df.dropna(subset=["lat", "lon"])                # centros con coordenadas

# ── 2. Geocodificador offline para CP de pacientes ──────────────────────────
nomi = pgeocode.Nominatim("es")                      # base GeoNames local

def geocode_cp(cp: str):
    """Devuelve (lat, lon) o None si el CP no existe en GeoNames."""
    q = nomi.query_postal_code(cp)
    if pd.isna(q.latitude):
        return None
    return float(q.latitude), float(q.longitude)

# ── 3. Lógica de búsqueda ───────────────────────────────────────────────────
def nearest_center(patient_cp: str):
    coords = geocode_cp(patient_cp)
    if coords is None:
        raise ValueError("CP no reconocido en GeoNames")

    distances = df.apply(
        lambda r: haversine(coords, (r.lat, r.lon)),
        axis=1,
    )
    idx = distances.idxmin()
    return df.loc[idx], distances.loc[idx]

# ── 4. UI Streamlit ─────────────────────────────────────────────────────────
st.set_page_config(page_title="Buscador UNESPA", page_icon="🚑", layout="centered")
st.title("🚑 Buscador UNESPA")
st.markdown(
    "Introduce el **código postal** del paciente para ver el centro UNESPA más cercano."
)

cp_input = st.text_input("Código postal", max_chars=5, placeholder="28042")

if cp_input:
    cp = re.sub(r"\D", "", cp_input)[:5].zfill(5)
    try:
        centro, km = nearest_center(cp)
        st.success(f"**{centro['CENTRO']}** — {km:.1f} km")
        st.dataframe(
            centro.to_frame().T,
            hide_index=True,
            column_config={
                "CENTRO": "Centro",
                "CPOSTAL": "C.P.",
                "POBLACIÓN": "Población",
                "PROVINCIA": "Provincia",
                "COMUNIDAD AUTÓNOMA": "C. Autónoma",
                "TELEFONO": "Teléfono",
            },
        )
    except ValueError as e:
        st.error(str(e))
