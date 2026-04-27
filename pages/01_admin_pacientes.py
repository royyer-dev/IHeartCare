import streamlit as st
import pandas as pd
from datetime import date
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

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Gestión de Pacientes", page_icon="❤️", layout="wide")

# --- BREADCRUMBS ---
breadcrumb_nav(["Home", "Administración", "Pacientes"])

# --- CONEXIÓN A LA BASE DE DATOS ---
try:
    conn = st.connection("postgresql", type="sql")
except Exception:
    st.error("No se pudo establecer conexión con la base de datos.")
    st.stop()

# --- LIMPIAR ESTADO AL NAVEGAR DESDE EL SIDEBAR ---
if st.session_state.get('_current_page') != 'pacientes':
    st.session_state.pop('ver_detalle_paciente_id', None)
    st.session_state['_current_page'] = 'pacientes'

# --- CHECK: Si venimos del detalle de un paciente y queremos ver detalle ---
if st.session_state.get('ver_detalle_paciente_id'):
    paciente_id = st.session_state['ver_detalle_paciente_id']
    
    # Botón para regresar a la lista
    if st.button("Regresar a la lista"):
        del st.session_state['ver_detalle_paciente_id']
        st.rerun()
    
    st.markdown("---")
    
    # Obtener datos completos del paciente
    try:
        with conn.session as s:
            query = text("""
                SELECT id, nombre, apellido_paterno, apellido_materno, fecha_nacimiento,
                       curp, nss, sexo, estado_civil, domicilio, email, telefono, diagnostico
                FROM public.pacientes
                WHERE id = :pid
            """)
            resultado = s.execute(query, {'pid': paciente_id}).fetchone()
        
        if resultado:
            nombre_completo = f"{resultado[1]} {resultado[2]} {resultado[3] or ''}".strip()
            
            st.markdown(f"## {nombre_completo}")
            st.caption(f"NSS: {resultado[6] or 'No registrado'}  |  CURP: {resultado[5] or 'No registrado'}")
            
            st.markdown("---")
            
            # --- INFORMACIÓN PERSONAL ---
            st.markdown("### Información Personal")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Fecha de Nacimiento**")
                st.write(str(resultado[4]) if resultado[4] else "No registrada")
                st.markdown("**Sexo**")
                st.write(resultado[7] or "No registrado")
            with col2:
                st.markdown("**Estado Civil**")
                st.write(resultado[8] or "No registrado")
                st.markdown("**Teléfono**")
                st.write(resultado[11] or "No registrado")
            with col3:
                st.markdown("**Correo Electrónico**")
                st.write(resultado[10] or "No registrado")
                st.markdown("**Domicilio**")
                st.write(resultado[9] or "No registrado")
            
            # --- DIAGNÓSTICO ---
            st.markdown("---")
            st.markdown("### Diagnóstico")
            st.write(resultado[12] if resultado[12] else "Sin diagnóstico registrado")
            
            # --- DISPOSITIVO ASIGNADO ---
            st.markdown("---")
            st.markdown("### Dispositivo Asignado")
            try:
                with conn.session as s:
                    disp_query = text("""
                        SELECT id, modelo, mac_address, activo, fecha_asignacion
                        FROM public.dispositivos
                        WHERE paciente_id = :pid
                        ORDER BY activo DESC, fecha_asignacion DESC
                        LIMIT 1
                    """)
                    dispositivo = s.execute(disp_query, {'pid': paciente_id}).fetchone()
                
                if dispositivo:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown("**Modelo**")
                        st.write(dispositivo[1])
                    with col2:
                        st.markdown("**MAC Address**")
                        st.write(dispositivo[2] or "N/A")
                    with col3:
                        st.markdown("**Estado**")
                        st.write("Activo" if dispositivo[3] else "Inactivo")
                else:
                    st.info("No tiene dispositivo asignado")
            except Exception as e:
                st.warning(f"No se pudo cargar dispositivo: {e}")
            
            # --- MÉDICOS ASIGNADOS ---
            st.markdown("---")
            st.markdown("### Médicos Asignados")
            try:
                with conn.session as s:
                    med_query = text("""
                        SELECT pm_med.nombre, pm_med.apellido_paterno, pm_med.especialidad
                        FROM public.personal_medico pm_med
                        JOIN public.pacientes_medicos pm ON pm_med.id = pm.medico_id
                        WHERE pm.paciente_id = :pid
                        ORDER BY pm_med.nombre
                    """)
                    medicos = s.execute(med_query, {'pid': paciente_id}).fetchall()
                
                if medicos:
                    for med in medicos:
                        with st.container(border=True):
                            st.markdown(f"**Dr(a). {med[0]} {med[1]}**")
                            st.caption(f"Especialidad: {med[2]}")
                else:
                    st.info("No tiene médicos asignados")
            except Exception as e:
                st.warning(f"No se pudieron cargar médicos: {e}")
            
            # --- ALERTAS PENDIENTES ---
            st.markdown("---")
            st.markdown("### Alertas Pendientes")
            try:
                with conn.session as s:
                    alertas_query = text("""
                        SELECT a.tipo_alerta, a.mensaje, a.timestamp,
                               m.tipo_medicion, m.valor, m.unidad_medida
                        FROM public.alertas a
                        JOIN public.mediciones m ON a.medicion_id = m.id
                        JOIN public.dispositivos d ON m.dispositivo_id = d.id
                        WHERE d.paciente_id = :pid AND a.leida = false
                        ORDER BY a.timestamp DESC
                        LIMIT 10
                    """)
                    alertas = s.execute(alertas_query, {'pid': paciente_id}).fetchall()
                
                if alertas:
                    for alerta in alertas:
                        with st.container(border=True):
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(f"**{alerta[3].replace('_', ' ').title()}:** {alerta[4]} {alerta[5]}")
                                st.caption(alerta[1])
                            with col2:
                                st.caption(alerta[2].strftime('%d/%m/%Y %H:%M'))
                else:
                    st.info("No hay alertas pendientes")
            except Exception as e:
                st.warning(f"No se pudieron cargar alertas: {e}")
            
            # --- HISTORIAL DE MEDICIONES ---
            st.markdown("---")
            st.markdown("### Historial de Mediciones")
            try:
                with conn.session as s:
                    historial_query = text("""
                        SELECT 
                            m.tipo_medicion,
                            m.valor,
                            m.unidad_medida,
                            m.timestamp
                        FROM public.mediciones m
                        JOIN public.dispositivos d ON m.dispositivo_id = d.id
                        WHERE d.paciente_id = :pid
                        ORDER BY m.timestamp DESC
                        LIMIT 100
                    """)
                    historial = s.execute(historial_query, {'pid': paciente_id}).fetchall()
                
                if historial:
                    historial_df = pd.DataFrame(
                        historial,
                        columns=['Tipo de Medición', 'Valor', 'Unidad', 'Fecha/Hora']
                    )
                    
                    for tipo_med in historial_df['Tipo de Medición'].unique():
                        st.markdown(f"#### {tipo_med.replace('_', ' ').title()}")
                        tipo_df = historial_df[historial_df['Tipo de Medición'] == tipo_med]
                        
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.dataframe(
                                tipo_df[['Valor', 'Unidad', 'Fecha/Hora']],
                                use_container_width=True,
                                hide_index=True
                            )
                        with col2:
                            valores = pd.to_numeric(tipo_df['Valor'], errors='coerce')
                            if not valores.empty:
                                st.metric("Promedio", f"{valores.mean():.2f}")
                                st.metric("Máximo", f"{valores.max():.2f}")
                                st.metric("Mínimo", f"{valores.min():.2f}")
                else:
                    st.info("Sin historial de mediciones")
            except Exception as e:
                st.warning(f"No se pudo cargar historial: {e}")
            
            # --- BOTÓN VER EN VIVO ---
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("Ver en Vivo", use_container_width=True, type="primary"):
                    try:
                        with conn.session as s:
                            dispositivo_query = text("""
                                SELECT id FROM public.dispositivos
                                WHERE paciente_id = :pid AND activo = true
                                LIMIT 1
                            """)
                            dispositivo_result = s.execute(dispositivo_query, {'pid': paciente_id}).fetchone()
                        
                        if dispositivo_result:
                            st.session_state['selected_dispositivo_id'] = dispositivo_result[0]
                            st.session_state['selected_paciente_id'] = paciente_id
                            st.session_state['ir_a_visualizacion'] = True
                            st.switch_page("pages/05_monitoreo_dashboard.py")
                        else:
                            st.warning("Este paciente no tiene un dispositivo activo asignado.")
                    except Exception as e:
                        st.error(f"Error al navegar: {e}")
        else:
            st.error("Paciente no encontrado")
            if st.button("Regresar"):
                del st.session_state['ver_detalle_paciente_id']
                st.rerun()
    
    except Exception as e:
        st.error(f"Error al cargar datos del paciente: {e}")
    
    st.stop()

