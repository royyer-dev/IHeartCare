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
st.set_page_config(page_title="Gestión de Personal Médico", page_icon="❤️", layout="wide")

# --- BREADCRUMBS ---
breadcrumb_nav(["Home", "Administración", "Personal Médico"])

# --- CONEXIÓN A LA BASE DE DATOS ---
try:
    conn = st.connection("postgresql", type="sql")
except Exception:
    st.error("No se pudo establecer conexión con la base de datos.")
    st.stop()

# --- LIMPIAR ESTADO AL NAVEGAR DESDE EL SIDEBAR ---
if st.session_state.get('_current_page') != 'medicos':
    st.session_state.pop('ver_detalle_medico_id', None)
    st.session_state['_current_page'] = 'medicos'

# --- CHECK: Vista dedicada de detalle de médico ---
if st.session_state.get('ver_detalle_medico_id'):
    medico_id = st.session_state['ver_detalle_medico_id']

    if st.button("Regresar a la lista"):
        del st.session_state['ver_detalle_medico_id']
        st.rerun()

    st.markdown("---")

    try:
        with conn.session as s:
            query = text("""
                SELECT id, nombre, apellido_paterno, apellido_materno, especialidad,
                       cedula_profesional, cedula_especialidad, universidad, email
                FROM public.personal_medico
                WHERE id = :mid
            """)
            resultado = s.execute(query, {'mid': medico_id}).fetchone()

        if resultado:
            nombre_completo = f"Dr(a). {resultado[1]} {resultado[2]} {resultado[3] or ''}".strip()

            st.markdown(f"## {nombre_completo}")
            st.caption(f"Especialidad: {resultado[4]}  |  Cédula: {resultado[5]}")

            st.markdown("---")

            # --- DATOS PROFESIONALES ---
            st.markdown("### Datos Profesionales")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Especialidad**")
                st.write(resultado[4])
                st.markdown("**Universidad**")
                st.write(resultado[7] or "No registrada")
            with col2:
                st.markdown("**Cédula Profesional**")
                st.write(resultado[5])
                st.markdown("**Cédula de Especialidad**")
                st.write(resultado[6] or "No registrada")
            with col3:
                st.markdown("**Correo Electrónico**")
                st.write(resultado[8])

            # --- CREDENCIALES DE ACCESO ---
            st.markdown("---")
            st.markdown("### Credenciales de Acceso")
            try:
                with conn.session as s:
                    usuario_query = text("""
                        SELECT u.id, u.username, u.activo
                        FROM public.usuarios u
                        WHERE u.id = (SELECT usuario_id FROM public.personal_medico WHERE id = :mid)
                    """)
                    usuario = s.execute(usuario_query, {'mid': medico_id}).fetchone()

                if usuario:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Nombre de usuario**")
                        st.write(f"`{usuario[1]}`")
                    with col2:
                        st.markdown("**Estado de la cuenta**")
                        if usuario[2]:
                            st.success("Cuenta activa")
                        else:
                            st.warning("Cuenta inactiva")
                else:
                    st.info("Este médico no tiene credenciales de acceso configuradas")
            except Exception as e:
                st.warning(f"No se pudieron cargar credenciales: {e}")

            # --- PACIENTES ASIGNADOS ---
            st.markdown("---")
            st.markdown("### Pacientes Asignados")
            try:
                with conn.session as s:
                    pacientes_query = text("""
                        SELECT p.id, p.nombre, p.apellido_paterno, p.apellido_materno,
                               p.diagnostico, p.nss
                        FROM public.pacientes p
                        JOIN public.pacientes_medicos pm ON p.id = pm.paciente_id
                        WHERE pm.medico_id = :mid
                        ORDER BY p.nombre
                    """)
                    pacientes_asignados = s.execute(pacientes_query, {'mid': medico_id}).fetchall()

                if pacientes_asignados:
                    for pac in pacientes_asignados:
                        pac_nombre = f"{pac[1]} {pac[2]} {pac[3] or ''}".strip()
                        with st.container(border=True):
                            col1, col2, col3 = st.columns([3, 3, 2])
                            with col1:
                                st.markdown(f"**{pac_nombre}**")
                            with col2:
                                st.caption(pac[4] or "Sin diagnóstico")
                            with col3:
                                st.caption(f"NSS: {pac[5] or 'N/A'}")
                else:
                    st.info("No tiene pacientes asignados")
            except Exception as e:
                st.warning(f"No se pudieron cargar pacientes: {e}")

            # --- ALERTAS DE SUS PACIENTES ---
            st.markdown("---")
            st.markdown("### Alertas Pendientes de sus Pacientes")
            try:
                with conn.session as s:
                    alertas_query = text("""
                        SELECT a.tipo_alerta, a.mensaje, a.timestamp,
                               p.nombre, p.apellido_paterno,
                               m.tipo_medicion, m.valor, m.unidad_medida
                        FROM public.alertas a
                        JOIN public.mediciones m ON a.medicion_id = m.id
                        JOIN public.dispositivos d ON m.dispositivo_id = d.id
                        JOIN public.pacientes p ON d.paciente_id = p.id
                        JOIN public.pacientes_medicos pm ON p.id = pm.paciente_id
                        WHERE pm.medico_id = :mid AND a.leida = false
                        ORDER BY a.timestamp DESC
                        LIMIT 10
                    """)
                    alertas = s.execute(alertas_query, {'mid': medico_id}).fetchall()

                if alertas:
                    for alerta in alertas:
                        with st.container(border=True):
                            col1, col2, col3 = st.columns([2, 3, 1])
                            with col1:
                                st.markdown(f"**{alerta[3]} {alerta[4]}**")
                            with col2:
                                st.caption(f"{alerta[5].replace('_', ' ').title()}: {alerta[6]} {alerta[7]}")
                                st.caption(alerta[1])
                            with col3:
                                st.caption(alerta[2].strftime('%d/%m/%Y %H:%M'))
                else:
                    st.info("No hay alertas pendientes")
            except Exception as e:
                st.warning(f"No se pudieron cargar alertas: {e}")

        else:
            st.error("Médico no encontrado")
            if st.button("Regresar"):
                del st.session_state['ver_detalle_medico_id']
                st.rerun()

    except Exception as e:
        st.error(f"Error al cargar datos del médico: {e}")

    st.stop()

