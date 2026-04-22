import streamlit as st
from auth import logout_user
from utils import mostrar_indicador_notificaciones, obtener_estadisticas_notificaciones

def render_sidebar():
    """Renders the custom sidebar based on the user's role."""
    
    # Si no hay sesión, no mostrar nada (o mostrar login si se desea)
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        return

    with st.sidebar:
        st.logo("https://img.icons8.com/color/96/heart-with-pulse.png", icon_image="https://img.icons8.com/color/96/heart-with-pulse.png")
        
        # Obtener notificaciones pendientes
        notificaciones_pendientes = mostrar_indicador_notificaciones(st.session_state.user_id)
        stats_notificaciones = obtener_estadisticas_notificaciones(st.session_state.user_id)
        
        # Header con información del usuario
        st.markdown("#### IHeartCare")
        
        # Rol badge - Minimalista y profesional
        rol_texto = st.session_state.rol.upper()
        rol_map = {
            'ADMINISTRADOR': '#1E40AF',
            'MEDICO': '#0891B2',
            'PACIENTE': '#10B981'
        }
        color_rol = rol_map.get(rol_texto, '#1E40AF')
        
        st.markdown(f"""
        <div style="
            background: {color_rol}22;
            border-left: 3px solid {color_rol};
            color: #1F2937;
            padding: 0.75rem;
            border-radius: 0.375rem;
            text-align: center;
            font-weight: 500;
            font-size: 0.9rem;
            margin: 0.75rem 0;
        ">
            {rol_texto}
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # ========== VISTA RÁPIDA DE NOTIFICACIONES ==========
        st.markdown("""
        <style>
        .notification-stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.75rem;
            margin-bottom: 1rem;
        }
        
        .notification-stat {
            padding: 0.75rem;
            border-radius: 0.375rem;
            font-size: 0.85rem;
            text-align: center;
            background: #F3F4F6;
            border: 1px solid #D1D5DB;
        }
        
        .notification-stat strong {
            display: block;
            font-size: 1.25rem;
            margin-bottom: 0.25rem;
            color: #1F2937;
        }
        
        .notification-stat.unread strong {
            color: #EF4444;
        }
        
        .notification-stat.read strong {
            color: #10B981;
        }
        
        .notification-item {
            background: #F9FAFB;
            padding: 0.75rem;
            border-left: 3px solid #1E40AF;
            border-radius: 0.375rem;
            margin-bottom: 0.5rem;
            font-size: 0.8rem;
        }
        
        .notification-item.critical {
            border-left-color: #EF4444;
        }
        
        .notification-item.warning {
            border-left-color: #F59E0B;
        }
        
        .notification-patient {
            font-weight: 500;
            color: #1F2937;
            margin-bottom: 0.25rem;
        }
        
        .notification-details {
            color: #6B7280;
            font-size: 0.75rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        with st.expander("Notificaciones", expanded=False):
            # Estadísticas
            st.markdown(f"""
            <div class="notification-stats">
                <div class="notification-stat unread">
                    <strong>{stats_notificaciones['no_leidas']}</strong>
                    Sin leer
                </div>
                <div class="notification-stat read">
                    <strong>{stats_notificaciones['leidas']}</strong>
                    Leídas
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.caption(f"Total: {stats_notificaciones['total']}")
            st.divider()
            
            # Últimas 3 notificaciones sin leer
            if stats_notificaciones['ultimas_3']:
                st.markdown("**Recientes:**")
                for notif in stats_notificaciones['ultimas_3']:
                    css_class = 'critical' if notif['tipo_alerta'] == 'crítica' else 'warning'
                    
                    st.markdown(f"""
                    <div class="notification-item {css_class}">
                        <div class="notification-patient">{notif['nombre_paciente']}</div>
                        <div class="notification-details">
                            {notif['tipo_medicion']}: {notif['valor']} {notif['unidad_medida']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Sin notificaciones pendientes", icon="ℹ️")
            
            st.divider()
            
            # Botón para marcar todas como leídas
            if stats_notificaciones['no_leidas'] > 0:
                from utils import marcar_todas_leidas
                if st.button("Marcar todas como leídas", use_container_width=True, key="marcar_todas_sidebar"):
                    marcar_todas_leidas(st.session_state.user_id)
                    st.success("Notificaciones actualizadas")
                    st.rerun()
        
        st.divider()
        
        # --- NAVEGACIÓN COMÚN ---
        st.markdown("### Inicio")
        st.page_link("app.py", label="Panel Principal")
        
        # --- NAVEGACIÓN ADMINISTRADOR ---
        if st.session_state.rol == 'administrador':
            st.markdown("### Administración")
            st.page_link("pages/01_admin_pacientes.py", label="Pacientes")
            st.page_link("pages/02_admin_medicos.py", label="Personal Médico")
            st.page_link("pages/03_admin_dispositivos.py", label="Dispositivos")
            st.page_link("pages/04_monitoreo_crear.py", label="Monitoreo")
            
            st.markdown("### Análisis")
            st.page_link("pages/05_monitoreo_dashboard.py", label="Visualización")
            st.page_link("pages/06_monitoreo_analisis.py", label="Análisis Clínico")

        # --- NAVEGACIÓN MÉDICO ---
        elif st.session_state.rol == 'medico':
            st.markdown("### Gestión Médica")
            st.page_link("pages/09_mis_pacientes.py", label="Mis Pacientes")
            st.page_link("pages/10_notificaciones.py", label=f"Alertas {f'({notificaciones_pendientes})' if notificaciones_pendientes > 0 else ''}")
            
            st.markdown("### Análisis")
            st.page_link("pages/05_monitoreo_dashboard.py", label="Visualización")
            st.page_link("pages/06_monitoreo_analisis.py", label="Análisis Clínico")

        # --- NAVEGACIÓN PACIENTE ---
        elif st.session_state.rol == 'paciente':
            st.markdown("### Mi Salud")
            st.page_link("pages/07_perfil_usuario.py", label="Perfil")
            st.page_link("pages/08_mediciones_personales.py", label="Mediciones")
            st.page_link("pages/10_notificaciones.py", label=f"Alertas {f'({notificaciones_pendientes})' if notificaciones_pendientes > 0 else ''}")

        # --- FOOTER / LOGOUT ---
        st.markdown("---")
        if st.button("Cerrar Sesión", use_container_width=True, type="secondary"):
            logout_user()
            st.rerun()
