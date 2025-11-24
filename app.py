import streamlit as st
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Calculadora Interceptor v2", layout="wide")

st.title("🚁 Calculadora Óptica 3D: Dron Interceptor")
st.markdown("Simulación de visibilidad considerando Pitch del dron y diferencia de altura con el objetivo.")

# --- BARRA LATERAL (INPUTS) ---
st.sidebar.header("1. Cámara y Sensor")
cam_option = st.sidebar.selectbox("Modelo de Cámara", 
    ["Arducam IMX519 (Actual)", "RPi HQ (Wide)", "GoPro Hero", "Personalizada"])

if cam_option == "Arducam IMX519 (Actual)":
    w_def, h_def, f_def, res_def = 5.6, 4.2, 4.28, 4656
elif cam_option == "RPi HQ (Wide)":
    w_def, h_def, f_def, res_def = 6.17, 4.55, 6.0, 4056
elif cam_option == "GoPro Hero":
    w_def, h_def, f_def, res_def = 6.17, 4.55, 2.5, 4000
else:
    w_def, h_def, f_def, res_def = 5.0, 4.0, 4.0, 3000

c1, c2 = st.sidebar.columns(2)
with c1:
    sensor_w = st.number_input("Ancho Sensor (mm)", value=w_def, format="%.2f")
    focal = st.number_input("Focal (mm)", value=f_def, format="%.2f")
with c2:
    sensor_h = st.number_input("Alto Sensor (mm)", value=h_def, format="%.2f")
    res_px = st.number_input("Resolución (px)", value=res_def)

st.sidebar.header("2. Geometría del Encuentro")
# Rango ampliado para distancias largas
dist = st.sidebar.slider("Distancia Horizontal (m)", 5, 200, 50)
# Nuevo slider de altura relativa (negativo = abajo, positivo = arriba)
altura_rel = st.sidebar.slider("Altura Relativa Objetivo (m)", -50, 50, 0, help="Positivo: Enemigo por encima de ti. Negativo: Por debajo.")

st.sidebar.header("3. Actitud del Dron")
pitch = st.sidebar.slider("Pitch de Ataque (Nariz Abajo) [º]", 0, 60, 30)
obj_size = st.sidebar.number_input("Tamaño Objetivo (m)", value=0.3)

# --- CÁLCULOS MATEMÁTICOS ---

# 1. FOVs de la cámara
hfov = 2 * math.degrees(math.atan(sensor_w / (2 * focal)))
vfov = 2 * math.degrees(math.atan(sensor_h / (2 * focal)))

# 2. Ángulo geométrico hacia el objetivo (Elevación necesaria para mirarlo)
# atan(Cateto Opuesto / Cateto Adyacente)
angulo_a_objetivo_rad = math.atan2(altura_rel, dist)
angulo_a_objetivo_deg = math.degrees(angulo_a_objetivo_rad)

# 3. Límites de visión de la cámara (Considerando que el dron mira hacia abajo 'pitch' grados)
# El centro de la cámara está en -pitch.
techo_visual_absoluto = -pitch + (vfov / 2)
suelo_visual_absoluto = -pitch - (vfov / 2)

# 4. ¿Está dentro del cono?
visible = suelo_visual_absoluto <= angulo_a_objetivo_deg <= techo_visual_absoluto

# 5. Resolución (Hipotenusa real, no solo distancia X)
distancia_real = math.sqrt(dist**2 + altura_rel**2)
px_on_target = (res_px * obj_size * focal) / (sensor_w * distancia_real)

# --- MOSTRAR MÉTRICAS ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("FOV Vertical", f"{vfov:.1f}º")
m2.metric("Ángulo al Objetivo", f"{angulo_a_objetivo_deg:.1f}º", help="Ángulo real geométrico hacia el enemigo")
m3.metric("Techo de Visión", f"{techo_visual_absoluto:.1f}º", help="Máximo ángulo hacia arriba que ve la cámara")
m4.metric("Píxeles en Objetivo", f"{px_on_target:.1f} px", delta_color="normal" if px_on_target > 15 else "inverse")

st.divider()

# --- VISUALIZACIÓN GRÁFICA ---
st.subheader(f"Simulación de Interceptación")

if visible:
    # Calculamos cuánto margen nos sobra
    margen = techo_visual_absoluto - angulo_a_objetivo_deg
    st.success(f"✅ **OBJETIVO VISIBLE** | Margen de seguridad superior: {margen:.1f}º")
else:
    if angulo_a_objetivo_deg > techo_visual_absoluto:
        st.error(f"🚨 **PÉRDIDA SUPERIOR:** El objetivo está demasiado ALTO ({angulo_a_objetivo_deg:.1f}º) para tu inclinación actual.")
    else:
        st.error(f"🚨 **PÉRDIDA INFERIOR:** El objetivo está demasiado BAJO.")

# Configuración del Plot
fig, ax = plt.subplots(figsize=(12, 6))

# 1. Dron en (0,0)
ax.plot(0, 0, 'ko', markersize=8, label="Interceptor")

# 2. Cono de visión
# Calculamos vectores para dibujar el triángulo
radio_vis = distancia_real + 10 # Hacemos el cono un poco más largo que el objetivo
ang_top_rad = math.radians(techo_visual_absoluto)
ang_bot_rad = math.radians(suelo_visual_absoluto)

x_top, y_top = radio_vis * math.cos(ang_top_rad), radio_vis * math.sin(ang_top_rad)
x_bot, y_bot = radio_vis * math.cos(ang_bot_rad), radio_vis * math.sin(ang_bot_rad)

# Dibujar zona visible
color_cono = 'green' if visible else 'red'
poly = patches.Polygon([[0,0], [x_top, y_top], [x_bot, y_bot]], 
                       closed=True, color=color_cono, alpha=0.2, label="FOV Cámara")
ax.add_patch(poly)
ax.plot([0, x_top], [0, y_top], color=color_cono, linestyle='--')
ax.plot([0, x_bot], [0, y_bot], color=color_cono, linestyle='--')

# 3. Objetivo
ax.plot(dist, altura_rel, marker='*', color='blue', markersize=18, label="Objetivo")
# Línea de visión ideal
ax.plot([0, dist], [0, altura_rel], color='blue', linestyle=':', alpha=0.5)

# 4. Referencias
ax.hlines(0, -10, dist+20, colors='gray', linestyles='-', alpha=0.3, label="Nivel 0m")
ax.axvline(0, color='gray', linestyle='-', alpha=0.1)

# Estética
ax.set_xlabel("Distancia Horizontal (m)")
ax.set_ylabel("Altura Relativa (m)")
ax.set_title(f"Vista Lateral (Side View) - Pitch: {pitch}º")
ax.legend(loc='upper left')
ax.grid(True, alpha=0.3)
ax.set_aspect('equal') # Importante para no deformar ángulos visualmente

# Ajustar límites dinámicamente
max_y = max(abs(altura_rel), abs(y_top), abs(y_bot)) + 5
ax.set_ylim(-max_y, max_y)
ax.set_xlim(-5, dist + 15)

st.pyplot(fig)
