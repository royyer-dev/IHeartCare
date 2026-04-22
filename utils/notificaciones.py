"""
Sistema de notificaciones para alertas críticas.
Gestiona creación, lectura y visualización de notificaciones.
"""

import streamlit as st
from sqlalchemy import text
from datetime import datetime
from typing import Optional, List, Dict
import json

def crear_notificacion(
    usuario_id: int,
    alerta_id: int,
    tipo: str = "evento_critico",
    payload: Optional[Dict] = None,
) -> Optional[int]:
    """
    Crea una notificación para un usuario cuando ocurre un evento crítico.
    
    Args:
        usuario_id: ID del usuario a notificar
        alerta_id: ID de la alerta asociada
        tipo: Tipo de notificación ('evento_critico', 'evento_paciente', etc.)
        payload: Datos adicionales JSON (info del paciente, medición, etc.)
    
    Returns:
        ID de notificación creada o None si falla
    """
    try:
        conn = st.connection("postgresql", type="sql")
        with conn.session as s:
            payload_json = json.dumps(payload) if payload else None
            
            query = text("""
                INSERT INTO public.notificaciones_alertas 
                (usuario_id, alerta_id, tipo, leida, payload)
                VALUES (:usuario_id, :alerta_id, :tipo, false, :payload)
                RETURNING id
            """)
            
            resultado = s.execute(
                query,
                {
                    "usuario_id": usuario_id,
                    "alerta_id": alerta_id,
                    "tipo": tipo,
                    "payload": payload_json,
                },
            ).fetchone()
            
            s.commit()
            
            if resultado:
                return resultado[0]
        
        return None
    
    except Exception as e:
        st.error(f"Error creando notificación: {str(e)}")
        return None


def obtener_notificaciones_pendientes(usuario_id: int, limite: int = 10) -> List[Dict]:
    """
    Obtiene las notificaciones no leídas de un usuario.
    
    Args:
        usuario_id: ID del usuario
        limite: Máximo de resultados
    
    Returns:
        Lista de diccionarios con información de notificaciones
    """
    try:
        conn = st.connection("postgresql", type="sql")
        with conn.session as s:
            query = text("""
                SELECT na.id, na.tipo, na.timestamp, a.mensaje, a.tipo_alerta,
                       p.nombre, p.apellido_paterno,
                       m.tipo_medicion, m.valor, m.unidad_medida,
                       na.payload
                FROM public.notificaciones_alertas na
                JOIN public.alertas a ON na.alerta_id = a.id
                JOIN public.mediciones m ON a.medicion_id = m.id
                JOIN public.dispositivos d ON m.dispositivo_id = d.id
                JOIN public.pacientes p ON d.paciente_id = p.id
                WHERE na.usuario_id = :usuario_id
                  AND na.leida = false
                ORDER BY na.timestamp DESC
                LIMIT :limite
            """)
            
            resultado = s.execute(
                query, 
                {"usuario_id": usuario_id, "limite": limite}
            ).fetchall()
            
            notificaciones = []
            for row in resultado:
                payload = json.loads(row[10]) if row[10] else {}
                
                notificaciones.append({
                    "id": row[0],
                    "tipo": row[1],
                    "timestamp": row[2],
                    "mensaje": row[3],
                    "tipo_alerta": row[4],
                    "nombre_paciente": f"{row[5]} {row[6]}",
                    "tipo_medicion": row[7],
                    "valor": row[8],
                    "unidad_medida": row[9],
                    "payload": payload,
                })
            
            return notificaciones
    
    except Exception as e:
        st.error(f"Error obteniendo notificaciones: {str(e)}")
        return []


