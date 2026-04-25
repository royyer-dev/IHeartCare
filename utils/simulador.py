"""
Simulador de eventos peligrosos para pacientes.
Genera mediciones anómalas para testing y demostración del sistema.
"""

import streamlit as st
from sqlalchemy import text
from datetime import datetime, timedelta
import random
from typing import Optional
from .alerta_generator import crear_alerta_directa

# Perfiles de eventos peligrosos con rangos de valores anómalos
TIPOS_EVENTOS = {
    "Taquicardia Severa": {
        "descripcion": "FC > 150 lpm",
        "mediciones": {
            "Ritmo Cardíaco": (150, 180, "lpm"),
        },
        "severidad": "crítica",
    },
    "Bradicardia Severa": {
        "descripcion": "FC < 40 lpm",
        "mediciones": {
            "Ritmo Cardíaco": (20, 40, "lpm"),
        },
        "severidad": "crítica",
    },
    "Caída de SpO₂": {
        "descripcion": "Saturación < 90%",
        "mediciones": {
            "Saturación Oxígeno": (75, 89, "%"),
            "Ritmo Cardíaco": (85, 130, "lpm"),
        },
        "severidad": "crítica",
    },
    "Crisis Hipertensiva": {
        "descripcion": "TA > 180/110 mmHg",
        "mediciones": {
            "Ritmo Cardíaco": (90, 130, "lpm"),
            "Presión Sistólica": (180, 220, "mmHg"),
            "Presión Diastólica": (110, 140, "mmHg"),
        },
        "severidad": "crítica",
    },
    "Hipotensión Severa": {
        "descripcion": "TA < 80/60 mmHg",
        "mediciones": {
            "Presión Sistólica": (50, 80, "mmHg"),
            "Presión Diastólica": (30, 60, "mmHg"),
            "Ritmo Cardíaco": (100, 150, "lpm"),
        },
        "severidad": "crítica",
    },
    "Arritmia Detectada": {
        "descripcion": "Cambios irregulares en FC",
        "mediciones": {
            "Ritmo Cardíaco": (40, 160, "lpm"),
        },
        "severidad": "crítica",
    },
    "Evento Anómalo Leve": {
        "descripcion": "Desviación moderada de parámetros",
        "mediciones": {
            "Ritmo Cardíaco": (110, 130, "lpm"),
            "Presión Sistólica": (140, 160, "mmHg"),
        },
        "severidad": "advertencia",
    },
}


def generar_medicion_anomala(
    dispositivo_id: int,
    tipo_evento: str,
    intensidad: str = "moderada",
    timestamp: Optional[datetime] = None,
) -> Optional[int]:
    """
    Genera una medición anómala para simular un evento peligroso.
    
    Args:
        dispositivo_id: ID del dispositivo del paciente
        tipo_evento: Tipo de evento ('Taquicardia Severa', 'Caída de SpO₂', etc.)
        intensidad: 'leve', 'moderada', 'crítica' (afecta la magnitud)
        timestamp: Timestamp de la medición (default: ahora)
    
    Returns:
        ID de la medición creada o None si falla
    """
    try:
        if tipo_evento not in TIPOS_EVENTOS:
            st.error(f"Tipo de evento desconocido: {tipo_evento}")
            return None
        
        if timestamp is None:
            timestamp = datetime.now()
        
        evento = TIPOS_EVENTOS[tipo_evento]
        conn = st.connection("postgresql", type="sql")
        
        medicion_ids = []
        
        with conn.session as s:
            # Generar medición para cada tipo incluido en el evento
            for tipo_medicion, (min_val, max_val, unidad) in evento["mediciones"].items():
                # Ajustar rango según intensidad
                if intensidad == "leve":
                    # Reducir la anormalidad hacia valores más cercanos a normal
                    min_val = min_val + (max_val - min_val) * 0.3
                elif intensidad == "moderada":
                    # Usar rango tal cual
                    pass
                else:  # crítica
                    # Extremar los valores
                    min_val = min_val - (max_val - min_val) * 0.2
                    max_val = max_val + (max_val - min_val) * 0.2
                
                valor = round(random.uniform(min_val, max_val), 1)
                
                # Insertar medición
                medicion_query = text("""
                    INSERT INTO public.mediciones 
                    (dispositivo_id, tipo_medicion, valor, unidad_medida, timestamp)
                    VALUES (:dispositivo_id, :tipo_medicion, :valor, :unidad_medida, :timestamp)
                    RETURNING id
                """)
                
                resultado = s.execute(
                    medicion_query,
                    {
                        "dispositivo_id": dispositivo_id,
                        "tipo_medicion": tipo_medicion,
                        "valor": valor,
                        "unidad_medida": unidad,
                        "timestamp": timestamp,
                    },
                ).fetchone()
                
                s.commit()
                
                if resultado:
                    medicion_id = resultado[0]
                    medicion_ids.append(medicion_id)
                    
                    # Crear alerta automáticamente
                    mensaje = f"⚠️ Evento simulado: {tipo_evento} - {tipo_medicion}: {valor} {unidad}"
                    crear_alerta_directa(
                        medicion_id,
                        evento["severidad"],
                        mensaje,
                    )
        
        return medicion_ids[0] if medicion_ids else None
    
    except Exception as e:
        st.error(f"Error generando medición anómala: {str(e)}")
        return None


