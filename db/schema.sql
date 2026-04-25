-- ============================================
-- I-HeartCare Database Schema
-- Sistema de Monitoreo Cardíaco
-- ============================================

-- Eliminar tablas existentes (solo para desarrollo)
DROP TABLE IF EXISTS public.alertas CASCADE;
DROP TABLE IF EXISTS public.mediciones CASCADE;
DROP TABLE IF EXISTS public.monitoreos CASCADE;
DROP TABLE IF EXISTS public.dispositivos CASCADE;
DROP TABLE IF EXISTS public.pacientes_medicos CASCADE;
DROP TABLE IF EXISTS public.pacientes CASCADE;
DROP TABLE IF EXISTS public.personal_medico CASCADE;
DROP TABLE IF EXISTS public.usuarios CASCADE;

-- ============================================
-- TABLA: usuarios
-- Gestiona la autenticación y roles del sistema
-- ============================================
CREATE TABLE public.usuarios (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL CHECK (rol IN ('administrador', 'medico', 'paciente')),
    activo BOOLEAN DEFAULT true,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultima_sesion TIMESTAMP
);

-- ============================================
-- TABLA: pacientes
-- Información de los pacientes del sistema
-- ============================================
CREATE TABLE public.pacientes (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER UNIQUE REFERENCES public.usuarios(id) ON DELETE SET NULL,
    nombre VARCHAR(100) NOT NULL,
    apellido_paterno VARCHAR(100) NOT NULL,
    apellido_materno VARCHAR(100),
    fecha_nacimiento DATE NOT NULL,
    curp VARCHAR(18) UNIQUE NOT NULL,
    nss VARCHAR(11),
    sexo VARCHAR(20) NOT NULL,
    estado_civil VARCHAR(50),
    domicilio TEXT,
    email VARCHAR(100),
    telefono VARCHAR(20),
    diagnostico VARCHAR(500),
    activo BOOLEAN DEFAULT true,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABLA: personal_medico
-- Información del personal médico
-- ============================================
CREATE TABLE public.personal_medico (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER UNIQUE REFERENCES public.usuarios(id) ON DELETE SET NULL,
    nombre VARCHAR(100) NOT NULL,
    apellido_paterno VARCHAR(100) NOT NULL,
    apellido_materno VARCHAR(100),
    especialidad VARCHAR(100) NOT NULL,
    cedula_profesional VARCHAR(50) NOT NULL,
    cedula_especialidad VARCHAR(50),
    universidad VARCHAR(200),
    email VARCHAR(100),
    activo BOOLEAN DEFAULT true,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABLA: pacientes_medicos
-- Relación entre pacientes y médicos asignados
-- ============================================
CREATE TABLE public.pacientes_medicos (
    id SERIAL PRIMARY KEY,
    paciente_id INTEGER NOT NULL REFERENCES public.pacientes(id) ON DELETE CASCADE,
    medico_id INTEGER NOT NULL REFERENCES public.personal_medico(id) ON DELETE CASCADE,
    fecha_asignacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(paciente_id, medico_id)
);

-- ============================================
-- TABLA: dispositivos
-- Dispositivos de monitoreo asignados a pacientes
-- ============================================
CREATE TABLE public.dispositivos (
    id SERIAL PRIMARY KEY,
    paciente_id INTEGER NOT NULL REFERENCES public.pacientes(id) ON DELETE CASCADE,
    modelo VARCHAR(100) NOT NULL,
    mac_address VARCHAR(17),
    direccion_url VARCHAR(2048),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    fecha_asignacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT true
);

-- ============================================
-- TABLA: monitoreos
-- Períodos de monitoreo activo de pacientes
-- ============================================
CREATE TABLE public.monitoreos (
    id SERIAL PRIMARY KEY,
    paciente_id INTEGER NOT NULL REFERENCES public.pacientes(id) ON DELETE CASCADE,
    fecha_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_fin TIMESTAMP,
    motivo TEXT,
    activo BOOLEAN DEFAULT true
);

-- ============================================
-- TABLA: mediciones
-- Datos biométricos capturados por los dispositivos
-- ============================================
CREATE TABLE public.mediciones (
    id SERIAL PRIMARY KEY,
    dispositivo_id INTEGER NOT NULL REFERENCES public.dispositivos(id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tipo_medicion VARCHAR(50) NOT NULL,
    valor NUMERIC(10, 2) NOT NULL,
    unidad_medida VARCHAR(20)
);

-- ============================================
-- TABLA: alertas
-- Alertas generadas por mediciones anormales
-- ============================================
CREATE TABLE public.alertas (
    id SERIAL PRIMARY KEY,
    medicion_id INTEGER NOT NULL REFERENCES public.mediciones(id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tipo_alerta VARCHAR(50) NOT NULL,
    mensaje TEXT NOT NULL,
    leida BOOLEAN DEFAULT false,
    fecha_lectura TIMESTAMP
);

-- ============================================
-- TABLA: notificaciones_alertas
-- Notificaciones de alertas para usuarios (admin/médico)
-- ============================================
CREATE TABLE public.notificaciones_alertas (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES public.usuarios(id) ON DELETE CASCADE,
    alerta_id INTEGER NOT NULL REFERENCES public.alertas(id) ON DELETE CASCADE,
    tipo VARCHAR(50) DEFAULT 'evento_critico',
    leida BOOLEAN DEFAULT false,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payload TEXT
);

-- ============================================
-- ÍNDICES para mejorar el rendimiento
-- ============================================
CREATE INDEX idx_usuarios_username ON public.usuarios(username);
CREATE INDEX idx_pacientes_curp ON public.pacientes(curp);
CREATE INDEX idx_pacientes_usuario_id ON public.pacientes(usuario_id);
CREATE INDEX idx_personal_medico_usuario_id ON public.personal_medico(usuario_id);
CREATE INDEX idx_dispositivos_paciente_id ON public.dispositivos(paciente_id);
CREATE INDEX idx_monitoreos_paciente_id ON public.monitoreos(paciente_id);
CREATE INDEX idx_monitoreos_activo ON public.monitoreos(activo);
CREATE INDEX idx_mediciones_dispositivo_id ON public.mediciones(dispositivo_id);
CREATE INDEX idx_mediciones_timestamp ON public.mediciones(timestamp);
CREATE INDEX idx_alertas_medicion_id ON public.alertas(medicion_id);
CREATE INDEX idx_alertas_leida ON public.alertas(leida);
CREATE INDEX idx_notificaciones_usuario_id ON public.notificaciones_alertas(usuario_id);
CREATE INDEX idx_notificaciones_leida ON public.notificaciones_alertas(leida);
CREATE INDEX idx_notificaciones_timestamp ON public.notificaciones_alertas(timestamp);

-- ============================================
-- COMENTARIOS en las tablas
-- ============================================
COMMENT ON TABLE public.usuarios IS 'Tabla de autenticación y control de acceso';
COMMENT ON TABLE public.pacientes IS 'Información personal de los pacientes';
COMMENT ON TABLE public.personal_medico IS 'Información del personal médico';
COMMENT ON TABLE public.pacientes_medicos IS 'Relación muchos a muchos entre pacientes y médicos';
COMMENT ON TABLE public.dispositivos IS 'Dispositivos de monitoreo wearables';
COMMENT ON TABLE public.monitoreos IS 'Períodos de vigilancia médica activa';
COMMENT ON TABLE public.mediciones IS 'Datos biométricos capturados';
COMMENT ON TABLE public.alertas IS 'Alertas médicas generadas automáticamente';
