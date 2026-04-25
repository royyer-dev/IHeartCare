import streamlit as st
import pandas as pd
import time
from sqlalchemy import text
from core.auth import require_auth, hash_password
from core.sidebar import render_sidebar
from core.theme import apply_global_theme
from utils import breadcrumb_nav

# --- PROTECCIÓN DE RUTA ---
require_auth(allowed_roles=['administrador'])
render_sidebar()
apply_global_theme()

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Gestión de Personal Médico", page_icon="👨‍⚕️", layout="wide")

# --- BREADCRUMBS ---
breadcrumb_nav(["Home", "Administración", "Personal Médico"])

# --- CONEXIÓN A LA BASE DE DATOS ---
try:
    conn = st.connection("postgresql", type="sql")
except Exception:
    st.error("No se pudo establecer conexión con la base de datos.")
    st.stop()

# --- ESTILOS CSS ---
st.markdown("""
<style>
    .doctor-card {
        background: linear-gradient(135deg, #f8f9ff 0%, #f0f4ff 100%);
        border-left: 4px solid #8b5cf6;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 12px;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .doctor-card:hover {
        box-shadow: 0 8px 16px rgba(139, 92, 246, 0.15);
        transform: translateX(4px);
        border-left-color: #6d28d9;
    }
    
    .credential-box {
        background: #f3f4f6;
        border: 1px solid #d1d5db;
        padding: 12px;
        border-radius: 6px;
        font-family: monospace;
        font-size: 0.9em;
        margin: 8px 0;
    }
    
    .patient-assigned {
        background: #dbeafe;
        padding: 8px 12px;
        border-radius: 6px;
        margin: 4px 0;
        border-left: 3px solid #0284c7;
    }
</style>
""", unsafe_allow_html=True)

st.title("👨‍⚕️ Gestión de Personal Médico")
st.markdown("---")

# --- TABS ---
tab_listado, tab_registro, tab_editar = st.tabs(["👥 Ver Médicos", "➕ Registrar Nuevo", "✏️ Editar/Eliminar"])

