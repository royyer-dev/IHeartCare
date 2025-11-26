import streamlit as st
from auth import login_user, logout_user

st.set_page_config(
    page_title="I-HeartCare - Inicio",
    page_icon="🩺",
    layout="wide"
)

# Inicializar session_state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# --- OCULTAR SIDEBAR Y TODO HASTA QUE INICIE SESIÓN ---
if not st.session_state.authenticated:
    # Ocultar sidebar completamente
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {display: none;}
            header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)
    
    # --- PÁGINA DE LOGIN (SIN DASHBOARD) ---
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🩺 I-HeartCare")
        st.subheader("Sistema de Monitoreo Cardíaco")
        st.markdown("---")
        
        tab1, tab2 = st.tabs(["🔐 Iniciar Sesión", "📝 Registro de Paciente"])
        
        with tab1:
            with st.form("login_form"):
                st.subheader("Iniciar Sesión")
                username = st.text_input("Usuario", placeholder="Ingrese su usuario")
                password = st.text_input("Contraseña", type="password", placeholder="Ingrese su contraseña")
                submit = st.form_submit_button("Ingresar", use_container_width=True)
                
                if submit:
                    if login_user(username, password):
                        st.success("✅ Inicio de sesión exitoso")
                        st.rerun()
                    else:
                        st.error("❌ Usuario o contraseña incorrectos")
        
        with tab2:
            st.subheader("¿Eres nuevo paciente?")
            st.info("Complete el formulario de registro para crear su cuenta de paciente.")
            st.page_link("pages/7_registro_paciente.py", label="➡️ Ir al Formulario de Registro", icon="📋", use_container_width=True)
    
    # Detener la ejecución aquí para que no se muestre nada más
    st.stop()

# --- AHORA SÍ, SI ESTÁ AUTENTICADO, MOSTRAR SIDEBAR Y DASHBOARD ---
with st.sidebar:
    st.success(f"✅ Sesión activa: **{st.session_state.username}**")
    st.info(f"🎭 Rol: **{st.session_state.rol.capitalize()}**")
    
    st.markdown("---")
    st.subheader("📋 Navegación")
    
    # MENÚ SEGÚN ROL
    if st.session_state.rol == 'administrador':
        st.markdown("### 🔧 Gestión")
        st.page_link("pages/1_ gestion_pacientes.py", label="👤 Gestión de Pacientes", icon="📝")
        st.page_link("pages/2_ gestion_personal_medico.py", label="👨‍⚕️ Gestión de Personal Médico", icon="📝")
        st.page_link("pages/3_gestion_dispositivos.py", label="⌚ Gestión de Dispositivos", icon="📝")
        st.page_link("pages/4_gestion_monitoreo.py", label="🩺 Gestión de Monitoreo", icon="📝")
        
        st.markdown("### 📊 Visualización")
        st.page_link("pages/5_dashboard_visualizacion.py", label="📊 Dashboard Visualización", icon="📈")
        st.page_link("pages/6_panel_analisis_clinico.py", label="🔬 Panel Análisis Clínico", icon="🔬")
    
    elif st.session_state.rol == 'medico':
        st.markdown("### 👨‍⚕️ Mis Pacientes")
        st.page_link("pages/10_mis_pacientes.py", label="👥 Ver Mis Pacientes", icon="📋")
        
        st.markdown("### 📊 Análisis")
        st.page_link("pages/5_dashboard_visualizacion.py", label="📊 Dashboard Visualización", icon="📈")
        st.page_link("pages/6_panel_analisis_clinico.py", label="🔬 Panel Análisis Clínico", icon="🔬")
    
    elif st.session_state.rol == 'paciente':
        st.markdown("### 👤 Mi Información")
        st.page_link("pages/8_mi_perfil.py", label="📋 Mi Perfil", icon="👤")
        st.page_link("pages/9_mis_mediciones.py", label="📊 Mis Mediciones", icon="📈")
        st.page_link("pages/11_mis_alertas.py", label="⚠️ Mis Alertas", icon="🔔")
    
    st.markdown("---")
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        logout_user()
        st.rerun()

