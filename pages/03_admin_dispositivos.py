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

st.set_page_config(page_title="Gestión de Dispositivos", page_icon="⌚", layout="wide")

# --- BREADCRUMBS ---
breadcrumb_nav(["Home", "Administración", "Dispositivos"])

# --- CONEXIÓN A LA BASE DE DATOS ---
try:
    conn = st.connection("postgresql", type="sql")
except Exception:
    st.error("No se pudo establecer conexión con la base de datos.")
    st.stop()

# --- ESTILOS CSS ---
st.markdown("""
<style>
    .device-card {
        background: linear-gradient(135deg, #fff8f0 0%, #fff0e6 100%);
        border-left: 4px solid #f97316;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 12px;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .device-card:hover {
        box-shadow: 0 8px 16px rgba(249, 115, 22, 0.15);
        transform: translateX(4px);
        border-left-color: #ea580c;
    }
    
    .status-active {
        color: #10b981;
    }
    
    .status-inactive {
        color: #f59e0b;
    }
    
    .status-unassigned {
        color: #6b7280;
    }
    
    .info-box {
        background: #f3f4f6;
        border: 1px solid #d1d5db;
        padding: 12px;
        border-radius: 6px;
        font-family: monospace;
        font-size: 0.9em;
        margin: 8px 0;
    }
    
    .patient-badge {
        background: #dbeafe;
        padding: 8px 12px;
        border-radius: 6px;
        margin: 4px 0;
        border-left: 3px solid #0284c7;
    }
</style>
""", unsafe_allow_html=True)

st.title("⌚ Gestión de Dispositivos de Monitoreo")
st.markdown("---")

# --- TABS ---
tab_listado, tab_registro, tab_editar = st.tabs(["📋 Ver Dispositivos", "➕ Registrar Nuevo", "✏️ Editar/Eliminar"])

# ==================== TAB 1: VER DISPOSITIVOS ====================
with tab_listado:
    
    # Obtener datos de dispositivos
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
                "🔍 Buscar dispositivo por modelo o paciente",
                placeholder="Ingresa el modelo o nombre del paciente...",
                key="search_dispositivo"
            )
        with col2:
            st.write("")
            if st.button("🔄 Refrescar", use_container_width=True):
                st.rerun()
        
        st.write("")
        
        # Filtrar dispositivos según búsqueda
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
            # --- LISTA DE DISPOSITIVOS ---
            st.subheader(f"Dispositivos Registrados ({len(filtered_df)})")
            
            # Estadísticas rápidas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Dispositivos", len(filtered_df))
            with col2:
                activos = (filtered_df['activo'] == True).sum()
                st.metric("Dispositivos Activos", activos)
            with col3:
                inactivos = (filtered_df['activo'] == False).sum()
                st.metric("Dispositivos Inactivos", inactivos)
            
            st.write("")
            
            for idx, dispositivo in filtered_df.iterrows():
                device_id = dispositivo['id']
                modelo = dispositivo['modelo']
                mac = dispositivo['mac_address']
                activo = dispositivo['activo']
                
                # Determinar estado
                if activo:
                    estado = "🟢 Activo"
                    estado_clase = "status-active"
                else:
                    estado = "🟡 Inactivo"
                    estado_clase = "status-inactive"
                
                # Información del paciente asignado
                if pd.notna(dispositivo['paciente_id']):
                    paciente_nombre = f"{dispositivo['nombre']} {dispositivo['apellido_paterno']} {dispositivo.get('apellido_materno', '')}".strip()
                    paciente_info = f"👤 {paciente_nombre}"
                else:
                    paciente_info = "⚠️ Sin paciente asignado"
                
                # Card del dispositivo
                with st.container(border=True):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.markdown(f"### ⌚ {modelo}")
                        st.caption(f"MAC: {mac if mac else 'No especificada'}")
                    
                    with col2:
                        st.write("**Información:**")
                        st.caption(f"Registrado: {pd.to_datetime(dispositivo['fecha_asignacion']).strftime('%d/%m/%Y')}")
                        st.caption(paciente_info)
                    
                    with col3:
                        st.write("")
                        st.markdown(f"<div class='{estado_clase}'>{estado}</div>", unsafe_allow_html=True)
                    
                    # Expandir para ver detalles
                    st.write("")
                    if st.button(f"📊 Detalles", key=f"btn_detalles_dev_{device_id}"):
                        st.session_state[f"expand_dev_{device_id}"] = True
                    
                    # Mostrar detalles si está expandido
                    if st.session_state.get(f"expand_dev_{device_id}", False):
                        st.markdown("---")
                        st.subheader(f"Detalles - {modelo}")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**Especificaciones Técnicas:**")
                            st.markdown(f"""
                            <div class="info-box">
                            Modelo: <b>{modelo}</b><br>
                            MAC Address: <b>{mac if mac else 'N/A'}</b><br>
                            ID Dispositivo: <b>{device_id}</b><br>
                            Estado: <b>{estado.replace('🟢', '').replace('🟡', '').strip()}</b>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown("**Asignación:**")
                            if pd.notna(dispositivo['paciente_id']):
                                st.markdown(f"""
                                <div class="patient-badge">
                                👤 Paciente ID: {dispositivo['paciente_id']}<br>
                                Nombre: {paciente_nombre}<br>
                                Asignado: {pd.to_datetime(dispositivo['fecha_asignacion']).strftime('%d/%m/%Y %H:%M')}
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.warning("Este dispositivo no está asignado a ningún paciente")
                        
                        st.write("")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"⚙️ Editar", key=f"btn_edit_{device_id}"):
                                st.info("Funcionalidad de edición disponible próximamente")
                        with col2:
                            if st.button(f"❌ Cerrar", key=f"btn_cerrar_dev_{device_id}"):
                                st.session_state[f"expand_dev_{device_id}"] = False
                                st.rerun()
    else:
        st.info("No hay dispositivos registrados en el sistema.")

