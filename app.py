import streamlit as st
import requests
import json
import os
from datetime import datetime

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Desafío Anatómico - Universidad Anáhuac",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# SECRETS DE STREAMLIT (Configurar en la nube)
# ==========================================
# En Streamlit Cloud, ve a: Settings > Secrets
# Y agrega:
# GITHUB_TOKEN = "ghp_tu_token_aqui"
# GITHUB_OWNER = "Alejandra-LozC"
# GITHUB_REPO = "desunidad2"

GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
GITHUB_OWNER = st.secrets.get("GITHUB_OWNER", "Alejandra-LozC")
GITHUB_REPO = st.secrets.get("GITHUB_REPO", "desunidad2")
GITHUB_PATH = "resultados/"

# ==========================================
# CARGAR ESTUDIANTES
# ==========================================
@st.cache_data
def cargar_estudiantes():
    """Carga la lista de estudiantes desde el JSON"""
    try:
        with open('estudiantes.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {str(e['id']).strip(): e['nombre'] for e in data}
    except Exception as e:
        st.error(f"Error cargando estudiantes: {e}")
        return {}

estudiantes = cargar_estudiantes()

# ==========================================
# FUNCIÓN PARA GUARDAR EN GITHUB
# ==========================================
def guardar_en_github(id_estudiante, nombre, puntaje, acertadas, falladas, logros):
    """Guarda el resultado del estudiante en GitHub"""
    if not GITHUB_TOKEN:
        return False, "Token de GitHub no configurado"
    
    try:
        fecha = datetime.now().strftime('%Y-%m-%d')
        filename = f"resultado_{id_estudiante}_{fecha}.csv"
        
        csv_content = f'"Estudiante","{nombre}"\n"ID","{id_estudiante}"\n"Fecha","{fecha}"\n"Puntaje",{puntaje}\n"Aciertos",{acertadas}\n"Fallos",{falladas}\n"Logros","{logros}"'
        
        # Codificar a Base64
        import base64
        base64_content = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
        
        api_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{GITHUB_PATH}{filename}"
        
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Verificar si el archivo ya existe
        sha = None
        check_response = requests.get(api_url, headers=headers)
        if check_response.status_code == 200:
            sha = check_response.json().get('sha')
        
        # Crear o actualizar
        payload = {
            'message': f'Resultado de {nombre} ({id_estudiante})',
            'content': base64_content,
            'branch': 'main'
        }
        if sha:
            payload['sha'] = sha
        
        response = requests.put(api_url, headers=headers, json=payload)
        
        if response.status_code in [200, 201]:
            return True, "Guardado exitosamente"
        else:
            return False, f"Error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return False, f"Error: {str(e)}"

# ==========================================
# RECIBIR DATOS DEL JUEGO (vía postMessage)
# ==========================================
def receive_message():
    """Recibe mensajes del juego HTML embebido"""
    st.components.v1.html("""
        <script>
        window.addEventListener('message', function(event) {
            if (event.data && event.data.tipo === 'resultado_final') {
                var xhr = new XMLHttpRequest();
                xhr.open('POST', window.location.href, true);
                xhr.setRequestHeader('Content-Type', 'application/json');
                xhr.send(JSON.stringify(event.data));
            }
        });
        </script>
    """, height=0)

# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================
st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #432f64 0%, #5d428c 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 20px;
    }
    .main-header h1 {
        color: #fd8103;
        font-size: 3rem;
        margin: 0;
    }
    .main-header p {
        color: #cdb9ef;
        font-size: 1.2rem;
        margin: 10px 0 0 0;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="main-header">
        <h1>🦴 DESAFÍO ANATÓMICO</h1>
        <p>Universidad Anáhuac | Sistema Locomotor</p>
    </div>
""", unsafe_allow_html=True)

# Tabs para diferentes secciones
tab_juego, tab_resultados, tab_admin = st.tabs([" Jugar", "📊 Resultados", "️ Admin"])

with tab_juego:
    st.info("👆 Ingresa tu ID de estudiante y haz clic en COMENZAR JUEGO")
    
    # Embeber el juego HTML
    with open('juego.html', 'r', encoding='utf-8') as f:
        juego_html = f.read()
    
    # Inyectar el número de estudiantes en el HTML
    juego_html = juego_html.replace(
        "✓ ' + Object.keys(estudiantes).length + ' estudiantes cargados",
        f"✓ {len(estudiantes)} estudiantes cargados"
    )
    
    componente = st.components.v1.html(juego_html, height=800, scrolling=True)
    
    # Recibir mensajes del juego
    receive_message()
    
    # Mostrar estado de conexión
    if GITHUB_TOKEN:
        st.success("✅ Conectado a GitHub - Los resultados se guardarán automáticamente")
    else:
        st.warning("⚠️ Token de GitHub no configurado. Los resultados no se guardarán.")

with tab_resultados:
    st.header("📊 Resultados de los Estudiantes")
    st.info("Los resultados se guardan automáticamente en la carpeta `resultados/` del repositorio de GitHub.")
    
    # Mostrar últimos resultados guardados localmente (si existen)
    if os.path.exists('resultados'):
        archivos = [f for f in os.listdir('resultados') if f.endswith('.csv')]
        if archivos:
            st.subheader(f"Últimos {len(archivos)} resultados guardados localmente")
            for archivo in sorted(archivos)[-10:]:  # Mostrar los últimos 10
                st.text(f"📄 {archivo}")
        else:
            st.info("Aún no hay resultados guardados localmente.")
    else:
        st.info("La carpeta de resultados aún no existe.")

with tab_admin:
    st.header("⚙️ Panel de Administración")
    
    st.subheader(" Lista de Estudiantes")
    st.write(f"Total de estudiantes registrados: **{len(estudiantes)}**")
    
    # Mostrar tabla de estudiantes
    if estudiantes:
        df_data = []
        for id_est, nombre in sorted(estudiantes.items()):
            df_data.append({"ID": id_est, "Nombre": nombre})
        
        import pandas as pd
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)
    
    st.subheader("🔑 Configuración de GitHub")
    st.code(f"""
GITHUB_OWNER = {GITHUB_OWNER}
GITHUB_REPO = {GITHUB_REPO}
GITHUB_TOKEN = {'*' * 20 + GITHUB_TOKEN[-4:] if GITHUB_TOKEN else 'NO CONFIGURADO'}
    """)
    
    if not GITHUB_TOKEN:
        st.warning("""
        **Para configurar el token de GitHub:**
        
        1. Ve a tu app en Streamlit Cloud
        2. Haz clic en el menú (⋮) > **Settings**
        3. Ve a la pestaña **Secrets**
        4. Agrega estas variables:
        
        ```
        GITHUB_TOKEN = "ghp_tu_token_aqui"
        GITHUB_OWNER = "Alejandra-LozC"
        GITHUB_REPO = "desunidad2"
        ```
        """)

# ==========================================
# FOOTER
# ==========================================
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        <p>🦴 Desafío Anatómico - Universidad Anáhuac | Sistema Locomotor</p>
        <p>Desarrollado para la Licenciatura en Ingeniería Biomédica</p>
    </div>
""", unsafe_allow_html=True)