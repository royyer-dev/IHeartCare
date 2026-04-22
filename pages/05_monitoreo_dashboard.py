import streamlit as st
import pandas as pd
import time
from datetime import datetime
from sqlalchemy import text

from auth import require_auth
from sidebar import render_sidebar
from theme import apply_global_theme
from utils import breadcrumb_nav

# --- PROTECCIÓN DE RUTA ---
require_auth(allowed_roles=['administrador', 'medico'])
render_sidebar()
apply_global_theme()

st.set_page_config(page_title="Dashboard en Vivo", page_icon="🫀", layout="wide")

# --- BREADCRUMBS ---
breadcrumb_nav(["Home", "Monitoreo", "Dashboard en Vivo"])

# --- CONEXIÓN A LA BASE DE DATOS ---
try:
    conn = st.connection("postgresql", type="sql")
except Exception as e:
    st.error("❌ No se pudo establecer conexión con la base de datos.")
    st.stop()

# --- ESTILOS CSS BÁSICOS ---
st.markdown("""
<style>
    body {
        background-color: white;
        color: #333;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #333;
    }
    
    p, label, span {
        color: #555;
    }
</style>
""", unsafe_allow_html=True)

st.title("🫀 Dashboard en Vivo de Monitoreo Cardíaco")
st.markdown("---")

# --- CONTROLES DE ACTUALIZACIÓN ---
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.markdown("### 📊 Monitoreos Activos")

with col2:
    refresh_interval = st.selectbox(
        "Actualizar cada",
        options=[5, 10, 15, 30],
        format_func=lambda x: f"{x} segundos",
        key="refresh_selector"
    )

with col3:
    if st.button("🔄 Actualizar Ahora", use_container_width=True):
        st.rerun()

st.markdown("---")

# --- OBTENER DISPOSITIVO SELECCIONADO ---
selected_dispositivo_id = st.session_state.get('selected_dispositivo_id')

# --- CONSULTAR MONITOREOS ---
try:
    # Query con filtrado por dispositivo si está seleccionado
    if selected_dispositivo_id:
        query = """
            SELECT 
                m.id as monitoreo_id,
                m.paciente_id,
                m.fecha_inicio,
                m.fecha_fin,
                m.motivo,
                m.activo as monitoreo_activo,
                p.nombre as paciente_nombre,
                p.apellido_paterno,
                p.apellido_materno,
                p.email,
                p.telefono,
                p.diagnostico,
                d.id as dispositivo_id,
                d.modelo,
                d.mac_address,
                d.latitude,
                d.longitude,
                d.activo as dispositivo_activo
            FROM public.monitoreos m
            JOIN public.pacientes p ON m.paciente_id = p.id
            LEFT JOIN public.dispositivos d ON p.id = d.paciente_id
            WHERE m.activo = true 
              AND d.id = :dispositivo_id
            ORDER BY m.fecha_inicio DESC
        """
        monitoreos_df = conn.query(query, params={"dispositivo_id": selected_dispositivo_id}, ttl="5s")
    else:
        query = """
            SELECT 
                m.id as monitoreo_id,
                m.paciente_id,
                m.fecha_inicio,
                m.fecha_fin,
                m.motivo,
                m.activo as monitoreo_activo,
                p.nombre as paciente_nombre,
                p.apellido_paterno,
                p.apellido_materno,
                p.email,
                p.telefono,
                p.diagnostico,
                d.id as dispositivo_id,
                d.modelo,
                d.mac_address,
                d.latitude,
                d.longitude,
                d.activo as dispositivo_activo
            FROM public.monitoreos m
            JOIN public.pacientes p ON m.paciente_id = p.id
            LEFT JOIN public.dispositivos d ON p.id = d.paciente_id
            WHERE m.activo = true
            ORDER BY m.fecha_inicio DESC
        """
        monitoreos_df = conn.query(query, ttl="5s")
    
    if monitoreos_df.empty:
        st.info("📭 No hay monitoreos activos en este momento.")
        st.stop()

except Exception as e:
    st.error(f"❌ Error al consultar monitoreos: {str(e)}")
    st.stop()

# --- MOSTRAR ESTADÍSTICAS GENERALES ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-label">Monitoreos Activos</div>
        <div class="stat-value">{len(monitoreos_df)}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    dispositivos_unicos = monitoreos_df['dispositivo_id'].nunique()
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-label">Dispositivos</div>
        <div class="stat-value">{dispositivos_unicos}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-label">Última Actualización</div>
        <div class="stat-value">{datetime.now().strftime("%H:%M:%S")}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-label">Estado Sistema</div>
        <div class="stat-value">🟢 Activo</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- MOSTRAR CADA MONITOREO ---
for idx, monitoreo in monitoreos_df.iterrows():
    paciente_nombre = f"{monitoreo['paciente_nombre']} {monitoreo['apellido_paterno']} {monitoreo['apellido_materno']}"
    
    # Crear expandable para cada monitoreo
    with st.expander(
        f"👤 {paciente_nombre} | 📱 {monitoreo['modelo']} | ⏱️ {monitoreo['fecha_inicio'].strftime('%Y-%m-%d %H:%M')}",
        expanded=(idx == 0)  # Expandir el primero por defecto
    ):
        # Mostrar información del paciente
        st.markdown(f"### 👤 Información del Paciente")
        
        st.markdown(f"""
        **Nombre:** {paciente_nombre}  
        **Diagnóstico:** {monitoreo['diagnostico'] or 'N/A'}  
        **Email:** {monitoreo['email']}  
        **Teléfono:** {monitoreo['telefono']}
        """)
        
        st.markdown("---")
        
        # Información del monitoreo
        st.markdown(f"### 📊 Período de Monitoreo")
        
        fecha_inicio = monitoreo['fecha_inicio'].strftime('%Y-%m-%d %H:%M:%S')
        fecha_fin = monitoreo['fecha_fin'].strftime('%Y-%m-%d %H:%M:%S') if pd.notna(monitoreo['fecha_fin']) else "En curso"
        
        st.markdown(f"""
        **Inicio:** {fecha_inicio}  
        **Fin Programado:** {fecha_fin}  
        **Motivo:** {monitoreo['motivo'] or 'Sin especificar'}
        """)
        
        st.markdown("---")
        
        # Información del dispositivo
        st.markdown(f"### 📱 Dispositivo")
        
        st.markdown(f"""
        **Modelo:** {monitoreo['modelo']}  
        **Dirección MAC:** `{monitoreo['mac_address'] or 'N/A'}`
        """)
        
        st.markdown("---")

# --- INFORMACIÓN DE AUTO-ACTUALIZACIÓN ---
st.markdown("<br>", unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(f"""
    <div style="color: #0891B2; font-size: 0.85em;">
    ⏱️ <strong>Auto-actualización configurada:</strong> Cada {refresh_interval} segundos
    </div>
    """, unsafe_allow_html=True)

with col2:
    if st.button("⏹️ Detener Auto-refresh", use_container_width=True):
        st.session_state.refresh_interval = None