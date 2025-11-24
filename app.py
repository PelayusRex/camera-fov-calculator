import streamlit as st
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# --- 1. CONFIGURACIÓN ---
st.set_page_config(
    page_title="Calculadora Interceptor Compacta", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Estilo CSS para ajustar márgenes y que se vea más compacto
st.markdown("""
    <style>
        .block-container {padding-top: 1rem; padding-bottom: 0rem;}
        h1 {margin-bottom: 0rem;}
    </style>
""", unsafe_allow_html=True)

# --- 2. GESTIÓN DE MEMORIA ---
if 'camaras_db' not in st.session_state:
    st.session_state['camaras_db'] = {
        "Arducam IMX519 (Stock)": {"w": 5.6, "h": 4.2, "f": 4.28, "r": 4656},
        "RPi HQ (Lente 6mm)":     {"w": 6.17, "h": 4.55, "f": 6.0, "r": 4056},
        "GoPro Hero (Wide)":      {"w": 6.17, "h": 4.55, "f": 2.5, "r": 4000},
        "Fisheye Genérica (1.8mm)":{"w": 5.6, "h": 4.2, "f": 1.8, "r": 2000}
    }

# --- 3. BARRA LATERAL ---
with st.sidebar:
    st.title("🚁 Configuración")
    
    # Selector de Cámara
    st.subheader("📷 Cámara")
    nombre_camara = st.selectbox("Preset", list(st.session_state['camaras_db'].keys()))
    datos_cam = st.session_state['camaras_db'][nombre_camara]
    
    # Edición compacta (Columns dentro del sidebar)
    c1, c2 = st.columns(2)
    with c1:
        sensor_w = st.number_input("Ancho (mm)", value=float(datos_cam['w']), format="%.2f")
        focal = st.number_input("Focal (mm)", value=float(datos_cam['f']), format="%.2f")
    with c2:
        sensor_h = st.number_input("Alto (mm)", value=float(datos_cam['h']), format="%.2f")
        res_px = st.number_input("Resolución", value=int(datos_cam['r']))

    # Guardar nueva
    with st.expander("💾 Guardar Nueva"):
        new_name = st.text_input("Nombre")
        if st.button("Guardar"):
            if new_name:
                st.session_state['camaras_db'][new_name] = {"w": sensor_w, "h": sensor_h, "f": focal, "r": res_px}
                st.rerun()

    st.markdown("---")
    
    # Vuelo
    st.subheader("✈️ Vuelo")
    pitch = st.slider("Pitch [º]", 0, 60, 30)
    dist = st.slider("Distancia [m]", 5, 200, 50)
    altura_rel = st.slider("Altura Rel. [m]", -50, 50, 0)
    obj_size = st.number_input("Tamaño Objetivo (m)", value=0.3)

# --- 4. CÁLCULOS ---
hfov = 2 * math.degrees(math.atan(sensor_w / (2 * focal)))
vfov = 2 * math.degrees(math.atan(sensor_h / (2 * focal)))

ang_obj_rad = math.atan2(altura_rel, dist)
ang_obj_deg = math.degrees(ang_obj_rad)
techo_visual = -pitch + (vfov / 2)
suelo_visual = -pitch - (vfov / 2)
visible = suelo_visual <= ang_obj_deg <= techo_visual

dist_real = math.sqrt(dist**2 + altura_rel**2)
px_target = (res_px * obj_size * focal) / (sensor_w * dist_real)

# --- 5. INTERFAZ PRINCIPAL (LAYOUT 2 COLUMNAS) ---

st.subheader("Análisis de Interceptación")

# CREAMOS DOS COLUMNAS: Izquierda (Datos) - Derecha (Gráfico)
# [1, 3] significa que la columna derecha es 3 veces más ancha que la izquierda
col_datos, col_grafico = st.columns([1, 3]) 

# --- COLUMNA IZQUIERDA: LOS DATOS ---
with col_datos:
    st.markdown("### 📊 Datos")
    
    # Usamos un container para agrupar visualmente
    with st.container(border=True):
        st.metric("FOV Vertical", f"{vfov:.1f}º")
        st.metric("Ángulo Objetivo", f"{ang_obj_deg:.1f}º")
        st.divider()
        st.metric("Píxeles Objetivo", f"{px_target:.1f} px", 
                 delta="Visible" if px_target > 15 else "Borroso",
                 delta_color="normal" if px_target > 15 else "inverse")
    
    # Alerta visual compacta
    if visible:
        st.success("✅ **VISIBLE**")
    else:
        st.error("🚨 **PERDIDO**")
        if ang_obj_deg > techo_visual:
            st.caption(f"El objetivo está {ang_obj_deg - techo_visual:.1f}º por encima de tu cámara.")

# --- COLUMNA DERECHA: EL GRÁFICO ---
with col_grafico:
    # Ajustamos figsize para que sea "Panorámico" (10 de ancho, 4.5 de alto)
    # Esto evita que se coma toda la altura de la pantalla
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 4.5)) 
    fig.patch.set_facecolor('#0E1117')
    ax.set_facecolor('#0E1117')

    # Dron
    ax.plot(0, 0, marker='o', color='white', markersize=8)

    # Cono FOV
    radio = dist_real * 1.15
    ang_t, ang_b = math.radians(techo_visual), math.radians(suelo_visual)
    xt, yt = radio * math.cos(ang_t), radio * math.sin(ang_t)
    xb, yb = radio * math.cos(ang_b), radio * math.sin(ang_b)

    poly = patches.Polygon([[0,0], [xt, yt], [xb, yb]], 
                           closed=True, color='#00FF00' if visible else '#FF4B4B', alpha=0.2)
    ax.add_patch(poly)
    ax.plot([0, xt], [0, yt], color='white', linestyle='--', alpha=0.5, linewidth=0.8)
    ax.plot([0, xb], [0, yb], color='white', linestyle='--', alpha=0.5, linewidth=0.8)

    # Objetivo
    ax.plot(dist, altura_rel, marker='*', color='#00FFFF', markersize=15)
    ax.plot([0, dist], [0, altura_rel], color='white', linestyle=':', alpha=0.2)

    # Decoración
    ax.grid(True, color='gray', linestyle=':', alpha=0.2)
    ax.set_xlabel("Distancia (m)", color='gray', fontsize=8)
    ax.set_ylabel("Altura (m)", color='gray', fontsize=8)
    
    # Limpiar bordes
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('gray')
    ax.spines['left'].set_color('gray')
    ax.tick_params(colors='gray', labelsize=8)

    # Zoom inteligente
    max_y = max(abs(altura_rel), abs(yt), abs(yb)) * 1.2
    ax.set_ylim(-max_y, max_y)
    ax.set_xlim(-2, radio)
    ax.set_aspect('equal') # Mantiene la proporción real para no engañar al ojo

    st.pyplot(fig, use_container_width=True)