# ==================== TAB 2: REGISTRAR DISPOSITIVO ====================
with tab_registro:
    st.subheader("➕ Registrar Nuevo Dispositivo")
    
    # Obtener lista de pacientes para asignación
    try:
        pacientes_df = conn.query("""
            SELECT id, nombre, apellido_paterno, apellido_materno 
            FROM public.pacientes 
            ORDER BY nombre
        """, ttl="10s")
        
        pacientes_opciones = {
            f"{p['nombre']} {p['apellido_paterno']} {p.get('apellido_materno', '')}".strip(): p['id']
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
            submit = st.form_submit_button("✅ Registrar", use_container_width=True, type="primary")
        
        if submit:
            if not modelo:
                st.warning("⚠️ Por favor, ingresa el modelo del dispositivo.")
            else:
                try:
                    # Obtener ID del paciente
                    if paciente_asignado == "Sin asignar":
                        paciente_id = None
                    else:
                        paciente_id = pacientes_opciones[paciente_asignado]
                    
                    # Insertar dispositivo
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
                    
                    st.success(f"✅ ¡Dispositivo registrado exitosamente! (ID: {device_id})")
                    st.markdown(f"""
                    **Dispositivo creado:**
                    - Modelo: `{modelo}`
                    - MAC: `{mac_address if mac_address else 'N/A'}`
                    - Paciente: {paciente_asignado}
                    - Estado: {'Activo ✅' if activo else 'Inactivo ⏸️'}
                    """)
                
                except Exception as e:
                    st.error(f"❌ Error al registrar: {e}")

# ==================== TAB 3: EDITAR/ELIMINAR DISPOSITIVO ====================
with tab_editar:
    st.subheader("✏️ Editar o Eliminar Dispositivo")
    st.info("Solo administradores pueden editar o eliminar dispositivos.")
    
    # Verificar permiso de admin
    if st.session_state.get('user_role') != 'administrador':
        st.error("❌ Solo administradores tienen acceso a esta sección.")
        st.stop()
    
    # Obtener lista de dispositivos activos
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
        # Selector de dispositivo
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
            # Obtener datos completos del dispositivo
            try:
                with conn.session as s:
                    query = text("""
                        SELECT id, modelo, mac_address, paciente_id, latitude, longitude, direccion_url
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
                        'latitude': resultado[4],
                        'longitude': resultado[5],
                        'direccion_url': resultado[6]
                    }
                    
                    st.markdown("---")
                    
                    # Tabs para editar o eliminar
                    col_editar, col_eliminar = st.columns(2)
                    
                    with col_editar:
                        if st.button("✏️ Editar Información", use_container_width=True):
                            st.session_state['mostrar_form_editar_dispositivo'] = True
                    
                    with col_eliminar:
                        if st.button("🗑️ Desactivar Dispositivo", use_container_width=True, type="secondary"):
                            st.session_state['confirmar_eliminar_dispositivo'] = True
                    
                    # Formulario de edición
                    if st.session_state.get('mostrar_form_editar_dispositivo', False):
                        st.markdown("### Editar Información del Dispositivo")
                        
                        # Obtener pacientes para selector
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
                                direccion_url_edit = st.text_input("URL de Dirección", value=dispositivo_data['direccion_url'] or "")
                            
                            with col2:
                                st.markdown("**Ubicación Geográfica**")
                                lat_edit = st.number_input(
                                    "Latitud",
                                    value=float(dispositivo_data['latitude']) if dispositivo_data['latitude'] else 0.0,
                                    format="%.8f",
                                    min_value=-90.0,
                                    max_value=90.0
                                )
                                lon_edit = st.number_input(
                                    "Longitud",
                                    value=float(dispositivo_data['longitude']) if dispositivo_data['longitude'] else 0.0,
                                    format="%.8f",
                                    min_value=-180.0,
                                    max_value=180.0
                                )
                            
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
                                submit_edit = st.form_submit_button("💾 Guardar Cambios", use_container_width=True, type="primary")
                            with col_cancel:
                                if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                    st.session_state['mostrar_form_editar_dispositivo'] = False
                                    st.rerun()
                            
                            if submit_edit:
                                try:
                                    with conn.session as s:
                                        query = text("""
                                            UPDATE public.dispositivos
                                            SET modelo = :modelo,
                                                mac_address = :mac,
                                                latitude = :lat,
                                                longitude = :lon,
                                                direccion_url = :url,
                                                paciente_id = :paciente_id
                                            WHERE id = :did
                                        """)
                                        s.execute(query, params={
                                            'modelo': modelo_edit,
                                            'mac': mac_edit if mac_edit else None,
                                            'lat': lat_edit if lat_edit != 0.0 else None,
                                            'lon': lon_edit if lon_edit != 0.0 else None,
                                            'url': direccion_url_edit if direccion_url_edit else None,
                                            'paciente_id': paciente_edit,
                                            'did': dispositivo_seleccionado
                                        })
                                        s.commit()
                                    
                                    st.success("✅ ¡Cambios guardados exitosamente!")
                                    st.session_state['mostrar_form_editar_dispositivo'] = False
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error al guardar cambios: {e}")
                    
                    # Confirmación de eliminación
                    if st.session_state.get('confirmar_eliminar_dispositivo', False):
                        st.markdown("---")
                        st.warning(
                            f"⚠️ ¿Estás seguro de que deseas desactivar el dispositivo **{dispositivo_data['modelo']} ({dispositivo_data['mac_address']})**? "
                            f"Esta acción se puede revertir."
                        )
                        
                        col_confirmar, col_cancelar = st.columns(2)
                        
                        with col_confirmar:
                            if st.button("🗑️ Sí, desactivar", use_container_width=True, type="primary"):
                                try:
                                    with conn.session as s:
                                        query = text("""
                                            UPDATE public.dispositivos
                                            SET activo = false
                                            WHERE id = :did
                                        """)
                                        s.execute(query, {'did': dispositivo_seleccionado})
                                        s.commit()
                                    
                                    st.success("✅ ¡Dispositivo desactivado exitosamente!")
                                    st.session_state['confirmar_eliminar_dispositivo'] = False
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error al desactivar dispositivo: {e}")
                        
                        with col_cancelar:
                            if st.button("❌ No, cancelar", use_container_width=True):
                                st.session_state['confirmar_eliminar_dispositivo'] = False
                                st.rerun()
            
            except Exception as e:
                st.error(f"Error al cargar datos del dispositivo: {e}")
    else:
        st.info("No hay dispositivos activos para editar.")