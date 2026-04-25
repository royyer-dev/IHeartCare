import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from core.auth import require_auth
from core.sidebar import render_sidebar
from core.theme import apply_global_theme
from utils import breadcrumb_nav

# --- PROTECCIÓN DE RUTA ---
require_auth(allowed_roles=['administrador', 'medico', 'paciente'])
render_sidebar()
apply_global_theme()

st.set_page_config(page_title="Mis Alertas", page_icon="🔔", layout="wide")

# --- BREADCRUMBS ---
breadcrumb_nav(["Home", "Monitoreo", "Mis Alertas"])

st.title("🔔 Centro de Notificaciones")
st.markdown("Alertas y eventos importantes de tu monitoreo de salud.")
st.markdown("---")

# --- CONEXIÓN A LA BASE DE DATOS ---
try:
    conn = st.connection("postgresql", type="sql")
except Exception:
    st.error("No se pudo establecer conexión con la base de datos.")
    st.stop()

# --- ESTILOS CSS ---
st.markdown("""
<style>
    .alert-critica {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border-left: 4px solid #dc2626;
        padding: 16px;
        border-radius: 8px;
        margin: 8px 0;
    }
    
    .alert-advertencia {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border-left: 4px solid #f59e0b;
        padding: 16px;
        border-radius: 8px;
        margin: 8px 0;
    }
    
    .alert-info {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        border-left: 4px solid #3b82f6;
        padding: 16px;
        border-radius: 8px;
        margin: 8px 0;
    }
    
    .alert-exito {
        background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
        border-left: 4px solid #16a34a;
        padding: 16px;
        border-radius: 8px;
        margin: 8px 0;
    }
    
    .alert-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    
    .alert-time {
        font-size: 0.85em;
        opacity: 0.7;
    }
</style>
""", unsafe_allow_html=True)

# --- OBTENER ALERTAS DE LA BD ---
try:
    alertas_df = conn.query("""
        SELECT 
            a.id,
            a.timestamp,
            a.tipo_alerta,
            a.mensaje,
            a.leida,
            d.numero_serie as dispositivo,
            p.nombre || ' ' || p.apellido_paterno as paciente,
            m.tipo_medicion,
            m.valor,
            m.unidad_medida
        FROM public.alertas a
        LEFT JOIN public.mediciones m ON a.medicion_id = m.id
        LEFT JOIN public.dispositivos d ON m.dispositivo_id = d.id
        LEFT JOIN public.pacientes p ON d.paciente_id = p.id
        ORDER BY a.timestamp DESC
        LIMIT 200
    """, ttl="10s")
except Exception as e:
    st.error(f"Error al cargar alertas: {e}")
    alertas_df = pd.DataFrame()

if alertas_df.empty:
    st.info("✅ No hay alertas en el sistema")
