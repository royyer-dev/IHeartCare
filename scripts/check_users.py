"""Script para verificar y crear usuarios de prueba

Uso: python scripts/check_users.py  (desde la raíz del proyecto)
"""

import os
from sqlalchemy import create_engine, text
import bcrypt

DB_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:312245cesar@localhost:5433/IHeartCareDB")

def hash_password(password: str) -> str:
    """Encripta una contraseña usando bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_and_create_users():
    """Verifica si existen usuarios y los crea si no existen"""
    engine = create_engine(DB_URL)
    
    try:
        with engine.connect() as conn:
            # Verificar usuarios existentes
            result = conn.execute(text('SELECT id, username, rol FROM public.usuarios'))
            usuarios = result.fetchall()
            
            print('\n=== USUARIOS ACTUALES ===')
            if usuarios:
                for u in usuarios:
                    print(f'✓ ID: {u[0]}, Username: {u[1]}, Rol: {u[2]}')
            else:
                print('❌ NO HAY USUARIOS EN LA BASE DE DATOS\n')
            
            # Definir usuarios a crear
            test_users = [
                ('admin', 'admin123', 'administrador'),
                ('doctor', 'doctor123', 'medico'),
                ('paciente', 'paciente123', 'paciente'),
            ]
            
            print('\n=== CREANDO/VERIFICANDO USUARIOS ===\n')
            
            for username, password, rol in test_users:
                # Verificar si el usuario existe
                check_query = text('SELECT id FROM public.usuarios WHERE username = :username')
                existing = conn.execute(check_query, {'username': username}).fetchone()
                
                if existing:
                    print(f'✓ Usuario {username} ({rol}) ya existe')
                else:
                    # Crear usuario
                    insert_query = text("""
                        INSERT INTO public.usuarios (username, password_hash, rol, activo)
                        VALUES (:username, :password_hash, :rol, true)
                        RETURNING id
                    """)
                    result = conn.execute(insert_query, {
                        'username': username,
                        'password_hash': hash_password(password),
                        'rol': rol
                    })
                    user_id = result.fetchone()[0]
                    conn.commit()
                    print(f'✓ Usuario {username} ({rol}) creado con ID: {user_id}')
            
            print('\n=== CREDENCIALES DE ACCESO ===')
            print('👨‍💼 Admin:    admin / admin123')
            print('👨‍⚕️ Doctor:   doctor / doctor123')
            print('👤 Paciente:  paciente / paciente123')
            print()
            
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_and_create_users()
