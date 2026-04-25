# ❤️ IHeartCare — Sistema de Monitoreo Cardíaco

Sistema web de monitoreo cardíaco en tiempo real construido con **Streamlit**, **PostgreSQL** y **Python**. Permite la gestión de pacientes, personal médico, dispositivos wearables y alertas médicas con dashboards interactivos.

---

## ✨ Características Principales

| Módulo | Descripción |
|--------|-------------|
| **Autenticación** | Login con bcrypt, 3 roles (administrador, médico, paciente) |
| **CRUD Completo** | Gestión de pacientes, médicos y dispositivos (crear, leer, editar, eliminar) |
| **Monitoreo en Vivo** | Dashboard con auto-refresh configurable (5/10/15/30s) |
| **Análisis Clínico** | Gráficas Plotly, mapas de calor, estadísticas avanzadas |
| **Notificaciones** | Alertas automáticas por mediciones anormales |
| **Simulador** | Generador de eventos médicos en tiempo real |

---

## 🚀 Inicio Rápido

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar Base de Datos

**Prerequisito:** PostgreSQL instalado y ejecutándose.

Crea el archivo `.streamlit/secrets.toml` con tus credenciales:

```toml
[connections.postgresql]
dialect = "postgresql"
host = "localhost"
port = "5432"
database = "iheartcare"
username = "postgres"
password = "tu_contraseña_aqui"
```

Ejecuta el schema:

```bash
python scripts/execute_schema.py
```

### 3. Crear Usuarios de Prueba

```bash
streamlit run scripts/init_users.py
```

Haz clic en el botón **"Crear Usuarios de Prueba"** y opcionalmente genera datos demo.

### 4. Iniciar la Aplicación

```bash
streamlit run app.py
```

Abre tu navegador en `http://localhost:8501`.

---

## 🔐 Credenciales de Prueba

| Rol | Usuario | Contraseña |
|-----|---------|------------|
| Administrador | `admin` | `admin123` |
| Médico | `doctor` | `doctor123` |
| Paciente | `paciente` | `paciente123` |

> ⚠️ **Importante:** Cambia estas contraseñas en producción.

---

## 📁 Estructura del Proyecto

```
IHeartCare/
├── app.py                     # Entry point principal
├── requirements.txt           # Dependencias Python
├── README.md                  # Documentación (este archivo)
│
├── core/                      # Módulos centrales
│   ├── auth.py                # Autenticación y roles
│   ├── sidebar.py             # Navegación lateral
│   └── theme.py               # Tema visual global
│
├── pages/                     # Páginas de Streamlit
│   ├── 01_admin_pacientes.py  # CRUD pacientes
│   ├── 02_admin_medicos.py    # CRUD personal médico
│   ├── 03_admin_dispositivos.py # CRUD dispositivos
│   ├── 04_monitoreo_crear.py  # Gestión de monitoreos
│   ├── 05_monitoreo_dashboard.py # Dashboard en vivo
│   ├── 06_monitoreo_analisis.py  # Análisis clínico avanzado
│   ├── 07_perfil_usuario.py   # Perfil del paciente
│   ├── 08_mediciones_personales.py # Mediciones del paciente
│   ├── 09_mis_pacientes.py    # Pacientes del médico
│   └── 10_notificaciones.py   # Centro de alertas
│
├── utils/                     # Utilidades y componentes
│   ├── ui_components.py       # Componentes UI reutilizables
│   ├── alerta_generator.py    # Generador de alertas
│   ├── simulador.py           # Simulador de eventos
│   └── notificaciones.py      # Sistema de notificaciones
│
├── db/                        # Base de datos
│   ├── schema.sql             # Schema completo
│   └── migrations/            # Migraciones futuras
│
├── scripts/                   # Scripts de setup y desarrollo
│   ├── init_users.py          # Inicializar usuarios de prueba
│   ├── generate_demo_data.py  # Generar datos demo
│   ├── execute_schema.py      # Ejecutar schema en BD
│   ├── check_users.py         # Verificar usuarios
│   └── generate_hashes.py     # Generar hashes de contraseñas
│
└── .streamlit/
    ├── config.toml            # Configuración de Streamlit
    └── secrets.toml           # Credenciales de BD (ignorado por git)
```

---

## 🎯 Flujos de Usuario

### Administrador
1. Login → Dashboard con métricas del sistema
2. Gestión completa de pacientes, médicos y dispositivos
3. Crear y gestionar monitoreos
4. Visualización de dashboards y análisis clínico

### Médico
1. Login → Dashboard con pacientes asignados
2. Visualización en vivo de pacientes
3. Panel de análisis clínico con gráficas
4. Centro de alertas y notificaciones

### Paciente
1. Login → Panel personal de salud
2. Ver perfil médico y dispositivo asignado
3. Historial de mediciones con gráficas
4. Alertas personales

---

## ⚙️ Requisitos del Sistema

- **Python** 3.8+
- **PostgreSQL** 10+
- Dependencias: `streamlit`, `sqlalchemy`, `psycopg2-binary`, `bcrypt`, `pandas`, `plotly`

---

## 🆘 Solución de Problemas

| Error | Solución |
|-------|----------|
| `ModuleNotFoundError` | Ejecutar `pip install -r requirements.txt` |
| `Connection refused` | Verificar que PostgreSQL esté corriendo y las credenciales en `secrets.toml` |
| Login no funciona | Ejecutar `streamlit run scripts/init_users.py` para crear usuarios |
