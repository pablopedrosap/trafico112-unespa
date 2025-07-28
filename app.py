import pandas as pd
from haversine import haversine
import streamlit as st

# -------- datos precalculados --------
df = pd.read_csv("centros_unespa_geo.csv")

nomi_coords = df[["CPOSTAL", "lat", "lon"]].dropna().set_index("CPOSTAL")

def lookup_cp(cp):
    if cp not in nomi_coords.index:
        return None
    return nomi_coords.loc[cp, ["lat", "lon"]].to_list()

def nearest_center(patient_cp):
    coords = lookup_cp(patient_cp)
    if coords is None:
        raise ValueError("CP no encontrado en la base UNESPA")

    distances = df.dropna(subset=["lat", "lon"]).apply(
        lambda r: haversine(coords, (r.lat, r.lon)), axis=1
    )
    idx = distances.idxmin()
    return df.loc[idx], distances.loc[idx]

# -------- interfaz --------
st.title("Buscador UNESPA")
cp_input = st.text_input("Código postal del paciente", max_chars=5)

if cp_input:
    cp = cp_input.strip().zfill(5)
    try:
        centro, km = nearest_center(cp)
        st.success(f"{centro['CENTRO']} — {km:.1f} km")
        st.dataframe(centro.to_frame().T)
    except ValueError as e:
        st.error(str(e))
