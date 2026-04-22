"""
Utilidades y componentes para IHeartCare.
"""

from .ui_components import (
    breadcrumb_nav,
    metric_card,
    metric_card_container,
    patient_status_badge,
    patient_card,
    toast_notification,
    hero_section,
    status_indicator,
    render_enhanced_table,
    section_divider,
    get_status_color,
    get_status_icon,
)

from .alerta_generator import (
    verificar_rango,
    crear_alerta_si_necesario,
    crear_alerta_directa,
    obtener_alertas_no_leidas,
    marcar_alerta_leida,
    marcar_alertas_leidas_paciente,
)

from .simulador import (
    generar_medicon_anomala,
    simular_evento_continuo,
    obtener_dispositivos_pacientes,
    obtener_ultimas_mediciones_paciente,
    TIPOS_EVENTOS,
)

from .notificaciones import (
    crear_notificacion,
    obtener_notificaciones_pendientes,
    obtener_historial_notificaciones,
    obtener_estadisticas_notificaciones,
    marcar_notificacion_leida,
    marcar_todas_leidas,
    contar_notificaciones_pendientes,
    mostrar_panel_notificaciones,
    mostrar_indicador_notificaciones,
)

from .geo_simulator import (
    generar_coordenadas_base,
    generar_coordenadas_actuales,
    validar_coordenadas,
    calcular_distancia_haversine,
)

from .mapas import (
    crear_mapa_dispositivos,
    crear_minimapa,
    generar_popup_dispositivo,
    crear_mapa_clustered,
)

__all__ = [
    # UI Components
    'breadcrumb_nav',
    'metric_card',
    'metric_card_container',
    'patient_status_badge',
    'patient_card',
    'toast_notification',
    'hero_section',
    'status_indicator',
    'render_enhanced_table',
    'section_divider',
    'get_status_color',
    'get_status_icon',
    # Alertas
    'verificar_rango',
    'crear_alerta_si_necesario',
    'crear_alerta_directa',
    'obtener_alertas_no_leidas',
    'marcar_alerta_leida',
    'marcar_alertas_leidas_paciente',
    # Simulador
    'generar_medicon_anomala',
    'simular_evento_continuo',
    'obtener_dispositivos_pacientes',
    'obtener_ultimas_mediciones_paciente',
    'TIPOS_EVENTOS',
    # Notificaciones
    'crear_notificacion',
    'obtener_notificaciones_pendientes',
    'obtener_historial_notificaciones',
    'obtener_estadisticas_notificaciones',
    'marcar_notificacion_leida',
    'marcar_todas_leidas',
    'contar_notificaciones_pendientes',
    'mostrar_panel_notificaciones',
    'mostrar_indicador_notificaciones',
    # Geo Simulator
    'generar_coordenadas_base',
    'generar_coordenadas_actuales',
    'validar_coordenadas',
    'calcular_distancia_haversine',
    # Mapas
    'crear_mapa_dispositivos',
    'crear_minimapa',
    'generar_popup_dispositivo',
    'crear_mapa_clustered',
]