# --- DASHBOARD SEGÚN ROL ---
# Título de bienvenida
st.title(f"🩺 Bienvenido, {st.session_state.username}")
st.markdown("---")

# ========== DASHBOARD ADMINISTRADOR ==========
if st.session_state.rol == 'administrador':
    st.header("🔧 Panel de Administrador")
    st.success("✅ Tienes acceso completo a todas las funcionalidades del sistema.")
    
    # Resumen de estadísticas
    try:
        from sqlalchemy import text
        conn = st.connection("postgresql", type="sql")
        with conn.session as s:
            total_pacientes = s.execute(text("SELECT COUNT(*) FROM public.pacientes")).fetchone()[0]
            total_medicos = s.execute(text("SELECT COUNT(*) FROM public.personal_medico")).fetchone()[0]
            total_dispositivos = s.execute(text("SELECT COUNT(*) FROM public.dispositivos")).fetchone()[0]
            monitoreos_activos = s.execute(text("SELECT COUNT(*) FROM public.monitoreos WHERE activo = true")).fetchone()[0]
    except:
        total_pacientes = 0
        total_medicos = 0
        total_dispositivos = 0
        monitoreos_activos = 0
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👤 Pacientes", total_pacientes)
    with col2:
        st.metric("👨‍⚕️ Médicos", total_medicos)
    with col3:
        st.metric("⌚ Dispositivos", total_dispositivos)
    with col4:
        st.metric("🩺 Monitoreos Activos", monitoreos_activos)
    
    st.markdown("---")
    
    # Accesos rápidos
    st.subheader("🚀 Accesos Rápidos")
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            st.markdown("### 📝 Gestión de Datos")
            st.page_link("pages/1_ gestion_pacientes.py", label="Gestión de Pacientes", icon="👤")
            st.page_link("pages/2_ gestion_personal_medico.py", label="Gestión de Personal Médico", icon="👨‍⚕️")
            st.page_link("pages/3_gestion_dispositivos.py", label="Gestión de Dispositivos", icon="⌚")
            st.page_link("pages/4_gestion_monitoreo.py", label="Gestión de Monitoreo", icon="🩺")
    
    with col2:
        with st.container(border=True):
            st.markdown("### 📊 Análisis y Reportes")
            st.page_link("pages/5_dashboard_visualizacion.py", label="Dashboard de Visualización", icon="📈")
            st.page_link("pages/6_panel_analisis_clinico.py", label="Panel de Análisis Clínico", icon="🔬")

# ========== DASHBOARD MÉDICO ==========
elif st.session_state.rol == 'medico':
    st.header("👨‍⚕️ Panel del Médico")
    st.info("Accede a la información de tus pacientes asignados.")
    
    # Estadísticas del médico
    try:
        from sqlalchemy import text
        conn = st.connection("postgresql", type="sql")
        with conn.session as s:
            query_pacientes = text("""
                SELECT COUNT(*) 
                FROM public.pacientes_medicos 
                WHERE medico_id = :medico_id
            """)
            total_pacientes = s.execute(query_pacientes, {"medico_id": st.session_state.medico_id}).fetchone()[0]
            
            query_monitoreos = text("""
                SELECT COUNT(DISTINCT m.id)
                FROM public.monitoreos m
                INNER JOIN public.pacientes_medicos pm ON m.paciente_id = pm.paciente_id
                WHERE pm.medico_id = :medico_id AND m.activo = true
            """)
            monitoreos_activos = s.execute(query_monitoreos, {"medico_id": st.session_state.medico_id}).fetchone()[0]
            
            query_alertas = text("""
                SELECT COUNT(DISTINCT a.id)
                FROM public.alertas a
                INNER JOIN public.mediciones med ON a.medicion_id = med.id
                INNER JOIN public.dispositivos d ON med.dispositivo_id = d.id
                INNER JOIN public.pacientes_medicos pm ON d.paciente_id = pm.paciente_id
                WHERE pm.medico_id = :medico_id AND a.leida = false
            """)
            alertas_pendientes = s.execute(query_alertas, {"medico_id": st.session_state.medico_id}).fetchone()[0]
    except:
        total_pacientes = 0
        monitoreos_activos = 0
        alertas_pendientes = 0
    
    # Métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👥 Mis Pacientes", total_pacientes)
    with col2:
        st.metric("🩺 Monitoreos Activos", monitoreos_activos)
    with col3:
        st.metric("⚠️ Alertas Pendientes", alertas_pendientes)
    
    st.markdown("---")
    
    # Accesos rápidos
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("### 👥 Mis Pacientes")
            st.page_link("pages/10_mis_pacientes.py", label="Ver Lista de Pacientes", icon="📋")
            st.caption("Revisa el estado de salud de tus pacientes asignados")
    
    with col2:
        with st.container(border=True):
            st.markdown("### 📊 Herramientas de Análisis")
            st.page_link("pages/5_dashboard_visualizacion.py", label="Dashboard de Visualización", icon="📈")
            st.page_link("pages/6_panel_analisis_clinico.py", label="Panel de Análisis Clínico", icon="🔬")

