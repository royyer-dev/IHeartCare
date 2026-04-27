
import streamlit as st
from sqlalchemy import text
from core.auth import login_user, logout_user
from core.theme import apply_global_theme
from core.sidebar import render_sidebar
from utils import (
    breadcrumb_nav,
    hero_section,
    metric_card,
    metric_card_container,
    section_divider,
    patient_card,
    status_indicator,
    obtener_notificaciones_pendientes,
    contar_notificaciones_pendientes,
)
import json
import os
from pathlib import Path

st.set_page_config(
    page_title="IHeartCare - Dashboard",
    page_icon="❤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_global_theme()

# Archivo para guardar credenciales recordadas
CREDENTIALS_FILE = Path.home() / ".iheartcare_credentials.json"

def load_saved_credentials():
    """Carga credenciales guardadas localmente."""
    if CREDENTIALS_FILE.exists():
        try:
            with open(CREDENTIALS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"username": "", "remember": False}
    return {"username": "", "remember": False}

def save_credentials(username, remember):
    """Guarda credenciales localmente."""
    try:
        with open(CREDENTIALS_FILE, 'w') as f:
            json.dump({"username": username, "remember": remember}, f)
    except:
        pass

# --- ANIMACIONES GLOBALES ---
st.markdown("""
<style>
@keyframes slideInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes fadeIn {
    from {
        opacity: 0;
    }
    to {
        opacity: 1;
    }
}

@keyframes pulse {
    0%, 100% {
        opacity: 1;
    }
    50% {
        opacity: 0.7;
    }
}

.page-container {
    animation: fadeIn 0.6s ease;
}
</style>
""", unsafe_allow_html=True)

# --- LOGIN LOGIC ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Cargar credenciales guardadas
        saved = load_saved_credentials()
        
        st.markdown("""
        <style>
        .login-header {
            text-align: center;
            margin-bottom: 2.5rem;
            animation: slideInDown 0.6s ease;
        }
        
        .login-header h1 {
            font-size: 1.75rem;
            color: #1E40AF;
            margin: 0 0 0.5rem 0;
            letter-spacing: -0.02em;
        }
        
        .login-header p {
            color: #6B7280;
            margin: 0.25rem 0 0 0;
            font-size: 0.95rem;
        }
        </style>
        
        <div class="login-header">
            <h1>IHeartCare</h1>
            <p>Sistema de Monitoreo Cardíaco</p>
            <p style="font-size: 0.85rem; margin-top: 0.5rem; color: #9CA3AF;">Iniciar sesión</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Campos de entrada (sin formulario para evitar "press enter")
        st.markdown("#### ")
        username = st.text_input(
            "Usuario",
            value=saved.get("username", "") if saved.get("remember") else "",
            placeholder="admin, doctor o paciente",
            label_visibility="visible",
            key="login_username"
        )
        
        password = st.text_input(
            "Contraseña",
            type="password",
            placeholder="Ingresa tu contraseña",
            label_visibility="visible",
            key="login_password"
        )
        
        # Checkbox recordar
        remember = st.checkbox(
            "Recordar usuario",
            value=saved.get("remember", False),
            key="login_remember"
        )
        
        # Botón de login
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            if st.button("Iniciar sesión", use_container_width=True, type="primary"):
                if login_user(username, password):
                    # Guardar credenciales si se marcó recordar
                    if remember:
                        save_credentials(username, True)
                    else:
                        save_credentials("", False)
                    
                    st.success("Sesión iniciada correctamente")
                    import time
                    time.sleep(0.8)
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas. Verifica usuario y contraseña.")
        
        # Información de cuentas de prueba - usando componentes nativos
        st.markdown("---")
        st.markdown("#### Cuentas de prueba")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Administrador**")
            st.code("Usuario: admin\nContraseña: admin123", language="text")
        
        with col2:
            st.write("**Doctor**")
            st.code("Usuario: doctor\nContraseña: doctor123", language="text")
        
        st.write("**Paciente**")
        st.code("Usuario: paciente\nContraseña: paciente123", language="text")
    
    st.stop()

render_sidebar()

# --- CONTENEDOR DE PÁGINA CON ANIMACIÓN ---
st.markdown('<div class="page-container">', unsafe_allow_html=True)

breadcrumb_nav(["Home"])

# ========== DASHBOARD ADMINISTRADOR ==========
if st.session_state.rol == 'administrador':
    
    hero_section(
        title="Panel de Administración",
        subtitle="Gestión completa del sistema de monitoreo cardíaco",
        user_role=st.session_state.rol,
        user_name=st.session_state.username,
    )
    
    # Obtener métricas del sistema
    try:
        conn = st.connection("postgresql", type="sql")
        with conn.session as s:
            # Query para obtener todas las métricas
            query_metrics = text("""
                SELECT 
                    (SELECT COUNT(*) FROM public.pacientes) as total_pacientes,
                    (SELECT COUNT(*) FROM public.personal_medico) as total_medicos,
                    (SELECT COUNT(*) FROM public.dispositivos WHERE activo = true) as dispositivos_activos,
                    (SELECT COUNT(*) FROM public.monitoreos WHERE activo = true) as monitoreos_activos,
                    (SELECT COUNT(*) FROM public.alertas WHERE leida = false) as alertas_pendientes,
                    (SELECT COUNT(*) FROM public.mediciones WHERE timestamp > NOW() - INTERVAL '24 hours') as mediciones_hoy
            """)
            metrics = s.execute(query_metrics).fetchone()
            
            total_pacientes = metrics[0]
            total_medicos = metrics[1]
            dispositivos_activos = metrics[2]
            monitoreos_activos = metrics[3]
            alertas_pendientes = metrics[4]
            mediciones_hoy = metrics[5]
    
    except Exception as e:
        st.error(f"Error cargando métricas: {str(e)}")
        total_pacientes = 0
        total_medicos = 0
        dispositivos_activos = 0
        monitoreos_activos = 0
        alertas_pendientes = 0
        mediciones_hoy = 0
    
    # Cards de métricas principales
    section_divider("Resumen del Sistema")
    
    metrics_data = [
        {
            "title": "Pacientes Activos",
            "value": total_pacientes,
            "icon": "",
            "color": "primary",
            "subtitle": "Incorporados al sistema"
        },
        {
            "title": "Personal Médico",
            "value": total_medicos,
            "icon": "",
            "color": "info",
            "subtitle": "Médicos registrados"
        },
        {
            "title": "Dispositivos Activos",
            "value": dispositivos_activos,
            "icon": "",
            "color": "success",
            "subtitle": "Wearables conectados"
        },
        {
            "title": "Monitoreos Activos",
            "value": monitoreos_activos,
            "icon": "",
            "color": "warning",
            "subtitle": "Monitoreos en curso"
        },
    ]
    
    metric_card_container(metrics_data, columns=4)
    
    # --- ACCESOS RÁPIDOS CON TARJETAS VISUALES ---
    section_divider("Gestión del Sistema")
    
    # Función auxiliar para card de navegación
    def nav_card(title, description, color, page_path):
        st.markdown(f"""
        <div style='
            background: white;
            border: 1px solid #E5E7EB;
            border-left: 4px solid {color};
            border-radius: 10px;
            padding: 1.25rem 1.5rem;
            margin-bottom: 0.75rem;
            transition: all 0.2s ease;
            cursor: pointer;
        ' onmouseover="this.style.boxShadow='0 4px 12px rgba(0,0,0,0.08)'; this.style.transform='translateX(4px)';"
           onmouseout="this.style.boxShadow='none'; this.style.transform='none';">
            <div style='font-size: 1rem; font-weight: 600; color: #1F2937; margin-bottom: 0.25rem;'>{title}</div>
            <div style='font-size: 0.8rem; color: #9CA3AF;'>{description}</div>
        </div>
        """, unsafe_allow_html=True)
        st.page_link(page_path, label=f"Ir a {title}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div style='font-size: 0.75rem; font-weight: 700; color: #6B7280; letter-spacing: 1.5px; margin-bottom: 1rem;'>ADMINISTRACIÓN DE DATOS</div>", unsafe_allow_html=True)
        nav_card("Pacientes", "Gestionar registros, datos y dispositivos de pacientes", "#0066CC", "pages/01_admin_pacientes.py")
        nav_card("Personal Médico", "Administrar médicos, credenciales y asignaciones", "#17A2B8", "pages/02_admin_medicos.py")
        nav_card("Dispositivos", "Registrar, editar y asignar dispositivos wearables", "#28A745", "pages/03_admin_dispositivos.py")
        nav_card("Monitoreos", "Crear y gestionar sesiones de monitoreo activas", "#FF9800", "pages/04_monitoreo_crear.py")
    
    with col2:
        st.markdown("<div style='font-size: 0.75rem; font-weight: 700; color: #6B7280; letter-spacing: 1.5px; margin-bottom: 1rem;'>ANÁLISIS Y HERRAMIENTAS</div>", unsafe_allow_html=True)
        nav_card("Visualización en Vivo", "Dashboard de monitoreo en tiempo real con signos vitales", "#DC3545", "pages/05_monitoreo_dashboard.py")
        nav_card("Análisis Clínico", "Tendencias, estadísticas y evaluación clínica por paciente", "#6F42C1", "pages/06_monitoreo_analisis.py")
    
    # --- ACTIVIDAD RECIENTE ---
    section_divider("Actividad Reciente")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Últimos Pacientes Registrados**")
        try:
            conn2 = st.connection("postgresql", type="sql")
            ultimos_pacientes = conn2.query("""
                SELECT nombre, apellido_paterno, diagnostico, fecha_registro
                FROM public.pacientes
                ORDER BY fecha_registro DESC NULLS LAST
                LIMIT 5
            """, ttl="10s")
            if not ultimos_pacientes.empty:
                for _, pac in ultimos_pacientes.iterrows():
                    nombre = f"{pac['nombre']} {pac['apellido_paterno']}"
                    diag = pac.get('diagnostico', 'Sin diagnóstico') or 'Sin diagnóstico'
                    with st.container(border=True):
                        st.markdown(f"**{nombre}**")
                        st.caption(diag)
            else:
                st.caption("Sin registros recientes")
        except Exception:
            st.caption("No se pudieron cargar los datos")
    
    with col2:
        st.markdown("**Monitoreos Activos**")
        try:
            conn3 = st.connection("postgresql", type="sql")
            monitoreos_recientes = conn3.query("""
                SELECT p.nombre, p.apellido_paterno, m.motivo, m.fecha_inicio
                FROM public.monitoreos m
                JOIN public.pacientes p ON m.paciente_id = p.id
                WHERE m.activo = true
                ORDER BY m.fecha_inicio DESC
                LIMIT 5
            """, ttl="10s")
            if not monitoreos_recientes.empty:
                for _, mon in monitoreos_recientes.iterrows():
                    nombre = f"{mon['nombre']} {mon['apellido_paterno']}"
                    motivo = mon.get('motivo', 'Sin motivo') or 'Sin motivo'
                    with st.container(border=True):
                        st.markdown(f"**{nombre}**")
                        st.caption(f"{motivo} — Desde {mon['fecha_inicio'].strftime('%d/%m/%Y')}")
            else:
                st.caption("Sin monitoreos activos")
        except Exception:
            st.caption("No se pudieron cargar los datos")

# ========== DASHBOARD MÉDICO ==========
elif st.session_state.rol == 'medico':
    
    hero_section(
        title="Panel del Médico",
        subtitle="Monitoreo de tus pacientes asignados",
        user_role=st.session_state.rol,
        user_name=st.session_state.username,
    )
    
    # Métricas del médico
    try:
        conn = st.connection("postgresql", type="sql")
        with conn.session as s:
            query = text("""
                SELECT 
                    (SELECT COUNT(*) FROM public.pacientes_medicos WHERE medico_id = :medico_id) as mis_pacientes,
                    (SELECT COUNT(*) FROM public.monitoreos m
                     JOIN public.pacientes_medicos pm ON m.paciente_id = pm.paciente_id
                     WHERE pm.medico_id = :medico_id AND m.activo = true) as monitoreos_activos,
                    (SELECT COUNT(*) FROM public.alertas a
                     JOIN public.mediciones med ON a.medicion_id = med.id
                     JOIN public.dispositivos d ON med.dispositivo_id = d.id
                     JOIN public.pacientes_medicos pm ON d.paciente_id = pm.paciente_id
                     WHERE pm.medico_id = :medico_id AND a.leida = false) as alertas_pendientes
            """)
            resultado = s.execute(query, {"medico_id": st.session_state.medico_id}).fetchone()
            
            mis_pacientes = resultado[0]
            monitoreos_activos = resultado[1]
            alertas_pendientes = resultado[2]
    
    except:
        mis_pacientes = 0
        monitoreos_activos = 0
        alertas_pendientes = 0
    
    # Cards de métricas
    section_divider("Mis Estadísticas")
    
    metrics_data = [
        {
            "title": "Pacientes Asignados",
            "value": mis_pacientes,
            "icon": "",
            "color": "primary",
            "subtitle": "Bajo mi cuidado"
        },
        {
            "title": "Monitoreos Activos",
            "value": monitoreos_activos,
            "icon": "",
            "color": "warning",
            "subtitle": "En tiempo real"
        },
        {
            "title": "Alertas Pendientes",
            "value": alertas_pendientes,
            "icon": "",
            "color": "danger",
            "subtitle": "Requieren atención"
        },
    ]
    
    metric_card_container(metrics_data, columns=3)
    
    # Accesos rápidos
    section_divider("Herramientas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.page_link(
            "pages/09_mis_pacientes.py",
            label="Ver Mis Pacientes"
        )
        st.page_link(
            "pages/05_monitoreo_dashboard.py",
            label="Dashboard de Visualización"
        )
    
    with col2:
        st.page_link(
            "pages/06_monitoreo_analisis.py",
            label="Panel de Análisis Clínico"
        )
        st.page_link(
            "pages/10_notificaciones.py",
            label="Ver Mis Alertas"
        )

# ========== DASHBOARD PACIENTE ==========
elif st.session_state.rol == 'paciente':
    
    hero_section(
        title="Mi Panel de Salud",
        subtitle="Monitorea tu información médica en tiempo real",
        user_role=st.session_state.rol,
        user_name=st.session_state.username,
    )
    
    # Información del paciente
    try:
        conn = st.connection("postgresql", type="sql")
        with conn.session as s:
            query = text("""
                SELECT 
                    p.nombre, p.apellido_paterno, p.diagnostico,
                    d.modelo, d.activo,
                    (SELECT COUNT(*) FROM public.alertas a
                     JOIN public.mediciones med ON a.medicion_id = med.id
                     JOIN public.dispositivos disp ON med.dispositivo_id = disp.id
                     WHERE disp.paciente_id = p.id AND a.leida = false) as alertas_pendientes,
                    COUNT(DISTINCT pm.medico_id) as total_medicos,
                    COUNT(DISTINCT med.id) as total_mediciones
                FROM public.pacientes p
                LEFT JOIN public.dispositivos d ON d.paciente_id = p.id AND d.activo = true
                LEFT JOIN public.pacientes_medicos pm ON p.id = pm.paciente_id
                LEFT JOIN public.mediciones med ON d.id = med.dispositivo_id
                WHERE p.id = :paciente_id
                GROUP BY p.id, d.id
                LIMIT 1
            """)
            datos = s.execute(query, {"paciente_id": st.session_state.paciente_id}).fetchone()
    
    except:
        datos = None
    
    if datos:
        # Métricas del paciente
        section_divider("Mi Estado Actual")
        
        metrics_data = [
            {
                "title": "Estado del Dispositivo",
                "value": "Activo" if datos[4] else "Inactivo",
                "icon": "",
                "color": "success" if datos[4] else "danger",
            },
            {
                "title": "Alertas Pendientes",
                "value": datos[5],
                "icon": "",
                "color": "warning",
            },
            {
                "title": "Médicos Asignados",
                "value": datos[6],
                "icon": "",
                "color": "info",
            },
            {
                "title": "Total de Mediciones",
                "value": datos[7],
                "icon": "",
                "color": "primary",
            },
        ]
        
        metric_card_container(metrics_data, columns=4)
        
        # Información clínica
        section_divider("Mi Información Clínica")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div style='
                background: #E8F4FF;
                border-radius: 12px;
                padding: 1.5rem;
            '>
                <h3 style='margin-top: 0;'>Diagnóstico</h3>
                <p style='font-size: 1.1rem; color: #0B3D5C; margin: 0;'>
                    {datos[2] if datos[2] else 'No especificado'}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style='
                background: #F0FDF4;
                border-radius: 12px;
                padding: 1.5rem;
            '>
                <h3 style='margin-top: 0;'>Dispositivo</h3>
                <p style='font-size: 1.1rem; color: #065F46; margin: 0;'>
                    {datos[3] if datos[3] else 'No asignado'}
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    # Accesos rápidos personalizados
    section_divider("Mi Información")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.page_link(
            "pages/07_perfil_usuario.py",
            label="Mi Perfil"
        )
    
    with col2:
        st.page_link(
            "pages/08_mediciones_personales.py",
            label="Mis Mediciones"
        )
    
    with col3:
        st.page_link(
            "pages/10_notificaciones.py",
            label="Mis Alertas"
        )

st.markdown('</div>', unsafe_allow_html=True)
