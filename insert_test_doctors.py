"""
Script para insertar 3 doctores ficticios con credenciales y asignarles pacientes
"""

from sqlalchemy import create_engine, text
import bcrypt

DB_URL = 'postgresql://postgres:312245cesar@localhost:5433/IHeartCareDB'
engine = create_engine(DB_URL)

def hash_password(password: str) -> str:
    """Encripta una contraseña usando bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Datos de doctores ficticios
doctores_ficticios = [
    {
        'nombre': 'Roberto',
        'apellido_paterno': 'Sánchez',
        'apellido_materno': 'Morales',
        'especialidad': 'Cardiología',
        'cedula_profesional': '1234567',
        'cedula_especialidad': '7654321',
        'universidad': 'UNAM',
        'email': 'roberto.sanchez@hospital.com',
        'username': 'dr.sanchez',
        'password': 'cardio123',
        'pacientes_ids': [1, 3, 5]  # Asignar algunos pacientes
    },
    {
        'nombre': 'Patricia',
        'apellido_paterno': 'Gutiérrez',
        'apellido_materno': 'López',
        'especialidad': 'Medicina Interna',
        'cedula_profesional': '2345678',
        'cedula_especialidad': '8765432',
        'universidad': 'IPN',
        'email': 'patricia.gutierrez@hospital.com',
        'username': 'dra.gutierrez',
        'password': 'medint456',
        'pacientes_ids': [2, 4, 6]
    },
    {
        'nombre': 'Luis',
        'apellido_paterno': 'Martínez',
        'apellido_materno': 'Ramírez',
        'especialidad': 'Electrofisiología Cardíaca',
        'cedula_profesional': '3456789',
        'cedula_especialidad': '9876543',
        'universidad': 'Universidad de Jalisco',
        'email': 'luis.martinez@hospital.com',
        'username': 'dr.martinez',
        'password': 'electro789',
        'pacientes_ids': [7, 8, 9, 10]
    }
]

def insertar_doctores():
    """Inserta los doctores ficticios con credenciales"""
    
    with engine.connect() as conn:
        print('\n=== INSERTANDO DOCTORES FICTICIOS CON CREDENCIALES ===\n')
        
        doctores_creados = []
        
        for idx, doctor in enumerate(doctores_ficticios, 1):
            try:
                # Verificar si el doctor ya existe por cédula profesional
                check_query = text('SELECT id FROM public.personal_medico WHERE cedula_profesional = :ced')
                existing = conn.execute(check_query, {'ced': doctor['cedula_profesional']}).fetchone()
                
                if existing:
                    print(f'{idx}. ✓ {doctor["nombre"]} {doctor["apellido_paterno"]} - Ya existe')
                    doctores_creados.append({'id': existing[0], 'username': doctor['username']})
                else:
                    # Insertar doctor
                    insert_query = text("""
                        INSERT INTO public.personal_medico 
                        (nombre, apellido_paterno, apellido_materno, especialidad, cedula_profesional, 
                         cedula_especialidad, universidad, email)
                        VALUES (:nombre, :apellido_paterno, :apellido_materno, :especialidad, 
                                :cedula_profesional, :cedula_especialidad, :universidad, :email)
                        RETURNING id
                    """)
                    
                    doctor_id = conn.execute(insert_query, {
                        'nombre': doctor['nombre'],
                        'apellido_paterno': doctor['apellido_paterno'],
                        'apellido_materno': doctor['apellido_materno'],
                        'especialidad': doctor['especialidad'],
                        'cedula_profesional': doctor['cedula_profesional'],
                        'cedula_especialidad': doctor['cedula_especialidad'],
                        'universidad': doctor['universidad'],
                        'email': doctor['email']
                    }).fetchone()[0]
                    
                    # Crear usuario para el doctor
                    usuario_query = text("""
                        INSERT INTO public.usuarios (username, password_hash, rol, activo)
                        VALUES (:username, :password_hash, 'medico', true)
                        RETURNING id
                    """)
                    
                    usuario_id = conn.execute(usuario_query, {
                        'username': doctor['username'],
                        'password_hash': hash_password(doctor['password'])
                    }).fetchone()[0]
                    
                    # Vincular usuario con doctor
                    link_query = text("""
                        UPDATE public.personal_medico 
                        SET usuario_id = :user_id 
                        WHERE id = :doctor_id
                    """)
                    
                    conn.execute(link_query, {'user_id': usuario_id, 'doctor_id': doctor_id})
                    conn.commit()
                    
                    # Asignar pacientes
                    for paciente_id in doctor['pacientes_ids']:
                        assign_query = text("""
                            INSERT INTO public.pacientes_medicos (paciente_id, medico_id)
                            VALUES (:paciente_id, :medico_id)
                            ON CONFLICT DO NOTHING
                        """)
                        conn.execute(assign_query, {'paciente_id': paciente_id, 'medico_id': doctor_id})
                    
                    conn.commit()
                    
                    print(f'{idx}. ✓ {doctor["nombre"]} {doctor["apellido_paterno"]} - Creado (ID: {doctor_id})')
                    print(f'   ├─ Usuario: {doctor["username"]}')
                    print(f'   ├─ Contraseña: {doctor["password"]}')
                    print(f'   └─ Pacientes asignados: {len(doctor["pacientes_ids"])}')
                    
                    doctores_creados.append({'id': doctor_id, 'username': doctor['username']})
            
            except Exception as e:
                print(f'{idx}. ✗ {doctor["nombre"]} {doctor["apellido_paterno"]} - Error: {str(e)[:50]}')
        
        # Mostrar resumen
        print('\n=== RESUMEN ===\n')
        result = conn.execute(text('SELECT COUNT(*) as total FROM public.personal_medico'))
        total = result.fetchone()[0]
        print(f'Total de médicos en la base de datos: {total}')
        
        print('\n=== CREDENCIALES DE DOCTORES ===\n')
        for doctor in doctores_ficticios:
            print(f'📋 Dr(a). {doctor["nombre"]} {doctor["apellido_paterno"]}')
            print(f'   Usuario: {doctor["username"]}')
            print(f'   Contraseña: {doctor["password"]}')
            print(f'   Especialidad: {doctor["especialidad"]}')
            print()

if __name__ == '__main__':
    insertar_doctores()
    print('✅ Proceso completado\n')
