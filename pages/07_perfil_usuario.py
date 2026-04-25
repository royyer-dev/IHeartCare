import streamlit as st
from sqlalchemy import text
from core.auth import require_auth
from core.sidebar import render_sidebar
from core.theme import apply_global_theme

st.set_page_config(page_title="Mi Perfil", page_icon=None, layout="wide")

require_auth(allowed_roles=['paciente'])
render_sidebar()
apply_global_theme()
st.title("Mi Perfil Médico")
st.markdown("---")

try:
    conn = st.connection("postgresql", type="sql")
    with conn.session as s:
        query = text("""
            SELECT p.*, d.modelo, d.mac_address, 
                   CONCAT(pm.nombre, ' ', pm.apellido_paterno) as medico_asignado
            FROM public.pacientes p
            LEFT JOIN public.dispositivos d ON d.paciente_id = p.id
            LEFT JOIN public.pacientes_medicos rel ON rel.paciente_id = p.id
            LEFT JOIN public.personal_medico pm ON pm.id = rel.medico_id
            WHERE p.id = :paciente_id
        """)
        datos = s.execute(query, {"paciente_id": st.session_state.paciente_id}).fetchone()
        
        if datos:
            col1, col2 = st.columns(2)
            with col1:
                with st.container(border=True):
                    st.subheader("Información Personal")
                    st.write(f"**Nombre:** {datos.nombre} {datos.apellido_paterno} {datos.apellido_materno}")
                    st.write(f"**CURP:** {datos.curp}")
                    st.write(f"**Fecha de Nacimiento:** {datos.fecha_nacimiento}")
                    st.write(f"**Sexo:** {datos.sexo}")
                    st.write(f"**Email:** {datos.email}")
                    st.write(f"**Teléfono:** {datos.telefono}")
            
            with col2:
                with st.container(border=True):
                    st.subheader("Dispositivo Asignado")
                    if datos.modelo:
                        st.write(f"**Modelo:** {datos.modelo}")
                        st.write(f"**MAC Address:** {datos.mac_address}")
                    else:
                        st.info("No tienes dispositivo asignado")
                
                with st.container(border=True):
                    st.subheader("Médico Asignado")
                    if datos.medico_asignado:
                        st.write(f"**Dr(a). {datos.medico_asignado}**")
                    else:
                        st.info("No tienes médico asignado")
        
except Exception as e:
    st.error(f"Error: {e}")