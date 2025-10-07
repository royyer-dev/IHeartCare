import streamlit as st

st.set_page_config(
    page_title="I-HeartCare - Inicio",
    page_icon="🩺",
    layout="wide"
)

# --- UI/UX Mejoras ---
# Usamos un contenedor principal para el contenido
with st.container():
    st.title("🩺 Bienvenido al Sistema I-HeartCare")
    st.markdown("---")
    
    st.header("Sistema Inteligente para la Detección Oportuna de Afecciones Cardíacas")
    
    # Usamos st.info para resaltar la descripción
    st.info("""
    Esta plataforma permite la gestión integral de la información clínica para el monitoreo de pacientes. 
    **Utilice la barra de navegación a la izquierda para acceder a las diferentes secciones.**
    """)

    # Columnas para organizar los módulos y hacerlos más visuales
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("👤 Módulo de Pacientes")
        st.markdown("""
        - **Registro:** Dar de alta a nuevos pacientes en el sistema.
        - **Consulta:** Visualizar y buscar el listado completo de pacientes.
        """)

    with col2:
        st.subheader("👨‍⚕️ Módulo de Personal Médico")
        st.markdown("""
        - **Registro:** Añadir nuevos profesionales de la salud.
        - **Consulta:** Visualizar el directorio de personal médico autorizado.
        """)