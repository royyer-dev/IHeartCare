import streamlit as st
import pandas as pd
from datetime import datetime
import time
from sqlalchemy import text
from core.auth import require_auth
from core.sidebar import render_sidebar
from core.theme import apply_global_theme
from utils import breadcrumb_nav

# --- PROTECCIÓN DE RUTA ---
require_auth(allowed_roles=['administrador'])
render_sidebar()
apply_global_theme()

st.set_page_config(page_title="Gestión de Dispositivos", page_icon="❤️", layout="wide")

# --- BREADCRUMBS ---
breadcrumb_nav(["Home", "Administración", "Dispositivos"])

# --- CONEXIÓN A LA BASE DE DATOS ---
try:
    conn = st.connection("postgresql", type="sql")
except Exception:
    st.error("No se pudo establecer conexión con la base de datos.")
    st.stop()

# --- LIMPIAR ESTADO AL NAVEGAR DESDE EL SIDEBAR ---
if st.session_state.get('_current_page') != 'dispositivos':
    st.session_state.pop('ver_detalle_dispositivo_id', None)
    st.session_state['_current_page'] = 'dispositivos'

# --- CHECK: Vista dedicada de detalle de dispositivo ---
if st.session_state.get('ver_detalle_dispositivo_id'):
    device_id = st.session_state['ver_detalle_dispositivo_id']

    if st.button("Regresar a la lista"):
        del st.session_state['ver_detalle_dispositivo_id']
        st.rerun()

    st.markdown("---")

    try:
        with conn.session as s:
            query = text("""
                SELECT d.id, d.modelo, d.mac_address, d.activo, d.fecha_asignacion,
                       p.id as paciente_id, p.nombre, p.apellido_paterno, p.apellido_materno,
                       p.diagnostico, p.email, p.telefono
                FROM public.dispositivos d
                LEFT JOIN public.pacientes p ON d.paciente_id = p.id
                WHERE d.id = :did
            """)
            resultado = s.execute(query, {'did': device_id}).fetchone()

        if resultado:
            st.markdown(f"## {resultado[1]}")
            st.caption(f"ID: {resultado[0]}  |  MAC: {resultado[2] or 'No especificada'}")

            st.markdown("---")

            # --- INFORMACIÓN DEL DISPOSITIVO ---
            st.markdown("### Especificaciones")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Modelo**")
                st.write(resultado[1])
            with col2:
                st.markdown("**Dirección MAC**")
                st.write(resultado[2] or "No especificada")
            with col3:
                st.markdown("**Estado**")
                st.write("Activo" if resultado[3] else "Inactivo")

            st.markdown("---")

            # --- FECHA DE ASIGNACIÓN ---
            st.markdown("### Registro")
            st.markdown("**Fecha de asignación**")
            if resultado[4]:
                st.write(pd.to_datetime(resultado[4]).strftime('%d/%m/%Y %H:%M'))
            else:
                st.write("No registrada")

            st.markdown("---")

            # --- PACIENTE ASIGNADO ---
            st.markdown("### Paciente Asignado")
            if resultado[5]:
                paciente_nombre = f"{resultado[6]} {resultado[7]} {resultado[8] or ''}".strip()
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Nombre**")
                    st.write(paciente_nombre)
                    st.markdown("**Diagnóstico**")
                    st.write(resultado[9] or "Sin diagnóstico")
                with col2:
                    st.markdown("**Correo**")
                    st.write(resultado[10] or "No registrado")
                    st.markdown("**Teléfono**")
                    st.write(resultado[11] or "No registrado")
            else:
                st.info("Este dispositivo no está asignado a ningún paciente")

            # --- ÚLTIMAS MEDICIONES ---
            st.markdown("---")
            st.markdown("### Últimas Mediciones")
            try:
                with conn.session as s:
                    med_query = text("""
                        SELECT tipo_medicion, valor, unidad_medida, timestamp
                        FROM public.mediciones
                        WHERE dispositivo_id = :did
                        ORDER BY timestamp DESC
                        LIMIT 20
                    """)
                    mediciones = s.execute(med_query, {'did': device_id}).fetchall()

                if mediciones:
                    med_df = pd.DataFrame(
                        mediciones,
                        columns=['Tipo', 'Valor', 'Unidad', 'Fecha/Hora']
                    )
                    st.dataframe(med_df, use_container_width=True, hide_index=True)
                else:
                    st.info("Sin mediciones registradas para este dispositivo")
            except Exception as e:
                st.warning(f"No se pudieron cargar mediciones: {e}")

        else:
            st.error("Dispositivo no encontrado")
            if st.button("Regresar"):
                del st.session_state['ver_detalle_dispositivo_id']
                st.rerun()

    except Exception as e:
        st.error(f"Error al cargar datos del dispositivo: {e}")

    st.stop()

