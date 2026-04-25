"""
Script para generar 10 pacientes simulados permanentes con datos realistas.
Incluye: nombres, diagnósticos, médicos asignados, dispositivos y mediciones iniciales.
"""

import streamlit as st
from sqlalchemy import text
from datetime import datetime, timedelta
import random

# Datos de ejemplo realistas para pacientes mexicanos
PACIENTES_DEMO = [
    {
        "nombre": "Carlos",
        "apellido_paterno": "González",
        "apellido_materno": "Rodríguez",
        "fecha_nacimiento": "1965-03-22",
        "curp": "GOCR650322HDFNCS08",
        "nss": "12345678901",
        "sexo": "Masculino",
        "estado_civil": "Casado",
        "email": "carlos.gonzalez@email.com",
        "telefono": "5551234001",
        "diagnostico": "Hipertensión Arterial Sistémica (HAS) - Grado II",
        "condicion": "hipertension",
    },
    {
        "nombre": "Ana",
        "apellido_paterno": "Martínez",
        "apellido_materno": "López",
        "fecha_nacimiento": "1978-07-14",
        "curp": "MALO780714MDFNNS06",
        "nss": "12345678902",
        "sexo": "Femenino",
        "estado_civil": "Casada",
        "email": "ana.martinez@email.com",
        "telefono": "5551234002",
        "diagnostico": "Diabetes Mellitus Tipo 2",
        "condicion": "diabetes",
    },
    {
        "nombre": "Francisco",
        "apellido_paterno": "Sánchez",
        "apellido_materno": "García",
        "fecha_nacimiento": "1952-11-30",
        "curp": "SAGF521130HDFNCS01",
        "nss": "12345678903",
        "sexo": "Masculino",
        "estado_civil": "Viudo",
        "email": "francisco.sanchez@email.com",
        "telefono": "5551234003",
        "diagnostico": "Arritmia Cardíaca - Fibrilación Auricular",
        "condicion": "arritmia",
    },
    {
        "nombre": "Rosa",
        "apellido_paterno": "Hernández",
        "apellido_materno": "Díaz",
        "fecha_nacimiento": "1985-09-08",
        "curp": "HEDR850908MDFNSS02",
        "nss": "12345678904",
        "sexo": "Femenino",
        "estado_civil": "Soltera",
        "email": "rosa.hernandez@email.com",
        "telefono": "5551234004",
        "diagnostico": "Apnea del Sueño - Moderada",
        "condicion": "apnea",
    },
    {
        "nombre": "Jorge",
        "apellido_paterno": "Ramírez",
        "apellido_materno": "Moreno",
        "fecha_nacimiento": "1970-01-16",
        "curp": "RAMJ700116HDFNMS09",
        "nss": "12345678905",
        "sexo": "Masculino",
        "estado_civil": "Casado",
        "email": "jorge.ramirez@email.com",
        "telefono": "5551234005",
        "diagnostico": "Insuficiencia Cardíaca - NY FC II",
        "condicion": "insuficiencia",
    },
    {
        "nombre": "Elena",
        "apellido_paterno": "Castro",
        "apellido_materno": "Vega",
        "fecha_nacimiento": "1995-04-27",
        "curp": "CAVE950427MDFNSG05",
        "nss": "12345678906",
        "sexo": "Femenino",
        "estado_civil": "Soltera",
        "email": "elena.castro@email.com",
        "telefono": "5551234006",
        "diagnostico": "Prehipertensión + Sobrepeso",
        "condicion": "prehipertension",
    },
    {
        "nombre": "Miguel",
        "apellido_paterno": "Flores",
        "apellido_materno": "Ruiz",
        "fecha_nacimiento": "1960-08-05",
        "curp": "FORM600805HDFNLS07",
        "nss": "12345678907",
        "sexo": "Masculino",
        "estado_civil": "Casado",
        "email": "miguel.flores@email.com",
        "telefono": "5551234007",
        "diagnostico": "Enfermedad Arterial Coronaria",
        "condicion": "coronaria",
    },
    {
        "nombre": "Gabriela",
        "apellido_paterno": "Torres",
        "apellido_materno": "Jiménez",
        "fecha_nacimiento": "1982-12-11",
        "curp": "TOJG821211MDFNRS04",
        "nss": "12345678908",
        "sexo": "Femenino",
        "estado_civil": "Divorciada",
        "email": "gabriela.torres@email.com",
        "telefono": "5551234008",
        "diagnostico": "Migraña Vasomotora + HAS",
        "condicion": "migraña",
    },
    {
        "nombre": "Rafael",
        "apellido_paterno": "Gutiérrez",
        "apellido_materno": "Álvarez",
        "fecha_nacimiento": "1975-06-19",
        "curp": "GUAR750619HDFNTS03",
        "nss": "12345678909",
        "sexo": "Masculino",
        "estado_civil": "Casado",
        "email": "rafael.gutierrez@email.com",
        "telefono": "5551234009",
        "diagnostico": "Obesidad - Complicada",
        "condicion": "obesidad",
    },
    {
        "nombre": "Sandra",
        "apellido_paterno": "Vargas",
        "apellido_materno": "Mendoza",
        "fecha_nacimiento": "1988-10-25",
        "curp": "VAMS881025MDFNRG08",
        "nss": "12345678910",
        "sexo": "Femenino",
        "estado_civil": "Casada",
        "email": "sandra.vargas@email.com",
        "telefono": "5551234010",
        "diagnostico": "Síndrome Metabólico",
        "condicion": "metabolico",
    },
]

