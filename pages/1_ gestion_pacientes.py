import streamlit as st
import pandas as pd
from datetime import date
from sqlalchemy import text
from auth import require_auth  # ← AGREGAR ESTA LÍNEA

# --- PROTECCIÓN DE RUTA ---
require_auth(allowed_roles=['administrador'])  # ← AGREGAR ESTA LÍNEA

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Gestión de Pacientes", page_icon="👤", layout="wide")
st.title("👤 Gestión de Pacientes")
st.markdown("---")

# --- CONEXIÓN A LA BASE DE DATOS ---
try:
    conn = st.connection("postgresql", type="sql")
except Exception:
    st.error("No se pudo establecer conexión con la base de datos.")
    st.stop()

# --- PESTAÑAS ---
tab1, tab2 = st.tabs(["📋 Registrar Nuevo Paciente", "📄 Ver Pacientes Registrados"])

# Pestaña para registrar
with tab1:
    with st.container(border=True): # Contenedor para el formulario
        st.header("Formulario de Registro")
        with st.form("registro_paciente_form", clear_on_submit=True):
            st.subheader("Información Personal")
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre(s)", placeholder="Ej. Juan")
                apellido_paterno = st.text_input("Apellido Paterno", placeholder="Ej. Pérez")
                fecha_nacimiento = st.date_input("Fecha de Nacimiento", min_value=date(1920, 1, 1))
                sexo = st.selectbox("Sexo", ["Masculino", "Femenino"], index=None, placeholder="Seleccione una opción")
            with col2:
                apellido_materno = st.text_input("Apellido Materno", placeholder="Ej. García")
                curp = st.text_input("CURP", max_chars=18, placeholder="18 caracteres")
                nss = st.text_input("NSS", max_chars=11, placeholder="11 dígitos")
                estado_civil = st.text_input("Estado Civil", placeholder="Ej. Soltero(a)")

            st.subheader("Información de Contacto")
            email = st.text_input("Correo Electrónico", placeholder="ejemplo@correo.com")
            telefono = st.text_input("Teléfono", placeholder="Ej. 312 123 4567")
            domicilio = st.text_area("Domicilio Completo", placeholder="Calle, número, colonia, C.P., ciudad...")

            submit_button = st.form_submit_button(label="Registrar Paciente", use_container_width=True)

            if submit_button:
                if not all([nombre, apellido_paterno, fecha_nacimiento, curp, email, sexo]):
                    st.warning("Por favor, completa todos los campos obligatorios.")
                else:
                    try:
                        with conn.session as s:
                            sql = """
                                INSERT INTO public.pacientes (nombre, apellido_paterno, apellido_materno, fecha_nacimiento, curp, nss, sexo, estado_civil, domicilio, email, telefono)
                                VALUES (:nombre, :paterno, :materno, :nacimiento, :curp, :nss, :sexo, :civil, :domicilio, :email, :telefono)
                            """
                            s.execute(text(sql), params={
                                "nombre": nombre, "paterno": apellido_paterno, "materno": apellido_materno,
                                "nacimiento": fecha_nacimiento, "curp": curp.upper(), "nss": nss, "sexo": sexo,
                                "civil": estado_civil, "domicilio": domicilio, "email": email, "telefono": telefono
                            })
                            s.commit()
                        st.success("¡Paciente registrado exitosamente!")
                    except Exception as e:
                        st.error(f"Ocurrió un error al registrar: {e}")

# Pestaña para visualizar
with tab2:
    with st.container(border=True): # Contenedor para la tabla
        st.header("Listado de Pacientes")
        try:
            df = conn.query('SELECT * FROM public.pacientes ORDER BY id;', ttl="10s")
            if df.empty:
                st.info("No hay pacientes registrados actualmente.")
            else:
                st.dataframe(df, use_container_width=True, hide_index=True)
                if st.button("Refrescar datos"):
                    st.rerun()
        except Exception as e:
            st.error(f"Ocurrió un error al cargar: {e}")

