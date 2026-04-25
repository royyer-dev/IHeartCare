import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import text
from core.auth import require_auth
from core.sidebar import render_sidebar
from core.theme import apply_global_theme
from utils import breadcrumb_nav

# --- PROTECCIÓN DE RUTA ---
require_auth(allowed_roles=['administrador'])
render_sidebar()
apply_global_theme()

st.set_page_config(page_title="Gestión de Monitoreos", page_icon="📊", layout="wide")

# --- BREADCRUMBS ---
breadcrumb_nav(["Home", "Administración", "Monitoreos"])

# --- CONEXIÓN A LA BASE DE DATOS ---
try:
    conn = st.connection("postgresql", type="sql")
except Exception:
    st.error("No se pudo establecer conexión con la base de datos.")
    st.stop()

# --- ESTILOS CSS ---
st.markdown("""
<style>
    .monitoring-card {
        background: linear-gradient(135deg, #f0fdf4 0%, #e8f9f0 100%);
        border-left: 4px solid #10b981;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 12px;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .monitoring-card:hover {
        box-shadow: 0 8px 16px rgba(16, 185, 129, 0.15);
        transform: translateX(4px);
        border-left-color: #059669;
    }
    
    .monitoring-card.inactive {
        background: linear-gradient(135deg, #f3f4f6 0%, #efefef 100%);
        border-left-color: #9ca3af;
    }
    
    .monitoring-card.inactive:hover {
        border-left-color: #6b7280;
    }
    
    .status-active {
        color: #10b981;
        font-weight: 600;
    }
    
    .status-inactive {
        color: #6b7280;
        font-weight: 600;
    }
    
    .info-box {
        background: #f3f4f6;
        border: 1px solid #d1d5db;
        padding: 12px;
        border-radius: 6px;
        font-size: 0.9em;
        margin: 8px 0;
    }
    
    .device-badge {
        background: #dbeafe;
        padding: 8px 12px;
        border-radius: 6px;
        margin: 4px 0;
        border-left: 3px solid #0284c7;
    }
    
    .time-badge {
        background: #fef3c7;
        padding: 8px 12px;
        border-radius: 6px;
        margin: 4px 0;
        border-left: 3px solid #f59e0b;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Gestión de Monitoreos Clínicos")
st.markdown("---")

# --- TABS ---
tab_crear, tab_activos, tab_historico = st.tabs(["➕ Crear Monitoreo", "🟢 Monitoreos Activos", "📜 Histórico"])

# ==================== TAB 1: CREAR MONITOREO ====================
with tab_crear:
    st.subheader("➕ Crear Nuevo Monitoreo")
    
    # Obtener pacientes
    try:
        pacientes_df = conn.query("""
            SELECT id, nombre, apellido_paterno, apellido_materno, diagnostico
            FROM public.pacientes
            ORDER BY nombre
        """, ttl="10s")
    except Exception as e:
        st.error(f"Error al cargar pacientes: {e}")
        pacientes_df = pd.DataFrame()
    
    if pacientes_df.empty:
        st.warning("No hay pacientes registrados en el sistema.")
    else:
        with st.form("crear_monitoreo_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Selecciona el Paciente**")
                pacientes_opciones = {
                    f"{p['nombre']} {p['apellido_paterno']} {p.get('apellido_materno', '')}".strip(): p['id']
                    for _, p in pacientes_df.iterrows()
                }
                paciente_nombre = st.selectbox(
                    "Paciente",
                    options=list(pacientes_opciones.keys()),
                    label_visibility="collapsed"
                )
                paciente_id = pacientes_opciones[paciente_nombre]
                
                # Obtener paciente seleccionado
                paciente_sel = pacientes_df[pacientes_df['id'] == paciente_id].iloc[0]
                st.caption(f"📋 Diagnóstico: {paciente_sel.get('diagnostico', 'No especificado')}")
            
            with col2:
                st.markdown("**Selecciona el Dispositivo**")
                
                # Obtener dispositivos del paciente
                try:
                    dispositivos_df = conn.query(f"""
                        SELECT id, modelo, mac_address, activo
                        FROM public.dispositivos
                        WHERE paciente_id = {paciente_id}
                        ORDER BY modelo
                    """, ttl="5s")
                except Exception:
                    dispositivos_df = pd.DataFrame()
                
                if dispositivos_df.empty:
                    st.warning("⚠️ Este paciente no tiene dispositivos asignados.")
                    dispositivo_id = None
                else:
                    dispositivos_opciones = {
                        f"{d['modelo']} {'✅' if d['activo'] else '⏸️'}": d['id']
                        for _, d in dispositivos_df.iterrows()
                    }
                    dispositivo_nombre = st.selectbox(
                        "Dispositivo",
                        options=list(dispositivos_opciones.keys()),
                        label_visibility="collapsed"
                    )
                    dispositivo_id = dispositivos_opciones[dispositivo_nombre]
            
            st.markdown("---")
            st.markdown("**Configura el Período de Monitoreo**")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                tiempo_tipo = st.radio(
                    "Tipo de Monitoreo",
                    options=["Período definido", "Indefinido (Para siempre)"],
                    label_visibility="collapsed"
                )
            
            with col2:
                if tiempo_tipo == "Período definido":
                    fecha_inicio = st.date_input(
                        "Fecha de Inicio",
                        value=datetime.now().date(),
                        label_visibility="collapsed"
                    )
                else:
                    fecha_inicio = None
            
            with col3:
                if tiempo_tipo == "Período definido":
                    fecha_fin = st.date_input(
                        "Fecha de Fin",
                        value=(datetime.now() + timedelta(days=30)).date(),
                        label_visibility="collapsed"
                    )
                else:
                    fecha_fin = None
            
            st.markdown("---")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                motivo = st.text_area(
                    "Motivo del Monitoreo (Opcional)",
                    placeholder="Ej. Control post-operatorio, ajuste de medicación, seguimiento cardíaco...",
                    height=80
                )
            
            with col2:
                st.write("")
                st.write("")
                submit = st.form_submit_button("✅ Crear Monitoreo", type="primary", use_container_width=True)
            
            if submit:
                if not dispositivo_id:
                    st.error("⚠️ El paciente no tiene dispositivos asignados.")
                else:
                    # Validar fechas
                    if tiempo_tipo == "Período definido":
                        if fecha_inicio >= fecha_fin:
                            st.error("⚠️ La fecha de fin debe ser posterior a la fecha de inicio.")
                        else:
                            try:
                                monitoreo_query = text("""
                                    INSERT INTO public.monitoreos 
                                    (paciente_id, fecha_inicio, fecha_fin, motivo, activo)
                                    VALUES (:paciente_id, :fecha_inicio, :fecha_fin, :motivo, true)
                                    RETURNING id
                                """)
                                
                                with conn.session as s:
                                    result = s.execute(monitoreo_query, {
                                        "paciente_id": paciente_id,
                                        "fecha_inicio": datetime.combine(fecha_inicio, datetime.min.time()),
                                        "fecha_fin": datetime.combine(fecha_fin, datetime.min.time()),
                                        "motivo": motivo if motivo else None
                                    })
                                    monitoreo_id = result.fetchone()[0]
                                    s.commit()
                                
                                st.success(f"✅ ¡Monitoreo creado exitosamente! (ID: {monitoreo_id})")
                                st.markdown(f"""
                                **Resumen:**
                                - Paciente: {paciente_nombre}
                                - Dispositivo: {dispositivo_nombre}
                                - Inicio: {fecha_inicio.strftime('%d/%m/%Y')}
                                - Fin: {fecha_fin.strftime('%d/%m/%Y')}
                                - Duración: {(fecha_fin - fecha_inicio).days} días
                                """)
                            except Exception as e:
                                st.error(f"❌ Error al crear monitoreo: {e}")
                    else:
                        try:
                            monitoreo_query = text("""
                                INSERT INTO public.monitoreos 
                                (paciente_id, fecha_inicio, motivo, activo)
                                VALUES (:paciente_id, :fecha_inicio, :motivo, true)
                                RETURNING id
                            """)
                            
                            with conn.session as s:
                                result = s.execute(monitoreo_query, {
                                    "paciente_id": paciente_id,
                                    "fecha_inicio": datetime.now(),
                                    "motivo": motivo if motivo else None
                                })
                                monitoreo_id = result.fetchone()[0]
                                s.commit()
                            
                            st.success(f"✅ ¡Monitoreo indefinido creado exitosamente! (ID: {monitoreo_id})")
                            st.markdown(f"""
                            **Resumen:**
                            - Paciente: {paciente_nombre}
                            - Dispositivo: {dispositivo_nombre}
                            - Duración: ∞ (Indefinido)
                            - Iniciado: {datetime.now().strftime('%d/%m/%Y %H:%M')}
                            """)
                        except Exception as e:
                            st.error(f"❌ Error al crear monitoreo: {e}")

# ==================== TAB 2: MONITOREOS ACTIVOS ====================
with tab_activos:
    st.subheader("🟢 Monitoreos Activos")
    
    try:
        monitoreos_activos = conn.query("""
            SELECT 
                m.id,
                m.fecha_inicio,
                m.fecha_fin,
                m.motivo,
                p.id as paciente_id,
                p.nombre,
                p.apellido_paterno,
                p.apellido_materno,
                p.diagnostico,
                d.id as dispositivo_id,
                d.modelo,
                d.mac_address,
                d.activo as dispositivo_activo
            FROM public.monitoreos m
            JOIN public.pacientes p ON m.paciente_id = p.id
            LEFT JOIN public.dispositivos d ON p.id = d.paciente_id
            WHERE m.activo = true
            ORDER BY m.fecha_inicio DESC
        """, ttl="5s")
    except Exception as e:
        st.error(f"Error al cargar monitoreos activos: {e}")
        monitoreos_activos = pd.DataFrame()
    
    if monitoreos_activos.empty:
        st.info("No hay monitoreos activos en el sistema.")
    else:
        # Estadísticas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Monitoreos Activos", len(monitoreos_activos['id'].unique()))
        with col2:
            dispositivos_activos = monitoreos_activos[monitoreos_activos['dispositivo_activo'] == True]['dispositivo_id'].nunique()
            st.metric("Dispositivos Activos", dispositivos_activos)
        with col3:
            indefinidos = monitoreos_activos[monitoreos_activos['fecha_fin'].isna()].shape[0]
            st.metric("Monitoreos Indefinidos", indefinidos)
        
        st.write("")
        
        # Mostrar monitoreos
        for _, mon in monitoreos_activos.groupby('id').first().reset_index().iterrows():
            paciente_nombre = f"{mon['nombre']} {mon['apellido_paterno']} {mon.get('apellido_materno', '')}".strip()
            
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.markdown(f"### 👤 {paciente_nombre}")
                    st.caption(f"📋 {mon['diagnostico'] if mon.get('diagnostico') else 'Sin diagnóstico'}")
                
                with col2:
                    dispositivo_sel = monitoreos_activos[monitoreos_activos['id'] == mon['id']].iloc[0]
                    st.caption(f"⌚ {dispositivo_sel['modelo']}")
                    if pd.isna(mon['fecha_fin']):
                        st.caption(f"⏱️ Indefinido (desde {pd.to_datetime(mon['fecha_inicio']).strftime('%d/%m/%Y')})")
                    else:
                        dias_restantes = (pd.to_datetime(mon['fecha_fin']).date() - datetime.now().date()).days
                        st.caption(f"⏱️ {dias_restantes} días restantes")
                
                with col3:
                    st.markdown(f"<div class='status-active'>🟢 Activo</div>", unsafe_allow_html=True)
                
                st.write("")
                
                if st.button(f"⏸️ Detener Monitoreo", key=f"detener_{mon['id']}", use_container_width=True):
                    try:
                        update_query = text("""
                            UPDATE public.monitoreos
                            SET activo = false, fecha_fin = :fecha_fin
                            WHERE id = :id
                        """)
                        
                        with conn.session as s:
                            s.execute(update_query, {
                                "id": mon['id'],
                                "fecha_fin": datetime.now()
                            })
                            s.commit()
                        
                        st.success(f"✅ Monitoreo detenido para {paciente_nombre}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al detener monitoreo: {e}")

# ==================== TAB 3: HISTÓRICO ====================
with tab_historico:
    st.subheader("📜 Histórico de Monitoreos")
    
    try:
        monitoreos_historico = conn.query("""
            SELECT 
                m.id,
                m.fecha_inicio,
                m.fecha_fin,
                m.motivo,
                m.activo,
                p.nombre,
                p.apellido_paterno,
                p.apellido_materno,
                d.modelo
            FROM public.monitoreos m
            JOIN public.pacientes p ON m.paciente_id = p.id
            LEFT JOIN public.dispositivos d ON p.id = d.paciente_id
            ORDER BY m.fecha_inicio DESC
        """, ttl="5s")
    except Exception as e:
        st.error(f"Error al cargar histórico: {e}")
        monitoreos_historico = pd.DataFrame()
    
    if monitoreos_historico.empty:
        st.info("No hay registros de monitoreo en el sistema.")
    else:
        # Filtros
        col1, col2 = st.columns([2, 1])
        with col1:
            estado_filtro = st.multiselect(
                "Filtrar por estado",
                options=["Activo", "Inactivo"],
                default=["Activo", "Inactivo"]
            )
        with col2:
            st.write("")
            if st.button("🔄 Refrescar", use_container_width=True):
                st.rerun()
        
        # Aplicar filtros
        monitoreos_filtrados = monitoreos_historico.copy()
        if "Activo" not in estado_filtro:
            monitoreos_filtrados = monitoreos_filtrados[monitoreos_filtrados['activo'] == False]
        if "Inactivo" not in estado_filtro:
            monitoreos_filtrados = monitoreos_filtrados[monitoreos_filtrados['activo'] == True]
        
        st.write("")
        
        # Tabla
        tabla_display = monitoreos_filtrados.copy()
        tabla_display['Paciente'] = tabla_display['nombre'] + ' ' + tabla_display['apellido_paterno'] + ' ' + tabla_display['apellido_materno'].fillna('')
        tabla_display['Estado'] = tabla_display['activo'].apply(lambda x: '🟢 Activo' if x else '⏸️ Inactivo')
        tabla_display['Inicio'] = pd.to_datetime(tabla_display['fecha_inicio']).dt.strftime('%d/%m/%Y')
        tabla_display['Fin'] = tabla_display['fecha_fin'].apply(lambda x: pd.to_datetime(x).strftime('%d/%m/%Y') if pd.notna(x) else '∞ Indefinido')
        tabla_display['Dispositivo'] = tabla_display['modelo'].fillna('No asignado')
        
        st.dataframe(
            tabla_display[['Paciente', 'Dispositivo', 'Inicio', 'Fin', 'Estado', 'motivo']].rename(columns={'motivo': 'Motivo'}),
            use_container_width=True,
            hide_index=True
        )