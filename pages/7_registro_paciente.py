import streamlit as st
from datetime import date
from sqlalchemy import text
from auth import registrar_usuario_paciente

st.set_page_config(page_title="Registro de Paciente", page_icon="📝", layout="wide")
st.title("📝 Registro de Nuevo Paciente")
st.markdown("---")

try:
    conn = st.connection("postgresql", type="sql")
except Exception:
    st.error("No se pudo establecer conexión con la base de datos.")
    st.stop()

with st.form("registro_paciente_completo", clear_on_submit=True):
    st.subheader("1️⃣ Información Personal")
    col1, col2, col3 = st.columns(3)
    with col1:
        nombre = st.text_input("Nombre(s)*", placeholder="Ej. Juan")
    with col2:
        apellido_paterno = st.text_input("Apellido Paterno*", placeholder="Ej. Pérez")
    with col3:
        apellido_materno = st.text_input("Apellido Materno*", placeholder="Ej. García")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        fecha_nacimiento = st.date_input("Fecha de Nacimiento*", min_value=date(1900, 1, 1), max_value=date.today())
    with col2:
        sexo = st.selectbox("Sexo*", ["Masculino", "Femenino"])
    with col3:
        estado_civil = st.selectbox("Estado Civil*", ["Soltero(a)", "Casado(a)", "Viudo(a)", "Divorciado(a)", "Unión libre"])
    
    col1, col2 = st.columns(2)
    with col1:
        curp = st.text_input("CURP*", placeholder="18 caracteres", max_chars=18)
    with col2:
        nss = st.text_input("Número de Seguro Social", placeholder="11 dígitos", max_chars=11)
    
    st.subheader("2️⃣ Información de Contacto")
    email = st.text_input("Correo Electrónico*", placeholder="ejemplo@correo.com")
    telefono = st.text_input("Teléfono*", placeholder="Ej. 312 123 4567")
    domicilio = st.text_area("Domicilio Completo*", placeholder="Calle, número, colonia, C.P., ciudad...")
    
    st.subheader("3️⃣ Credenciales de Acceso")
    st.warning("⚠️ Estas credenciales te permitirán acceder a tu información médica.")
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("Nombre de Usuario*", placeholder="Ej. juan.perez")
    with col2:
        password = st.text_input("Contraseña*", type="password", placeholder="Mínimo 6 caracteres")
    
    password_confirm = st.text_input("Confirmar Contraseña*", type="password")
    
    submit = st.form_submit_button("Registrarse", use_container_width=True)
    
    if submit:
        if not all([nombre, apellido_paterno, apellido_materno, curp, email, telefono, domicilio, username, password]):
            st.error("❌ Por favor complete todos los campos obligatorios marcados con *")
        elif len(password) < 6:
            st.error("❌ La contraseña debe tener al menos 6 caracteres")
        elif password != password_confirm:
            st.error("❌ Las contraseñas no coinciden")
        else:
            try:
                with conn.session as s:
                    query_paciente = text("""
                        INSERT INTO public.pacientes 
                        (nombre, apellido_paterno, apellido_materno, fecha_nacimiento, 
                         curp, nss, sexo, estado_civil, domicilio, email, telefono)
                        VALUES (:nombre, :ap_paterno, :ap_materno, :fecha_nac, 
                                :curp, :nss, :sexo, :estado_civil, :domicilio, :email, :telefono)
                        RETURNING id
                    """)
                    paciente_id = s.execute(query_paciente, {
                        "nombre": nombre,
                        "ap_paterno": apellido_paterno,
                        "ap_materno": apellido_materno,
                        "fecha_nac": fecha_nacimiento,
                        "curp": curp.upper(),
                        "nss": nss if nss else None,
                        "sexo": sexo,
                        "estado_civil": estado_civil,
                        "domicilio": domicilio,
                        "email": email,
                        "telefono": telefono
                    }).fetchone()[0]
                    
                    s.commit()
                    
                    if registrar_usuario_paciente(username, password, paciente_id):
                        st.success("✅ Registro exitoso. Ya puedes iniciar sesión.")
                        st.balloons()
                        st.page_link("app.py", label="← Volver al inicio de sesión")
                    else:
                        st.error("❌ Error al crear las credenciales de acceso")
                        
            except Exception as e:
                st.error(f"❌ Error en el registro: {e}")