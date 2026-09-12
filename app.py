import streamlit as st
import requests
import json
import os
import base64
from datetime import datetime

st.set_page_config(
    page_title="Desafío Anatómico - Universidad Anáhuac",
    page_icon="🦴",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# CONFIGURACIÓN (desde Secrets de Streamlit)
# ==========================================
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
GITHUB_OWNER = st.secrets.get("GITHUB_OWNER", "Alejandra-LozC")
GITHUB_REPO = st.secrets.get("GITHUB_REPO", "desunidad2")
GITHUB_PATH = "resultados/"

# ==========================================
# CARGAR ESTUDIANTES
# ==========================================
@st.cache_data
def cargar_estudiantes():
    try:
        with open('estudiantes.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {str(e['id']).strip(): e['nombre'] for e in data}
    except Exception as e:
        st.error(f"Error cargando estudiantes: {e}")
        return {}

estudiantes = cargar_estudiantes()

# ==========================================
# GUARDAR EN GITHUB
# ==========================================
def guardar_en_github(id_est, nombre, puntaje, acertadas, falladas, logros, csv_content):
    if not GITHUB_TOKEN:
        return False, "Token no configurado"
    
    try:
        fecha = datetime.now().strftime('%Y-%m-%d')
        filename = f"resultado_{id_est}_{fecha}.csv"
        base64_content = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
        api_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{GITHUB_PATH}{filename}"
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        sha = None
        check = requests.get(api_url, headers=headers)
        if check.status_code == 200:
            sha = check.json().get('sha')
        
        payload = {
            'message': f'Resultado de {nombre} ({id_est})',
            'content': base64_content,
            'branch': 'main'
        }
        if sha:
            payload['sha'] = sha
        
        resp = requests.put(api_url, headers=headers, json=payload)
        if resp.status_code in [200, 201]:
            return True, "Guardado exitosamente"
        else:
            return False, f"Error {resp.status_code}: {resp.text}"
    except Exception as e:
        return False, f"Error: {str(e)}"

# ==========================================
# ESTILOS CSS
# ==========================================
st.markdown("""
<style>
.main-header {
    text-align: center;
    padding: 30px;
    background: linear-gradient(135deg, #432f64 0%, #5d428c 100%);
    color: white;
    border-radius: 15px;
    margin-bottom: 20px;
}
.main-header h1 { color: #fd8103; font-size: 3rem; margin: 0; }
.main-header p { color: #cdb9ef; font-size: 1.2rem; margin: 10px 0 0 0; }
.stTabs [data-baseweb="tab-list"] { gap: 20px; }
.stTabs [data-baseweb="tab"] { font-size: 1.1rem; padding: 10px 20px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>🦴 DESAFÍO ANATÓMICO</h1>
    <p>Universidad Anáhuac | Sistema Locomotor</p>
</div>
""", unsafe_allow_html=True)

tab_juego, tab_resultados, tab_admin = st.tabs(["🎮 Jugar", "📊 Resultados", "⚙️ Admin"])

# ==========================================
# TAB: JUGAR
# ==========================================
with tab_juego:
    st.info("👆 Ingresa tu ID de estudiante y haz clic en COMENZAR JUEGO")
    
    with open('juego.html', 'r', encoding='utf-8') as f:
        juego_html = f.read()
    
    st.components.v1.html(juego_html, height=900, scrolling=True)
    
    if GITHUB_TOKEN:
        st.success("✅ Conectado a GitHub")
    else:
        st.warning("⚠️ Token de GitHub no configurado")

# ==========================================
# TAB: RESULTADOS
# ==========================================
with tab_resultados:
    st.header("📊 Sube tu resultado")
    st.info("Después de jugar, descarga tu CSV y súbelo aquí para que tu profesora lo reciba.")
    
    uploaded_file = st.file_uploader("📤 Selecciona tu archivo CSV", type=['csv'])
    
    if uploaded_file is not None:
        contenido = uploaded_file.read().decode('utf-8-sig')
        lineas = contenido.strip().split('\n')
        
        id_est = ""
        nombre = ""
        puntaje = 0
        acertadas = 0
        falladas = 0
        logros = ""
        
        for linea in lineas:
            if linea.startswith('"ID"'):
                id_est = linea.split(',')[1].strip('"')
            elif linea.startswith('"Estudiante"'):
                nombre = linea.split(',', 1)[1].strip('"')
            elif linea.startswith('"Puntaje"'):
                puntaje = int(linea.split(',')[1])
            elif linea.startswith('"Aciertos"'):
                acertadas = int(linea.split(',')[1])
            elif linea.startswith('"Fallos"'):
                falladas = int(linea.split(',')[1])
            elif linea.startswith('"Logros"'):
                logros = linea.split(',', 1)[1].strip('"')
        
        st.write(f"**Estudiante:** {nombre}")
        st.write(f"**ID:** {id_est}")
        st.write(f"**Puntaje:** {puntaje}")
        st.write(f"**Aciertos:** {acertadas} | **Fallos:** {falladas}")
        st.write(f"**Logros:** {logros}")
        
        if st.button("✅ Confirmar y guardar en GitHub", type="primary"):
            ok, msg = guardar_en_github(id_est, nombre, puntaje, acertadas, falladas, logros, contenido)
            if ok:
                st.success(f"✅ {msg}")
            else:
                st.error(f"❌ {msg}")

# ==========================================
# TAB: ADMIN
# ==========================================
with tab_admin:
    st.header("⚙️ Panel de Administración")
    
    st.subheader("👥 Lista de Estudiantes")
    st.write(f"Total registrados: **{len(estudiantes)}**")
    
    if estudiantes:
        import pandas as pd
        df = pd.DataFrame([{"ID": k, "Nombre": v} for k, v in sorted(estudiantes.items())])
        st.dataframe(df, use_container_width=True)
    
    st.subheader("🔑 Configuración GitHub")
    token_status = "✅ Configurado" if GITHUB_TOKEN else "❌ No configurado"
    st.write(f"Token: {token_status}")
    st.write(f"Owner: {GITHUB_OWNER}")
    st.write(f"Repo: {GITHUB_REPO}")
    
    if not GITHUB_TOKEN:
        st.warning("""
        **Para configurar el token:**
        1. Ve a tu app en Streamlit Cloud
        2. Menú (⋮) → Settings → Secrets
        3. Agrega:
        ```
        GITHUB_TOKEN = "ghp_tu_token_aqui"
        GITHUB_OWNER = "Alejandra-LozC"
        GITHUB_REPO = "desunidad2"
        ```
        """)

st.markdown("---")
st.markdown("<div style='text-align: center; color: #666; font-size: 0.9rem;'><p>🦴 Desafío Anatómico - Universidad Anáhuac | Sistema Locomotor</p></div>", unsafe_allow_html=True)