# --- PÁGINA PRINCIPAL: GESTIÓN DE PACIENTES ---
st.title("Gestión de Pacientes")
st.markdown("---")

# --- TABS ---
tab_listado, tab_registro, tab_editar = st.tabs(["Ver Pacientes", "Registrar Nuevo", "Editar / Eliminar"])

# ==================== TAB 1: VER PACIENTES (LISTA SIMPLIFICADA) ====================
with tab_listado:
    
    try:
        pacientes_df = conn.query(
            'SELECT id, nombre, apellido_paterno, apellido_materno, diagnostico, nss FROM public.pacientes ORDER BY nombre;',
            ttl="10s"
        )
    except Exception as e:
        st.error(f"Error al cargar pacientes: {e}")
        pacientes_df = pd.DataFrame()
    
    if not pacientes_df.empty:
        # --- BUSCADOR ---
        col1, col2 = st.columns([3, 1])
        with col1:
            search_term = st.text_input(
                "Buscar paciente",
                placeholder="Ingresa el nombre del paciente...",
                key="search_paciente"
            )
        with col2:
            st.write("")
            if st.button("Refrescar", use_container_width=True):
                st.rerun()
        
        st.write("")
        
        # Filtrar pacientes según búsqueda
        if search_term:
            filtered_df = pacientes_df[
                pacientes_df['nombre'].str.contains(search_term, case=False, na=False) |
                pacientes_df['apellido_paterno'].str.contains(search_term, case=False, na=False) |
                pacientes_df['apellido_materno'].str.contains(search_term, case=False, na=False)
            ]
        else:
            filtered_df = pacientes_df
        
        if filtered_df.empty:
            st.info("No se encontraron pacientes con ese nombre.")
        else:
            st.subheader(f"Pacientes ({len(filtered_df)})")
            
            for idx, paciente in filtered_df.iterrows():
                paciente_id = paciente['id']
                nombre_completo = f"{paciente['nombre']} {paciente['apellido_paterno']} {paciente.get('apellido_materno', '') or ''}".strip()
                diagnostico = paciente.get('diagnostico', '') or 'Sin diagnóstico'
                nss = paciente.get('nss', '') or 'N/A'
                
                with st.container(border=True):
                    col1, col2, col3, col4 = st.columns([3, 3, 2, 1])
                    
                    with col1:
                        st.markdown(f"**{nombre_completo}**")
                    
                    with col2:
                        st.caption(f"{diagnostico}")
                    
                    with col3:
                        st.caption(f"NSS: {nss}")
                    
                    with col4:
                        if st.button("Ver detalle", key=f"btn_detalle_{paciente_id}", use_container_width=True):
                            st.session_state['ver_detalle_paciente_id'] = paciente_id
                            st.rerun()
    else:
        st.info("No hay pacientes registrados en el sistema.")

