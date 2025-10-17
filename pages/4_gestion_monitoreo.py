import streamlit as st
from sqlalchemy import text
import pandas as pd

# Configuración de la página
st.set_page_config(
    page_title="Gestión de Monitoreo",
    page_icon="🩺",
    layout="wide"
)

# Título principal
st.title("🩺 Gestión de Monitoreos Clínicos")
st.caption("Inicie, detenga y consulte los períodos de vigilancia de los pacientes.")

# Inicializar conexión a la BD
try:
    conn = st.connection("postgresql", type="sql")
except Exception as e:
    st.error(f"No se pudo conectar a la base de datos: {e}")
    st.stop()

# --- FUNCIONES DE BASE DE DATOS ---

def cargar_pacientes_sin_monitoreo_activo():
    """Carga solo los pacientes que no tienen un monitoreo activo."""
    with conn.session as s:
        query = text("""
            SELECT p.id, p.nombre, p.apellido_paterno, COALESCE(p.apellido_materno, '') as apellido_materno
            FROM Pacientes p
            LEFT JOIN Monitoreos m ON p.id = m.paciente_id AND m.activo = TRUE
            WHERE m.id IS NULL
            ORDER BY p.apellido_paterno, p.apellido_materno, p.nombre;
        """)
        df = pd.read_sql(query, s.connection())
        df["nombre_completo"] = (df["nombre"] + " " + df["apellido_paterno"] + " " + df["apellido_materno"]).str.strip()
        return df

def cargar_monitoreos_activos():
    """Carga los monitoreos que están actualmente activos."""
    with conn.session as s:
        query = text("""
            SELECT m.id, p.nombre || ' ' || p.apellido_paterno AS paciente_nombre
            FROM Monitoreos m
            JOIN Pacientes p ON m.paciente_id = p.id
            WHERE m.activo = TRUE
            ORDER BY paciente_nombre;
        """)
        df = pd.read_sql(query, s.connection())
        df["display_label"] = "ID Monitoreo: " + df["id"].astype(str) + " - Paciente: " + df["paciente_nombre"]
        return df

def cargar_historial_monitoreos():
    """Carga el historial completo de monitoreos."""
    with conn.session as s:
        query = text("""
            SELECT
                m.id AS "ID Monitoreo",
                p.nombre || ' ' || p.apellido_paterno AS "Paciente",
                m.fecha_inicio AS "Inicio",
                m.fecha_fin AS "Fin",
                CASE WHEN m.activo = TRUE THEN 'Sí' ELSE 'No' END AS "Activo",
                m.motivo AS "Motivo"
            FROM Monitoreos m
            JOIN Pacientes p ON m.paciente_id = p.id
            ORDER BY m.fecha_inicio DESC;
        """)
        return pd.read_sql(query, s.connection())

# --- INTERFAZ DE USUARIO ---

tab1, tab2, tab3 = st.tabs([
    "➕ Iniciar Nuevo Monitoreo",
    "➖ Detener Monitoreo Activo",
    "📋 Historial Completo"
])

# --- PESTAÑA 1: INICIAR MONITOREO ---
with tab1:
    st.subheader("Formulario de Inicio de Monitoreo")

    pacientes_disponibles_df = cargar_pacientes_sin_monitoreo_activo()
    pacientes_map = pd.Series(pacientes_disponibles_df.id.values, index=pacientes_disponibles_df.nombre_completo).to_dict()

    if not pacientes_map:
        st.info("Todos los pacientes ya tienen un monitoreo activo.")
    else:
        with st.form(key="iniciar_monitoreo_form", clear_on_submit=True):
            paciente_seleccionado = st.selectbox(
                "Seleccione el Paciente a Monitorear*",
                options=pacientes_map.keys(),
                index=None,
                placeholder="Busque o seleccione un paciente..."
            )
            motivo = st.text_area(
                "Motivo del Monitoreo (Opcional)",
                help="Describa la razón para iniciar este período de vigilancia (ej. Post-operatorio, ajuste de medicación, etc.)."
            )
            submit_button = st.form_submit_button("✅ Iniciar Monitoreo")

            if submit_button:
                if not paciente_seleccionado:
                    st.warning("Debe seleccionar un paciente.")
                else:
                    paciente_id = pacientes_map[paciente_seleccionado]
                    try:
                        with conn.session as s:
                            query = text("""
                                INSERT INTO Monitoreos (paciente_id, fecha_inicio, motivo, activo)
                                VALUES (:paciente_id, NOW(), :motivo, TRUE);
                            """)
                            s.execute(query, {"paciente_id": paciente_id, "motivo": motivo})
                            s.commit()
                        st.success(f"Monitoreo iniciado exitosamente para {paciente_seleccionado}.")
                    except Exception as e:
                        st.error(f"No se pudo iniciar el monitoreo. Error: {e}")

# --- PESTAÑA 2: DETENER MONITOREO ---
with tab2:
    st.subheader("Detener un Monitoreo Activo")

    monitoreos_activos_df = cargar_monitoreos_activos()
    monitoreos_map = pd.Series(monitoreos_activos_df.id.values, index=monitoreos_activos_df.display_label).to_dict()

    if not monitoreos_map:
        st.info("No hay monitoreos activos para detener en este momento.")
    else:
        monitoreo_a_detener = st.selectbox(
            "Seleccione el Monitoreo a Detener*",
            options=monitoreos_map.keys(),
            index=None,
            placeholder="Seleccione un monitoreo..."
        )
        if st.button("🛑 Detener Monitoreo Seleccionado", disabled=(not monitoreo_a_detener)):
            monitoreo_id = monitoreos_map[monitoreo_a_detener]
            try:
                with conn.session as s:
                    query = text("""
                        UPDATE Monitoreos
                        SET activo = FALSE, fecha_fin = NOW()
                        WHERE id = :monitoreo_id;
                    """)
                    s.execute(query, {"monitoreo_id": monitoreo_id})
                    s.commit()
                st.success(f"¡Monitoreo ID {monitoreo_id} detenido correctamente!")
                # Usamos st.rerun() para refrescar la lista de monitoreos activos inmediatamente
                st.rerun()
            except Exception as e:
                st.error(f"No se pudo detener el monitoreo. Error: {e}")

# --- PESTAÑA 3: HISTORIAL ---
with tab3:
    st.subheader("Historial de Todos los Monitoreos")
    try:
        historial_df = cargar_historial_monitoreos()
        if historial_df.empty:
            st.info("No hay registros de monitoreo en el sistema.")
        else:
            st.dataframe(historial_df, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"No se pudo cargar el historial. Error: {e}")