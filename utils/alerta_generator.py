"""
Generador automático de alertas basado en rangos clínicos.
Verifica mediciones contra umbrales y crea alertas automáticamente.
"""

import streamlit as st
from sqlalchemy import text
from datetime import datetime
from typing import Optional, Dict, Tuple

# Rangos clínicos normales y críticos
CLINICAL_RANGES = {
    "Ritmo Cardíaco": {
        "normal": (60, 100),
        "alerta": (40, 130),
        "critica": (40, 150),
        "unidad": "lpm",
    },
    "Saturación Oxígeno": {
        "normal": (95, 100),
        "alerta": (92, 95),
        "critica": (0, 92),
        "unidad": "%",
    },
    "Presión Sistólica": {
        "normal": (90, 130),
        "alerta": (80, 140),
        "critica": (0, 80),
        "unidad": "mmHg",
    },
    "Presión Diastólica": {
        "normal": (60, 85),
        "alerta": (50, 90),
        "critica": (0, 50),
        "unidad": "mmHg",
    },
}


def verificar_rango(
    tipo_medicion: str, valor: float
) -> Tuple[Optional[str], Optional[str]]:
    """
    Verifica si un valor está dentro de los rangos normales.
    
    Args:
        tipo_medicion: Nombre del tipo de medición
        valor: Valor medido
    
    Returns:
        Tupla (tipo_alerta, mensaje) o (None, None) si está normal
        tipo_alerta: 'advertencia' | 'crítica' | None
    """
    if tipo_medicion not in CLINICAL_RANGES:
        return None, None
    
    ranges = CLINICAL_RANGES[tipo_medicion]
    min_normal, max_normal = ranges["normal"]
    min_alerta, max_alerta = ranges["alerta"]
    min_critica, max_critica = ranges["critica"]
    unidad = ranges["unidad"]
    
    # Verificar si está en rango normal
    if min_normal <= valor <= max_normal:
        return None, None
    
    # Verificar si es crítico
    if valor < min_critica or valor > max_critica:
        if valor < min_critica:
            mensaje = f"🚨 **CRÍTICA**: {tipo_medicion} muy bajo ({valor} {unidad}, crítico: <{min_critica})"
            return "crítica", mensaje
        else:
            mensaje = f"🚨 **CRÍTICA**: {tipo_medicion} muy alto ({valor} {unidad}, crítico: >{max_critica})"
            return "crítica", mensaje
    
    # Verificar si es alerta
    if valor < min_alerta or valor > max_alerta:
        if valor < min_alerta:
            mensaje = f"⚠️ **ADVERTENCIA**: {tipo_medicion} bajo ({valor} {unidad}, alerta: <{min_alerta})"
            return "advertencia", mensaje
        else:
            mensaje = f"⚠️ **ADVERTENCIA**: {tipo_medicion} alto ({valor} {unidad}, alerta: >{max_alerta})"
            return "advertencia", mensaje
    
    return None, None


def crear_alerta_si_necesario(medicion_id: int, tipo_medicion: str, valor: float) -> bool:
    """
    Verifica si una medición debe generar alerta y la crea en BD.
    
    Args:
        medicion_id: ID de la medición
        tipo_medicion: Tipo de medición
        valor: Valor de la medición
    
    Returns:
        True si se creó alerta, False si está normal
    """
    try:
        tipo_alerta, mensaje = verificar_rango(tipo_medicion, valor)
        
        if tipo_alerta is None:
            return False  # Está normal
        
        # Crear alerta en BD
        conn = st.connection("postgresql", type="sql")
        with conn.session as s:
            alerta_query = text("""
                INSERT INTO public.alertas 
                (medicion_id, tipo_alerta, mensaje, leida)
                VALUES (:medicion_id, :tipo_alerta, :mensaje, false)
                RETURNING id
            """)
            
            alerta_result = s.execute(
                alerta_query,
                {
                    "medicion_id": medicion_id,
                    "tipo_alerta": tipo_alerta,
                    "mensaje": mensaje,
                },
            ).fetchone()
            
            s.commit()
            
            if alerta_result:
                return True
        
        return False
    
    except Exception as e:
        st.error(f"Error creando alerta: {str(e)}")
        return False


def crear_alerta_directa(
    medicion_id: int, tipo_alerta: str, mensaje: str
) -> Optional[int]:
    """
    Crea una alerta directamente con tipo y mensaje personalizados.
    Útil para simulación de eventos específicos.
    
    Args:
        medicion_id: ID de la medición
        tipo_alerta: 'advertencia' | 'crítica'
        mensaje: Mensaje personalizado
    
    Returns:
        ID de alerta creada o None si falla
    """
    try:
        conn = st.connection("postgresql", type="sql")
        with conn.session as s:
            alerta_query = text("""
                INSERT INTO public.alertas 
                (medicion_id, tipo_alerta, mensaje, leida)
                VALUES (:medicion_id, :tipo_alerta, :mensaje, false)
                RETURNING id
            """)
            
            alerta_result = s.execute(
                alerta_query,
                {
                    "medicion_id": medicion_id,
                    "tipo_alerta": tipo_alerta,
                    "mensaje": mensaje,
                },
            ).fetchone()
            
            s.commit()
            
            if alerta_result:
                return alerta_result[0]
        
        return None
    
    except Exception as e:
        st.error(f"Error creando alerta: {str(e)}")
        return None