# ==================== TAB 2: REGISTRAR PACIENTE ====================
with tab_registro:
    st.subheader("Registrar Nuevo Paciente")
    
    with st.form("registro_paciente_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Información Personal**")
            nombre = st.text_input("Nombre(s)", placeholder="Ej. Juan")
            apellido_paterno = st.text_input("Apellido Paterno", placeholder="Ej. Pérez")
            fecha_nacimiento = st.date_input("Fecha de Nacimiento", min_value=date(1920, 1, 1))
            sexo = st.selectbox("Sexo", ["Masculino", "Femenino"], index=None, placeholder="Seleccione")
        
        with col2:
            st.markdown("**Información Adicional**")
            apellido_materno = st.text_input("Apellido Materno", placeholder="Ej. García")
            curp = st.text_input("CURP", max_chars=18, placeholder="18 caracteres")
            nss = st.text_input("NSS", max_chars=11, placeholder="11 dígitos")
            estado_civil = st.text_input("Estado Civil", placeholder="Ej. Soltero(a)")
        
        st.markdown("**Información de Contacto**")
        col1, col2 = st.columns(2)
        with col1:
            email = st.text_input("Correo Electrónico", placeholder="ejemplo@correo.com")
        with col2:
            telefono = st.text_input("Teléfono", placeholder="Ej. 312 123 4567")
        
        domicilio = st.text_area("Domicilio Completo", placeholder="Calle, número, colonia, C.P., ciudad...")
        diagnostico = st.text_area("Diagnóstico (opcional)", placeholder="Información clínica relevante")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            submit = st.form_submit_button("Registrar", use_container_width=True, type="primary")
        
        if submit:
            if not all([nombre, apellido_paterno, fecha_nacimiento, curp, email, sexo]):
                st.warning("Por favor, completa todos los campos obligatorios.")
            else:
                try:
                    with conn.session as s:
                        sql = text("""
                            INSERT INTO public.pacientes 
                            (nombre, apellido_paterno, apellido_materno, fecha_nacimiento, curp, nss, 
                             sexo, estado_civil, domicilio, email, telefono, diagnostico)
                            VALUES (:nombre, :paterno, :materno, :nacimiento, :curp, :nss, :sexo, 
                                    :civil, :domicilio, :email, :telefono, :diagnostico)
                        """)
                        s.execute(sql, params={
                            "nombre": nombre,
                            "paterno": apellido_paterno,
                            "materno": apellido_materno,
                            "nacimiento": fecha_nacimiento,
                            "curp": curp.upper(),
                            "nss": nss,
                            "sexo": sexo,
                            "civil": estado_civil,
                            "domicilio": domicilio,
                            "email": email,
                            "telefono": telefono,
                            "diagnostico": diagnostico
                        })
                        s.commit()
                    st.success("Paciente registrado exitosamente")
                except Exception as e:
                    st.error(f"Error al registrar: {e}")

