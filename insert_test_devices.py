import psycopg2
from psycopg2 import sql
import random
import uuid
from datetime import datetime, timedelta

# Configuración de conexión
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'IHeartCareDB',
    'user': 'postgres',
    'password': '312245cesar'
}

# Modelos de dispositivos realistas (smartwatches)
DEVICE_MODELS = [
    "Apple Watch Series 9",
    "Fitbit Sense 2",
    "Samsung Galaxy Watch 6",
    "Garmin Forerunner 965",
    "Xiaomi Mi Band 8 Pro",
    "Huawei Watch 4 Pro",
    "Polar Vantage V3",
    "COROS Apex 2 Pro",
    "Withings ScanWatch 2",
    "Amazfit GTR 4"
]

def generate_mac_address():
    """Genera una dirección MAC válida aleatoria"""
    return "02:" + ":".join([f"{random.randint(0x00, 0xff):02x}" for _ in range(5)])

def generate_device_serial():
    """Genera un número de serie único"""
    return f"DEV-{random.randint(100000, 999999)}"

try:
    # Conectar a la base de datos
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("=== INSERTANDO DISPOSITIVOS FICTICIOS ===\n")
    
    # Obtener pacientes existentes
    cursor.execute("SELECT id FROM public.pacientes ORDER BY id")
    pacientes = cursor.fetchall()
    pacientes_ids = [p[0] for p in pacientes]
    
    if len(pacientes_ids) < 10:
        print(f"⚠️ Solo hay {len(pacientes_ids)} pacientes. Se necesitan 10.")
        conn.close()
        exit(1)
    
    # Devices a insertar
    dispositivos_data = []
    device_estados = []
    
    for idx, modelo in enumerate(DEVICE_MODELS, 1):
        paciente_id = pacientes_ids[idx - 1]  # Uno por paciente
        mac_address = generate_mac_address()
        serial = generate_device_serial()
        
        # Estados variados: 7 activos, 2 inactivos, 1 sin paciente
        if idx <= 8:
            activo = True
            estado_texto = "✅ Activo"
        else:
            activo = False
            estado_texto = "⏸️ Inactivo"
        
        dispositivos_data.append({
            'idx': idx,
            'paciente_id': paciente_id,
            'modelo': modelo,
            'mac': mac_address,
            'serial': serial,
            'activo': activo,
            'estado': estado_texto
        })
    
    # Insertar dispositivos
    for device in dispositivos_data:
        cursor.execute("""
            INSERT INTO public.dispositivos 
            (paciente_id, modelo, mac_address, fecha_asignacion, activo)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (
            device['paciente_id'],
            device['modelo'],
            device['mac'],
            datetime.now() - timedelta(days=random.randint(1, 60)),
            device['activo']
        ))
        
        device_id = cursor.fetchone()[0]
        
        print(f"{device['idx']}. {device['estado']} {device['modelo']}")
        print(f"   ├─ Dispositivo ID: {device_id}")
        print(f"   ├─ Paciente ID: {device['paciente_id']}")
        print(f"   ├─ MAC Address: {device['mac']}")
        print(f"   ├─ Serial: {device['serial']}")
        print(f"   └─ Asignado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    conn.commit()
    
    # Mostrar resumen
    print("=== RESUMEN ===")
    cursor.execute("SELECT COUNT(*) FROM public.dispositivos")
    total_dispositivos = cursor.fetchone()[0]
    print(f"Total de dispositivos: {total_dispositivos}")
    
    cursor.execute("SELECT COUNT(*) FROM public.dispositivos WHERE activo = true")
    activos = cursor.fetchone()[0]
    print(f"Dispositivos activos: {activos}")
    
    cursor.execute("SELECT COUNT(*) FROM public.dispositivos WHERE activo = false")
    inactivos = cursor.fetchone()[0]
    print(f"Dispositivos inactivos: {inactivos}")
    
    print("\n✅ Proceso completado exitosamente")
    
    cursor.close()
    conn.close()

except psycopg2.Error as e:
    print(f"❌ Error en la base de datos: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