# --- PÁGINA PRINCIPAL ---
st.title("Gestión de Dispositivos de Monitoreo")
st.markdown("---")

# --- TABS ---
tab_listado, tab_registro, tab_editar = st.tabs(["Ver Dispositivos", "Registrar Nuevo", "Editar / Eliminar"])

# ==================== TAB 1: VER DISPOSITIVOS (LISTA SIMPLIFICADA) ====================
with tab_listado:

    try:
        dispositivos_df = conn.query("""
            SELECT 
                d.id,
                d.modelo,
                d.mac_address,
                d.fecha_asignacion,
                d.activo,
                p.id as paciente_id,
                p.nombre,
                p.apellido_paterno,
                p.apellido_materno
            FROM public.dispositivos d
            LEFT JOIN public.pacientes p ON d.paciente_id = p.id
            ORDER BY d.modelo
        """, ttl="10s")
    except Exception as e:
        st.error(f"Error al cargar dispositivos: {e}")
        dispositivos_df = pd.DataFrame()

    if not dispositivos_df.empty:
        # --- BUSCADOR ---
        col1, col2 = st.columns([3, 1])
        with col1:
            search_term = st.text_input(
                "Buscar dispositivo",
                placeholder="Modelo o nombre del paciente...",
                key="search_dispositivo"
            )
        with col2:
            st.write("")
            if st.button("Refrescar", use_container_width=True):
                st.rerun()

        st.write("")

        # Filtrar
        if search_term:
            filtered_df = dispositivos_df[
                dispositivos_df['modelo'].str.contains(search_term, case=False, na=False) |
                dispositivos_df['nombre'].str.contains(search_term, case=False, na=False) |
                dispositivos_df['apellido_paterno'].str.contains(search_term, case=False, na=False)
            ]
        else:
            filtered_df = dispositivos_df

        if filtered_df.empty:
            st.info("No se encontraron dispositivos con ese criterio.")
        else:
            # Estadísticas rápidas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total", len(filtered_df))
            with col2:
                activos = (filtered_df['activo'] == True).sum()
                st.metric("Activos", activos)
            with col3:
                inactivos = (filtered_df['activo'] == False).sum()
                st.metric("Inactivos", inactivos)

            st.write("")
            st.subheader(f"Dispositivos ({len(filtered_df)})")

            for idx, dispositivo in filtered_df.iterrows():
                device_id = dispositivo['id']
                modelo = dispositivo['modelo']
                mac = dispositivo['mac_address']
                activo = dispositivo['activo']
                estado_txt = "Activo" if activo else "Inactivo"

                if pd.notna(dispositivo['paciente_id']):
                    paciente_nombre = f"{dispositivo['nombre']} {dispositivo['apellido_paterno']} {dispositivo.get('apellido_materno', '') or ''}".strip()
                else:
                    paciente_nombre = "Sin asignar"

                with st.container(border=True):
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

                    with col1:
                        st.markdown(f"**{modelo}**")
                        st.caption(f"MAC: {mac or 'N/A'}")

                    with col2:
                        st.caption(f"Paciente: {paciente_nombre}")

                    with col3:
                        st.caption(f"Estado: {estado_txt}")

                    with col4:
                        if st.button("Ver detalle", key=f"btn_detalle_dev_{device_id}", use_container_width=True):
                            st.session_state['ver_detalle_dispositivo_id'] = device_id
                            st.rerun()
    else:
        st.info("No hay dispositivos registrados en el sistema.")