# Rangos de valores para cada condición (para simular mediciones realistas)
MEDICIONES_POR_CONDICION = {
    "normal": {
        "Ritmo Cardíaco": (60, 100, "lpm"),
        "Saturación Oxígeno": (95, 100, "%"),
        "Presión Sistólica": (90, 130, "mmHg"),
        "Presión Diastólica": (60, 85, "mmHg"),
    },
    "hipertension": {
        "Ritmo Cardíaco": (70, 110, "lpm"),
        "Saturación Oxígeno": (96, 100, "%"),
        "Presión Sistólica": (140, 160, "mmHg"),
        "Presión Diastólica": (85, 100, "mmHg"),
    },
    "diabetes": {
        "Ritmo Cardíaco": (75, 105, "lpm"),
        "Saturación Oxígeno": (94, 100, "%"),
        "Presión Sistólica": (120, 145, "mmHg"),
        "Presión Diastólica": (75, 95, "mmHg"),
    },
    "arritmia": {
        "Ritmo Cardíaco": (45, 150, "lpm"),
        "Saturación Oxígeno": (95, 100, "%"),
        "Presión Sistólica": (100, 140, "mmHg"),
        "Presión Diastólica": (60, 90, "mmHg"),
    },
    "apnea": {
        "Ritmo Cardíaco": (55, 95, "lpm"),
        "Saturación Oxígeno": (85, 98, "%"),
        "Presión Sistólica": (100, 140, "mmHg"),
        "Presión Diastólica": (60, 85, "mmHg"),
    },
    "insuficiencia": {
        "Ritmo Cardíaco": (80, 120, "lpm"),
        "Saturación Oxígeno": (92, 98, "%"),
        "Presión Sistólica": (110, 150, "mmHg"),
        "Presión Diastólica": (65, 95, "mmHg"),
    },
    "coronaria": {
        "Ritmo Cardíaco": (65, 110, "lpm"),
        "Saturación Oxígeno": (94, 100, "%"),
        "Presión Sistólica": (120, 160, "mmHg"),
        "Presión Diastólica": (70, 100, "mmHg"),
    },
    "prehipertension": {
        "Ritmo Cardíaco": (65, 95, "lpm"),
        "Saturación Oxígeno": (96, 100, "%"),
        "Presión Sistólica": (120, 139, "mmHg"),
        "Presión Diastólica": (80, 89, "mmHg"),
    },
    "migraña": {
        "Ritmo Cardíaco": (70, 100, "lpm"),
        "Saturación Oxígeno": (96, 100, "%"),
        "Presión Sistólica": (110, 150, "mmHg"),
        "Presión Diastólica": (70, 90, "mmHg"),
    },
    "metabolico": {
        "Ritmo Cardíaco": (75, 105, "lpm"),
        "Saturación Oxígeno": (94, 99, "%"),
        "Presión Sistólica": (125, 155, "mmHg"),
        "Presión Diastólica": (80, 100, "mmHg"),
    },
    "obesidad": {
        "Ritmo Cardíaco": (80, 110, "lpm"),
        "Saturación Oxígeno": (95, 99, "%"),
        "Presión Sistólica": (130, 160, "mmHg"),
        "Presión Diastólica": (85, 100, "mmHg"),
    },
}


def generate_mediciones_for_patient(
    dispositivo_id: int, condicion: str, num_mediciones: int = 8
) -> list:
    """
    Genera mediciones realistas para un paciente según su condición.
    Retorna lista de tuplas (tipo_medicion, valor, unidad_medida, timestamp)
    """
    mediciones = []
    tipos = list(MEDICIONES_POR_CONDICION[condicion].keys())
    
    for i in range(num_mediciones):
        # Timestamp: últimos 7 días
        dias_atras = random.randint(0, 6)
        horas_atras = random.randint(0, 23)
        timestamp = datetime.now() - timedelta(days=dias_atras, hours=horas_atras)
        
        for tipo_medicion in tipos:
            min_val, max_val, unidad = MEDICIONES_POR_CONDICION[condicion][tipo_medicion]
            valor = round(random.uniform(min_val, max_val), 1)
            
            mediciones.append({
                "dispositivo_id": dispositivo_id,
                "tipo_medicion": tipo_medicion,
                "valor": valor,
                "unidad_medida": unidad,
                "timestamp": timestamp,
            })
    
    return mediciones


