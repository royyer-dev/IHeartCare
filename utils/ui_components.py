"""
Componentes UI reutilizables para IHeartCare.
Incluye: metric cards, patient cards, breadcrumbs, toasts, y componentes visuales.
"""

import streamlit as st
from typing import Optional, List, Dict, Any
from datetime import datetime

# =============================================================================
# BREADCRUMBS Y NAVEGACIÓN
# =============================================================================

def breadcrumb_nav(path: List[str], separator: str = " / "):
    """
    Renderiza una navegación de breadcrumbs.
    
    Args:
        path: Lista de nombres de secciones (ej: ["Home", "Administración", "Pacientes"])
        separator: Texto del separador (default: " / ")
    
    Ejemplo:
        breadcrumb_nav(["Home", "Pacientes", "Detalle"])
    """
    breadcrumb_html = "<div style='display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1.5rem; font-size: 0.9rem; color: #6B7280;'>"
    
    for i, item in enumerate(path):
        if i == len(path) - 1:  # Último elemento (actual)
            breadcrumb_html += f"<span style='color: #0066CC; font-weight: 600;'>{item}</span>"
        else:
            breadcrumb_html += f"<span>{item}</span>"
            if i < len(path) - 1:
                breadcrumb_html += f"<span style='color: #D1D5DB;'>{separator}</span>"
    
    breadcrumb_html += "</div>"
    st.markdown(breadcrumb_html, unsafe_allow_html=True)


# =============================================================================
# METRIC CARDS
# =============================================================================

def metric_card(
    title: str,
    value: Any,
    subtitle: Optional[str] = None,
    icon: str = "📊",
    color: str = "primary",
    animated: bool = True,
):
    """
    Renderiza una tarjeta de métrica con diseño moderno.
    
    Args:
        title: Título de la métrica
        value: Valor a mostrar (puede ser número, string)
        subtitle: Subtítulo opcional (ej: "vs mes anterior")
        icon: Emoji o ícono a mostrar
        color: Color de la tarjeta ('primary', 'success', 'warning', 'danger', 'info')
        animated: Si debe tener animación de entrada
    
    Ejemplo:
        metric_card("Pacientes", 42, "↑ 5 nuevos", "👥", "success")
    """
    color_map = {
        'primary': '#0066CC',
        'success': '#28A745',
        'warning': '#FF9800',
        'danger': '#DC3545',
        'info': '#17A2B8',
    }
    
    card_color = color_map.get(color, color_map['primary'])
    animation = "animation: slideInUp 0.5s ease;" if animated else ""
    
    html = f"""
    <div style='
        background: linear-gradient(135deg, {card_color}08 0%, {card_color}12 100%);
        border: 1px solid {card_color}20;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
        cursor: pointer;
        {animation}
    ' onmouseover="this.style.transform='translateY(-4px)'; this.style.boxShadow='0 8px 20px {card_color}15';"
       onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">
        <div style='font-size: 2rem; margin-bottom: 0.5rem;'>{icon}</div>
        <div style='font-size: 0.85rem; color: #6B7280; font-weight: 500; margin-bottom: 0.5rem;'>{title}</div>
        <div style='font-size: 2rem; font-weight: 700; color: {card_color}; margin: 0.5rem 0;'>{value}</div>
        {f'<div style="font-size: 0.8rem; color: {card_color}; margin-top: 0.5rem;">{subtitle}</div>' if subtitle else ''}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def metric_card_container(metrics: List[Dict[str, Any]], columns: int = 4):
    """
    Renderiza múltiples metric cards en un contenedor con columnas ajustables.
    
    Args:
        metrics: Lista de diccionarios con claves: title, value, subtitle, icon, color
        columns: Número de columnas (default: 4)
    
    Ejemplo:
        metrics = [
            {"title": "Pacientes", "value": 42, "icon": "👥", "color": "success"},
            {"title": "Alertas", "value": 3, "icon": "🚨", "color": "danger"},
        ]
        metric_card_container(metrics, columns=4)
    """
    cols = st.columns(columns)
    for i, metric in enumerate(metrics):
        with cols[i % columns]:
            metric_card(
                title=metric.get('title', 'Métrica'),
                value=metric.get('value', '-'),
                subtitle=metric.get('subtitle'),
                icon=metric.get('icon', '📊'),
                color=metric.get('color', 'primary'),
            )


# =============================================================================
# PATIENT CARDS
# =============================================================================

def patient_status_badge(status: str) -> str:
    """
    Retorna HTML de badge de estado de paciente.
    
    States: 'normal', 'warning', 'critical'
    """
    status_map = {
        'normal': ('#28A745', 'Normal'),
        'warning': ('#FF9800', 'Anormal'),
        'critical': ('#DC3545', 'Crítico'),
    }
    
    color, label = status_map.get(status, ('#6B7280', 'Desconocido'))
    
    return f"""
    <span style='
        display: inline-block;
        background-color: {color}20;
        color: {color};
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        border: 1px solid {color}40;
    '>{label}</span>
    """


def patient_card(
    name: str,
    paciente_id: int,
    status: str = "normal",
    last_measurement: Optional[str] = None,
    doctor: Optional[str] = None,
    on_click_callback: Optional[callable] = None,
):
    """
    Renderiza una tarjeta de paciente con información resumida.
    
    Args:
        name: Nombre completo del paciente
        paciente_id: ID del paciente en BD
        status: Estado ('normal', 'warning', 'critical')
        last_measurement: Texto de última medición (ej: "FC: 78 lpm")
        doctor: Nombre del doctor asignado
        on_click_callback: Función a llamar si se clickea (recibe paciente_id)
    """
    
    html = f"""
    <div style='
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 1.25rem;
        transition: all 0.3s ease;
        cursor: pointer;
        animation: fadeIn 0.4s ease;
    ' onmouseover="this.style.transform='translateY(-4px)'; this.style.boxShadow='0 10px 25px rgba(0, 102, 204, 0.15)';"
       onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 1px 3px rgba(0, 0, 0, 0.1)';">
        
        <div style='display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.75rem;'>
            <div style='flex: 1;'>
                <h4 style='margin: 0 0 0.25rem 0; color: #1F2937; font-size: 1rem;'>{name}</h4>
                <p style='margin: 0; color: #9CA3AF; font-size: 0.8rem;'>ID: {paciente_id}</p>
            </div>
            <div>{patient_status_badge(status)}</div>
        </div>
        
        {f'<p style="margin: 0.5rem 0; color: #6B7280; font-size: 0.85rem;">📊 {last_measurement}</p>' if last_measurement else ''}
        {f'<p style="margin: 0.5rem 0; color: #6B7280; font-size: 0.85rem;">👨‍⚕️ {doctor}</p>' if doctor else ''}
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)


