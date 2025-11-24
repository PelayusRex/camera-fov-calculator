import streamlit as st
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Calculadora Interceptor", layout="wide")

# Gestión de memoria para guardar cámaras
if 'camaras_db' not in st.session_state:
    st.session_state['camaras_db'] = {
        "Arducam IMX519 (Stock)": {"w": 5.6, "h": 4.2, "f": 4.28, "r": 4656},
        "RPi HQ (Lente 6mm)":     {"w": 6.17, "h": 4.55, "f": 6.0, "r": 4056},
        "GoPro Hero (Wide)":      {"w": 6.17, "h": 4.55, "f": 2.5, "r": 4000},
    }

# --- BARRA LATERAL ---
st.sidebar.header("1. Configuración de Cámara")
nombre_camara = st.sidebar.selectbox("Cargar Preset", list(st.session_state['camaras_db'].keys()))
datos_cam = st.session_state['camaras_db'][nombre_camara]

c1, c2 = st.sidebar.columns(2)
with c1:
    sensor_w = st.number_input("Ancho (mm)", value=float(datos_cam['w']), format="%.2f")
    focal = st.number_input("Focal (mm)", value=float(datos_cam['f']), format="%.2f")
with c2:
    sensor_h = st.number_input("Alto (mm)", value=float(datos_cam['h']), format="%.2f")
    res_px = st.number_input("Resolución (px)", value=int(datos_cam['r']))

# Guardar nueva cámara
with st.sidebar.expander("💾 Guardar Preset Nuevo"):
    new_name = st.text_input("Nombre Modelo")
    if st.button("Guardar"):
        if new_name:
            st.session_state['camaras_db'][new_name] = {"w": sensor_w, "h": sensor_h, "f": focal, "r": res_px}
            st.rerun()

st.sidebar.header("2. Escenario de Vuelo")
pitch = st.sidebar.slider("Pitch (Inclinación) [º]", 0, 60, 30)
dist = st.sidebar.slider("Distancia [m]", 5, 200, 50)
altura_rel = st.sidebar.slider("Altura Relativa [m]", -50, 50, 0)
obj_size = st.sidebar.number_input("Tamaño Objetivo (m)", value=0.3)

# --- CÁLCULOS ---
hfov = 2 * math.degrees(math.atan(sensor_w / (2 * focal)))
vfov = 2 * math.degrees(math.atan(sensor_h / (2 * focal)))

ang_obj_rad = math.atan2(altura_rel, dist)
ang_obj_deg = math.degrees(ang_obj_rad)
techo_visual = -pitch + (vfov / 2)
suelo_visual = -pitch - (vfov / 2)
visible = suelo_visual <= ang_obj_deg <= techo_visual

dist_real = math.sqrt(dist**2 + altura_rel**2)
px_target = (res_px * obj_size * focal) / (sensor_w * dist_real)

# --- INTERFAZ PRINCIPAL ---

st.title(f"🚁 Análisis: {nombre_camara}")

# Métricas Claras
m1, m2, m3, m4 = st.columns(4)
m1.metric("FOV Vertical", f"{vfov:.1f}º")
m2.metric("Ángulo Objetivo", f"{ang_obj_deg:.1f}º")
m3.metric("Límite Superior", f"{techo_visual:.1f}º")
m4.metric("Píxeles Objetivo", f"{px_target:.1f} px", delta="OK" if px_target > 15 else "Bajo")

# Mensaje de estado
if not visible:
    st.error(f"🚨 **OBJETIVO PERDIDO**: El enemigo está fuera del ángulo de visión.")
else:
    st.success(f"✅ **OBJETIVO VISIBLE**")

st.divider()

# --- GRÁFICO CONTROLADO ---
# 1. Definimos un tamaño fijo más ancho que alto (10x4 pulgadas)
fig, ax = plt.subplots(figsize=(10, 4)) 

# Dron y Objetivo
ax.plot(0, 0, 'ko', markersize=8, label="Interceptor")
ax.plot(dist, altura_rel, 'r*', markersize=15, label="Objetivo")

# Cono
radio = dist_real * 1.2
ang_t, ang_b = math.radians(techo_visual), math.radians(suelo_visual)
xt, yt = radio * math.cos(ang_t), radio * math.sin(ang_t)
xb, yb = radio * math.cos(ang_b), radio * math.sin(ang_b)

poly = patches.Polygon([[0,0], [xt, yt], [xb, yb]], closed=True, color='green' if visible else 'red', alpha=0.2)
ax.add_patch(poly)
ax.plot([0, xt], [0, yt], 'g--' if visible else 'r--', alpha=0.5)
ax.plot([0, xb], [0, yb], 'g--' if visible else 'r--', alpha=0.5)

# Decoración
ax.grid(True, alpha=0.3)
ax.set_xlabel("Distancia (m)")
ax.set_ylabel("Altura (m)")
ax.set_title(f"Vista Lateral (Pitch: {pitch}º)")

# Límites automáticos pero con margen
max_val = max(abs(altura_rel), abs(yt), abs(yb), 10) * 1.2
ax.set_ylim(-max_val, max_val)
ax.set_xlim(-5, radio)
ax.set_aspect('equal')

# AQUÍ ESTÁ LA CLAVE DEL TAMAÑO:
# use_container_width=False -> No estira el gráfico al ancho total de la pantalla.
# Se quedará del tamaño que definimos en figsize (10x4).
col_centrada, _ = st.columns([3, 1]) # Truco para centrarlo un poco pero sin llenar todo
with col_centrada:
    st.pyplot(fig, use_container_width=False)
