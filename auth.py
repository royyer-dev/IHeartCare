import streamlit as st
import bcrypt
from sqlalchemy import text

def hash_password(password: str) -> str:
    """Encripta una contraseña usando bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """Verifica si una contraseña coincide con su hash."""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def login_user(username: str, password: str):
    """Autentica un usuario y guarda su sesión."""
    try:
        conn = st.connection("postgresql", type="sql")
        with conn.session as s:
            query = text("""
                SELECT u.id, u.password_hash, u.username, u.rol, u.activo,
                       p.id as paciente_id, pm.id as medico_id
                FROM public.usuarios u
                LEFT JOIN public.pacientes p ON u.id = p.usuario_id
                LEFT JOIN public.personal_medico pm ON u.id = pm.usuario_id
                WHERE u.username = :username
            """)
            result = s.execute(query, {"username": username}).fetchone()
            
            if result and result.activo and verify_password(password, result.password_hash):
                st.session_state.authenticated = True
                st.session_state.user_id = result.id
                st.session_state.username = result.username
                st.session_state.rol = result.rol
                st.session_state.paciente_id = result.paciente_id
                st.session_state.medico_id = result.medico_id
                return True
            return False
    except Exception as e:
        st.error(f"Error de autenticación: {e}")
        return False

def logout_user():
    """Cierra la sesión del usuario."""
    for key in ['authenticated', 'user_id', 'username', 'rol', 'paciente_id', 'medico_id']:
        if key in st.session_state:
            del st.session_state[key]

def require_auth(allowed_roles=None):
    """Decorador para proteger páginas según rol."""
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.warning("⚠️ Debes iniciar sesión para acceder a esta página.")
        st.stop()
    
    if allowed_roles and st.session_state.rol not in allowed_roles:
        st.error("🚫 No tienes permisos para acceder a esta sección.")
        st.stop()

def registrar_usuario_paciente(username, password, paciente_id):
    """Registra un nuevo usuario tipo paciente."""
    try:
        conn = st.connection("postgresql", type="sql")
        with conn.session as s:
            query_user = text("""
                INSERT INTO public.usuarios (username, password_hash, rol)
                VALUES (:username, :password_hash, 'paciente')
                RETURNING id
            """)
            user_id = s.execute(query_user, {
                "username": username,
                "password_hash": hash_password(password)
            }).fetchone()[0]
            
            query_link = text("""
                UPDATE public.pacientes 
                SET usuario_id = :user_id 
                WHERE id = :paciente_id
            """)
            s.execute(query_link, {"user_id": user_id, "paciente_id": paciente_id})
            s.commit()
            return True
    except Exception as e:
        st.error(f"Error al registrar usuario: {e}")
        return False

def registrar_usuario_medico(username, password, medico_id):
    """Registra un nuevo usuario tipo médico."""
    try:
        conn = st.connection("postgresql", type="sql")
        with conn.session as s:
            query_user = text("""
                INSERT INTO public.usuarios (username, password_hash, rol)
                VALUES (:username, :password_hash, 'medico')
                RETURNING id
            """)
            user_id = s.execute(query_user, {
                "username": username,
                "password_hash": hash_password(password)
            }).fetchone()[0]
            
            query_link = text("""
                UPDATE public.personal_medico 
                SET usuario_id = :user_id 
                WHERE id = :medico_id
            """)
            s.execute(query_link, {"user_id": user_id, "medico_id": medico_id})
            s.commit()
            return True
    except Exception as e:
        st.error(f"Error al registrar usuario: {e}")
        return False