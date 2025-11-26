import streamlit as st
from sqlalchemy import text
import pandas as pd
from auth import require_auth  # ← AGREGAR ESTA LÍNEA

# --- PROTECCIÓN DE RUTA ---
require_auth(allowed_roles=['administrador'])  # ← AGREGAR ESTA LÍNEA
# Configuración de la página
st.set_page_config(
    page_title="Gestión de Dispositivos",
    page_icon="⌚",
    layout="wide"
)

# Título principal de la página
st.title("⌚ Gestión de Dispositivos de Monitoreo")

# Inicializar conexión con la base de datos
try:
    conn = st.connection("postgresql", type="sql")
except Exception as e:
    st.error(f"No se pudo conectar a la base de datos: {e}")
    st.stop() # Detiene la ejecución si no hay conexión

# --- FUNCIONES DE BASE DE DATOS ---

def cargar_pacientes():
    """Carga los pacientes para poblar el selector del formulario."""
    with conn.session as s:
        query = text("""
            SELECT id, nombre, apellido_paterno, COALESCE(apellido_materno, '') as apellido_materno
            FROM Pacientes
            ORDER BY apellido_paterno, apellido_materno, nombre;
        """)
        df_pacientes = pd.read_sql(query, s.connection())
        # Se crea un nombre completo para mostrarlo en el selector
        df_pacientes["nombre_completo"] = (
            df_pacientes["nombre"] + " " +
            df_pacientes["apellido_paterno"] + " " +
            df_pacientes["apellido_materno"]
        ).str.strip()
        return df_pacientes

def cargar_dispositivos():
    """Carga y muestra los dispositivos ya registrados en la base de datos."""
    with conn.session as s:
        # La consulta une Dispositivos y Pacientes para mostrar el nombre del paciente
        query = text("""
            SELECT
                d.id AS "ID Dispositivo",
                p.nombre || ' ' || p.apellido_paterno AS "Paciente Asignado",
                d.modelo AS "Modelo",
                d.mac_address AS "Dirección MAC",
                d.direccion_url AS "URL",
                d.fecha_asignacion AS "Fecha de Asignación"
            FROM Dispositivos d
            JOIN Pacientes p ON d.paciente_id = p.id
            ORDER BY d.fecha_asignacion DESC;
        """)
        df_dispositivos = pd.read_sql(query, s.connection())
        return df_dispositivos

# --- INTERFAZ DE USUARIO ---

# Carga de datos inicial para el formulario
try:
    pacientes_df = cargar_pacientes()
    # Se crea un diccionario para mapear el nombre completo al ID del paciente
    pacientes_map = pd.Series(pacientes_df.id.values, index=pacientes_df.nombre_completo).to_dict()
except Exception as e:
    st.error(f"Error al cargar la lista de pacientes: {e}")
    pacientes_map = {} # Previene un error si la carga falla

# Pestañas para organizar el contenido de la página
tab1, tab2 = st.tabs(["➕ Registrar Nuevo Dispositivo", "📋 Ver Dispositivos Asignados"])

# --- PESTAÑA 1: FORMULARIO DE REGISTRO ---
with tab1:
    st.subheader("Formulario de Asignación de Dispositivo")

    with st.form(key="registro_dispositivo_form", clear_on_submit=True):
        # Si no hay pacientes, el formulario se deshabilita
        if not pacientes_map:
            st.warning("No hay pacientes registrados. Por favor, registre un paciente antes de asignar un dispositivo.")
            submit_button = st.form_submit_button(label="Registrar Dispositivo", disabled=True)
        else:
            paciente_seleccionado = st.selectbox(
                "Seleccione el Paciente*",
                options=pacientes_map.keys(),
                index=None,
                placeholder="Busque o seleccione un paciente..."
            )

            # --- CORRECCIÓN APLICADA ---
            # Se añaden límites de caracteres (max_chars) a cada campo de texto
            # para que coincidan con la definición VARCHAR de la base de datos.
            modelo = st.text_input(
                "Modelo del Dispositivo*",
                max_chars=100, # Coincide con VARCHAR(100) en la tabla Dispositivos 
                help="Máximo 100 caracteres."
            )
            
            mac_address = st.text_input(
                "Dirección MAC (Opcional)",
                max_chars=17, # Coincide con VARCHAR(17) en la tabla Dispositivos 
                help="Formato: XX:XX:XX:XX:XX:XX. Máximo 17 caracteres."
            )
            
            direccion_url = st.text_input(
                "URL del Dispositivo (Opcional)",
                max_chars=2048, # Coincide con VARCHAR(2048) en la tabla Dispositivos 
                help="Dirección IP o URL para la API del dispositivo. Máximo 2048 caracteres."
            )

            submit_button = st.form_submit_button(label="✅ Asignar Dispositivo")

            if submit_button:
                if not paciente_seleccionado or not modelo:
                    st.warning("Los campos con * son obligatorios.")
                else:
                    paciente_id = pacientes_map[paciente_seleccionado]

                    try:
                        with conn.session as s:
                            query = text("""
                                INSERT INTO Dispositivos (paciente_id, modelo, mac_address, direccion_url, fecha_asignacion)
                                VALUES (:paciente_id, :modelo, :mac_address, :direccion_url, NOW());
                            """)
                            s.execute(query, {
                                "paciente_id": paciente_id,
                                "modelo": modelo,
                                "mac_address": mac_address if mac_address else None,
                                "direccion_url": direccion_url if direccion_url else None
                            })
                            s.commit()
                        st.success(f"¡Dispositivo '{modelo}' asignado exitosamente a {paciente_seleccionado}!")
                    except Exception as e:
                        st.error(f"No se pudo registrar el dispositivo. Error: {e}")

# --- PESTAÑA 2: VISUALIZACIÓN DE DATOS ---
with tab2:
    st.subheader("Listado de Dispositivos Asignados")

    try:
        dispositivos_df = cargar_dispositivos()
        if dispositivos_df.empty:
            st.info("Aún no se ha asignado ningún dispositivo en el sistema.")
        else:
            st.dataframe(dispositivos_df, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"No se pudieron cargar los dispositivos. Error: {e}")