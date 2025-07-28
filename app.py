# app.py
import pandas as pd
from haversine import haversine
import streamlit as st

# ─────────────────────────────────────────────────────────────
# 1.  Cargar la base precalculada con lat/lon
# ─────────────────────────────────────────────────────────────
df = pd.read_csv("centros_unespa_geo.csv")           # ≈ 1 MB
df = df.dropna(subset=["lat", "lon"])                # por si queda algún NaN

# Dejar un solo registro por CPOSTAL (media de lat/lon → <3 km de error)
df_uni = df.groupby("CPOSTAL", as_index=False)[["lat", "lon"]].mean()

# Índice único para búsqueda rápida
nomi_coords = df_uni.set_index("CPOSTAL")

# ─────────────────────────────────────────────────────────────
# 2.  Funciones de negocio
# ─────────────────────────────────────────────────────────────
def lookup_cp(cp: str):
    """
    Devuelve [lat, lon] del CP si existe; si no, None.
    """
    try:
        lat, lon = nomi_coords.loc[cp]
        return [lat, lon]
    except KeyError:
        return None


def nearest_center(patient_cp: str):
    """
    Devuelve (fila_centro, distancia_km) del centro adherido más próximo.
    """
    coords = lookup_cp(patient_cp)
    if coords is None:
        raise ValueError("CP no encontrado en la base UNESPA")

    # Distancia a todos los centros (sin filtrar duplicados; da igual)
    distances = df.apply(
        lambda r: haversine(coords, (r.lat, r.lon)), axis=1
    )
    idx = distances.idxmin()
    return df.loc[idx], distances.loc[idx]


# ─────────────────────────────────────────────────────────────
# 3.  Interfaz Streamlit
# ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="Buscador UNESPA", page_icon="🚑", layout="centered")

st.title("🚑 Buscador UNESPA")
st.markdown(
    "Introduce el **código postal** del paciente y obtén el centro adherido "
    "al convenio UNESPA más cercano."
)

cp_input = st.text_input("Código postal", max_chars=5)

if cp_input:
    cp = cp_input.strip().zfill(5)
    try:
        centro, km = nearest_center(cp)
        st.success(f"**{centro['CENTRO']}**  \nDistancia aproximada: **{km:.1f} km**")
        st.dataframe(
            centro.to_frame().T,
            column_config={
                "CENTRO": st.column_config.Column("Centro"),
                "CPOSTAL": st.column_config.Column("C.P."),
                "POBLACIÓN": st.column_config.Column("Población"),
                "PROVINCIA": st.column_config.Column("Provincia"),
            },
            hide_index=True,
        )
    except ValueError as e:
        st.error(str(e))
