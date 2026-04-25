import streamlit as st
import pandas as pd
from datetime import date
from sqlalchemy import text
from core.auth import require_auth
from core.sidebar import render_sidebar
from core.theme import apply_global_theme
from utils import breadcrumb_nav

require_auth(allowed_roles=['medico'])
render_sidebar()
apply_global_theme()

st.set_page_config(page_title="Mis Pacientes", page_icon="👥", layout="wide")

# --- BREADCRUMBS ---
breadcrumb_nav(["Home", "Gestión Médica", "Mis Pacientes"])

# --- CONEXIÓN A LA BASE DE DATOS ---
try:
    conn = st.connection("postgresql", type="sql")
except Exception:
    st.error("No se pudo establecer conexión con la base de datos.")
    st.stop()

# --- ESTILOS CSS ---
st.markdown("""
<style>
    .patient-card {
        background: linear-gradient(135deg, #f8f9ff 0%, #f0f4ff 100%);
        border-left: 4px solid #0066CC;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 12px;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .patient-card:hover {
        box-shadow: 0 8px 16px rgba(0, 102, 204, 0.15);
        transform: translateX(4px);
        border-left-color: #004499;
    }
    
    .metric-value {
        font-weight: 600;
        color: #0066CC;
    }
    
    .status-healthy {
        color: #10b981;
    }
    
    .status-alert {
        color: #ef4444;
    }
</style>
""", unsafe_allow_html=True)

st.title("👥 Mis Pacientes Asignados")
st.markdown("---")

# Obtener datos de pacientes asignados al médico actual
try:
    pacientes_df = conn.query(f"""
        SELECT p.id, p.nombre, p.apellido_paterno, p.apellido_materno, 
               p.email, p.telefono, p.diagnostico
        FROM public.pacientes p
        INNER JOIN public.pacientes_medicos pm ON p.id = pm.paciente_id
        WHERE pm.medico_id = :medico_id
        ORDER BY p.nombre
    """, params={"medico_id": st.session_state.medico_id}, ttl="10s")
except Exception as e:
    st.error(f"Error al cargar pacientes: {e}")
    pacientes_df = pd.DataFrame()