def generate_demo_data():
    """
    Genera 10 pacientes simulados con todos los datos relacionados.
    Se ejecuta una sola vez, ignora si ya existen.
    """
    st.subheader("📊 Generador de Datos Demo")
    st.info(
        "Este script inserta 10 pacientes simulados permanentes con diagnósticos variados, "
        "médicos asignados, dispositivos y mediciones históricas."
    )
    
    if st.button("🚀 Generar Pacientes Demo", type="primary", key="gen_demo"):
        try:
            conn = st.connection("postgresql", type="sql")
            with conn.session as s:
                # Obtener al menos un médico existente
                medicos_query = text("SELECT id FROM public.personal_medico LIMIT 1")
                medicos_result = s.execute(medicos_query).fetchall()
                
                if not medicos_result:
                    st.error("❌ No hay médicos registrados. Crea un médico primero.")
                    return
                
                medico_id = medicos_result[0][0]
                total_pacientes_creados = 0
                total_mediciones_creadas = 0
                
                for paciente_data in PACIENTES_DEMO:
                    try:
                        # 1. Crear paciente
                        paciente_query = text("""
                            INSERT INTO public.pacientes 
                            (nombre, apellido_paterno, apellido_materno, fecha_nacimiento, 
                             curp, nss, sexo, estado_civil, email, telefono, diagnostico)
                            VALUES (:nombre, :apellido_paterno, :apellido_materno, :fecha_nacimiento,
                                    :curp, :nss, :sexo, :estado_civil, :email, :telefono, :diagnostico)
                            ON CONFLICT (curp) DO NOTHING
                            RETURNING id
                        """)
                        
                        paciente_result = s.execute(
                            paciente_query,
                            {
                                "nombre": paciente_data["nombre"],
                                "apellido_paterno": paciente_data["apellido_paterno"],
                                "apellido_materno": paciente_data["apellido_materno"],
                                "fecha_nacimiento": paciente_data["fecha_nacimiento"],
                                "curp": paciente_data["curp"],
                                "nss": paciente_data["nss"],
                                "sexo": paciente_data["sexo"],
                                "estado_civil": paciente_data["estado_civil"],
                                "email": paciente_data["email"],
                                "telefono": paciente_data["telefono"],
                                "diagnostico": paciente_data["diagnostico"],
                            },
                        ).fetchone()
                        
                        if not paciente_result:
                            continue  # Paciente ya existe
                        
                        paciente_id = paciente_result[0]
                        total_pacientes_creados += 1
                        
                        # 2. Asignar médico
                        asignar_medico_query = text("""
                            INSERT INTO public.pacientes_medicos (paciente_id, medico_id)
                            VALUES (:paciente_id, :medico_id)
                            ON CONFLICT DO NOTHING
                        """)
                        s.execute(asignar_medico_query, {"paciente_id": paciente_id, "medico_id": medico_id})
                        
                        # 3. Crear dispositivo
                        dispositivo_query = text("""
                            INSERT INTO public.dispositivos 
                            (paciente_id, modelo, mac_address, activo)
                            VALUES (:paciente_id, :modelo, :mac_address, true)
                            RETURNING id
                        """)
                        
                        mac_address = ":".join(f"{random.randint(0, 255):02x}" for _ in range(6))
                        dispositivo_result = s.execute(
                            dispositivo_query,
                            {
                                "paciente_id": paciente_id,
                                "modelo": "SmartWatch Pro X1",
                                "mac_address": mac_address,
                            },
                        ).fetchone()
                        
                        dispositivo_id = dispositivo_result[0]
                        
                        # 4. Generar mediciones
                        mediciones = generate_mediciones_for_patient(
                            dispositivo_id, paciente_data["condicion"]
                        )
                        
                        mediciones_query = text("""
                            INSERT INTO public.mediciones 
                            (dispositivo_id, tipo_medicion, valor, unidad_medida, timestamp)
                            VALUES (:dispositivo_id, :tipo_medicion, :valor, :unidad_medida, :timestamp)
                        """)
                        
                        for med in mediciones:
                            s.execute(mediciones_query, med)
                            total_mediciones_creadas += 1
                        
                    except Exception as e:
                        st.warning(f"⚠️ Error procesando {paciente_data['nombre']}: {str(e)}")
                        continue
                
                # Commit cambios
                s.commit()
                
                st.success(
                    f"✅ **{total_pacientes_creados}** pacientes demo creados exitosamente!\n"
                    f"✅ **{total_mediciones_creadas}** mediciones históricas insertadas."
                )
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    generate_demo_data()