# ==================== TAB 1: VER MÉDICOS ====================
with tab_listado:
    
    # Obtener datos de médicos
    try:
        medicos_df = conn.query(
            'SELECT id, nombre, apellido_paterno, apellido_materno, especialidad, cedula_profesional, email FROM public.personal_medico ORDER BY nombre;',
            ttl="10s"
        )
    except Exception as e:
        st.error(f"Error al cargar médicos: {e}")
        medicos_df = pd.DataFrame()
    
    if not medicos_df.empty:
        # --- BUSCADOR ---
        col1, col2 = st.columns([3, 1])
        with col1:
            search_term = st.text_input(
                "🔍 Buscar médico por nombre",
                placeholder="Ingresa el nombre del médico...",
                key="search_medico"
            )
        with col2:
            st.write("")
            if st.button("🔄 Refrescar", use_container_width=True):
                st.rerun()
        
        st.write("")
        
        # Filtrar médicos según búsqueda
        if search_term:
            filtered_df = medicos_df[
                medicos_df['nombre'].str.contains(search_term, case=False, na=False) |
                medicos_df['apellido_paterno'].str.contains(search_term, case=False, na=False) |
                medicos_df['apellido_materno'].str.contains(search_term, case=False, na=False)
            ]
        else:
            filtered_df = medicos_df
        
        if filtered_df.empty:
            st.info("No se encontraron médicos con ese nombre.")
        else:
            # --- LISTA DE MÉDICOS ---
            st.subheader(f"Médicos Registrados ({len(filtered_df)})")
            
            for idx, medico in filtered_df.iterrows():
                medico_id = medico['id']
                nombre_completo = f"Dr(a). {medico['nombre']} {medico['apellido_paterno']} {medico.get('apellido_materno', '')}".strip()
                
                # Obtener información del usuario (credenciales)
                try:
                    usuario_query = text('SELECT id, username FROM public.usuarios WHERE id IN (SELECT usuario_id FROM public.personal_medico WHERE id = :mid)')
                    usuario = conn.session.execute(usuario_query, {'mid': medico_id}).fetchone()
                    tiene_usuario = usuario is not None
                    username = usuario[1] if usuario else None
                except Exception as e:
                    tiene_usuario = False
                    username = None
                
                # Obtener pacientes asignados
                try:
                    pacientes_query = text("""
                        SELECT p.id, p.nombre, p.apellido_paterno, p.apellido_materno
                        FROM public.pacientes p
                        JOIN public.pacientes_medicos pm ON p.id = pm.paciente_id
                        WHERE pm.medico_id = :mid
                        ORDER BY p.nombre
                    """)
                    
                    pacientes_asignados = conn.session.execute(pacientes_query, {'mid': medico_id}).fetchall()
                    cantidad_pacientes = len(pacientes_asignados)
                
                except Exception as e:
                    pacientes_asignados = []
                    cantidad_pacientes = 0
                
                # Card del médico
                with st.container(border=True):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.markdown(f"### {nombre_completo}")
                        st.caption(f"🏥 {medico['especialidad']}")
                        st.caption(f"📧 {medico['email']}")
                    
                    with col2:
                        st.write("**Estado:**")
                        if tiene_usuario:
                            st.success(f"✅ Usuario activo: `{username}`")
                        else:
                            st.warning("⚠️ Sin credenciales de acceso")
                        st.caption(f"👥 {cantidad_pacientes} paciente(s) asignado(s)")
                    
                    with col3:
                        st.write("")
                        st.write("")
                        if st.button(f"📋 Detalles", key=f"btn_detalles_med_{medico_id}"):
                            st.session_state[f"expand_med_{medico_id}"] = True
                    
                    # Mostrar detalles si está expandido
                    if st.session_state.get(f"expand_med_{medico_id}", False):
                        st.markdown("---")
                        st.subheader("Información Detallada")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Datos Profesionales:**")
                            st.caption(f"Cédula Profesional: {medico['cedula_profesional']}")
                        with col2:
                            st.markdown("**Credenciales de Acceso:**")
                            if tiene_usuario:
                                st.markdown(f"""
                                <div class="credential-box">
                                Usuario: <b>{username}</b><br>
                                Estado: ✅ Activo
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.info("No tiene credenciales configuradas")
                        
                        st.markdown("**Pacientes Asignados:**")
                        if pacientes_asignados:
                            for pac in pacientes_asignados:
                                pac_nombre = f"{pac[1]} {pac[2]} {pac[3] or ''}".strip()
                                st.markdown(f"""
                                <div class="patient-assigned">
                                👤 {pac_nombre}
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.info("No tiene pacientes asignados")
                        
                        st.write("")
                        if st.button(f"❌ Cerrar Detalles", key=f"btn_cerrar_med_{medico_id}"):
                            st.session_state[f"expand_med_{medico_id}"] = False
                            st.rerun()
    else:
        st.info("No hay médicos registrados en el sistema.")

# ==================== TAB 2: REGISTRAR MÉDICO ====================
with tab_registro:
    st.subheader("➕ Registrar Nuevo Profesional Médico")
    
    with st.form("registro_medico_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Información Profesional**")
            nombre = st.text_input("Nombre(s)", placeholder="Ej. Ana")
            apellido_paterno = st.text_input("Apellido Paterno", placeholder="Ej. López")
            especialidad = st.text_input("Especialidad", placeholder="Ej. Cardiología")
            cedula_profesional = st.text_input("Cédula Profesional")
        
        with col2:
            st.markdown("**Información Adicional**")
            apellido_materno = st.text_input("Apellido Materno", placeholder="Ej. Martínez")
            cedula_especialidad = st.text_input("Cédula de Especialidad (opcional)")
            universidad = st.text_input("Universidad de Egreso", placeholder="Ej. UNAM")
            email = st.text_input("Correo Electrónico", placeholder="ejemplo@correo.com")
        
        st.markdown("**Credenciales de Acceso**")
        st.info("Configure un usuario y contraseña para que el médico pueda iniciar sesión")
        
        col1, col2 = st.columns(2)
        with col1:
            username_medico = st.text_input("Nombre de Usuario", placeholder="Ej. dr.lopez")
        with col2:
            password_medico = st.text_input("Contraseña", type="password", placeholder="Mínimo 6 caracteres")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            submit = st.form_submit_button("✅ Registrar", use_container_width=True, type="primary")
        
        if submit:
            if not all([nombre, apellido_paterno, especialidad, cedula_profesional, email, username_medico, password_medico]):
                st.warning("⚠️ Por favor, completa todos los campos obligatorios.")
            elif len(password_medico) < 6:
                st.warning("⚠️ La contraseña debe tener mínimo 6 caracteres.")
            else:
                try:
                    with conn.session as s:
                        # Insertar médico
                        medico_sql = text("""
                            INSERT INTO public.personal_medico 
                            (nombre, apellido_paterno, apellido_materno, especialidad, cedula_profesional, 
                             cedula_especialidad, universidad, email)
                            VALUES (:nombre, :paterno, :materno, :especialidad, :ced_prof, 
                                    :ced_esp, :uni, :email)
                            RETURNING id
                        """)
                        medico_id = s.execute(medico_sql, params={
                            "nombre": nombre,
                            "paterno": apellido_paterno,
                            "materno": apellido_materno,
                            "especialidad": especialidad,
                            "ced_prof": cedula_profesional,
                            "ced_esp": cedula_especialidad,
                            "uni": universidad,
                            "email": email
                        }).fetchone()[0]
                        
                        # Crear usuario para el médico
                        usuario_sql = text("""
                            INSERT INTO public.usuarios (username, password_hash, rol, activo)
                            VALUES (:username, :password_hash, 'medico', true)
                            RETURNING id
                        """)
                        usuario_id = s.execute(usuario_sql, params={
                            "username": username_medico,
                            "password_hash": hash_password(password_medico)
                        }).fetchone()[0]
                        
                        # Vincular usuario con médico
                        link_sql = text("""
                            UPDATE public.personal_medico 
                            SET usuario_id = :user_id 
                            WHERE id = :medico_id
                        """)
                        s.execute(link_sql, {"user_id": usuario_id, "medico_id": medico_id})
                        
                        s.commit()
                    
                    st.success("✅ ¡Médico registrado exitosamente!")
                    st.markdown(f"""
                    **Credenciales creadas:**
                    - Usuario: `{username_medico}`
                    - Contraseña: (configurada al momento)
                    
                    El médico puede iniciar sesión con estas credenciales.
                    """)
                except Exception as e:
                    st.error(f"❌ Error al registrar: {e}")

# ==================== TAB 3: EDITAR/ELIMINAR MÉDICO ====================
with tab_editar:
    st.subheader("✏️ Editar o Eliminar Médico")
    st.info("Solo administradores pueden editar o eliminar médicos.")
    
    # Verificar permiso de admin
    if st.session_state.get('user_role') != 'administrador':
        st.error("❌ Solo administradores tienen acceso a esta sección.")
        st.stop()
    
    # Obtener lista de médicos activos
    try:
        medicos_activos = conn.query(
            'SELECT id, nombre, apellido_paterno, apellido_materno FROM public.personal_medico WHERE activo = true ORDER BY nombre;',
            ttl="10s"
        )
    except Exception as e:
        st.error(f"Error al cargar médicos: {e}")
        medicos_activos = pd.DataFrame()
    
    if not medicos_activos.empty:
        # Selector de médico
        medicos_activos['nombre_completo'] = (
            medicos_activos['nombre'] + ' ' + 
            medicos_activos['apellido_paterno'] + ' ' +
            medicos_activos['apellido_materno'].fillna('')
        ).str.strip()
        
        medico_seleccionado = st.selectbox(
            "Selecciona un médico",
            options=medicos_activos['id'].tolist(),
            format_func=lambda x: medicos_activos[medicos_activos['id'] == x]['nombre_completo'].values[0],
            key="edit_medico_selector"
        )
        
        if medico_seleccionado:
            # Obtener datos del médico
            try:
                with conn.session as s:
                    query = text("""
                        SELECT id, nombre, apellido_paterno, apellido_materno, especialidad, 
                               cedula_profesional, cedula_especialidad, universidad, email
                        FROM public.personal_medico
                        WHERE id = :mid
                    """)
                    resultado = s.execute(query, {'mid': medico_seleccionado}).fetchone()
                
                if resultado:
                    medico_data = {
                        'id': resultado[0],
                        'nombre': resultado[1],
                        'apellido_paterno': resultado[2],
                        'apellido_materno': resultado[3],
                        'especialidad': resultado[4],
                        'cedula_profesional': resultado[5],
                        'cedula_especialidad': resultado[6],
                        'universidad': resultado[7],
                        'email': resultado[8]
                    }
                    
                    st.markdown("---")
                    
                    # Tabs para editar o eliminar
                    col_editar, col_eliminar = st.columns(2)
                    
                    with col_editar:
                        if st.button("✏️ Editar Información", use_container_width=True):
                            st.session_state['mostrar_form_editar_medico'] = True
                    
                    with col_eliminar:
                        if st.button("🗑️ Desactivar Médico", use_container_width=True, type="secondary"):
                            st.session_state['confirmar_eliminar_medico'] = True
                    
                    # Formulario de edición
                    if st.session_state.get('mostrar_form_editar_medico', False):
                        st.markdown("### Editar Información del Médico")
                        
                        with st.form("editar_medico_form"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("**Información Personal**")
                                nombre_edit = st.text_input("Nombre(s)", value=medico_data['nombre'])
                                apellido_paterno_edit = st.text_input("Apellido Paterno", value=medico_data['apellido_paterno'])
                                especialidad_edit = st.text_input("Especialidad", value=medico_data['especialidad'])
                            
                            with col2:
                                st.markdown("**Credenciales Profesionales**")
                                apellido_materno_edit = st.text_input("Apellido Materno", value=medico_data['apellido_materno'] or "")
                                cedula_edit = st.text_input("Cédula Profesional", value=medico_data['cedula_profesional'])
                                cedula_especialidad_edit = st.text_input("Cédula de Especialidad", value=medico_data['cedula_especialidad'] or "")
                            
                            st.markdown("**Información Adicional**")
                            col1, col2 = st.columns(2)
                            with col1:
                                universidad_edit = st.text_input("Universidad", value=medico_data['universidad'] or "")
                            with col2:
                                email_edit = st.text_input("Correo Electrónico", value=medico_data['email'])
                            
                            col_submit, col_cancel = st.columns(2)
                            with col_submit:
                                submit_edit = st.form_submit_button("💾 Guardar Cambios", use_container_width=True, type="primary")
                            with col_cancel:
                                if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                    st.session_state['mostrar_form_editar_medico'] = False
                                    st.rerun()
                            
                            if submit_edit:
                                try:
                                    with conn.session as s:
                                        query = text("""
                                            UPDATE public.personal_medico
                                            SET nombre = :nombre,
                                                apellido_paterno = :paterno,
                                                apellido_materno = :materno,
                                                especialidad = :especialidad,
                                                cedula_profesional = :cedula,
                                                cedula_especialidad = :cedula_esp,
                                                universidad = :universidad,
                                                email = :email
                                            WHERE id = :mid
                                        """)
                                        s.execute(query, params={
                                            'nombre': nombre_edit,
                                            'paterno': apellido_paterno_edit,
                                            'materno': apellido_materno_edit,
                                            'especialidad': especialidad_edit,
                                            'cedula': cedula_edit,
                                            'cedula_esp': cedula_especialidad_edit,
                                            'universidad': universidad_edit,
                                            'email': email_edit,
                                            'mid': medico_seleccionado
                                        })
                                        s.commit()
                                    
                                    st.success("✅ ¡Cambios guardados exitosamente!")
                                    st.session_state['mostrar_form_editar_medico'] = False
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error al guardar cambios: {e}")
                    
                    # Confirmación de eliminación
                    if st.session_state.get('confirmar_eliminar_medico', False):
                        st.markdown("---")
                        st.warning(
                            f"⚠️ ¿Estás seguro de que deseas desactivar a **{medico_data['nombre']} {medico_data['apellido_paterno']}**? "
                            f"Esta acción se puede revertir."
                        )
                        
                        col_confirmar, col_cancelar = st.columns(2)
                        
                        with col_confirmar:
                            if st.button("🗑️ Sí, desactivar", use_container_width=True, type="primary"):
                                try:
                                    with conn.session as s:
                                        query = text("""
                                            UPDATE public.personal_medico
                                            SET activo = false
                                            WHERE id = :mid
                                        """)
                                        s.execute(query, {'mid': medico_seleccionado})
                                        s.commit()
                                    
                                    st.success("✅ ¡Médico desactivado exitosamente!")
                                    st.session_state['confirmar_eliminar_medico'] = False
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error al desactivar médico: {e}")
                        
                        with col_cancelar:
                            if st.button("❌ No, cancelar", use_container_width=True):
                                st.session_state['confirmar_eliminar_medico'] = False
                                st.rerun()
            
            except Exception as e:
                st.error(f"Error al cargar datos del médico: {e}")
    else:
        st.info("No hay médicos activos para editar.")