def simular_evento_continuo(
    dispositivo_id: int,
    tipo_evento: str,
    duracion_minutos: int = 5,
    intervalo_segundos: int = 30,
    progress_container=None,
):
    """
    Simula un evento continuo generando mediciones cada N segundos.
    
    Args:
        dispositivo_id: ID del dispositivo
        tipo_evento: Tipo de evento
        duracion_minutos: Cuánto tiempo simular
        intervalo_segundos: Cada cuántos segundos generar medición
        progress_container: Contenedor Streamlit para mostrar progreso
    
    Returns:
        Cantidad de mediciones generadas
    """
    import time
    
    try:
        total_mediciones = 0
        inicio = datetime.now()
        duracion_total = timedelta(minutes=duracion_minutos)
        
        evento = TIPOS_EVENTOS[tipo_evento]
        
        while True:
            elapsed = datetime.now() - inicio
            
            if progress_container:
                progreso = min(100, int((elapsed.total_seconds() / duracion_total.total_seconds()) * 100))
                progress_container.progress(progreso)
            
            if elapsed > duracion_total:
                break
            
            # Generar medición
            generar_medicion_anomala(
                dispositivo_id,
                tipo_evento,
                intensidad="moderada",
                timestamp=datetime.now(),
            )
            total_mediciones += 1
            
            # Esperar antes de siguiente medición
            time.sleep(intervalo_segundos)
        
        return total_mediciones
    
    except Exception as e:
        st.error(f"Error en simulación continua: {str(e)}")
        return 0


def obtener_dispositivos_pacientes() -> list:
    """
    Obtiene lista de dispositivos disponibles para simulación.
    
    Returns:
        Lista de diccionarios con id, paciente_id, nombre_paciente, estado
    """
    try:
        conn = st.connection("postgresql", type="sql")
        with conn.session as s:
            query = text("""
                SELECT d.id, d.paciente_id, d.modelo, p.nombre, p.apellido_paterno, 
                       COUNT(m.id) as total_mediciones
                FROM public.dispositivos d
                JOIN public.pacientes p ON d.paciente_id = p.id
                LEFT JOIN public.mediciones m ON d.id = m.dispositivo_id
                WHERE d.activo = true
                GROUP BY d.id, p.id, p.nombre, p.apellido_paterno
                ORDER BY p.nombre ASC
            """)
            
            resultado = s.execute(query).fetchall()
            
            dispositivos = []
            for row in resultado:
                dispositivos.append({
                    "id": row[0],
                    "paciente_id": row[1],
                    "modelo": row[2],
                    "nombre_paciente": f"{row[3]} {row[4]}",
                    "total_mediciones": row[5],
                })
            
            return dispositivos
    
    except Exception as e:
        st.error(f"Error obteniendo dispositivos: {str(e)}")
        return []


def obtener_ultimas_mediciones_paciente(paciente_id: int, limite: int = 10) -> list:
    """
    Obtiene las últimas mediciones de un paciente.
    
    Returns:
        Lista de diccionarios con información de mediciones
    """
    try:
        conn = st.connection("postgresql", type="sql")
        with conn.session as s:
            query = text("""
                SELECT m.id, m.tipo_medicion, m.valor, m.unidad_medida, m.timestamp,
                       CASE 
                           WHEN a.id IS NOT NULL THEN a.tipo_alerta
                           ELSE 'normal'
                       END as estado
                FROM public.mediciones m
                JOIN public.dispositivos d ON m.dispositivo_id = d.id
                LEFT JOIN public.alertas a ON m.id = a.medicion_id
                WHERE d.paciente_id = :paciente_id
                ORDER BY m.timestamp DESC
                LIMIT :limite
            """)
            
            resultado = s.execute(query, {"paciente_id": paciente_id, "limite": limite}).fetchall()
            
            mediciones = []
            for row in resultado:
                mediciones.append({
                    "id": row[0],
                    "tipo_medicion": row[1],
                    "valor": row[2],
                    "unidad_medida": row[3],
                    "timestamp": row[4],
                    "estado": row[5],
                })
            
            return mediciones
    
    except Exception as e:
        st.error(f"Error obteniendo mediciones: {str(e)}")
        return []