def obtener_alertas_no_leidas(usuario_id: int, rol: str) -> list:
    """
    Obtiene alertas no leídas para un usuario según su rol.
    
    - Admin: todas las alertas no leídas del sistema
    - Médico: alertas de sus pacientes asignados
    - Paciente: alertas de sus propias mediciones
    
    Returns:
        Lista de diccionarios con información de alertas
    """
    try:
        conn = st.connection("postgresql", type="sql")
        with conn.session as s:
            if rol == "administrador":
                # Admin ve todas las alertas no leídas
                query = text("""
                    SELECT a.id, a.tipo_alerta, a.mensaje, a.timestamp,
                           m.tipo_medicion, m.valor, d.paciente_id,
                           p.nombre, p.apellido_paterno
                    FROM public.alertas a
                    JOIN public.mediciones m ON a.medicion_id = m.id
                    JOIN public.dispositivos d ON m.dispositivo_id = d.id
                    JOIN public.pacientes p ON d.paciente_id = p.id
                    WHERE a.leida = false
                    ORDER BY a.tipo_alerta DESC, a.timestamp DESC
                    LIMIT 20
                """)
            
            elif rol == "medico":
                # Médico ve alertas de sus pacientes asignados
                query = text("""
                    SELECT a.id, a.tipo_alerta, a.mensaje, a.timestamp,
                           m.tipo_medicion, m.valor, d.paciente_id,
                           p.nombre, p.apellido_paterno
                    FROM public.alertas a
                    JOIN public.mediciones m ON a.medicion_id = m.id
                    JOIN public.dispositivos d ON m.dispositivo_id = d.id
                    JOIN public.pacientes p ON d.paciente_id = p.id
                    JOIN public.pacientes_medicos pm ON p.id = pm.paciente_id
                    JOIN public.personal_medico pmed ON pm.medico_id = pmed.id
                    WHERE a.leida = false
                      AND pmed.usuario_id = :usuario_id
                    ORDER BY a.tipo_alerta DESC, a.timestamp DESC
                    LIMIT 20
                """)
            
            else:  # paciente
                # Paciente ve solo sus alertas
                query = text("""
                    SELECT a.id, a.tipo_alerta, a.mensaje, a.timestamp,
                           m.tipo_medicion, m.valor, d.paciente_id,
                           p.nombre, p.apellido_paterno
                    FROM public.alertas a
                    JOIN public.mediciones m ON a.medicion_id = m.id
                    JOIN public.dispositivos d ON m.dispositivo_id = d.id
                    JOIN public.pacientes p ON d.paciente_id = p.id
                    WHERE a.leida = false
                      AND p.usuario_id = :usuario_id
                    ORDER BY a.tipo_alerta DESC, a.timestamp DESC
                    LIMIT 20
                """)
            
            result = s.execute(query, {"usuario_id": usuario_id}).fetchall()
            
            alertas = []
            for row in result:
                alertas.append({
                    "id": row[0],
                    "tipo_alerta": row[1],
                    "mensaje": row[2],
                    "timestamp": row[3],
                    "tipo_medicion": row[4],
                    "valor": row[5],
                    "paciente_id": row[6],
                    "nombre_paciente": f"{row[7]} {row[8]}",
                })
            
            return alertas
    
    except Exception as e:
        st.error(f"Error obteniendo alertas: {str(e)}")
        return []


def marcar_alerta_leida(alerta_id: int) -> bool:
    """
    Marca una alerta como leída.
    
    Args:
        alerta_id: ID de la alerta
    
    Returns:
        True si se actualizó correctamente
    """
    try:
        conn = st.connection("postgresql", type="sql")
        with conn.session as s:
            update_query = text("""
                UPDATE public.alertas
                SET leida = true, fecha_lectura = CURRENT_TIMESTAMP
                WHERE id = :alerta_id
            """)
            
            s.execute(update_query, {"alerta_id": alerta_id})
            s.commit()
            
            return True
    
    except Exception as e:
        st.error(f"Error marcando alerta: {str(e)}")
        return False


def marcar_alertas_leidas_paciente(paciente_id: int) -> int:
    """
    Marca todas las alertas de un paciente como leídas.
    
    Returns:
        Cantidad de alertas marcadas
    """
    try:
        conn = st.connection("postgresql", type="sql")
        with conn.session as s:
            update_query = text("""
                UPDATE public.alertas
                SET leida = true, fecha_lectura = CURRENT_TIMESTAMP
                WHERE medicion_id IN (
                    SELECT m.id FROM public.mediciones m
                    JOIN public.dispositivos d ON m.dispositivo_id = d.id
                    WHERE d.paciente_id = :paciente_id
                )
                AND leida = false
            """)
            
            result = s.execute(update_query, {"paciente_id": paciente_id})
            s.commit()
            
            return result.rowcount
    
    except Exception as e:
        st.error(f"Error marcando alertas: {str(e)}")
        return 0
