# 🚀 GUÍA RÁPIDA DE INICIO - IHeartCare 2.0

## 1️⃣ Instalación (2 minutos)

```bash
# En la carpeta del proyecto
pip install -r requirements.txt
```

## 2️⃣ Base de Datos (1 minuto)

Ejecutar una de estas opciones:

**Opción A - Script automático:**

```bash
python execute_schema.py
```

**Opción B - SQL directo (PostgreSQL):**

```sql
ALTER TABLE public.dispositivos ADD COLUMN IF NOT EXISTS latitude DECIMAL(10, 8);
ALTER TABLE public.dispositivos ADD COLUMN IF NOT EXISTS longitude DECIMAL(11, 8);
ALTER TABLE public.pacientes ADD COLUMN IF NOT EXISTS activo BOOLEAN DEFAULT true;
ALTER TABLE public.personal_medico ADD COLUMN IF NOT EXISTS activo BOOLEAN DEFAULT true;
```

## 3️⃣ Ejecutar la Aplicación (instant)

```bash
streamlit run app.py
```

## 4️⃣ Credenciales de Prueba

- **Admin:** `admin` / `admin123`
- **Doctor:** `doctor` / `doctor123`
- **Paciente:** `paciente` / `paciente123`

---

## ✨ Características Nuevas

| Característica       | Ubicación        | Descripción                                                      |
| -------------------- | ---------------- | ---------------------------------------------------------------- |
| **Mapa Principal**   | Dashboard        | Muestra todos los dispositivos activos                           |
| **Minimapa en Vivo** | 05_monitoreo     | Ubicación GPS actual del dispositivo                             |
| **CRUDs Completos**  | 01, 02, 03 admin | CREATE, READ, UPDATE, DELETE para pacientes/médicos/dispositivos |
| **Tema Oscuro**      | 05, 06 páginas   | Paleta profesional con #0F172A, #1E293B, #0891B2                 |
| **Auto-refresh**     | 05_monitoreo     | Selector de 5/10/15/30 segundos                                  |
| **Geolocalización**  | DB + utils       | Coordenadas GPS simuladas con movimiento realista                |

---

## 🎯 Flujos Principales

### Administrador

1. Login → Dashboard (ve mapa principal)
2. Gestión Pacientes → Buscar paciente → Botón "Ver en Vivo"
3. Dashboard filtrado muestra datos + minimapa del paciente

### Doctor

1. Login → Dashboard (ve mapa de pacientes asignados)
2. Visualización en vivo de pacientes asignados

### Paciente

1. Login → Panel personal
2. Ver mediciones propias

---

## 📁 Archivos Clave Modificados

```
✅ app.py                              - Mapa principal agregado
✅ pages/01_admin_pacientes.py         - CRUDs + "Ver en Vivo"
✅ pages/02_admin_medicos.py           - CRUDs completos
✅ pages/03_admin_dispositivos.py      - CRUDs + geo fields
✅ pages/05_monitoreo_dashboard.py     - Rediseño completo + minimapa
✅ pages/06_monitoreo_analisis.py      - Tema oscuro
✅ utils/geo_simulator.py              - NUEVO: Simulador GPS
✅ utils/mapas.py                      - NUEVO: Componentes folium
✅ requirements.txt                    - folium, streamlit-folium, geopy
```

---

## 🐛 Verificación de Funcionalidad

Después de ejecutar `streamlit run app.py`, verificar:

- [ ] Login funciona
- [ ] Dashboard muestra mapa con dispositivos
- [ ] Admin puede editar/eliminar pacientes
- [ ] "Ver en Vivo" navega correctamente
- [ ] Visualización muestra minimapa
- [ ] Auto-refresh funciona

---

## 💡 Tips Útiles

**Para agregar más dispositivos con coordenadas:**

```python
# En admin > Dispositivos > Registrar
Latitud: 25.6866 (ejemplo: CDMX)
Longitud: -100.3161
```

**Para cambiar velocidad de simulación GPS:**
Editar en `utils/geo_simulator.py` línea con `±0.0005`

**Para cambiar tema de colores:**
Editar CSS en `pages/05_monitoreo_dashboard.py` y `pages/06_monitoreo_analisis.py`

---

## ⚙️ Dependencias Requeridas

```
streamlit          - Framework web
folium>=0.14.0     - Mapas interactivos
streamlit-folium   - Integración de folium en streamlit
geopy>=2.3.0       - Cálculos de distancia GPS
sqlalchemy         - ORM para BD
psycopg2-binary    - Driver PostgreSQL
pandas             - Manipulación de datos
plotly             - Gráficos interactivos
bcrypt             - Hash de contraseñas
```

Todas ya están en `requirements.txt`

---

## 🆘 Solución de Problemas

**Error: "ModuleNotFoundError: No module named 'folium'"**
→ Ejecutar: `pip install -r requirements.txt`

**Error: "Connection refused localhost:5433"**
→ Verificar que PostgreSQL esté corriendo en puerto 5433
→ Credenciales en `auth.py` línea con connection string

**Error: "No columns named latitude"**
→ Ejecutar migraciones de BD (ver sección 2️⃣)

**Mapa no aparece**
→ Verificar que haya dispositivos activos en BD con coordenadas
→ Verificar que monitoreos estén activos

---

**Documentación completa:** Ver `INSTRUCCIONES_INSTALACION.md`

**¿Problemas?** Revisar `INSTRUCCIONES_INSTALACION.md` → Próximos Pasos Opcionales
