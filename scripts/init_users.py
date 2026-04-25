"""
Script para inicializar usuarios de prueba en el sistema I-HeartCare
Ejecutar una sola vez para crear usuarios de prueba para cada rol.

Uso: streamlit run scripts/init_users.py  (desde la raíz del proyecto)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from sqlalchemy import text
from core.auth import hash_password
from scripts.generate_demo_data import generate_demo_data

def init_test_users():
    """Crea usuarios de prueba para cada rol del sistema."""
    
    st.title("🔧 Inicialización de Usuarios de Prueba")
    st.warning("⚠️ Este script creará usuarios de prueba. Ejecutar solo una vez.")
    
    if st.button("🚀 Crear Usuarios de Prueba", type="primary"):
        try:
            conn = st.connection("postgresql", type="sql")
            with conn.session as s:
                # 1. CREAR USUARIO ADMINISTRADOR
                st.info("Creando usuario administrador...")
                admin_query = text("""
                    INSERT INTO public.usuarios (username, password_hash, rol, activo)
                    VALUES (:username, :password_hash, 'administrador', true)
                    ON CONFLICT (username) DO NOTHING
                    RETURNING id
                """)
                admin_result = s.execute(admin_query, {
                    "username": "admin",
                    "password_hash": hash_password("admin123")
                }).fetchone()
                
                if admin_result:
                    st.success("✅ Usuario administrador creado: **admin** / **admin123**")
                else:
                    st.info("ℹ️ Usuario administrador ya existe")
                
                # 2. CREAR MÉDICO DE PRUEBA
                st.info("Creando médico de prueba...")
                
                # Primero crear el registro en personal_medico
                medico_data_query = text("""
                    INSERT INTO public.personal_medico 
                    (nombre, apellido_paterno, apellido_materno, especialidad, cedula_profesional, 
                     cedula_especialidad, universidad, email)
                    VALUES ('Juan', 'Pérez', 'García', 'Cardiología', '12345678', 
                            '87654321', 'UNAM', 'juan.perez@hospital.com')
                    ON CONFLICT DO NOTHING
                    RETURNING id
                """)
                medico_data = s.execute(medico_data_query).fetchone()
                
                if medico_data:
                    medico_id = medico_data[0]
                    
                    # Crear usuario para el médico
                    medico_user_query = text("""
                        INSERT INTO public.usuarios (username, password_hash, rol, activo)
                        VALUES (:username, :password_hash, 'medico', true)
                        ON CONFLICT (username) DO NOTHING
                        RETURNING id
                    """)
                    medico_user = s.execute(medico_user_query, {
                        "username": "doctor",
                        "password_hash": hash_password("doctor123")
                    }).fetchone()
                    
                    if medico_user:
                        user_id = medico_user[0]
                        
                        # Vincular usuario con médico
                        link_query = text("""
                            UPDATE public.personal_medico 
                            SET usuario_id = :user_id 
                            WHERE id = :medico_id
                        """)
                        s.execute(link_query, {"user_id": user_id, "medico_id": medico_id})
                        st.success("✅ Usuario médico creado: **doctor** / **doctor123**")
                    else:
                        st.info("ℹ️ Usuario médico ya existe")
                else:
                    st.info("ℹ️ Médico de prueba ya existe")
                
                # 3. CREAR PACIENTE DE PRUEBA
                st.info("Creando paciente de prueba...")
                
                # Primero crear el registro en pacientes
                paciente_data_query = text("""
                    INSERT INTO public.pacientes 
                    (nombre, apellido_paterno, apellido_materno, fecha_nacimiento, curp, nss, 
                     sexo, estado_civil, domicilio, email, telefono)
                    VALUES ('María', 'López', 'Martínez', '1990-05-15', 'LOMM900515MDFPRT01', 
                            '12345678901', 'Femenino', 'Soltera', 'Calle Principal #123', 
                            'maria.lopez@email.com', '5551234567')
                    ON CONFLICT DO NOTHING
                    RETURNING id
                """)
                paciente_data = s.execute(paciente_data_query).fetchone()
                
                if paciente_data:
                    paciente_id = paciente_data[0]
                    
                    # Crear usuario para el paciente
                    paciente_user_query = text("""
                        INSERT INTO public.usuarios (username, password_hash, rol, activo)
                        VALUES (:username, :password_hash, 'paciente', true)
                        ON CONFLICT (username) DO NOTHING
                        RETURNING id
                    """)
                    paciente_user = s.execute(paciente_user_query, {
                        "username": "paciente",
                        "password_hash": hash_password("paciente123")
                    }).fetchone()
                    
                    if paciente_user:
                        user_id = paciente_user[0]
                        
                        # Vincular usuario con paciente
                        link_query = text("""
                            UPDATE public.pacientes 
                            SET usuario_id = :user_id 
                            WHERE id = :paciente_id
                        """)
                        s.execute(link_query, {"user_id": user_id, "paciente_id": paciente_id})
                        st.success("✅ Usuario paciente creado: **paciente** / **paciente123**")
                    else:
                        st.info("ℹ️ Usuario paciente ya existe")
                else:
                    st.info("ℹ️ Paciente de prueba ya existe")
                
                # Confirmar cambios
                s.commit()
                
                st.markdown("---")
                st.success("🎉 ¡Proceso completado!")
                
                # Mostrar resumen
                st.markdown("""
                ### 📋 Credenciales de Acceso
                
                #### 🔧 Administrador
                - **Usuario:** `admin`
                - **Contraseña:** `admin123`
                - **Permisos:** Acceso completo al sistema
                
                #### 👨‍⚕️ Médico
                - **Usuario:** `doctor`
                - **Contraseña:** `doctor123`
                - **Permisos:** Gestión de pacientes asignados
                
                #### 👤 Paciente
                - **Usuario:** `paciente`
                - **Contraseña:** `paciente123`
                - **Permisos:** Ver su propia información médica
                
                ---
                **⚠️ IMPORTANTE:** Cambia estas contraseñas en producción.
                """)
                
                # Adicional: Generar pacientes demo
                st.markdown("---")
                st.markdown("## 📊 Paso 2: Generar Datos Demo (Opcional)")
                st.info("A continuación puede generar 10 pacientes simulados con data realista para testing.")
                
                generate_demo_data()
                
        except Exception as e:
            st.error(f"❌ Error al crear usuarios: {e}")
            st.exception(e)

if __name__ == "__main__":
    st.set_page_config(
        page_title="Inicializar Usuarios",
        page_icon=None,
        layout="wide"
    )
    init_test_users()
