import streamlit as st
import pandas as pd
from datetime import date, timedelta
import time
from sqlalchemy import text
from auth import require_auth
from sidebar import render_sidebar
from theme import apply_global_theme
from utils import breadcrumb_nav

# --- PROTECCIÓN DE RUTA ---
require_auth(allowed_roles=['administrador'])
render_sidebar()
apply_global_theme()

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Gestión de Pacientes", page_icon="👥", layout="wide")

# --- BREADCRUMBS ---
breadcrumb_nav(["Home", "Administración", "Pacientes"])

# --- CONEXIÓN A LA BASE DE DATOS ---
try:
    conn = st.connection("postgresql", type="sql")
except Exception:
    st.error("No se pudo establecer conexión con la base de datos.")
    st.stop()

# --- ESTILOS CSS ---
st.markdown("""
<style>
    .patient-card {
        background: linear-gradient(135deg, #f8f9ff 0%, #f0f4ff 100%);
        border-left: 4px solid #0066CC;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 12px;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .patient-card:hover {
        box-shadow: 0 8px 16px rgba(0, 102, 204, 0.15);
        transform: translateX(4px);
        border-left-color: #004499;
    }
    
    .metric-badge {
        display: inline-block;
        background: white;
        padding: 6px 12px;
        border-radius: 16px;
        font-size: 0.85em;
        margin: 0 4px 4px 0;
        border: 1px solid #e0e0e0;
    }
    
    .metric-value {
        font-weight: 600;
        color: #0066CC;
    }
    
    .status-healthy {
        color: #10b981;
    }
    
    .status-alert {
        color: #ef4444;
    }
    
    .status-warning {
        color: #f59e0b;
    }
</style>
""", unsafe_allow_html=True)

st.title("👥 Gestión de Pacientes")
st.markdown("---")

# --- TABS ---
tab_listado, tab_registro, tab_editar = st.tabs(["📋 Ver Pacientes", "➕ Registrar Nuevo", "✏️ Editar/Eliminar"])

# ==================== TAB 1: VER PACIENTES ====================
with tab_listado:
    
    # Obtener datos de pacientes
    try:
        pacientes_df = conn.query(
            'SELECT id, nombre, apellido_paterno, apellido_materno, email, telefono, diagnostico FROM public.pacientes ORDER BY nombre;',
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
                "🔍 Buscar paciente por nombre",
                placeholder="Ingresa el nombre del paciente...",
                key="search_paciente"
            )
        with col2:
            st.write("")
            if st.button("🔄 Refrescar", use_container_width=True):
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
            # --- LISTA DE PACIENTES ---
            st.subheader(f"Pacientes Encontrados ({len(filtered_df)})")
            
            for idx, paciente in filtered_df.iterrows():
                paciente_id = paciente['id']
                nombre_completo = f"{paciente['nombre']} {paciente['apellido_paterno']} {paciente.get('apellido_materno', '')}".strip()
                
                # Obtener métricas recientes del paciente
                try:
                    with conn.session as s:
                        metrics_query = text("""
                            SELECT 
                                m.tipo_medicion,
                                m.valor,
                                m.unidad_medida,
                                m.timestamp
                            FROM public.mediciones m
                            JOIN public.dispositivos d ON m.dispositivo_id = d.id
                            WHERE d.paciente_id = :pid
                            ORDER BY m.timestamp DESC
                            LIMIT 10
                        """)
                        
                        metrics = s.execute(metrics_query, {'pid': paciente_id}).fetchall()
                    
                    # Agrupar métricas por tipo
                    last_metrics = {}
                    for m in metrics:
                        if m[0] not in last_metrics:
                            last_metrics[m[0]] = (m[1], m[2], m[3])
                    
                    # Obtener alertas pendientes
                    alertas_query_result = conn.query(
                        f"""SELECT COUNT(*) as alertas FROM public.alertas a 
                           WHERE a.medicion_id IN (SELECT id FROM public.mediciones 
                                                   WHERE dispositivo_id IN (SELECT id FROM public.dispositivos WHERE paciente_id = {paciente_id}))
                           AND a.leida = false""",
                        ttl="5s"
                    )
                    alertas = alertas_query_result.iloc[0]['alertas'] if not alertas_query_result.empty else 0
                    
                except Exception as e:
                    last_metrics = {}
                    alertas = 0
                
                # Estado del paciente
                estado = "🟢 Estable"
                color_estado = "status-healthy"
                if alertas > 0:
                    estado = f"🔴 {alertas} Alerta(s)"
                    color_estado = "status-alert"
                
                # Card del paciente
                with st.container(border=True):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.markdown(f"### {nombre_completo}")
                        if paciente.get('diagnostico'):
                            st.caption(f"📋 {paciente['diagnostico']}")
                        if paciente.get('email'):
                            st.caption(f"📧 {paciente['email']}")
                    
                    with col2:
                        st.write("**Últimas Métricas:**")
                        if last_metrics:
                            cols = st.columns(len(last_metrics))
                            for col_idx, (tipo, (valor, unidad, timestamp)) in enumerate(list(last_metrics.items())[:3]):
                                with cols[col_idx]:
                                    st.metric(
                                        label=tipo.replace('_', ' ').title(),
                                        value=f"{valor} {unidad}",
                                    )
                        else:
                            st.caption("Sin mediciones registradas")
                    
                    with col3:
                        st.write("")
                        st.markdown(f"<div class='{color_estado}'>{estado}</div>", unsafe_allow_html=True)
                    
                    # Expandir para ver detalles
                    st.write("")
                    if st.button(f"📊 Ver Detalles", key=f"btn_detalles_{paciente_id}"):
                        st.session_state[f"expand_{paciente_id}"] = True
                    
                    # Mostrar detalles si está expandido
                    if st.session_state.get(f"expand_{paciente_id}", False):
                        st.markdown("---")
                        st.subheader(f"Métricas Detalladas - {nombre_completo}")
                        
                        # Obtener historial completo
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
                                # Convertir a dataframe para mejor visualización
                                historial_df = pd.DataFrame(
                                    historial,
                                    columns=['Tipo de Medición', 'Valor', 'Unidad', 'Fecha/Hora']
                                )
                                
                                # Agrupar por tipo de medición
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
                                st.info("Sin historial de mediciones para este paciente.")
                        
                        except Exception as e:
                            st.error(f"Error al cargar historial: {e}")
                        
                        st.write("")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"👁️ Ver en Vivo", key=f"btn_vivo_{paciente_id}"):
                                # Obtener dispositivo del paciente
                                try:
                                    with conn.session as s:
                                        dispositivo_query = text("""
                                            SELECT id FROM public.dispositivos
                                            WHERE paciente_id = :pid AND activo = true
                                            LIMIT 1
                                        """)
                                        dispositivo_result = s.execute(dispositivo_query, {'pid': paciente_id}).fetchone()
                                    
                                    if dispositivo_result:
                                        dispositivo_id = dispositivo_result[0]
                                        st.session_state['selected_dispositivo_id'] = dispositivo_id
                                        st.session_state['selected_paciente_id'] = paciente_id
                                        st.session_state['ir_a_visualizacion'] = True
                                        st.success("Navegando a visualización en vivo...")
                                        time.sleep(0.5)
                                        st.switch_page("pages/05_monitoreo_dashboard.py")
                                    else:
                                        st.warning(f"Este paciente no tiene un dispositivo activo asignado.")
                                except Exception as e:
                                    st.error(f"Error al navegar: {e}")
                        with col2:
                            if st.button(f"❌ Cerrar Detalles", key=f"btn_cerrar_{paciente_id}"):
                                st.session_state[f"expand_{paciente_id}"] = False
                                st.rerun()
    else:
        st.info("No hay pacientes registrados en el sistema.")

