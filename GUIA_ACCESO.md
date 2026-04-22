# 🔐 Guía de Acceso al Sistema I-HeartCare

## 📋 Credenciales de Acceso

### 🔧 Administrador
- **Usuario:** `admin`
- **Contraseña:** `admin123`
- **Permisos:** 
  - Acceso completo al sistema
  - Gestión de pacientes
  - Gestión de personal médico
  - Gestión de dispositivos
  - Gestión de monitoreo
  - Visualización de dashboards y análisis clínicos

### 👨‍⚕️ Médico/Doctor
- **Usuario:** `doctor`
- **Contraseña:** `doctor123`
- **Permisos:**
  - Ver lista de pacientes asignados
  - Acceso a dashboards de visualización
  - Panel de análisis clínico
  - Revisar mediciones de sus pacientes

### 👤 Paciente
- **Usuario:** `paciente`
- **Contraseña:** `paciente123`
- **Permisos:**
  - Ver su perfil personal
  - Ver sus mediciones
  - Ver sus alertas médicas
  - Información de su médico asignado

---

## 🚀 Cómo Inicializar los Usuarios

### Opción 1: Ejecutar el Script de Inicialización

1. Abre una nueva terminal
2. Navega al directorio del proyecto:
   ```bash
   cd "c:\Users\cesar\OneDrive\Escritorio\Tareas\SERVICIO SOCIAL\IHeartCare"
   ```
3. Ejecuta el script de inicialización:
   ```bash
   streamlit run init_users.py
   ```
4. Se abrirá una página web
5. Haz clic en el botón **"🚀 Crear Usuarios de Prueba"**
6. Espera a que se creen los usuarios
7. Cierra la ventana del navegador
8. Los usuarios ya están listos para usar

### Opción 2: Crear Usuarios Manualmente desde el Panel de Administrador

Si ya tienes acceso como administrador, puedes crear usuarios adicionales desde:
- **Gestión de Personal Médico** → Para crear médicos
- **Gestión de Pacientes** → Para crear pacientes
- Luego asignar credenciales de acceso

---

## 🌐 Cómo Acceder al Sistema

1. Asegúrate de que la aplicación esté corriendo:
   ```bash
   streamlit run app.py
   ```

2. Abre tu navegador en: `http://localhost:8501`

3. En la pantalla de inicio de sesión, ingresa:
   - **Usuario:** Uno de los usuarios mencionados arriba
   - **Contraseña:** La contraseña correspondiente

4. Haz clic en **"Ingresar"**

5. Serás redirigido al dashboard correspondiente a tu rol

---

## 🎯 Funcionalidades por Rol

### Panel de Administrador
- **Gestión de Pacientes:** Crear, editar, eliminar pacientes
- **Gestión de Personal Médico:** Administrar médicos y especialistas
- **Gestión de Dispositivos:** Asignar y configurar dispositivos de monitoreo
- **Gestión de Monitoreo:** Configurar monitoreos para pacientes
- **Dashboard de Visualización:** Ver estadísticas generales
- **Panel de Análisis Clínico:** Análisis detallado de datos médicos

### Panel del Médico
- **Mis Pacientes:** Lista de pacientes asignados
- **Dashboard de Visualización:** Gráficas y estadísticas de pacientes
- **Panel de Análisis Clínico:** Análisis detallado de mediciones
- **Alertas:** Notificaciones de anomalías en pacientes

### Panel del Paciente
- **Mi Perfil:** Información personal y médica
- **Mis Mediciones:** Historial de mediciones cardíacas
- **Mis Alertas:** Notificaciones sobre su salud
- **Información del Médico:** Datos de contacto del médico asignado

---

## ⚠️ Notas Importantes

1. **Seguridad:** Estas son credenciales de prueba. En producción, debes cambiar todas las contraseñas.

2. **Primera Vez:** Si es la primera vez que ejecutas el sistema, primero ejecuta `init_users.py` para crear los usuarios de prueba.

3. **Base de Datos:** Asegúrate de que la base de datos PostgreSQL esté configurada correctamente en `.streamlit/secrets.toml`

4. **Dependencias:** Verifica que todas las dependencias estén instaladas:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🔄 Restablecer Contraseñas

Si olvidas una contraseña, puedes:

1. **Como Administrador:** Contactar al administrador del sistema
2. **Ejecutar el script nuevamente:** El script `init_users.py` puede recrear los usuarios de prueba
3. **Acceder a la base de datos directamente:** Modificar el hash de contraseña en la tabla `usuarios`

---

## 📞 Soporte

Si tienes problemas para acceder:
- Verifica que la aplicación esté corriendo
- Revisa la conexión a la base de datos
- Consulta los logs de la aplicación
- Contacta al administrador del sistema