# --- PÁGINA PRINCIPAL ---
st.title("Gestión de Personal Médico")
st.markdown("---")

# --- TABS ---
tab_listado, tab_registro, tab_editar = st.tabs(["Ver Médicos", "Registrar Nuevo", "Editar / Eliminar"])

# ==================== TAB 1: VER MÉDICOS (LISTA SIMPLIFICADA) ====================
with tab_listado:

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
                "Buscar médico",
                placeholder="Ingresa el nombre del médico...",
                key="search_medico"
            )
        with col2:
            st.write("")
            if st.button("Refrescar", use_container_width=True):
                st.rerun()

        st.write("")

        # Filtrar
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
            st.subheader(f"Médicos Registrados ({len(filtered_df)})")

            for idx, medico in filtered_df.iterrows():
                medico_id = medico['id']
                nombre_completo = f"Dr(a). {medico['nombre']} {medico['apellido_paterno']} {medico.get('apellido_materno', '') or ''}".strip()

                with st.container(border=True):
                    col1, col2, col3, col4 = st.columns([3, 3, 2, 1])

                    with col1:
                        st.markdown(f"**{nombre_completo}**")

                    with col2:
                        st.caption(f"{medico['especialidad']}")

                    with col3:
                        st.caption(f"Cédula: {medico['cedula_profesional']}")

                    with col4:
                        if st.button("Ver detalle", key=f"btn_detalle_med_{medico_id}", use_container_width=True):
                            st.session_state['ver_detalle_medico_id'] = medico_id
                            st.rerun()
    else:
        st.info("No hay médicos registrados en el sistema.")

