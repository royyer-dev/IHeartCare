# Instrucciones para Configurar la Base de Datos

## 1. Crear la Base de Datos (si no existe)

```bash
# Conectarse a PostgreSQL
psql -U postgres

# Crear la base de datos
CREATE DATABASE iheartcare;

# Salir
\q
```

## 2. Ejecutar el Schema

```bash
# Ejecutar el archivo schema.sql
psql -U postgres -d iheartcare -f schema.sql
```

O desde dentro de psql:

```sql
\c iheartcare
\i schema.sql
```

## 3. Verificar las Tablas

```sql
\dt public.*
```

Deberías ver las siguientes tablas:
- usuarios
- pacientes
- personal_medico
- pacientes_medicos
- dispositivos
- monitoreos
- mediciones
- alertas

## 4. Configurar Streamlit Secrets

Edita el archivo `.streamlit/secrets.toml` con tus credenciales:

```toml
[connections.postgresql]
dialect = "postgresql"
host = "localhost"
port = "5432"
database = "iheartcare"
username = "postgres"
password = "tu_contraseña"
```

## 5. Inicializar Usuarios de Prueba

```bash
streamlit run init_users.py
```

Luego haz clic en el botón "Crear Usuarios de Prueba".

## 6. Iniciar la Aplicación

```bash
streamlit run app.py
```

## Credenciales de Prueba

Después de ejecutar `init_users.py`:

- **Admin**: `admin` / `admin123`
- **Doctor**: `doctor` / `doctor123`
- **Paciente**: `paciente` / `paciente123`
