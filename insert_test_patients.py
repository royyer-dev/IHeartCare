"""
Script para insertar 10 pacientes ficticios en la base de datos
"""

from sqlalchemy import create_engine, text
from datetime import date
import random

DB_URL = 'postgresql://postgres:312245cesar@localhost:5433/IHeartCareDB'
engine = create_engine(DB_URL)

# Datos ficticios de pacientes
pacientes_ficticios = [
    {
        'nombre': 'Carlos',
        'apellido_paterno': 'González',
        'apellido_materno': 'López',
        'fecha_nacimiento': date(1965, 3, 15),
        'curp': 'GOLC650315HDFNXS09',
        'nss': '12345678901',
        'sexo': 'Masculino',
        'estado_civil': 'Casado',
        'domicilio': 'Avenida Paseo de la Reforma 505, CDMX',
        'email': 'carlos.gonzalez@email.com',
        'telefono': '5551234567',
        'diagnostico': 'Hipertensión Arterial'
    },
    {
        'nombre': 'María',
        'apellido_paterno': 'Rodríguez',
        'apellido_materno': 'Martínez',
        'fecha_nacimiento': date(1978, 7, 22),
        'curp': 'ROMM780722MDFPST04',
        'nss': '23456789012',
        'sexo': 'Femenino',
        'estado_civil': 'Soltera',
        'domicilio': 'Calle Juárez 250, Guadalajara, Jalisco',
        'email': 'maria.rodriguez@email.com',
        'telefono': '3335678901',
        'diagnostico': 'Arritmia Cardíaca'
    },
    {
        'nombre': 'Juan',
        'apellido_paterno': 'Pérez',
        'apellido_materno': 'García',
        'fecha_nacimiento': date(1955, 11, 8),
        'curp': 'PEGJ551108HDFNXR07',
        'nss': '34567890123',
        'sexo': 'Masculino',
        'estado_civil': 'Viudo',
        'domicilio': 'Plaza Mayor 120, Monterrey, Nuevo León',
        'email': 'juan.perez@email.com',
        'telefono': '8181234567',
        'diagnostico': 'Infarto Previo'
    },
    {
        'nombre': 'Ana',
        'apellido_paterno': 'Hernández',
        'apellido_materno': 'Flores',
        'fecha_nacimiento': date(1982, 5, 19),
        'curp': 'HEHA820519MDFNRL08',
        'nss': '45678901234',
        'sexo': 'Femenino',
        'estado_civil': 'Casada',
        'domicilio': 'Calle Libertad 85, Puebla, Puebla',
        'email': 'ana.hernandez@email.com',
        'telefono': '2222234567',
        'diagnostico': 'Diabetes e Hipertensión'
    },
    {
        'nombre': 'Roberto',
        'apellido_paterno': 'García',
        'apellido_materno': 'López',
        'fecha_nacimiento': date(1972, 2, 3),
        'curp': 'GALR720203HDFNPS05',
        'nss': '56789012345',
        'sexo': 'Masculino',
        'estado_civil': 'Divorciado',
        'domicilio': 'Avenida Libertad 450, Cancún, Quintana Roo',
        'email': 'roberto.garcia@email.com',
        'telefono': '9988234567',
        'diagnostico': 'Insuficiencia Cardíaca'
    },
    {
        'nombre': 'Patricia',
        'apellido_paterno': 'López',
        'apellido_materno': 'Sánchez',
        'fecha_nacimiento': date(1968, 9, 12),
        'curp': 'LOSP680912MDFNCT06',
        'nss': '67890123456',
        'sexo': 'Femenino',
        'estado_civil': 'Soltera',
        'domicilio': 'Calle Colón 320, León, Guanajuato',
        'email': 'patricia.lopez@email.com',
        'telefono': '4774234567',
        'diagnostico': 'Soplo Cardíaco'
    },
    {
        'nombre': 'Fernando',
        'apellido_paterno': 'Martínez',
        'apellido_materno': 'Gutiérrez',
        'fecha_nacimiento': date(1960, 6, 28),
        'curp': 'MAGF600628HDFNST03',
        'nss': '78901234567',
        'sexo': 'Masculino',
        'estado_civil': 'Casado',
        'domicilio': 'Boulevard Central 890, Tijuana, Baja California',
        'email': 'fernando.martinez@email.com',
        'telefono': '6641234567',
        'diagnostico': 'Colesterol Alto'
    },
    {
        'nombre': 'Laura',
        'apellido_paterno': 'Sánchez',
        'apellido_materno': 'Ramírez',
        'fecha_nacimiento': date(1990, 1, 14),
        'curp': 'SARL900114MDFNMR01',
        'nss': '89012345678',
        'sexo': 'Femenino',
        'estado_civil': 'Casada',
        'domicilio': 'Calle Principal 567, Querétaro, Querétaro',
        'email': 'laura.sanchez@email.com',
        'telefono': '4421234567',
        'diagnostico': 'Palpitaciones'
    },
    {
        'nombre': 'Miguel',
        'apellido_paterno': 'Flores',
        'apellido_materno': 'Torres',
        'fecha_nacimiento': date(1975, 10, 5),
        'curp': 'FOTM751005HDFNRS02',
        'nss': '90123456789',
        'sexo': 'Masculino',
        'estado_civil': 'Soltero',
        'domicilio': 'Paseo de los Insurgentes 234, Morelia, Michoacán',
        'email': 'miguel.flores@email.com',
        'telefono': '4433234567',
        'diagnostico': 'Presión Arterial Elevada'
    },
    {
        'nombre': 'Gabriela',
        'apellido_paterno': 'Castillo',
        'apellido_materno': 'Mendoza',
        'fecha_nacimiento': date(1985, 4, 20),
        'curp': 'CAMG850420MDFNST04',
        'nss': '01234567890',
        'sexo': 'Femenino',
        'estado_civil': 'Soltera',
        'domicilio': 'Avenida Universidad 678, Cuernavaca, Morelos',
        'email': 'gabriela.castillo@email.com',
        'telefono': '7771234567',
        'diagnostico': 'Control post-operatorio'
    }
]

