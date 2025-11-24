import streamlit as st
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# --- 1. CONFIGURACIÓN DE PÁGINA (WIDE MODE) ---
st.set_page_config(
    page_title="Calculadora Interceptor Pro", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- 2. GESTIÓN DE MEMORIA (SESSION STATE) ---
# Aquí guardamos las cámaras para que no se borren
if 'camaras_db' not in st.session_state:
    st.session_state['camaras_db'] = {
        "Arducam IMX519 (Stock)": {"w": 5.6, "h": 4.2, "f": 4.28, "r": 4656},
        "RPi HQ (Lente 6mm)":     {"w": 6.17, "h": 4.55, "f": 6.0, "r": 4056},
        "GoPro Hero (Wide)":      {"w": 6.17, "h": 4.55, "f": 2.5, "r": 4000},
        "Fisheye Genérica (1.8mm)":{"w": 5.6, "h": 4.2, "f": 1.8, "r": 2000}
    }

st.title("🚁 Calculadora Óptica: Dron Interceptor (v3.0)")
st.markdown("---")

# --- 3. BARRA LATERAL: GESTIÓN DE CÁMARAS ---
with st.sidebar:
    st.header("📷 Selección de Cámara")
    
    # Selector de cámara basado en la "Base de Datos"
    nombre_camara = st.selectbox("Cargar Preset", list(st.session_state['camaras_db'].keys()))
    
    # Cargar datos de la selección
    datos_cam = st.session_state['camaras_db'][nombre_camara]

    st.subheader("⚙️ Configuración Actual")
    st.info("Puedes editar estos valores y guardarlos como una cámara nueva abajo.")
    
    c1, c2 = st.columns(2)
    with c1:
        sensor_w = st.number_input("Ancho Sensor (mm)", value=float(datos_cam['w']), format="%.2f")
        focal = st.number_input("Focal (mm)", value=float(datos_cam['f']), format="%.2f")
    with c2:
        sensor_h = st.number_input("Alto Sensor (mm)", value=float(datos_cam['h']), format="%.2f")
        res_px = st.number_input("Resolución (px)", value=int(datos_cam['r']))

    # --- ZONA DE GUARDADO ---
    with st.expander("💾 Guardar como Nueva Cámara"):
        nuevo_nombre = st.text_input("Nombre del Modelo", placeholder="Ej: Sony IMX con Lente Zoom")
        if st.button("Guardar en Lista"):
            if nuevo_nombre:
                st.session_state['camaras_db'][nuevo_nombre] = {
                    "w": sensor_w, "h": sensor_h, "f": focal, "r": res_px
                }
                st.success(f"¡{nuevo_nombre} guardada!")
                st.rerun() # Recarga la página para actualizar la lista
            else:
                st.error("Escribe un nombre primero.")

    st.markdown("---")
    st.header("✈️ Escenario de Vuelo")
    pitch = st.slider("Pitch (Inclinación) [º]", 0, 60, 30)
    dist = st.slider("Distancia Horizontal (m)", 5, 200, 50)
    altura_rel = st.slider("Altura Relativa (m)", -50, 50, 0, help="Positivo = Objetivo más alto que tú")
    obj_size = st.number_input("Tamaño Objetivo (m)", value=0.3)

# --- 4. CÁLCULOS ---
hfov = 2 * math.degrees(math.atan(sensor_w / (2 * focal)))
vfov = 2 * math.degrees(math.atan(sensor_h / (2 * focal)))

# Geometría
angulo_a_objetivo_rad = math.atan2(altura_rel, dist)
angulo_a_objetivo_deg = math.degrees(angulo_a_objetivo_rad)
techo_visual = -pitch + (vfov / 2)
suelo_visual = -pitch - (vfov / 2)
visible = suelo_visual <= angulo_a_objetivo_deg <= techo_visual

distancia_real = math.sqrt(dist**2 + altura_rel**2)
px_on_target = (res_px * obj_size * focal) / (sensor_w * distancia_real)

# --- 5. VISUALIZACIÓN PRINCIPAL ---

# Métricas en columnas grandes
col1, col2, col3, col4 = st.columns(4)
col1.metric("FOV Vertical", f"{vfov:.1f}º")
col2.metric("Ángulo Objetivo", f"{angulo_a_objetivo_deg:.1f}º")
col3.metric("Límite Superior", f"{techo_visual:.1f}º", delta_color="off")
col4.metric("Píxeles Objetivo", f"{px_on_target:.1f} px", 
            delta="Detectado" if px_on_target > 15 else "Crítico",
            delta_color="normal" if px_on_target > 15 else "inverse")

# Mensaje de estado
if not visible:
    if angulo_a_objetivo_deg > techo_visual:
        st.error(f"🚨 **PÉRDIDA DE OBJETIVO POR ARRIBA:** Necesitas subir la cámara o reducir el Pitch.")
    else:
        st.error(f"🚨 **PÉRDIDA DE OBJETIVO POR ABAJO:** El objetivo está demasiado bajo.")
else:
    st.success("✅ **OBJETIVO DENTRO DEL CAMPO DE VISIÓN**")

# --- GRÁFICO RESPONSIVE ---
# Usamos un estilo oscuro para que quede más 'tech'
plt.style.use('dark_background')

fig, ax = plt.subplots(figsize=(12, 6)) # Tamaño base, Streamlit lo estirará
fig.patch.set_facecolor('#0E1117') # Color de fondo igual al de Streamlit
ax.set_facecolor('#0E1117')

# Dron
ax.plot(0, 0, marker='o', color='white', markersize=10, label="Interceptor")

# Cono FOV
radio = distancia_real * 1.2
ang_top = math.radians(techo_visual)
ang_bot = math.radians(suelo_visual)
x_t, y_t = radio * math.cos(ang_top), radio * math.sin(ang_top)
x_b, y_b = radio * math.cos(ang_bot), radio * math.sin(ang_bot)

poly = patches.Polygon([[0,0], [x_t, y_t], [x_b, y_b]], 
                       closed=True, color='#00FF00' if visible else '#FF4B4B', alpha=0.2)
ax.add_patch(poly)
ax.plot([0, x_t], [0, y_t], color='#00FF00' if visible else '#FF4B4B', linestyle='--', linewidth=1)
ax.plot([0, x_b], [0, y_b], color='#00FF00' if visible else '#FF4B4B', linestyle='--', linewidth=1)

# Objetivo
ax.plot(dist, altura_rel, marker='*', color='#00FFFF', markersize=20, label="Objetivo")
ax.plot([0, dist], [0, altura_rel], color='white', linestyle=':', alpha=0.3)

# Grid y Ejes
ax.grid(True, color='gray', linestyle=':', alpha=0.2)
ax.set_xlabel("Distancia (m)", color='white')
ax.set_ylabel("Altura (m)", color='white')
ax.spines['bottom'].set_color('white')
ax.spines['left'].set_color('white')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.tick_params(axis='x', colors='white')
ax.tick_params(axis='y', colors='white')

# Auto-zoom inteligente para que siempre se vea todo
max_y = max(abs(altura_rel), abs(y_t), abs(y_b)) * 1.1
ax.set_ylim(-max_y, max_y)
ax.set_xlim(-5, radio)
ax.set_aspect('equal')

# ESTO ES LO QUE ARREGLA EL TAMAÑO DE VENTANA
st.pyplot(fig, use_container_width=True)