# ==================== TAB 2: REGISTRAR PACIENTE ====================
with tab_registro:
    st.subheader("➕ Registrar Nuevo Paciente")
    
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
            submit = st.form_submit_button("✅ Registrar", use_container_width=True, type="primary")
        
        if submit:
            if not all([nombre, apellido_paterno, fecha_nacimiento, curp, email, sexo]):
                st.warning("⚠️ Por favor, completa todos los campos obligatorios.")
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
                    st.success("✅ ¡Paciente registrado exitosamente!")
                except Exception as e:
                    st.error(f"❌ Error al registrar: {e}")

# ==================== TAB 3: EDITAR/ELIMINAR PACIENTE ====================
with tab_editar:
    st.subheader("✏️ Editar o Eliminar Paciente")
    st.info("Solo administradores pueden editar o eliminar pacientes.")
    
    # Verificar permiso de admin
    if st.session_state.get('user_role') != 'administrador':
        st.error("❌ Solo administradores tienen acceso a esta sección.")
        st.stop()
    
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
                    
                    # Tabs para editar o eliminar
                    col_editar, col_eliminar = st.columns(2)
                    
                    with col_editar:
                        if st.button("✏️ Editar Información", use_container_width=True):
                            st.session_state['mostrar_form_editar'] = True
                    
                    with col_eliminar:
                        if st.button("🗑️ Desactivar Paciente", use_container_width=True, type="secondary"):
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
                                submit_edit = st.form_submit_button("💾 Guardar Cambios", use_container_width=True, type="primary")
                            with col_cancel:
                                if st.form_submit_button("❌ Cancelar", use_container_width=True):
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
                                    
                                    st.success("✅ ¡Cambios guardados exitosamente!")
                                    st.session_state['mostrar_form_editar'] = False
                                    import time
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error al guardar cambios: {e}")
                    
                    # Confirmación de eliminación
                    if st.session_state.get('confirmar_eliminar', False):
                        st.markdown("---")
                        st.warning(
                            f"⚠️ ¿Estás seguro de que deseas desactivar a **{paciente_data['nombre']} {paciente_data['apellido_paterno']}**? "
                            f"Esta acción se puede revertir."
                        )
                        
                        col_confirmar, col_cancelar = st.columns(2)
                        
                        with col_confirmar:
                            if st.button("🗑️ Sí, desactivar", use_container_width=True, type="primary"):
                                try:
                                    with conn.session as s:
                                        query = text("""
                                            UPDATE public.pacientes
                                            SET activo = false
                                            WHERE id = :pid
                                        """)
                                        s.execute(query, {'pid': paciente_seleccionado})
                                        s.commit()
                                    
                                    st.success("✅ ¡Paciente desactivado exitosamente!")
                                    st.session_state['confirmar_eliminar'] = False
                                    import time
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error al desactivar paciente: {e}")
                        
                        with col_cancelar:
                            if st.button("❌ No, cancelar", use_container_width=True):
                                st.session_state['confirmar_eliminar'] = False
                                st.rerun()
            
            except Exception as e:
                st.error(f"Error al cargar datos del paciente: {e}")
    else:
        st.info("No hay pacientes activos para editar.")

