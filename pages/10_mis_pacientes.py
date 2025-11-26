import streamlit as st
import pandas as pd
from sqlalchemy import text
from auth import require_auth

require_auth(allowed_roles=['medico'])

st.set_page_config(page_title="Mis Pacientes", page_icon="👥", layout="wide")
st.title("👥 Mis Pacientes Asignados")
st.markdown("---")

try:
    conn = st.connection("postgresql", type="sql")
    with conn.session as s:
        query = text("""
            SELECT 
                p.id,
                CONCAT(p.nombre, ' ', p.apellido_paterno, ' ', p.apellido_materno) as nombre_completo,
                p.curp,
                p.email,
                p.telefono,
                d.modelo as dispositivo,
                CASE WHEN m.activo THEN 'Activo' ELSE 'Inactivo' END as estado_monitoreo,
                m.fecha_inicio as inicio_monitoreo
            FROM public.pacientes p
            INNER JOIN public.pacientes_medicos pm ON p.id = pm.paciente_id
            LEFT JOIN public.dispositivos d ON d.paciente_id = p.id
            LEFT JOIN public.monitoreos m ON m.paciente_id = p.id AND m.activo = true
            WHERE pm.medico_id = :medico_id
            ORDER BY p.apellido_paterno, p.apellido_materno, p.nombre
        """)
        df = pd.read_sql(query, s.connection(), params={"medico_id": st.session_state.medico_id})
    
    if df.empty:
        st.info("📭 Aún no tienes pacientes asignados")
    else:
        st.success(f"Total de pacientes: **{len(df)}**")
        
        # Búsqueda
        buscar = st.text_input("🔍 Buscar paciente por nombre o CURP", "")
        if buscar:
            df = df[df['nombre_completo'].str.contains(buscar, case=False, na=False) | 
                    df['curp'].str.contains(buscar, case=False, na=False)]
        
        # Tabla con formato
        st.dataframe(
            df,
            column_config={
                "id": "ID",
                "nombre_completo": "Nombre Completo",
                "curp": "CURP",
                "email": "Email",
                "telefono": "Teléfono",
                "dispositivo": "Dispositivo",
                "estado_monitoreo": st.column_config.TextColumn(
                    "Estado",
                    help="Estado del monitoreo"
                ),
                "inicio_monitoreo": "Inicio Monitoreo"
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Seleccionar paciente para ver detalles
        st.markdown("---")
        st.subheader("📊 Ver Detalles de Paciente")
        paciente_seleccionado = st.selectbox(
            "Selecciona un paciente:",
            options=df['id'].tolist(),
            format_func=lambda x: df[df['id']==x]['nombre_completo'].iloc[0]
        )
        
        if st.button("Ver Dashboard del Paciente", type="primary"):
            st.switch_page("pages/5_dashboard_visualizacion.py")
        
except Exception as e:
    st.error(f"Error al cargar pacientes: {e}")