# =============================================================================
# ALERT / NOTIFICATION TOAST
# =============================================================================

def toast_notification(
    message: str,
    notification_type: str = "info",
    duration: int = 3,
    position: str = "top-right",
):
    """
    Muestra una notificación toast (esquina superior derecha).
    
    Args:
        message: Texto del mensaje
        notification_type: 'success', 'error', 'warning', 'info', 'critical'
        duration: Duración en segundos
        position: 'top-right', 'top-center', 'bottom-right'
    
    Ejemplo:
        toast_notification("Evento crítico detectado", "critical")
    """
    
    color_map = {
        'success': '#28A745',
        'error': '#DC3545',
        'warning': '#FF9800',
        'info': '#17A2B8',
        'critical': '#DC3545',
    }
    
    icon_map = {
        'success': '✓',
        'error': '✕',
        'warning': '⚠',
        'info': 'ℹ',
        'critical': '❗',
    }
    
    color = color_map.get(notification_type, color_map['info'])
    icon = icon_map.get(notification_type, '')
    
    position_css = {
        'top-right': 'top: 20px; right: 20px;',
        'top-center': 'top: 20px; left: 50%; transform: translateX(-50%);',
        'bottom-right': 'bottom: 20px; right: 20px;',
    }
    
    html = f"""
    <div id="toast-{datetime.now().timestamp()}" style='
        position: fixed;
        {position_css.get(position, position_css["top-right"])}
        background: {color};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
        font-weight: 600;
        z-index: 9999;
        animation: slideInDown 0.3s ease;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    '>
        <span style='font-size: 1.2rem;'>{icon}</span>
        <span>{message}</span>
    </div>
    
    <script>
        setTimeout(() => {{
            const toast = document.getElementById('toast-{datetime.now().timestamp()}');
            if (toast) {{
                toast.style.animation = 'slideInUp 0.3s ease';
                setTimeout(() => toast.remove(), 300);
            }}
        }}, {duration * 1000});
    </script>
    """
    
    st.markdown(html, unsafe_allow_html=True)


# =============================================================================
# HERO SECTION
# =============================================================================

