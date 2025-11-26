import streamlit as st
import pandas as pd
from sqlalchemy import text
from auth import require_auth, registrar_usuario_medico  # ← AGREGAR

# --- PROTECCIÓN DE RUTA ---
require_auth(allowed_roles=['administrador'])  # ← AGREGAR ESTA LÍNEA

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Gestión de Personal Médico", page_icon="👨‍⚕️", layout="wide")
st.title("👨‍⚕️ Gestión de Personal Médico")
st.markdown("---")

# --- CONEXIÓN A LA BASE DE DATOS ---
try:
    conn = st.connection("postgresql", type="sql")
except Exception:
    st.error("No se pudo establecer conexión con la base de datos.")
    st.stop()

# --- PESTAÑAS ---
tab1, tab2 = st.tabs(["📋 Registrar Nuevo Profesional", "📄 Ver Personal Registrado"])

with tab1:
    with st.container(border=True):
        st.header("Formulario de Registro Profesional")
        with st.form("registro_medico_form", clear_on_submit=True):
            st.subheader("Información Profesional")
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre(s)", placeholder="Ej. Ana")
                apellido_paterno = st.text_input("Apellido Paterno", placeholder="Ej. López")
                especialidad = st.text_input("Especialidad", placeholder="Ej. Cardiología")
                cedula_profesional = st.text_input("Cédula Profesional (Licenciatura)")
            with col2:
                apellido_materno = st.text_input("Apellido Materno", placeholder="Ej. Martínez")
                universidad = st.text_input("Universidad de Egreso")
                cedula_especialidad = st.text_input("Cédula de Especialidad (si aplica)")
            
            st.subheader("Información de Contacto")
            email = st.text_input("Correo Electrónico", placeholder="ejemplo@correo.com")
            
            # AGREGAR NUEVA SECCIÓN ANTES DEL BOTÓN SUBMIT:
            st.subheader("Credenciales de Acceso (Opcional)")
            st.info("Si desea crear un usuario para este médico, complete los siguientes campos:")
            crear_usuario = st.checkbox("Crear usuario para acceso al sistema")
            
            username_medico = None
            password_medico = None
            
            if crear_usuario:
                col1, col2 = st.columns(2)
                with col1:
                    username_medico = st.text_input("Nombre de Usuario", placeholder="Ej. dr.lopez")
                with col2:
                    password_medico = st.text_input("Contraseña", type="password", placeholder="Mínimo 6 caracteres")
            
            submit_button = st.form_submit_button(label="Registrar Profesional", use_container_width=True)

            if submit_button:
                if not all([nombre, apellido_paterno, especialidad, cedula_profesional, email]):
                    st.warning("Por favor, completa todos los campos obligatorios.")
                else:
                    try:
                        with conn.session as s:
                            sql = """
                                INSERT INTO public.personal_medico (nombre, apellido_paterno, apellido_materno, especialidad, cedula_profesional, cedula_especialidad, universidad, email)
                                VALUES (:nombre, :paterno, :materno, :especialidad, :ced_prof, :ced_esp, :uni, :email)
                                RETURNING id
                            """
                            medico_id = s.execute(text(sql), params={
                                "nombre": nombre, "paterno": apellido_paterno, "materno": apellido_materno,
                                "especialidad": especialidad, "ced_prof": cedula_profesional, 
                                "ced_esp": cedula_especialidad, "uni": universidad, "email": email
                            }).fetchone()[0]
                            s.commit()
                        
                        st.success("¡Profesional registrado exitosamente!")
                        
                        # CREAR USUARIO SI SE SOLICITÓ
                        if crear_usuario and username_medico and password_medico:
                            if registrar_usuario_medico(username_medico, password_medico, medico_id):
                                st.success("✅ Usuario médico creado exitosamente")
                            else:
                                st.warning("⚠️ Médico registrado pero no se pudo crear el usuario")
                                
                    except Exception as e:
                        st.error(f"Ocurrió un error al registrar: {e}")

with tab2:
    with st.container(border=True):
        st.header("Listado de Personal Médico")
        try:
            df_medicos = conn.query('SELECT * FROM public.personal_medico ORDER BY id;', ttl="10s")
            if df_medicos.empty:
                st.info("No hay personal médico registrado actualmente.")
            else:
                st.dataframe(df_medicos, use_container_width=True, hide_index=True)
                if st.button("Refrescar personal"):
                    st.rerun()
        except Exception as e:
            st.error(f"Ocurrió un error al cargar: {e}")

