import psycopg2
from datetime import datetime, timedelta
import random
import math

# Configuración de conexión
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'IHeartCareDB',
    'user': 'postgres',
    'password': '312245cesar'
}

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("=== INSERTANDO MEDICIONES FICTICIAS ===\n")
    
    # Obtener dispositivos
    cursor.execute("SELECT id, paciente_id FROM public.dispositivos ORDER BY id")
    dispositivos = cursor.fetchall()
    
    if not dispositivos:
        print("❌ No hay dispositivos registrados.")
        conn.close()
        exit(1)
    
    # Parámetros fisiológicos realistas por tipo de medición
    mediciones_config = {
        'frecuencia_cardiaca': {
            'unidad': 'bpm',
            'rango_normal': (60, 100),
            'rango_maximo': (40, 150),
        },
        'presion_sistolica': {
            'unidad': 'mmHg',
            'rango_normal': (90, 130),
            'rango_maximo': (70, 180),
        },
        'presion_diastolica': {
            'unidad': 'mmHg',
            'rango_normal': (60, 85),
            'rango_maximo': (40, 120),
        },
        'saturacion_oxigeno': {
            'unidad': '%',
            'rango_normal': (95, 100),
            'rango_maximo': (85, 100),
        },
        'temperatura': {
            'unidad': '°C',
            'rango_normal': (36.5, 37.5),
            'rango_maximo': (35.0, 39.0),
        },
        'variabilidad_frecuencia_cardiaca': {
            'unidad': 'ms',
            'rango_normal': (50, 100),
            'rango_maximo': (20, 200),
        },
    }
    
    total_mediciones = 0
    
    # Para cada dispositivo, generar mediciones
    for dispositivo_id, paciente_id in dispositivos:
        print(f"Generando mediciones para dispositivo {dispositivo_id} (Paciente {paciente_id})...\n")
        
        # Generar datos para los últimos 30 días
        ahora = datetime.now()
        
        # Crear 200 mediciones por dispositivo (aproximadamente cada 2 horas durante 30 días)
        for dias_atras in range(30, 0, -1):
            fecha = ahora - timedelta(days=dias_atras)
            
            for hora in range(0, 24, 2):  # Cada 2 horas
                fecha_medicion = fecha.replace(hour=hora, minute=random.randint(0, 59), second=random.randint(0, 59))
                
                # Generar valores realistas con variación
                fc = random.gauss(75, 8)  # Distribución normal alrededor de 75
                sys = random.gauss(120, 10)
                dia = random.gauss(80, 8)
                o2 = random.gauss(97, 1.5)
                temp = random.gauss(37, 0.3)
                vfc = random.gauss(65, 15)
                
                # Asegurar rangos fisiológicos
                fc = max(40, min(150, fc))
                sys = max(70, min(180, sys))
                dia = max(40, min(120, dia))
                o2 = max(85, min(100, o2))
                temp = max(35, min(39, temp))
                vfc = max(20, min(200, vfc))
                
                # Insertar cada medición
                mediciones = [
                    (dispositivo_id, fecha_medicion, 'frecuencia_cardiaca', round(fc, 2), 'bpm'),
                    (dispositivo_id, fecha_medicion, 'presion_sistolica', round(sys, 2), 'mmHg'),
                    (dispositivo_id, fecha_medicion, 'presion_diastolica', round(dia, 2), 'mmHg'),
                    (dispositivo_id, fecha_medicion, 'saturacion_oxigeno', round(o2, 2), '%'),
                    (dispositivo_id, fecha_medicion, 'temperatura', round(temp, 2), '°C'),
                    (dispositivo_id, fecha_medicion, 'variabilidad_frecuencia_cardiaca', round(vfc, 2), 'ms'),
                ]
                
                for med in mediciones:
                    cursor.execute("""
                        INSERT INTO public.mediciones 
                        (dispositivo_id, timestamp, tipo_medicion, valor, unidad_medida)
                        VALUES (%s, %s, %s, %s, %s)
                    """, med)
                    total_mediciones += 1
        
        print(f"✓ Dispositivo {dispositivo_id}: Mediciones generadas\n")
    
    conn.commit()
    
    # Mostrar resumen
    print("=== RESUMEN ===")
    print(f"Total de mediciones insertadas: {total_mediciones}")
    
    # Estadísticas
    cursor.execute("SELECT COUNT(*) FROM public.mediciones")
    total_db = cursor.fetchone()[0]
    print(f"Total de mediciones en BD: {total_db}")
    
    cursor.execute("SELECT COUNT(DISTINCT tipo_medicion) FROM public.mediciones")
    tipos = cursor.fetchone()[0]
    print(f"Tipos de mediciones: {tipos}")
    
    cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM public.mediciones")
    min_fecha, max_fecha = cursor.fetchone()
    print(f"Rango de fechas: {min_fecha} a {max_fecha}")
    
    print("\n✅ Proceso completado exitosamente")
    
    cursor.close()
    conn.close()

except psycopg2.Error as e:
    print(f"❌ Error en la base de datos: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
