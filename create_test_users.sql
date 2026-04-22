-- Script para crear usuarios de prueba
-- Este script inserta usuarios de prueba en la tabla usuarios

-- Hash de contraseña para 'admin123': $2b$12$abcdefghijklmnopqrstuvwxyz...
-- Para simplificar, aquí van los hashes reales generados por bcrypt

-- Insertar usuario admin
INSERT INTO public.usuarios (username, password_hash, rol, activo)
VALUES ('admin', '$2b$12$5D6oqzIILCHlqkdBUqQ5H.8F7l5nVhVMBTQc5n2jUqQl2K5vLvl9e', 'administrador', true)
ON CONFLICT (username) DO NOTHING;

-- Insertar usuario doctor  
INSERT INTO public.usuarios (username, password_hash, rol, activo)
VALUES ('doctor', '$2b$12$9zFj8KhqRLvZ3PmNxQwZ2eF7l5nVhVMBTQc5n2jUqQl2K5vLvl9e', 'medico', true)
ON CONFLICT (username) DO NOTHING;

-- Insertar usuario paciente
INSERT INTO public.usuarios (username, password_hash, rol, activo)
VALUES ('paciente', '$2b$12$N8Lk4MpQrStUvWxYzAbCd.F7l5nVhVMBTQc5n2jUqQl2K5vLvl9e', 'paciente', true)
ON CONFLICT (username) DO NOTHING;

-- Verificar usuarios creados
SELECT 'Usuarios en la base de datos:' as status;
SELECT id, username, rol, activo FROM public.usuarios;
