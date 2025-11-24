import streamlit as st
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Calculadora Interceptor", layout="wide")

st.title("🚁 Calculadora de Óptica: Dron Interceptor")
st.markdown("Herramienta para validar si la cámara perderá el objetivo por el ángulo de ataque (Pitch).")

# --- BARRA LATERAL ---
st.sidebar.header("1. Configuración Cámara")
cam_option = st.sidebar.selectbox("Preset de Cámara", 
    ["Arducam IMX519 (Actual)", "RPi HQ (Wide)", "GoPro Hero", "Personalizada"])

# Valores por defecto según selección
if cam_option == "Arducam IMX519 (Actual)":
    w_def, h_def, f_def, res_def = 5.6, 4.2, 4.28, 4656
elif cam_option == "RPi HQ (Wide)":
    w_def, h_def, f_def, res_def = 6.17, 4.55, 6.0, 4056
elif cam_option == "GoPro Hero":
    w_def, h_def, f_def, res_def = 6.17, 4.55, 2.5, 4000
else:
    w_def, h_def, f_def, res_def = 5.0, 4.0, 4.0, 3000

# Inputs manuales
sensor_w = st.sidebar.number_input("Ancho Sensor (mm)", value=w_def, format="%.2f")
sensor_h = st.sidebar.number_input("Alto Sensor (mm)", value=h_def, format="%.2f")
focal = st.sidebar.number_input("Focal (mm)", value=f_def, format="%.2f")
res_px = st.sidebar.number_input("Resolución Horizontal (px)", value=res_def)

st.sidebar.header("2. Vuelo")
pitch = st.sidebar.slider("Inclinación (Pitch) [º]", 0, 60, 30)
dist = st.sidebar.slider("Distancia Objetivo (m)", 1, 100, 50)
obj_size = st.sidebar.number_input("Tamaño Objetivo (m)", value=0.3)

# --- CÁLCULOS ---
hfov = 2 * math.degrees(math.atan(sensor_w / (2 * focal)))
vfov = 2 * math.degrees(math.atan(sensor_h / (2 * focal)))

# Ángulo límite superior visible (desde el horizonte)
# Si el dron se inclina PITCH grados hacia abajo, el "techo" de la cámara baja PITCH grados.
# Techo visual relativo = (VFOV / 2) - Pitch
margen_superior = (vfov / 2) - pitch

px_on_target = (res_px * obj_size * focal) / (sensor_w * dist)

# --- MOSTRAR RESULTADOS ---
col1, col2, col3 = st.columns(3)
col1.metric("FOV Horizontal", f"{hfov:.1f}º")
col2.metric("FOV Vertical", f"{vfov:.1f}º")
col3.metric("Píxeles en Objetivo", f"{px_on_target:.1f} px", 
            delta="Detectado" if px_on_target > 15 else "Invisible",
            delta_color="normal" if px_on_target > 15 else "inverse")

st.divider()

# --- GRÁFICO ---
st.subheader(f"Simulación Visual: Pitch -{pitch}º")

if margen_superior < 0:
    st.error(f"⚠️ **PÉRDIDA DE OBJETIVO:** Estás mirando al suelo. El objetivo está {abs(margen_superior):.1f}º por encima de tu cámara.")
else:
    st.success(f"✅ **OBJETIVO VISIBLE:** Tienes {margen_superior:.1f}º de margen superior.")

# Matplotlib
fig, ax = plt.subplots(figsize=(10, 4))

# Dron en (0,0)
ax.plot(0, 0, 'ko', label="Dron")

# Cono de visión
# El centro de la cámara apunta hacia abajo (-pitch)
angulo_centro = math.radians(-pitch)
angulo_mitad_fov = math.radians(vfov / 2)

angulo_arriba = angulo_centro + angulo_mitad_fov
angulo_abajo = angulo_centro - angulo_mitad_fov

r = dist + 10 # Largo de las lineas
x_up, y_up = r * math.cos(angulo_arriba), r * math.sin(angulo_arriba)
x_dw, y_dw = r * math.cos(angulo_abajo), r * math.sin(angulo_abajo)

# Zona visible (Triángulo)
poly = patches.Polygon([[0,0], [x_up, y_up], [x_dw, y_dw]], 
                       closed=True, color='green' if margen_superior >= 0 else 'red', alpha=0.3)
ax.add_patch(poly)

# Objetivo (asumimos que está recto a la misma altura, y=0)
ax.plot(dist, 0, 'b*', markersize=15, label="Objetivo")
ax.hlines(0, 0, r, colors='gray', linestyles='--')

ax.set_xlim(-5, r)
ax.set_ylim(-r/2, r/2)
ax.set_aspect('equal')
ax.legend()
ax.grid(True, alpha=0.3)

st.pyplot(fig)