def obtener_historial_notificaciones(usuario_id: int, limite: int = 20) -> List[Dict]:
    """
    Obtiene el historial completo de notificaciones (leídas y no leídas).
    
    Args:
        usuario_id: ID del usuario
        limite: Máximo de resultados
    
    Returns:
        Lista de diccionarios con información de notificaciones
    """
    try:
        conn = st.connection("postgresql", type="sql")
        with conn.session as s:
            query = text("""
                SELECT na.id, na.tipo, na.timestamp, a.mensaje, a.tipo_alerta,
                       p.nombre, p.apellido_paterno,
                       m.tipo_medicion, m.valor, m.unidad_medida,
                       na.leida
                FROM public.notificaciones_alertas na
                JOIN public.alertas a ON na.alerta_id = a.id
                JOIN public.mediciones m ON a.medicion_id = m.id
                JOIN public.dispositivos d ON m.dispositivo_id = d.id
                JOIN public.pacientes p ON d.paciente_id = p.id
                WHERE na.usuario_id = :usuario_id
                ORDER BY na.timestamp DESC
                LIMIT :limite
            """)
            
            resultado = s.execute(
                query,
                {"usuario_id": usuario_id, "limite": limite}
            ).fetchall()
            
            notificaciones = []
            for row in resultado:
                notificaciones.append({
                    "id": row[0],
                    "tipo": row[1],
                    "timestamp": row[2],
                    "mensaje": row[3],
                    "tipo_alerta": row[4],
                    "nombre_paciente": f"{row[5]} {row[6]}",
                    "tipo_medicion": row[7],
                    "valor": row[8],
                    "unidad_medida": row[9],
                    "leida": row[10],
                })
            
            return notificaciones
    
    except Exception as e:
        st.error(f"Error obteniendo historial: {str(e)}")
        return []


def marcar_notificacion_leida(notificacion_id: int) -> bool:
    """
    Marca una notificación como leída.
    
    Args:
        notificacion_id: ID de la notificación
    
    Returns:
        True si se actualizó correctamente
    """
    try:
        conn = st.connection("postgresql", type="sql")
        with conn.session as s:
            query = text("""
                UPDATE public.notificaciones_alertas
                SET leida = true
                WHERE id = :notificacion_id
            """)
            
            s.execute(query, {"notificacion_id": notificacion_id})
            s.commit()
            
            return True
    
    except Exception as e:
        st.error(f"Error marcando notificación: {str(e)}")
        return False


def marcar_todas_leidas(usuario_id: int) -> int:
    """
    Marca todas las notificaciones de un usuario como leídas.
    
    Returns:
        Cantidad de notificaciones actualizadas
    """
    try:
        conn = st.connection("postgresql", type="sql")
        with conn.session as s:
            query = text("""
                UPDATE public.notificaciones_alertas
                SET leida = true
                WHERE usuario_id = :usuario_id
                  AND leida = false
            """)
            
            result = s.execute(query, {"usuario_id": usuario_id})
            s.commit()
            
            return result.rowcount
    
    except Exception as e:
        st.error(f"Error marcando notificaciones: {str(e)}")
        return 0


def contar_notificaciones_pendientes(usuario_id: int) -> int:
    """
    Cuenta cuántas notificaciones no leídas tiene un usuario.
    
    Returns:
        Cantidad de notificaciones pendientes
    """
    try:
        conn = st.connection("postgresql", type="sql")
        with conn.session as s:
            query = text("""
                SELECT COUNT(*) FROM public.notificaciones_alertas
                WHERE usuario_id = :usuario_id
                  AND leida = false
            """)
            
            resultado = s.execute(query, {"usuario_id": usuario_id}).fetchone()
            
            return resultado[0] if resultado else 0
    
    except Exception as e:
        st.error(f"Error contando notificaciones: {str(e)}")
        return 0


