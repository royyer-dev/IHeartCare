"""
Página para inicializar usuarios de prueba
Ejecutar: streamlit run setup_users.py
"""

import streamlit as st
from sqlalchemy import text
import bcrypt
import os

st.set_page_config(page_title="Setup Usuarios", page_icon="🔧")

st.title("🔧 Configuración Inicial - Crear Usuarios de Prueba")

def hash_password(password: str) -> str:
    """Encripta una contraseña usando bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_test_users():
    """Crea usuarios de prueba"""
    try:
        conn = st.connection("postgresql", type="sql")
        
        test_users = [
            ('admin', 'admin123', 'administrador'),
            ('doctor', 'doctor123', 'medico'),
            ('paciente', 'paciente123', 'paciente'),
        ]
        
        with conn.session as s:
            created = []
            exists = []
            
            for username, password, rol in test_users:
                # Verificar si existe
                check = text("SELECT id FROM public.usuarios WHERE username = :username")
                result = s.execute(check, {'username': username}).fetchone()
                
                if result:
                    exists.append(f"✓ {username} ({rol})")
                else:
                    # Crear usuario
                    insert = text("""
                        INSERT INTO public.usuarios (username, password_hash, rol, activo)
                        VALUES (:username, :password_hash, :rol, true)
                    """)
                    s.execute(insert, {
                        'username': username,
                        'password_hash': hash_password(password),
                        'rol': rol
                    })
                    created.append(f"✓ {username} ({rol})")
            
            s.commit()
            
        return created, exists
    
    except Exception as e:
        return None, str(e)

# Mostrar información
st.info("""
Esta página configurará los usuarios de prueba para el sistema.
Los usuarios serán creados automáticamente en la base de datos.
""")

# Crear usuarios automáticamente
st.subheader("⚙️ Estado de Creación")
with st.spinner("Creando usuarios..."):
    created, exists = create_test_users()
    
    if isinstance(exists, str):
        st.error(f"Error: {exists}")
    else:
        if created:
            st.success("✅ Usuarios creados:")
            for user in created:
                st.success(user)
        
        if exists:
            st.info("ℹ️ Usuarios que ya existían:")
            for user in exists:
                st.info(user)

if created or exists:
    st.success("✅ ¡Configuración completada! Ahora puedes iniciar sesión en la aplicación principal.")

# Mostrar credenciales
st.divider()
st.subheader("📋 Credenciales de Acceso")

credentials = {
    "👨‍💼 Administrador": ("admin", "admin123"),
    "👨‍⚕️ Médico/Doctor": ("doctor", "doctor123"),
    "👤 Paciente": ("paciente", "paciente123"),
}

for rol, (user, pwd) in credentials.items():
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.code(user, language="text")
    with col2:
        st.code(pwd, language="text")
    with col3:
        st.write(rol)
