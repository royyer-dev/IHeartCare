import streamlit as st
import pandas as pd
from sqlalchemy import text
import altair as alt

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Dashboard de Visualización",
    page_icon="📊",
    layout="wide"
)

# --- Título Principal ---
st.title("📊 Dashboard de Visualización en Tiempo Real")
st.caption("Supervise las mediciones biométricas de los pacientes con un monitoreo activo.")

# --- Conexión a la Base de Datos ---
try:
    conn = st.connection("postgresql", type="sql")
except Exception as e:
    st.error(f"Error de conexión con la base de datos: {e}")
    st.stop()

# --- Funciones de Carga de Datos (con caché para optimización) ---

@st.cache_data(ttl=60) # La lista de pacientes no cambia tan rápido
def cargar_pacientes_activos():
    """Carga la lista de pacientes que tienen un monitoreo activo."""
    with conn.session as s:
        query = text("""
            SELECT
                p.id AS paciente_id,
                m.id AS monitoreo_id,
                p.nombre || ' ' || p.apellido_paterno AS nombre_completo
            FROM Pacientes p
            JOIN Monitoreos m ON p.id = m.paciente_id
            WHERE m.activo = TRUE
            ORDER BY nombre_completo;
        """)
        return pd.read_sql(query, s.connection())

@st.cache_data(ttl=15) # Los datos de mediciones cambian más seguido
def cargar_datos_monitoreo(_monitoreo_id):
    """Carga todas las mediciones y alertas para un monitoreo específico."""
    with conn.session as s:
        # Consulta para obtener las mediciones
        q_mediciones = text("""
            SELECT "timestamp", tipo_medicion, valor, unidad_medida
            FROM Mediciones
            WHERE dispositivo_id IN (
                SELECT id FROM Dispositivos WHERE paciente_id = (
                    SELECT paciente_id FROM Monitoreos WHERE id = :monitoreo_id
                )
            )
            ORDER BY "timestamp" ASC;
        """)
        df_mediciones = pd.read_sql(q_mediciones, s.connection(), params={"monitoreo_id": _monitoreo_id})

        # Consulta para obtener las alertas no leídas
        q_alertas = text("""
            SELECT a."timestamp", a.tipo_alerta, a.mensaje, m.valor, m.tipo_medicion
            FROM Alertas a
            JOIN Mediciones m ON a.medicion_id = m.id
            WHERE m.id IN (
                SELECT id FROM Mediciones WHERE dispositivo_id IN (
                    SELECT id FROM Dispositivos WHERE paciente_id = (
                        SELECT paciente_id FROM Monitoreos WHERE id = :monitoreo_id
                    )
                )
            ) AND a.leida = FALSE
            ORDER BY a."timestamp" DESC;
        """)
        df_alertas = pd.read_sql(q_alertas, s.connection(), params={"monitoreo_id": _monitoreo_id})
        
    return df_mediciones, df_alertas

# --- Interfaz de Usuario ---

pacientes_activos_df = cargar_pacientes_activos()

if pacientes_activos_df.empty:
    st.info("ℹ️ No hay pacientes con un monitoreo activo en este momento.")
    st.stop()

# Mapeo de nombre de paciente a ID de monitoreo para el selector
pacientes_map = pd.Series(
    pacientes_activos_df.monitoreo_id.values,
    index=pacientes_activos_df.nombre_completo
).to_dict()

# Selector de paciente
paciente_seleccionado = st.selectbox(
    "Seleccione un paciente para visualizar sus datos:",
    options=pacientes_map.keys(),
    index=None,
    placeholder="Seleccione un paciente..."
)

# Botón para forzar la recarga de datos
if st.button("Refrescar Datos 🔄"):
    # Limpia la caché de la función de carga de datos para obtener lo más nuevo
    st.cache_data.clear()
    st.rerun()

# --- Lógica de Visualización ---

if paciente_seleccionado:
    monitoreo_id = pacientes_map[paciente_seleccionado]
    mediciones_df, alertas_df = cargar_datos_monitoreo(monitoreo_id)

    st.header(f"Mostrando datos para: {paciente_seleccionado}", divider="rainbow")

    # Sección de Alertas
    if not alertas_df.empty:
        st.subheader("🚨 Alertas Recientes (No Leídas)")
        for _, row in alertas_df.iterrows():
            st.error(
                f"**{row['tipo_alerta']}** ({row['timestamp'].strftime('%Y-%m-%d %H:%M')}) | "
                f"**Medición:** {row['valor']} ({row['tipo_medicion']}) | "
                f"**Mensaje:** {row['mensaje']}",
                icon="🚨"
            )
    else:
        st.subheader("✅ Sin Alertas Recientes")
        st.success("No hay alertas no leídas para este paciente.", icon="✅")

    st.divider()

    # Sección de Gráficos
    st.subheader("📈 Gráficos de Mediciones")
    if mediciones_df.empty:
        st.warning(f"Aún no se han registrado mediciones para **{paciente_seleccionado}**.")
    else:
        tipos_de_medicion = mediciones_df["tipo_medicion"].unique()

        for tipo in tipos_de_medicion:
            with st.container(border=True):
                st.markdown(f"#### Historial de: **{tipo}**")
                df_filtrado = mediciones_df[mediciones_df["tipo_medicion"] == tipo]

                chart = alt.Chart(df_filtrado).mark_line(
                    point=alt.OverlayMarkDef(color="red", size=25),
                    tooltip=True
                ).encode(
                    x=alt.X('timestamp:T', title='Fecha y Hora'),
                    y=alt.Y('valor:Q', title=f"Valor ({df_filtrado['unidad_medida'].iloc[0] or ''})"),
                    tooltip=['timestamp:T', 'valor:Q']
                ).interactive()

                st.altair_chart(chart, use_container_width=True)
else:
    st.info("↑ Seleccione un paciente de la lista para comenzar la visualización.")