def hero_section(
    title: str,
    subtitle: Optional[str] = None,
    user_role: Optional[str] = None,
    user_name: Optional[str] = None,
):
    """
    Renderiza una sección hero (bienvenida) con título y subtítulo animado.
    
    Args:
        title: Título principal
        subtitle: Subtítulo (descripción)
        user_role: Rol del usuario autenticado
        user_name: Nombre del usuario
    """
    
    role_emoji = {
        'administrador': '🛡️',
        'medico': '👨‍⚕️',
        'paciente': '👤',
    }
    
    emoji = role_emoji.get(user_role, '👤')
    
    html = f"""
    <div style='
        background: linear-gradient(135deg, #0066CC 0%, #2E7D8C 100%);
        color: white;
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        animation: slideInDown 0.5s ease;
    '>
        <div style='display: flex; justify-content: space-between; align-items: start;'>
            <div>
                <h1 style='margin: 0 0 0.5rem 0; font-size: 2rem;'>{title}</h1>
                {f'<p style="margin: 0; font-size: 1rem; opacity: 0.95;">{subtitle}</p>' if subtitle else ''}
            </div>
            {f'<div style="font-size: 3rem;">{emoji}</div>' if user_role else ''}
        </div>
        {f'<p style="margin: 1rem 0 0 0; font-size: 0.95rem; opacity: 0.9;">Bienvenido, <strong>{user_name}</strong></p>' if user_name else ''}
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)


# =============================================================================
# STATUS INDICATOR
# =============================================================================

def status_indicator(
    status: str,
    label: Optional[str] = None,
    size: str = "medium"
):
    """
    Renderiza un indicador de estado con color y animación.
    
    Args:
        status: 'normal', 'warning', 'critical', 'offline'
        label: Texto a mostrar junto al indicador
        size: 'small', 'medium', 'large'
    """
    
    status_map = {
        'normal': ('#28A745', 'Normal'),
        'warning': ('#FF9800', 'Anormal'),
        'critical': ('#DC3545', 'Crítico'),
        'offline': ('#9CA3AF', 'Offline'),
    }
    
    color, default_label = status_map.get(status, status_map['offline'])
    display_label = label or default_label
    
    size_map = {
        'small': ('8px', '0.75rem'),
        'medium': ('12px', '1rem'),
        'large': ('16px', '1.25rem'),
    }
    
    dot_size, font_size = size_map.get(size, size_map['medium'])
    
    # Animación de pulse para estados críticos
    animation = "animation: pulse 1.5s infinite;" if status == 'critical' else ""
    
    html = f"""
    <div style='display: flex; align-items: center; gap: 0.5rem;'>
        <div style='
            width: {dot_size};
            height: {dot_size};
            background-color: {color};
            border-radius: 50%;
            {animation}
        '></div>
        <span style='color: {color}; font-size: {font_size}; font-weight: 600;'>{display_label}</span>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)


# =============================================================================
# DATA TABLE ENHANCEMENT
# =============================================================================

def render_enhanced_table(
    dataframe,
    highlight_columns: Optional[List[str]] = None,
    status_column: Optional[str] = None,
):
    """
    Renderiza un DataFrame con estilos mejorados.
    
    Args:
        dataframe: DataFrame de pandas
        highlight_columns: Columnas a destacar (ej: críticas)
        status_column: Nombre de columna que contiene estado para color
    
    Nota: Streamlit maneja la renderización de tablas, esto agrega CSS global.
    """
    
    st.markdown("""
    <style>
    [role="grid"] {
        border-radius: 8px;
        overflow: hidden;
    }
    
    thead {
        background: linear-gradient(90deg, #0066CC, #2E7D8C);
        color: white;
        font-weight: 600;
    }
    
    tbody tr:hover {
        background-color: #E8F4FF !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.dataframe(dataframe, use_container_width=True)


# =============================================================================
# SECTION DIVIDER
# =============================================================================

def section_divider(title: Optional[str] = None):
    """
    Renderiza un divisor de sección con título opcional.
    
    Args:
        title: Título de la sección (opcional)
    
    Ejemplo:
        section_divider("Últimas Mediciones")
    """
    if title:
        html = f"""
        <div style='margin: 2rem 0 1.5rem 0;'>
            <h3 style='margin: 0; color: #1F2937; font-size: 1.25rem;'>{title}</h3>
            <div style='height: 2px; background: linear-gradient(90deg, #0066CC, transparent); margin-top: 0.75rem;'></div>
        </div>
        """
    else:
        html = """
        <div style='height: 2px; background: linear-gradient(90deg, #0066CC, transparent); margin: 2rem 0;'></div>
        """
    
    st.markdown(html, unsafe_allow_html=True)


# =============================================================================
# UTILITY HELPERS
# =============================================================================

def get_status_color(status: str) -> str:
    """
    Retorna el color hexadecimal asociado a un estado.
    """
    status_colors = {
        'normal': '#28A745',
        'warning': '#FF9800',
        'critical': '#DC3545',
        'offline': '#9CA3AF',
    }
    return status_colors.get(status, '#6B7280')


def get_status_icon(status: str) -> str:
    """
    Retorna el ícono asociado a un estado.
    """
    status_icons = {
        'normal': '✓',
        'warning': '⚠',
        'critical': '❗',
        'offline': '⊘',
    }
    return status_icons.get(status, '?')
