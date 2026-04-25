#!/usr/bin/env python3
"""Genera hashes bcrypt para las contraseñas de prueba"""

import sys
import os

# Añadir el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from core.auth import hash_password
    
    # Generar hashes
    passwords = {
        'admin': 'admin123',
        'doctor': 'doctor123', 
        'paciente': 'paciente123'
    }
    
    print("=== HASHES GENERADOS ===\n")
    for user, pwd in passwords.items():
        hashed = hash_password(pwd)
        print(f"INSERT INTO public.usuarios (username, password_hash, rol, activo)")
        print(f"VALUES ('{user}', '{hashed}', '{'administrador' if user == 'admin' else 'medico' if user == 'doctor' else 'paciente'}', true)")
        print(f"ON CONFLICT (username) DO NOTHING;\n")
        
except ImportError as e:
    print(f"Error importando auth: {e}")
    print("\nIntentando generar hashes manualmente...")
    
    try:
        import bcrypt
        
        passwords = {
            'admin': 'admin123',
            'doctor': 'doctor123',
            'paciente': 'paciente123'
        }
        
        print("=== HASHES GENERADOS ===\n")
        for user, pwd in passwords.items():
            hashed = bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            rol = 'administrador' if user == 'admin' else 'medico' if user == 'doctor' else 'paciente'
            print(f"INSERT INTO public.usuarios (username, password_hash, rol, activo)")
            print(f"VALUES ('{user}', '{hashed}', '{rol}', true)")
            print(f"ON CONFLICT (username) DO NOTHING;\n")
    except ImportError:
        print("No bcrypt disponible")