if not pacientes_df.empty:
    # --- BUSCADOR ---
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input(
            "🔍 Buscar paciente por nombre",
            placeholder="Ingresa el nombre del paciente...",
            key="search_paciente"
        )
    with col2:
        st.write("")
        if st.button("🔄 Refrescar", use_container_width=True):
            st.rerun()
    
    st.write("")
    
    # Filtrar pacientes según búsqueda
    if search_term:
        filtered_df = pacientes_df[
            pacientes_df['nombre'].str.contains(search_term, case=False, na=False) |
            pacientes_df['apellido_paterno'].str.contains(search_term, case=False, na=False) |
            pacientes_df['apellido_materno'].str.contains(search_term, case=False, na=False)
        ]
    else:
        filtered_df = pacientes_df
    
    if filtered_df.empty:
        st.info("No se encontraron pacientes con ese nombre.")
    else:
        # --- LISTA DE PACIENTES ---
        st.subheader(f"Pacientes Bajo mi Cuidado ({len(filtered_df)})")
        
        for idx, paciente in filtered_df.iterrows():
            paciente_id = paciente['id']
            nombre_completo = f"{paciente['nombre']} {paciente['apellido_paterno']} {paciente.get('apellido_materno', '')}".strip()
            
            # Obtener métricas recientes del paciente
            try:
                with conn.session as s:
                    metrics_query = text("""
                        SELECT 
                            m.tipo_medicion,
                            m.valor,
                            m.unidad_medida,
                            m.timestamp
                        FROM public.mediciones m
                        JOIN public.dispositivos d ON m.dispositivo_id = d.id
                        WHERE d.paciente_id = :pid
                        ORDER BY m.timestamp DESC
                        LIMIT 10
                    """)
                    
                    metrics = s.execute(metrics_query, {'pid': paciente_id}).fetchall()
                
                # Agrupar métricas por tipo
                last_metrics = {}
                for m in metrics:
                    if m[0] not in last_metrics:
                        last_metrics[m[0]] = (m[1], m[2], m[3])
                
                # Obtener alertas pendientes
                alertas_query_result = conn.query(
                    f"""SELECT COUNT(*) as alertas FROM public.alertas a 
                       WHERE a.medicion_id IN (SELECT id FROM public.mediciones 
                                               WHERE dispositivo_id IN (SELECT id FROM public.dispositivos WHERE paciente_id = {paciente_id}))
                       AND a.leida = false""",
                    ttl="5s"
                )
                alertas = alertas_query_result.iloc[0]['alertas'] if not alertas_query_result.empty else 0
                
            except Exception as e:
                last_metrics = {}
                alertas = 0
            
            # Estado del paciente
            estado = "🟢 Estable"
            color_estado = "status-healthy"
            if alertas > 0:
                estado = f"🔴 {alertas} Alerta(s)"
                color_estado = "status-alert"
            
            # Card del paciente
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.markdown(f"### {nombre_completo}")
                    if paciente.get('diagnostico'):
                        st.caption(f"📋 {paciente['diagnostico']}")
                    if paciente.get('email'):
                        st.caption(f"📧 {paciente['email']}")
                
                with col2:
                    st.write("**Últimas Métricas:**")
                    if last_metrics:
                        cols = st.columns(len(last_metrics))
                        for col_idx, (tipo, (valor, unidad, timestamp)) in enumerate(list(last_metrics.items())[:3]):
                            with cols[col_idx]:
                                st.metric(
                                    label=tipo.replace('_', ' ').title(),
                                    value=f"{valor} {unidad}",
                                )
                    else:
                        st.caption("Sin mediciones registradas")
                
                with col3:
                    st.write("")
                    st.markdown(f"<div class='{color_estado}'>{estado}</div>", unsafe_allow_html=True)
                
                # Expandir para ver detalles
                st.write("")
                if st.button(f"📊 Ver Detalles", key=f"btn_detalles_{paciente_id}"):
                    st.session_state[f"expand_{paciente_id}"] = True
                
                # Mostrar detalles si está expandido
                if st.session_state.get(f"expand_{paciente_id}", False):
                    st.markdown("---")
                    st.subheader(f"Métricas Detalladas - {nombre_completo}")
                    
                    # Obtener historial completo
                    try:
                        with conn.session as s:
                            historial_query = text("""
                                SELECT 
                                    m.tipo_medicion,
                                    m.valor,
                                    m.unidad_medida,
                                    m.timestamp
                                FROM public.mediciones m
                                JOIN public.dispositivos d ON m.dispositivo_id = d.id
                                WHERE d.paciente_id = :pid
                                ORDER BY m.timestamp DESC
                                LIMIT 100
                            """)
                            
                            historial = s.execute(historial_query, {'pid': paciente_id}).fetchall()
                        
                        if historial:
                            # Convertir a dataframe para mejor visualización
                            historial_df = pd.DataFrame(
                                historial,
                                columns=['Tipo de Medición', 'Valor', 'Unidad', 'Fecha/Hora']
                            )
                            
                            # Agrupar por tipo de medición
                            for tipo_med in historial_df['Tipo de Medición'].unique():
                                st.markdown(f"#### {tipo_med.replace('_', ' ').title()}")
                                tipo_df = historial_df[historial_df['Tipo de Medición'] == tipo_med]
                                
                                col1, col2 = st.columns([2, 1])
                                with col1:
                                    st.dataframe(
                                        tipo_df[['Valor', 'Unidad', 'Fecha/Hora']],
                                        use_container_width=True,
                                        hide_index=True
                                    )
                                with col2:
                                    valores = pd.to_numeric(tipo_df['Valor'], errors='coerce')
                                    if not valores.empty:
                                        st.metric("Promedio", f"{valores.mean():.2f}")
                                        st.metric("Máximo", f"{valores.max():.2f}")
                                        st.metric("Mínimo", f"{valores.min():.2f}")
                        else:
                            st.info("Sin historial de mediciones para este paciente.")
                    
                    except Exception as e:
                        st.error(f"Error al cargar historial: {e}")
                    
                    st.write("")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"👁️ Ver en Vivo", key=f"btn_vivo_{paciente_id}"):
                            st.info("Funcionalidad de visualización en vivo disponible en la sección correspondiente")
                    with col2:
                        if st.button(f"❌ Cerrar Detalles", key=f"btn_cerrar_{paciente_id}"):
                            st.session_state[f"expand_{paciente_id}"] = False
                            st.rerun()
else:
    st.info("Aún no tienes pacientes asignados")