# ==================== TAB 2: REGISTRAR MÉDICO ====================
with tab_registro:
    st.subheader("Registrar Nuevo Profesional Médico")

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
        st.caption("Configure un usuario y contraseña para que el médico pueda iniciar sesión")

        col1, col2 = st.columns(2)
        with col1:
            username_medico = st.text_input("Nombre de Usuario", placeholder="Ej. dr.lopez")
        with col2:
            password_medico = st.text_input("Contraseña", type="password", placeholder="Mínimo 6 caracteres")

        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            submit = st.form_submit_button("Registrar", use_container_width=True, type="primary")

        if submit:
            if not all([nombre, apellido_paterno, especialidad, cedula_profesional, email, username_medico, password_medico]):
                st.warning("Por favor, completa todos los campos obligatorios.")
            elif len(password_medico) < 6:
                st.warning("La contraseña debe tener mínimo 6 caracteres.")
            else:
                try:
                    with conn.session as s:
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

                        usuario_sql = text("""
                            INSERT INTO public.usuarios (username, password_hash, rol, activo)
                            VALUES (:username, :password_hash, 'medico', true)
                            RETURNING id
                        """)
                        usuario_id = s.execute(usuario_sql, params={
                            "username": username_medico,
                            "password_hash": hash_password(password_medico)
                        }).fetchone()[0]

                        link_sql = text("""
                            UPDATE public.personal_medico 
                            SET usuario_id = :user_id 
                            WHERE id = :medico_id
                        """)
                        s.execute(link_sql, {"user_id": usuario_id, "medico_id": medico_id})

                        s.commit()

                    st.success("Médico registrado exitosamente")
                    st.markdown(f"""
                    **Credenciales creadas:**
                    - Usuario: `{username_medico}`
                    - Contraseña: (configurada al momento)
                    
                    El médico puede iniciar sesión con estas credenciales.
                    """)
                except Exception as e:
                    st.error(f"Error al registrar: {e}")

# ==================== TAB 3: EDITAR/ELIMINAR MÉDICO ====================
with tab_editar:
    st.subheader("Editar o Eliminar Médico")

    try:
        medicos_activos = conn.query(
            'SELECT id, nombre, apellido_paterno, apellido_materno FROM public.personal_medico WHERE activo = true ORDER BY nombre;',
            ttl="10s"
        )
    except Exception as e:
        st.error(f"Error al cargar médicos: {e}")
        medicos_activos = pd.DataFrame()

    if not medicos_activos.empty:
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

                    col_editar, col_eliminar = st.columns(2)

                    with col_editar:
                        if st.button("Editar Información", use_container_width=True):
                            st.session_state['mostrar_form_editar_medico'] = True

                    with col_eliminar:
                        if st.button("Desactivar Médico", use_container_width=True, type="secondary"):
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
                                submit_edit = st.form_submit_button("Guardar Cambios", use_container_width=True, type="primary")
                            with col_cancel:
                                if st.form_submit_button("Cancelar", use_container_width=True):
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

                                    st.success("Cambios guardados exitosamente")
                                    st.session_state['mostrar_form_editar_medico'] = False
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error al guardar cambios: {e}")

                    # Confirmación de eliminación
                    if st.session_state.get('confirmar_eliminar_medico', False):
                        st.markdown("---")
                        st.warning(
                            f"¿Estás seguro de que deseas desactivar a **{medico_data['nombre']} {medico_data['apellido_paterno']}**? "
                            f"Esta acción se puede revertir."
                        )

                        col_confirmar, col_cancelar = st.columns(2)

                        with col_confirmar:
                            if st.button("Sí, desactivar", use_container_width=True, type="primary"):
                                try:
                                    with conn.session as s:
                                        query = text("""
                                            UPDATE public.personal_medico
                                            SET activo = false
                                            WHERE id = :mid
                                        """)
                                        s.execute(query, {'mid': medico_seleccionado})
                                        s.commit()

                                    st.success("Médico desactivado exitosamente")
                                    st.session_state['confirmar_eliminar_medico'] = False
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error al desactivar médico: {e}")

                        with col_cancelar:
                            if st.button("No, cancelar", use_container_width=True):
                                st.session_state['confirmar_eliminar_medico'] = False
                                st.rerun()

            except Exception as e:
                st.error(f"Error al cargar datos del médico: {e}")
    else:
        st.info("No hay médicos activos para editar.")
