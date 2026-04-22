"""Verifica si los usuarios se crearon correctamente"""

import subprocess
import sys
import os
import tempfile

# Obtener el Python que está usando Streamlit
python_exe = sys.executable

print(f"Usando Python: {python_exe}")
print(f"Versión: {sys.version}")
print()

# Ejecutar setup_users.py como módulo dentro de Streamlit
code = """
import os
os.chdir(r'c:\\Users\\cesar\\OneDrive\\Escritorio\\Tareas\\SERVICIO SOCIAL\\IHeartCare')

from sqlalchemy import create_engine, text
import bcrypt

DB_URL = 'postgresql://postgres:312245cesar@localhost:5433/IHeartCareDB'
engine = create_engine(DB_URL)

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Crear usuarios de prueba
test_users = [
    ('admin', 'admin123', 'administrador'),
    ('doctor', 'doctor123', 'medico'),
    ('paciente', 'paciente123', 'paciente'),
]

with engine.connect() as conn:
    print('\\n=== VERIFICANDO Y CREANDO USUARIOS ===\\n')
    
    for username, password, rol in test_users:
        # Verificar si existe
        check = text('SELECT id FROM public.usuarios WHERE username = :username')
        result = conn.execute(check, {'username': username}).fetchone()
        
        if result:
            print(f'✓ {username} ({rol}) ya existe')
        else:
            # Crear usuario
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
            print(f'✓ {username} ({rol}) creado exitosamente')
    
    # Verificar todos los usuarios
    print('\\n=== USUARIOS EN LA BASE DE DATOS ===\\n')
    result = conn.execute(text('SELECT id, username, rol FROM public.usuarios ORDER BY id'))
    for row in result:
        print(f'ID: {row[0]}, Usuario: {row[1]}, Rol: {row[2]}')
    
    print('\\n✅ Proceso completado')
"""

# Ejecutar en el mismo Python de Streamlit
import tempfile
with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
    f.write(code)
    f.flush()
    
    result = subprocess.run([python_exe, f.name], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("ERRORES:")
        print(result.stderr)
    
    os.unlink(f.name)