else:
    # --- TABS ---
    tab_todas, tab_criticas, tab_advertencias, tab_informativas, tab_resueltas = st.tabs([
        "📋 Todas",
        "🚨 Críticas",
        "⚠️ Advertencias",
        "ℹ️ Informativas",
        "✅ Resueltas"
    ])
    
    # --- FUNCIONES AUXILIARES ---
    def renderizar_alerta(row):
        """Renderiza una tarjeta de alerta con su tipo de color"""
        timestamp = pd.to_datetime(row['timestamp'])
        tiempo_relativo = (datetime.now() - timestamp).total_seconds()
        
        if tiempo_relativo < 60:
            tiempo_str = "hace unos segundos"
        elif tiempo_relativo < 3600:
            tiempo_str = f"hace {int(tiempo_relativo // 60)} minutos"
        elif tiempo_relativo < 86400:
            tiempo_str = f"hace {int(tiempo_relativo // 3600)} horas"
        else:
            tiempo_str = timestamp.strftime("%d/%m/%Y %H:%M")
        
        tipo_alerta = str(row['tipo_alerta']).lower()
        
        # Seleccionar clase CSS y ícono
        if 'critica' in tipo_alerta or 'paro' in tipo_alerta or 'arritmia' in tipo_alerta:
            css_class = 'alert-critica'
            icono = "🚨"
        elif 'advertencia' in tipo_alerta or 'elevada' in tipo_alerta or 'baja' in tipo_alerta:
            css_class = 'alert-advertencia'
            icono = "⚠️"
        elif 'info' in tipo_alerta or 'normal' in tipo_alerta:
            css_class = 'alert-info'
            icono = "ℹ️"
        else:
            css_class = 'alert-exito'
            icono = "✅"
        
        # Obtener valor de medición si existe
        valor_str = ""
        if pd.notna(row.get('valor')):
            valor_str = f" • <b>{row['valor']:.1f} {row.get('unidad_medida', '')}</b>"
        
        html = f"""
        <div class="{css_class}">
            <div class="alert-header">
                <div>
                    <b>{icono} {row['tipo_alerta']}</b>
                    {valor_str}
                </div>
                <span class="alert-time">{tiempo_str}</span>
            </div>
            <p style="margin: 8px 0 0 0;">{row['mensaje']}</p>
            <small style="opacity: 0.7;">
                📱 {row.get('dispositivo', 'N/A')} • 👤 {row.get('paciente', 'N/A')} • 📊 {row.get('tipo_medicion', 'N/A')}
            </small>
        </div>
        """
        return html
    
    # --- TAB 1: TODAS LAS ALERTAS ---
    with tab_todas:
        if len(alertas_df) == 0:
            st.info("No hay alertas")
        else:
            # Resumen estadístico
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                criticas = len(alertas_df[alertas_df['tipo_alerta'].str.lower().str.contains('critica|paro|arritmia', na=False)])
                st.metric("🚨 Críticas", criticas)
            with col2:
                advertencias = len(alertas_df[alertas_df['tipo_alerta'].str.lower().str.contains('advertencia|elevada|baja', na=False)])
                st.metric("⚠️ Advertencias", advertencias)
            with col3:
                info = len(alertas_df[~alertas_df['tipo_alerta'].str.lower().str.contains('critica|paro|arritmia|advertencia|elevada|baja', na=False)])
                st.metric("ℹ️ Informativas", info)
            with col4:
                leidas = len(alertas_df[alertas_df['leida'] == True])
                st.metric("✅ Leídas", leidas)
            
            st.markdown("---")
            
            # Mostrar todas las alertas
            for _, row in alertas_df.iterrows():
                st.markdown(renderizar_alerta(row), unsafe_allow_html=True)
    
    # --- TAB 2: ALERTAS CRÍTICAS ---
    with tab_criticas:
        criticas_df = alertas_df[alertas_df['tipo_alerta'].str.lower().str.contains('critica|paro|arritmia', na=False)]
        
        if len(criticas_df) == 0:
            st.success("✅ No hay alertas críticas")
        else:
            st.warning(f"⚠️ {len(criticas_df)} alertas críticas detectadas")
            st.markdown("---")
            
            for _, row in criticas_df.iterrows():
                st.markdown(renderizar_alerta(row), unsafe_allow_html=True)
    
    # --- TAB 3: ADVERTENCIAS ---
    with tab_advertencias:
        advertencias_df = alertas_df[alertas_df['tipo_alerta'].str.lower().str.contains('advertencia|elevada|baja', na=False)]
        
        if len(advertencias_df) == 0:
            st.success("✅ No hay advertencias")
        else:
            st.info(f"ℹ️ {len(advertencias_df)} advertencias en el sistema")
            st.markdown("---")
            
            for _, row in advertencias_df.iterrows():
                st.markdown(renderizar_alerta(row), unsafe_allow_html=True)
    
    # --- TAB 4: INFORMATIVAS ---
    with tab_informativas:
        info_df = alertas_df[~alertas_df['tipo_alerta'].str.lower().str.contains('critica|paro|arritmia|advertencia|elevada|baja', na=False)]
        
        if len(info_df) == 0:
            st.info("No hay alertas informativas")
        else:
            st.markdown(f"ℹ️ {len(info_df)} notificaciones informativas")
            st.markdown("---")
            
            for _, row in info_df.iterrows():
                st.markdown(renderizar_alerta(row), unsafe_allow_html=True)
    
    # --- TAB 5: RESUELTAS ---
    with tab_resueltas:
        resueltas_df = alertas_df[alertas_df['leida'] == True]
        
        if len(resueltas_df) == 0:
            st.info("No hay alertas marcadas como leídas")
        else:
            st.success(f"✅ {len(resueltas_df)} alertas leídas")
            st.markdown("---")
            
            for _, row in resueltas_df.iterrows():
                st.markdown(renderizar_alerta(row), unsafe_allow_html=True)