def insertar_pacientes():
    """Inserta los 10 pacientes ficticios en la base de datos"""
    
    with engine.connect() as conn:
        print('\n=== INSERTANDO PACIENTES FICTICIOS ===\n')
        
        for idx, paciente in enumerate(pacientes_ficticios, 1):
            try:
                # Verificar si el paciente ya existe por CURP
                check_query = text('SELECT id FROM public.pacientes WHERE curp = :curp')
                existing = conn.execute(check_query, {'curp': paciente['curp']}).fetchone()
                
                if existing:
                    print(f'{idx}. ✓ {paciente["nombre"]} {paciente["apellido_paterno"]} - Ya existe')
                else:
                    # Insertar paciente
                    insert_query = text("""
                        INSERT INTO public.pacientes 
                        (nombre, apellido_paterno, apellido_materno, fecha_nacimiento, curp, nss, 
                         sexo, estado_civil, domicilio, email, telefono, diagnostico)
                        VALUES (:nombre, :apellido_paterno, :apellido_materno, :fecha_nacimiento, 
                                :curp, :nss, :sexo, :estado_civil, :domicilio, :email, :telefono, :diagnostico)
                        RETURNING id
                    """)
                    
                    result = conn.execute(insert_query, paciente)
                    paciente_id = result.fetchone()[0]
                    conn.commit()
                    
                    print(f'{idx}. ✓ {paciente["nombre"]} {paciente["apellido_paterno"]} - Creado (ID: {paciente_id})')
            
            except Exception as e:
                print(f'{idx}. ✗ {paciente["nombre"]} {paciente["apellido_paterno"]} - Error: {str(e)[:50]}')
        
        # Mostrar resumen
        print('\n=== RESUMEN ===\n')
        result = conn.execute(text('SELECT COUNT(*) as total FROM public.pacientes'))
        total = result.fetchone()[0]
        print(f'Total de pacientes en la base de datos: {total}')
        
        print('\n=== PACIENTES INSERTADOS ===\n')
        result = conn.execute(text(
            'SELECT id, nombre, apellido_paterno, email, diagnostico FROM public.pacientes ORDER BY id DESC LIMIT 10'
        ))
        
        for row in result:
            print(f'ID: {row[0]:<3} | {row[1]} {row[2]:<15} | {row[3]:<30} | {row[4]}')

if __name__ == '__main__':
    insertar_pacientes()
    print('\n✅ Proceso completado\n')