# ========== DASHBOARD PACIENTE ==========
elif st.session_state.rol == 'paciente':
    st.header("👤 Panel del Paciente")
    st.info("Visualiza tu información médica y monitoreo en tiempo real.")
    
    # Información del paciente
    try:
        from sqlalchemy import text
        conn = st.connection("postgresql", type="sql")
        with conn.session as s:
            query = text("""
                SELECT 
                    p.nombre, p.apellido_paterno,
                    d.modelo as dispositivo,
                    m.activo as monitoreo_activo,
                    (SELECT COUNT(*) FROM public.alertas a 
                     INNER JOIN public.mediciones med ON a.medicion_id = med.id
                     INNER JOIN public.dispositivos disp ON med.dispositivo_id = disp.id
                     WHERE disp.paciente_id = p.id AND a.leida = false) as alertas_pendientes,
                    CONCAT(pm.nombre, ' ', pm.apellido_paterno) as medico
                FROM public.pacientes p
                LEFT JOIN public.dispositivos d ON d.paciente_id = p.id
                LEFT JOIN public.monitoreos m ON m.paciente_id = p.id AND m.activo = true
                LEFT JOIN public.pacientes_medicos rel ON rel.paciente_id = p.id
                LEFT JOIN public.personal_medico pm ON pm.id = rel.medico_id
                WHERE p.id = :paciente_id
                LIMIT 1
            """)
            datos = s.execute(query, {"paciente_id": st.session_state.paciente_id}).fetchone()
    except:
        datos = None
    
    if datos:
        # Métricas
        col1, col2, col3 = st.columns(3)
        with col1:
            estado = "🟢 Activo" if datos.monitoreo_activo else "🔴 Inactivo"
            st.metric("Estado de Monitoreo", estado)
        with col2:
            dispositivo = datos.dispositivo if datos.dispositivo else "Sin asignar"
            st.metric("⌚ Dispositivo", dispositivo)
        with col3:
            st.metric("⚠️ Alertas Pendientes", datos.alertas_pendientes or 0)
        
        st.markdown("---")
        
        # Información del médico
        if datos.medico:
            st.success(f"👨‍⚕️ **Tu médico asignado:** Dr(a). {datos.medico}")
        else:
            st.warning("⚠️ Aún no tienes un médico asignado")
    
    st.markdown("---")
    
    # Accesos rápidos
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("### 📋 Mi Información")
            st.page_link("pages/8_mi_perfil.py", label="Ver Mi Perfil Completo", icon="👤")
            st.caption("Revisa tus datos personales y de contacto")
    
    with col2:
        with st.container(border=True):
            st.markdown("### 📊 Mis Datos de Salud")
            st.page_link("pages/9_mis_mediciones.py", label="Ver Mis Mediciones", icon="📈")
            st.page_link("pages/11_mis_alertas.py", label="Ver Mis Alertas", icon="⚠️")