# ==================== TAB 2: REGISTRAR DISPOSITIVO ====================
with tab_registro:
    st.subheader("Registrar Nuevo Dispositivo")

    try:
        pacientes_df = conn.query("""
            SELECT id, nombre, apellido_paterno, apellido_materno 
            FROM public.pacientes 
            ORDER BY nombre
        """, ttl="10s")

        pacientes_opciones = {
            f"{p['nombre']} {p['apellido_paterno']} {p.get('apellido_materno', '') or ''}".strip(): p['id']
            for _, p in pacientes_df.iterrows()
        }
    except Exception:
        pacientes_opciones = {}

    with st.form("registro_dispositivo_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Información del Dispositivo**")
            modelo = st.text_input("Modelo del Dispositivo", placeholder="Ej. Apple Watch Series 9")
            mac_address = st.text_input("Dirección MAC (opcional)", placeholder="Ej. 02:42:ac:11:00:02")

        with col2:
            st.markdown("**Asignación**")
            paciente_asignado = st.selectbox(
                "Asignar a Paciente",
                options=list(pacientes_opciones.keys()) + ["Sin asignar"],
                index=0
            )
            activo = st.checkbox("Dispositivo Activo", value=True)

        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            submit = st.form_submit_button("Registrar", use_container_width=True, type="primary")

        if submit:
            if not modelo:
                st.warning("Por favor, ingresa el modelo del dispositivo.")
            else:
                try:
                    if paciente_asignado == "Sin asignar":
                        paciente_id = None
                    else:
                        paciente_id = pacientes_opciones[paciente_asignado]

                    dispositivo_query = text("""
                        INSERT INTO public.dispositivos 
                        (paciente_id, modelo, mac_address, activo)
                        VALUES (:paciente_id, :modelo, :mac_address, :activo)
                        RETURNING id
                    """)

                    with conn.session as s:
                        result = s.execute(dispositivo_query, {
                            "paciente_id": paciente_id,
                            "modelo": modelo,
                            "mac_address": mac_address if mac_address else None,
                            "activo": activo
                        })
                        device_id = result.fetchone()[0]
                        s.commit()

                    st.success(f"Dispositivo registrado exitosamente (ID: {device_id})")
                    st.markdown(f"""
                    **Dispositivo creado:**
                    - Modelo: `{modelo}`
                    - MAC: `{mac_address if mac_address else 'N/A'}`
                    - Paciente: {paciente_asignado}
                    - Estado: {'Activo' if activo else 'Inactivo'}
                    """)

                except Exception as e:
                    st.error(f"Error al registrar: {e}")