def mostrar_panel_notificaciones(usuario_id: int, rol: str):
    """
    Renderiza un panel de notificaciones con historial y opciones.
    
    Args:
        usuario_id: ID del usuario
        rol: Rol del usuario ('administrador', 'medico', 'paciente')
    """
    from .ui_components import section_divider, status_indicator, toast_notification
    
    # Obtener notificaciones
    notificaciones = obtener_historial_notificaciones(usuario_id, limite=15)
    
    if not notificaciones:
        st.info("📭 No hay notificaciones aún.")
        return
    
    # Contar pendientes
    pendientes = sum(1 for n in notificaciones if not n["leida"])
    
    col1, col2 = st.columns([0.85, 0.15])
    
    with col1:
        section_divider(f"🔔 Notificaciones Recientes ({pendientes} nuevas)")
    
    with col2:
        if pendientes > 0:
            if st.button("✓ Marcar todas como leídas", key="mark_all_read"):
                marcar_todas_leidas(usuario_id)
                st.rerun()
    
    # Mostrar notificaciones
    for notificacion in notificaciones:
        status = "leída" if notificacion["leida"] else "sin leer"
        
        # Color según severidad
        if notificacion["tipo_alerta"] == "crítica":
            color_border = "#DC3545"
            bg_color = "#DC354515"
        else:
            color_border = "#FF9800"
            bg_color = "#FF980015"
        
        with st.container(border=True):
            col1, col2, col3 = st.columns([0.15, 0.7, 0.15])
            
            with col1:
                if notificacion["tipo_alerta"] == "crítica":
                    st.markdown("🚨")
                else:
                    st.markdown("⚠️")
            
            with col2:
                st.markdown(f"**{notificacion['nombre_paciente']}**")
                st.caption(notificacion["mensaje"])
                st.caption(
                    f"📊 {notificacion['tipo_medicion']}: {notificacion['valor']} {notificacion['unidad_medida']}"
                )
                st.caption(f"🕐 {notificacion['timestamp'].strftime('%d/%m/%Y %H:%M')}")
            
            with col3:
                if not notificacion["leida"]:
                    if st.button("✓", key=f"read_{notificacion['id']}", help="Marcar como leída"):
                        marcar_notificacion_leida(notificacion["id"])
                        st.rerun()
                else:
                    st.caption("✓ Leída")


def obtener_estadisticas_notificaciones(usuario_id: int) -> Dict:
    """
    Obtiene estadísticas completas de notificaciones para el usuario.
    
    Returns:
        Diccionario con: total, leidas, no_leidas, ultimas_3
    """
    try:
        conn = st.connection("postgresql", type="sql")
        with conn.session as s:
            # Contar leídas y no leídas
            query_stats = text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN leida = true THEN 1 END) as leidas,
                    COUNT(CASE WHEN leida = false THEN 1 END) as no_leidas
                FROM public.notificaciones_alertas
                WHERE usuario_id = :usuario_id
            """)
            
            stats = s.execute(query_stats, {"usuario_id": usuario_id}).fetchone()
            total, leidas, no_leidas = stats if stats else (0, 0, 0)
            
            # Obtener últimas 3 no leídas
            query_recientes = text("""
                SELECT na.id, na.tipo, na.timestamp, a.mensaje, a.tipo_alerta,
                       p.nombre, p.apellido_paterno,
                       m.tipo_medicion, m.valor, m.unidad_medida
                FROM public.notificaciones_alertas na
                JOIN public.alertas a ON na.alerta_id = a.id
                JOIN public.mediciones m ON a.medicion_id = m.id
                JOIN public.dispositivos d ON m.dispositivo_id = d.id
                JOIN public.pacientes p ON d.paciente_id = p.id
                WHERE na.usuario_id = :usuario_id
                  AND na.leida = false
                ORDER BY na.timestamp DESC
                LIMIT 3
            """)
            
            recientes = s.execute(query_recientes, {"usuario_id": usuario_id}).fetchall()
            
            ultimas_3 = []
            for row in recientes:
                ultimas_3.append({
                    "id": row[0],
                    "tipo": row[1],
                    "timestamp": row[2],
                    "mensaje": row[3],
                    "tipo_alerta": row[4],
                    "nombre_paciente": f"{row[5]} {row[6]}",
                    "tipo_medicion": row[7],
                    "valor": row[8],
                    "unidad_medida": row[9],
                })
            
            return {
                "total": total,
                "leidas": leidas,
                "no_leidas": no_leidas,
                "ultimas_3": ultimas_3
            }
    
    except Exception as e:
        st.error(f"Error obteniendo estadísticas: {str(e)}")
        return {"total": 0, "leidas": 0, "no_leidas": 0, "ultimas_3": []}


def mostrar_indicador_notificaciones(usuario_id: int) -> int:
    """
    Retorna un badge con el número de notificaciones pendientes.
    Útil para mostrar en el sidebar.
    
    Returns:
        Cantidad de notificaciones pendientes
    """
    return contar_notificaciones_pendientes(usuario_id)
