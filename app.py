# app.py
import pandas as pd
from haversine import haversine
import streamlit as st
import re

# ─────────────────────────────────────────────────────────────
# 1.  Cargar y limpiar la base UNESPA
# ─────────────────────────────────────────────────────────────
FILE_CSV = "centros_unespa_geo.csv"   # el fichero que acabas de generar

df = pd.read_csv(FILE_CSV)

# --- Limpieza mínima ---
# • Extraer primer bloque de 5 dígitos (ignora “00nan”, espacios, etc.)
df["CPOSTAL"] = (
    df["CPOSTAL"]
    .astype(str)
    .str.extract(r"(\d{5})")          # solo los 5 primeros dígitos consecutivos
    .fillna("")                       # NaN → ""
)

# • Normalizar lat/lon (a veces están vacíos)
df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
df = df.dropna(subset=["lat", "lon", "CPOSTAL"])       # fuera filas incompletas

# --- Garantizar CPOSTAL único (media de coordenadas si hay varios) ---
df_uni = df.groupby("CPOSTAL", as_index=False)[["lat", "lon"]].mean()
cp_coords = df_uni.set_index("CPOSTAL")                 # para búsquedas rápidas

# ─────────────────────────────────────────────────────────────
# 2.  Lógica de negocio
# ─────────────────────────────────────────────────────────────
def lookup_cp(cp: str):
    """Devuelve [lat, lon] del CP o None si no existe."""
    try:
        lat, lon = cp_coords.loc[cp]
        return [lat, lon]
    except KeyError:
        return None

def nearest_center(patient_cp: str):
    """Devuelve (fila_centro, distancia_km) del centro más próximo."""
    coords = lookup_cp(patient_cp)
    if coords is None:
        raise ValueError("CP no encontrado en la base UNESPA")

    # Distancia a todos los centros con datos válidos
    distances = df.apply(
        lambda r: haversine(coords, (r.lat, r.lon)),
        axis=1,
    )
    idx = distances.idxmin()
    return df.loc[idx], distances.loc[idx]

# ─────────────────────────────────────────────────────────────
# 3.  Interfaz Streamlit
# ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="Buscador UNESPA", page_icon="🚑", layout="centered")
st.title("🚑 Buscador UNESPA")
st.markdown(
    "Introduce el **código postal** del paciente para obtener el centro "
    "adherido al convenio UNESPA más cercano."
)

cp_input = st.text_input("Código postal", max_chars=5, placeholder="28042")

if cp_input:
    cp = re.sub(r"\D", "", cp_input)[:5].zfill(5)   # limpia y formatea a 5 dígitos
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