# ==================== TAB 3: EDITAR/ELIMINAR DISPOSITIVO ====================
with tab_editar:
    st.subheader("Editar o Eliminar Dispositivo")

    try:
        dispositivos_activos = conn.query("""
            SELECT 
                d.id,
                d.modelo,
                d.mac_address,
                p.nombre,
                p.apellido_paterno
            FROM public.dispositivos d
            LEFT JOIN public.pacientes p ON d.paciente_id = p.id
            WHERE d.activo = true
            ORDER BY d.modelo;
        """, ttl="10s")
    except Exception as e:
        st.error(f"Error al cargar dispositivos: {e}")
        dispositivos_activos = pd.DataFrame()

    if not dispositivos_activos.empty:
        dispositivos_activos['label'] = (
            dispositivos_activos['modelo'] + ' (' + 
            dispositivos_activos['mac_address'].fillna('N/A') + ')'
        )

        dispositivo_seleccionado = st.selectbox(
            "Selecciona un dispositivo",
            options=dispositivos_activos['id'].tolist(),
            format_func=lambda x: dispositivos_activos[dispositivos_activos['id'] == x]['label'].values[0],
            key="edit_dispositivo_selector"
        )

        if dispositivo_seleccionado:
            try:
                with conn.session as s:
                    query = text("""
                        SELECT id, modelo, mac_address, paciente_id
                        FROM public.dispositivos
                        WHERE id = :did
                    """)
                    resultado = s.execute(query, {'did': dispositivo_seleccionado}).fetchone()

                if resultado:
                    dispositivo_data = {
                        'id': resultado[0],
                        'modelo': resultado[1],
                        'mac_address': resultado[2],
                        'paciente_id': resultado[3],
                    }

                    st.markdown("---")

                    col_editar, col_eliminar = st.columns(2)

                    with col_editar:
                        if st.button("Editar Información", use_container_width=True):
                            st.session_state['mostrar_form_editar_dispositivo'] = True

                    with col_eliminar:
                        if st.button("Desactivar Dispositivo", use_container_width=True, type="secondary"):
                            st.session_state['confirmar_eliminar_dispositivo'] = True

                    # Formulario de edición
                    if st.session_state.get('mostrar_form_editar_dispositivo', False):
                        st.markdown("### Editar Información del Dispositivo")

                        pacientes = conn.query(
                            'SELECT id, nombre, apellido_paterno FROM public.pacientes WHERE activo = true ORDER BY nombre;',
                            ttl="10s"
                        )

                        with st.form("editar_dispositivo_form"):
                            col1, col2 = st.columns(2)

                            with col1:
                                st.markdown("**Información del Dispositivo**")
                                modelo_edit = st.text_input("Modelo", value=dispositivo_data['modelo'])
                                mac_edit = st.text_input("Dirección MAC", value=dispositivo_data['mac_address'] or "")

                            with col2:
                                st.markdown("**Paciente Asignado**")
                                if not pacientes.empty:
                                    pacientes['label'] = pacientes['nombre'] + ' ' + pacientes['apellido_paterno']
                                    paciente_edit = st.selectbox(
                                        "Selecciona paciente",
                                        options=pacientes['id'].tolist() + [None],
                                        format_func=lambda x: (pacientes[pacientes['id'] == x]['label'].values[0] if x is not None else "Sin asignar"),
                                        index=list(pacientes['id']).index(dispositivo_data['paciente_id']) if dispositivo_data['paciente_id'] in pacientes['id'].values else len(pacientes)
                                    )

                            col_submit, col_cancel = st.columns(2)
                            with col_submit:
                                submit_edit = st.form_submit_button("Guardar Cambios", use_container_width=True, type="primary")
                            with col_cancel:
                                if st.form_submit_button("Cancelar", use_container_width=True):
                                    st.session_state['mostrar_form_editar_dispositivo'] = False
                                    st.rerun()

                            if submit_edit:
                                try:
                                    with conn.session as s:
                                        query = text("""
                                            UPDATE public.dispositivos
                                            SET modelo = :modelo,
                                                mac_address = :mac,
                                                paciente_id = :paciente_id
                                            WHERE id = :did
                                        """)
                                        s.execute(query, params={
                                            'modelo': modelo_edit,
                                            'mac': mac_edit if mac_edit else None,
                                            'paciente_id': paciente_edit,
                                            'did': dispositivo_seleccionado
                                        })
                                        s.commit()

                                    st.success("Cambios guardados exitosamente")
                                    st.session_state['mostrar_form_editar_dispositivo'] = False
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error al guardar cambios: {e}")

                    # Confirmación de eliminación
                    if st.session_state.get('confirmar_eliminar_dispositivo', False):
                        st.markdown("---")
                        st.warning(
                            f"¿Estás seguro de que deseas desactivar el dispositivo **{dispositivo_data['modelo']} ({dispositivo_data['mac_address']})**? "
                            f"Esta acción se puede revertir."
                        )

                        col_confirmar, col_cancelar = st.columns(2)

                        with col_confirmar:
                            if st.button("Sí, desactivar", use_container_width=True, type="primary"):
                                try:
                                    with conn.session as s:
                                        query = text("""
                                            UPDATE public.dispositivos
                                            SET activo = false
                                            WHERE id = :did
                                        """)
                                        s.execute(query, {'did': dispositivo_seleccionado})
                                        s.commit()

                                    st.success("Dispositivo desactivado exitosamente")
                                    st.session_state['confirmar_eliminar_dispositivo'] = False
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error al desactivar dispositivo: {e}")

                        with col_cancelar:
                            if st.button("No, cancelar", use_container_width=True):
                                st.session_state['confirmar_eliminar_dispositivo'] = False
                                st.rerun()

            except Exception as e:
                st.error(f"Error al cargar datos del dispositivo: {e}")
    else:
        st.info("No hay dispositivos activos para editar.")