"""Script para crear usuarios en la base de datos"""
import os
import sys

os.chdir(r'c:\Users\cesar\OneDrive\Escritorio\Tareas\SERVICIO SOCIAL\IHeartCare')

from sqlalchemy import create_engine, text
import bcrypt

DB_URL = 'postgresql://postgres:312245cesar@localhost:5433/IHeartCareDB'
engine = create_engine(DB_URL)

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

test_users = [
    ('admin', 'admin123', 'administrador'),
    ('doctor', 'doctor123', 'medico'),
    ('paciente', 'paciente123', 'paciente'),
]

print('\n=== CREANDO USUARIOS DE PRUEBA ===\n')

try:
    with engine.connect() as conn:
        for username, password, rol in test_users:
            check = text('SELECT id FROM public.usuarios WHERE username = :username')
            result = conn.execute(check, {'username': username}).fetchone()
            
            if result:
                print('OK - {} ({}) ya existe'.format(username, rol))
            else:
                insert = text('''
                    INSERT INTO public.usuarios (username, password_hash, rol, activo)
                    VALUES (:username, :password_hash, :rol, true)
                ''')
                conn.execute(insert, {
                    'username': username,
                    'password_hash': hash_password(password),
                    'rol': rol
                })
                conn.commit()
                print('OK - {} ({}) creado'.format(username, rol))
        
        print('\n=== USUARIOS FINALES ===\n')
        result = conn.execute(text('SELECT id, username, rol FROM public.usuarios ORDER BY id'))
        for row in result:
            print('ID: {}, Usuario: {}, Rol: {}'.format(row[0], row[1], row[2]))
        
        print('\n=== EXITO - Usuarios listos para login ===\n')

except Exception as e:
    print('ERROR: {}'.format(str(e)))
    import traceback
    traceback.print_exc()
