import psycopg2
from psycopg2 import sql
from datetime import datetime, timedelta
import random

# Configuración de conexión
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'IHeartCareDB',
    'user': 'postgres',
    'password': '312245cesar'
}

try:
    # Conectar a la base de datos
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("=== INSERTANDO MONITOREOS FICTICIOS ===\n")
    
    # Obtener pacientes
    cursor.execute("SELECT id FROM public.pacientes ORDER BY id")
    pacientes = cursor.fetchall()
    pacientes_ids = [p[0] for p in pacientes]
    
    if not pacientes_ids:
        print("❌ No hay pacientes registrados.")
        conn.close()
        exit(1)
    
    # Motivos variados
    motivos = [
        "Control post-operatorio cardíaco",
        "Seguimiento por arritmia cardíaca",
        "Ajuste de medicación antihipertensiva",
        "Monitoreo preventivo",
        "Control de insuficiencia cardíaca",
        "Evaluación de síntomas cardiovasculares",
        "Seguimiento post-infarto",
        "Control de presión arterial",
        None,  # Sin motivo
    ]
    
    # Crear 6 monitoreos activos y 4 históricos
    monitoreos_data = []
    
    # 6 Monitoreos activos
    for idx in range(6):
        paciente_id = pacientes_ids[idx % len(pacientes_ids)]
        fecha_inicio = datetime.now() - timedelta(days=random.randint(5, 60))
        
        # Algunos indefinidos, otros con fecha fin
        if idx < 3:
            fecha_fin = None  # Indefinido
            tipo_mon = "∞ Indefinido"
        else:
            fecha_fin = datetime.now() + timedelta(days=random.randint(10, 30))
            tipo_mon = f"Hasta {fecha_fin.strftime('%d/%m/%Y')}"
        
        motivo = random.choice(motivos)
        
        cursor.execute("""
            INSERT INTO public.monitoreos 
            (paciente_id, fecha_inicio, fecha_fin, motivo, activo)
            VALUES (%s, %s, %s, %s, true)
            RETURNING id
        """, (paciente_id, fecha_inicio, fecha_fin, motivo))
        
        mon_id = cursor.fetchone()[0]
        monitoreos_data.append({
            'id': mon_id,
            'paciente_id': paciente_id,
            'tipo': tipo_mon,
            'activo': True,
            'motivo': motivo or "Monitoreo general"
        })
    
    # 4 Monitoreos inactivos (histórico)
    for idx in range(4):
        paciente_id = pacientes_ids[(6 + idx) % len(pacientes_ids)]
        fecha_inicio = datetime.now() - timedelta(days=random.randint(30, 120))
        fecha_fin = fecha_inicio + timedelta(days=random.randint(15, 45))
        motivo = random.choice(motivos)
        
        cursor.execute("""
            INSERT INTO public.monitoreos 
            (paciente_id, fecha_inicio, fecha_fin, motivo, activo)
            VALUES (%s, %s, %s, %s, false)
            RETURNING id
        """, (paciente_id, fecha_inicio, fecha_fin, motivo))
        
        mon_id = cursor.fetchone()[0]
        monitoreos_data.append({
            'id': mon_id,
            'paciente_id': paciente_id,
            'tipo': f"Completado {fecha_fin.strftime('%d/%m/%Y')}",
            'activo': False,
            'motivo': motivo or "Monitoreo completado"
        })
    
    conn.commit()
    
    # Mostrar resumen
    print("✅ Monitoreos Activos:\n")
    for mon in monitoreos_data[:6]:
        estado_icon = "🟢" if mon['activo'] else "⏸️"
        print(f"{estado_icon} ID {mon['id']}: Paciente {mon['paciente_id']}")
        print(f"   ├─ Estado: {'Activo' if mon['activo'] else 'Inactivo'}")
        print(f"   ├─ Tipo: {mon['tipo']}")
        print(f"   └─ Motivo: {mon['motivo']}\n")
    
    print("⏸️ Monitoreos Históricos:\n")
    for mon in monitoreos_data[6:]:
        print(f"ID {mon['id']}: Paciente {mon['paciente_id']}")
        print(f"   ├─ Estado: Inactivo")
        print(f"   ├─ Tipo: {mon['tipo']}")
        print(f"   └─ Motivo: {mon['motivo']}\n")
    
    # Resumen final
    print("=== RESUMEN ===")
    cursor.execute("SELECT COUNT(*) FROM public.monitoreos WHERE activo = true")
    activos = cursor.fetchone()[0]
    print(f"Monitoreos activos: {activos}")
    
    cursor.execute("SELECT COUNT(*) FROM public.monitoreos WHERE activo = false")
    inactivos = cursor.fetchone()[0]
    print(f"Monitoreos inactivos: {inactivos}")
    
    cursor.execute("SELECT COUNT(*) FROM public.monitoreos WHERE fecha_fin IS NULL")
    indefinidos = cursor.fetchone()[0]
    print(f"Monitoreos indefinidos: {indefinidos}")
    
    print("\n✅ Proceso completado exitosamente")
    
    cursor.close()
    conn.close()

except psycopg2.Error as e:
    print(f"❌ Error en la base de datos: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