# ==================== TAB 3: EDITAR/ELIMINAR PACIENTE ====================
with tab_editar:
    st.subheader("Editar o Eliminar Paciente")
    
    # Obtener lista de pacientes activos
    try:
        pacientes_activos = conn.query(
            'SELECT id, nombre, apellido_paterno, apellido_materno FROM public.pacientes WHERE activo = true ORDER BY nombre;',
            ttl="10s"
        )
    except Exception as e:
        st.error(f"Error al cargar pacientes: {e}")
        pacientes_activos = pd.DataFrame()
    
    if not pacientes_activos.empty:
        # Selector de paciente
        pacientes_activos['nombre_completo'] = (
            pacientes_activos['nombre'] + ' ' + 
            pacientes_activos['apellido_paterno'] + ' ' +
            pacientes_activos['apellido_materno'].fillna('')
        ).str.strip()
        
        paciente_seleccionado = st.selectbox(
            "Selecciona un paciente",
            options=pacientes_activos['id'].tolist(),
            format_func=lambda x: pacientes_activos[pacientes_activos['id'] == x]['nombre_completo'].values[0],
            key="edit_paciente_selector"
        )
        
        if paciente_seleccionado:
            # Obtener datos del paciente
            try:
                with conn.session as s:
                    query = text("""
                        SELECT id, nombre, apellido_paterno, apellido_materno, fecha_nacimiento, 
                               curp, nss, sexo, estado_civil, domicilio, email, telefono, diagnostico
                        FROM public.pacientes
                        WHERE id = :pid
                    """)
                    resultado = s.execute(query, {'pid': paciente_seleccionado}).fetchone()
                
                if resultado:
                    paciente_data = {
                        'id': resultado[0],
                        'nombre': resultado[1],
                        'apellido_paterno': resultado[2],
                        'apellido_materno': resultado[3],
                        'fecha_nacimiento': resultado[4],
                        'curp': resultado[5],
                        'nss': resultado[6],
                        'sexo': resultado[7],
                        'estado_civil': resultado[8],
                        'domicilio': resultado[9],
                        'email': resultado[10],
                        'telefono': resultado[11],
                        'diagnostico': resultado[12]
                    }
                    
                    st.markdown("---")
                    
                    col_editar, col_eliminar = st.columns(2)
                    
                    with col_editar:
                        if st.button("Editar Información", use_container_width=True):
                            st.session_state['mostrar_form_editar'] = True
                    
                    with col_eliminar:
                        if st.button("Desactivar Paciente", use_container_width=True, type="secondary"):
                            st.session_state['confirmar_eliminar'] = True
                    
                    # Formulario de edición
                    if st.session_state.get('mostrar_form_editar', False):
                        st.markdown("### Editar Información del Paciente")
                        
                        with st.form("editar_paciente_form"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("**Información Personal**")
                                nombre_edit = st.text_input("Nombre(s)", value=paciente_data['nombre'])
                                apellido_paterno_edit = st.text_input("Apellido Paterno", value=paciente_data['apellido_paterno'])
                                fecha_nacimiento_edit = st.date_input("Fecha de Nacimiento", value=paciente_data['fecha_nacimiento'])
                                sexo_edit = st.selectbox("Sexo", ["Masculino", "Femenino"], index=0 if paciente_data['sexo'] == "Masculino" else 1)
                            
                            with col2:
                                st.markdown("**Información Adicional**")
                                apellido_materno_edit = st.text_input("Apellido Materno", value=paciente_data['apellido_materno'] or "")
                                curp_edit = st.text_input("CURP", value=paciente_data['curp'])
                                nss_edit = st.text_input("NSS", value=paciente_data['nss'] or "")
                                estado_civil_edit = st.text_input("Estado Civil", value=paciente_data['estado_civil'] or "")
                            
                            st.markdown("**Información de Contacto**")
                            col1, col2 = st.columns(2)
                            with col1:
                                email_edit = st.text_input("Correo Electrónico", value=paciente_data['email'])
                            with col2:
                                telefono_edit = st.text_input("Teléfono", value=paciente_data['telefono'] or "")
                            
                            domicilio_edit = st.text_area("Domicilio Completo", value=paciente_data['domicilio'] or "")
                            diagnostico_edit = st.text_area("Diagnóstico", value=paciente_data['diagnostico'] or "")
                            
                            col_submit, col_cancel = st.columns(2)
                            with col_submit:
                                submit_edit = st.form_submit_button("Guardar Cambios", use_container_width=True, type="primary")
                            with col_cancel:
                                if st.form_submit_button("Cancelar", use_container_width=True):
                                    st.session_state['mostrar_form_editar'] = False
                                    st.rerun()
                            
                            if submit_edit:
                                try:
                                    with conn.session as s:
                                        query = text("""
                                            UPDATE public.pacientes
                                            SET nombre = :nombre,
                                                apellido_paterno = :paterno,
                                                apellido_materno = :materno,
                                                fecha_nacimiento = :nacimiento,
                                                curp = :curp,
                                                nss = :nss,
                                                sexo = :sexo,
                                                estado_civil = :civil,
                                                domicilio = :domicilio,
                                                email = :email,
                                                telefono = :telefono,
                                                diagnostico = :diagnostico
                                            WHERE id = :pid
                                        """)
                                        s.execute(query, params={
                                            'nombre': nombre_edit,
                                            'paterno': apellido_paterno_edit,
                                            'materno': apellido_materno_edit,
                                            'nacimiento': fecha_nacimiento_edit,
                                            'curp': curp_edit.upper(),
                                            'nss': nss_edit,
                                            'sexo': sexo_edit,
                                            'civil': estado_civil_edit,
                                            'domicilio': domicilio_edit,
                                            'email': email_edit,
                                            'telefono': telefono_edit,
                                            'diagnostico': diagnostico_edit,
                                            'pid': paciente_seleccionado
                                        })
                                        s.commit()
                                    
                                    st.success("Cambios guardados exitosamente")
                                    st.session_state['mostrar_form_editar'] = False
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error al guardar cambios: {e}")
                    
                    # Confirmación de eliminación
                    if st.session_state.get('confirmar_eliminar', False):
                        st.markdown("---")
                        st.warning(
                            f"¿Estás seguro de que deseas desactivar a **{paciente_data['nombre']} {paciente_data['apellido_paterno']}**? "
                            f"Esta acción se puede revertir."
                        )
                        
                        col_confirmar, col_cancelar = st.columns(2)
                        
                        with col_confirmar:
                            if st.button("Sí, desactivar", use_container_width=True, type="primary"):
                                try:
                                    with conn.session as s:
                                        query = text("""
                                            UPDATE public.pacientes
                                            SET activo = false
                                            WHERE id = :pid
                                        """)
                                        s.execute(query, {'pid': paciente_seleccionado})
                                        s.commit()
                                    
                                    st.success("Paciente desactivado exitosamente")
                                    st.session_state['confirmar_eliminar'] = False
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error al desactivar paciente: {e}")
                        
                        with col_cancelar:
                            if st.button("No, cancelar", use_container_width=True):
                                st.session_state['confirmar_eliminar'] = False
                                st.rerun()
            
            except Exception as e:
                st.error(f"Error al cargar datos del paciente: {e}")
    else:
        st.info("No hay pacientes activos para editar.")
