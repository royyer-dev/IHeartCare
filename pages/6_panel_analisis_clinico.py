import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from sqlalchemy import text
from datetime import datetime, timedelta, time
from auth import require_auth  # ← AGREGAR

# --- PROTECCIÓN DE RUTA ---
require_auth(allowed_roles=['administrador', 'medico'])  # ← AGREGAR
# --- Configuración de la Página ---
st.set_page_config(
    page_title="Panel de Análisis Clínico",
    page_icon="🔬",
    layout="wide"
)

# --- Título Principal ---
st.title("🔬 Panel de Análisis Clínico Avanzado")
st.caption("Herramientas visuales contextuales para la toma de decisiones clínicas.")

# --- Definición de Rangos Clínicos ---
# Estos rangos definen los colores de las tarjetas de KPI
RANGOS_CLINICOS = {
    'Ritmo Cardíaco': {'normal': (60, 100), 'alerta': (40, 130)},
    'Saturación Oxígeno': {'normal': (95, 100), 'alerta': (92, 95)},
    'Presión Sistólica': {'normal': (90, 130), 'alerta': (80, 140)},
    'Presión Diastólica': {'normal': (60, 85), 'alerta': (50, 90)},
}

# --- Inicialización del Session State ---
if 'mediciones_df' not in st.session_state:
    st.session_state.mediciones_df = pd.DataFrame()

# --- Conexión a la Base de Datos ---
try:
    conn = st.connection("postgresql", type="sql")
except Exception as e:
    st.error(f"Error de conexión con la base de datos: {e}")
    st.stop()

# --- Funciones de Carga de Datos (Sin Cambios) ---
@st.cache_data(ttl=300)
def cargar_pacientes_activos():
    with conn.session as s:
        query = text("""
            SELECT p.id, p.nombre || ' ' || p.apellido_paterno AS nombre_completo
            FROM Pacientes p JOIN Monitoreos m ON p.id = m.paciente_id
            WHERE m.activo = TRUE ORDER BY nombre_completo;
        """)
        return pd.read_sql(query, s.connection())

@st.cache_data(ttl=30)
def cargar_datos_paciente(paciente_id):
    with conn.session as s:
        query = text("""
            SELECT "timestamp", tipo_medicion, valor, unidad_medida
            FROM Mediciones WHERE dispositivo_id IN (
                SELECT id FROM Dispositivos WHERE paciente_id = :paciente_id
            ) ORDER BY "timestamp" ASC;
        """)
        df = pd.read_sql(query, s.connection(), params={"paciente_id": paciente_id})
        if not df.empty:
            df = df.pivot_table(index='timestamp', columns='tipo_medicion', values='valor').reset_index()
    return df

# --- FUNCIÓN DE DATOS DE MUESTRA MEJORADA ---
def generar_datos_muestra(dias=1):
    """Genera un DataFrame de mediciones clínicamente coherentes."""
    n_samples = dias * 96  # Muestras cada 15 minutos
    start_time = datetime.now() - timedelta(days=dias)
    timestamps = [start_time + timedelta(minutes=15 * i) for i in range(n_samples)]
    
    # 1. Actividad (0 = Reposo, 1 = Activo)
    actividad = np.zeros(n_samples)
    for _ in range(dias * 2): # Dos períodos de actividad por día
        start_idx = np.random.randint(0, n_samples - 10)
        end_idx = start_idx + np.random.randint(4, 12) # Actividad de 1 a 3 horas
        actividad[start_idx : min(end_idx, n_samples)] = 1
    
    # 2. Ritmo Cardíaco (Depende de la actividad)
    ritmo_base_reposo = np.random.normal(75, 5, n_samples)
    ritmo_base_activo = np.random.normal(130, 10, n_samples)
    # Jitter (variabilidad natural)
    jitter = np.random.normal(0, 2, n_samples)
    ritmo = (1 - actividad) * (ritmo_base_reposo + jitter) + actividad * (ritmo_base_activo + jitter)
    
    # 3. Presión Arterial (Sistólica y Diastólica)
    sistolica = (1 - actividad) * np.random.normal(120, 5, n_samples) + actividad * np.random.normal(130, 7, n_samples)
    diastolica = (1 - actividad) * np.random.normal(80, 4, n_samples) + actividad * np.random.normal(85, 5, n_samples)
    
    # 4. Saturación de Oxígeno (Muy estable, con posible evento)
    saturacion = np.random.normal(98, 0.5, n_samples).clip(95, 100)
    # Simular una desaturación anómala (1% de probabilidad)
    if np.random.rand() < 0.1:
        start_idx = np.random.randint(0, n_samples - 5)
        saturacion[start_idx : start_idx + 4] = np.random.normal(90, 1, 4) # Cae a 90% por 1 hora
        
    df = pd.DataFrame({
        'timestamp': pd.to_datetime(timestamps),
        'Ritmo Cardíaco': ritmo.round(0),
        'Saturación Oxígeno': saturacion.round(1),
        'Presión Sistólica': sistolica.round(0),
        'Presión Diastólica': diastolica.round(0),
        'Actividad (0=Reposo, 1=Activo)': actividad.round(0)
    })
    return df

# --- BARRA LATERAL (CONTROLES) ---
st.sidebar.header("Fuente de Datos")
data_source = st.sidebar.radio("Seleccione el origen de los datos:",
                               ("Cargar desde la Base de Datos", "Usar Datos de Prueba (CSV/Muestra)"),
                               key="data_source_radio")

if data_source == "Cargar desde la Base de Datos":
    pacientes_activos_df = cargar_pacientes_activos()
    if pacientes_activos_df.empty:
        st.sidebar.warning("No hay pacientes con monitoreo activo.")
    else:
        pacientes_map = pd.Series(pacientes_activos_df.id.values, index=pacientes_activos_df.nombre_completo).to_dict()
        paciente_seleccionado = st.sidebar.selectbox("Seleccione un paciente:", options=pacientes_map.keys())
        if paciente_seleccionado:
            st.session_state.mediciones_df = cargar_datos_paciente(pacientes_map[paciente_seleccionado])
else:
    st.sidebar.info("Utilice esta opción para probar las visualizaciones.")
    uploaded_file = st.sidebar.file_uploader("Suba su archivo CSV de mediciones", type="csv")
    if uploaded_file:
        st.session_state.mediciones_df = pd.read_csv(uploaded_file)
        if 'timestamp' in st.session_state.mediciones_df.columns:
            st.session_state.mediciones_df['timestamp'] = pd.to_datetime(st.session_state.mediciones_df['timestamp'])

    st.sidebar.subheader("Generar Datos de Muestra")
    gen_cols = st.sidebar.columns(2)
    if gen_cols[0].button("1 Día"):
        st.session_state.mediciones_df = generar_datos_muestra(dias=1)
    if gen_cols[1].button("1 Semana"):
        st.session_state.mediciones_df = generar_datos_muestra(dias=7)
    if gen_cols[0].button("1 Mes"):
        st.session_state.mediciones_df = generar_datos_muestra(dias=30)
    if gen_cols[1].button("3 Meses"):
        st.session_state.mediciones_df = generar_datos_muestra(dias=90)

# --- PANEL PRINCIPAL (VISUALIZACIONES) ---

if 'mediciones_df' not in st.session_state or st.session_state.mediciones_df.empty:
    st.info("Seleccione un paciente o cargue datos de muestra para ver el panel de análisis.")
else:
    master_df = st.session_state.mediciones_df.copy()
    master_df['timestamp'] = pd.to_datetime(master_df['timestamp'])
    
    st.success(f"Datos cargados: {master_df.shape[0]} registros, desde {master_df['timestamp'].min().strftime('%Y-%m-%d')} hasta {master_df['timestamp'].max().strftime('%Y-%m-%d')}.")

    # --- FILTRO DE RANGO DE TIEMPO ---
    st.header("Controles de Visualización", divider="rainbow")
    filtro_tiempo = st.radio(
        "Filtrar vista por período:",
        ["Último Día", "Última Semana", "Último Mes", "Todo el Período"],
        index=3, horizontal=True, key="filtro_tiempo_radio"
    )
    
    end_date = master_df['timestamp'].max()
    if filtro_tiempo == "Último Día":
        start_date = end_date - timedelta(days=1)
    elif filtro_tiempo == "Última Semana":
        start_date = end_date - timedelta(days=7)
    elif filtro_tiempo == "Último Mes":
        start_date = end_date - timedelta(days=30)
    else:
        start_date = master_df['timestamp'].min()
    
    df_filtrado = master_df[master_df['timestamp'] >= start_date].copy()

    if df_filtrado.empty:
        st.warning(f"No hay datos disponibles para el período seleccionado: '{filtro_tiempo}'.")
    else:
        st.caption(f"Mostrando {df_filtrado.shape[0]} registros del {start_date.strftime('%Y-%m-%d %H:%M')} al {end_date.strftime('%Y-%m-%d %H:%M')}.")
        
        # --- 1. NUEVOS KPIs CON CÓDIGO DE COLOR ---
        st.header("Indicadores Clave (Última Medición)", divider="rainbow")
        
        def get_kpi_card(metric_name, unit, value, rangos):
            if value < rangos['alerta'][0] or value > rangos['alerta'][1]:
                color = "#FF4B4B" # Rojo
                status = "Crítico"
            elif value < rangos['normal'][0] or value > rangos['normal'][1]:
                color = "#FFD04B" # Ámbar
                status = "Alerta"
            else:
                color = "#28A745" # Verde
                status = "Normal"
            
            return f"""
            <div style="background-color: {color}; padding: 15px; border-radius: 10px; color: white; text-align: center;">
                <h4 style="color: white; margin: 0;">{metric_name}</h4>
                <h1 style="color: white; margin: 0; font-size: 2.5em;">{value:.0f} <span style="font-size: 0.6em;">{unit}</span></h1>
                <p style="color: white; margin: 0;">{status}</p>
            </div>
            """

        kpi_cols = st.columns(4)
        last_row = df_filtrado.iloc[-1]
        
        if 'Ritmo Cardíaco' in last_row:
            kpi_cols[0].markdown(get_kpi_card("Ritmo Cardíaco", "lpm", last_row['Ritmo Cardíaco'], RANGOS_CLINICOS['Ritmo Cardíaco']), unsafe_allow_html=True)
        if 'Saturación Oxígeno' in last_row:
            kpi_cols[1].markdown(get_kpi_card("Saturación O₂", "%", last_row['Saturación Oxígeno'], RANGOS_CLINICOS['Saturación Oxígeno']), unsafe_allow_html=True)
        if 'Presión Sistólica' in last_row:
            kpi_cols[2].markdown(get_kpi_card("P. Sistólica", "mmHg", last_row['Presión Sistólica'], RANGOS_CLINICOS['Presión Sistólica']), unsafe_allow_html=True)
        if 'Presión Diastólica' in last_row:
            kpi_cols[3].markdown(get_kpi_card("P. Diastólica", "mmHg", last_row['Presión Diastólica'], RANGOS_CLINICOS['Presión Diastólica']), unsafe_allow_html=True)

        # --- 2. GRÁFICO DE CORRELACIÓN CONTEXTUAL (HR vs Actividad) ---
        st.header("Correlación: Ritmo Cardíaco vs Actividad", divider="rainbow")
        st.info("Visualice cómo la actividad física (fondo sombreado) impacta el ritmo cardíaco (línea).")
        
        # Gráfico de área para la actividad (fondo)
        actividad_chart = alt.Chart(df_filtrado).mark_area(
            opacity=0.3,
            color="#5276A7"
        ).encode(
            x=alt.X('timestamp:T', title='Fecha y Hora'),
            y=alt.Y('Actividad (0=Reposo, 1=Activo):Q', title='Actividad', axis=None),
            tooltip=['timestamp', 'Actividad (0=Reposo, 1=Activo)']
        )
        
        # Gráfico de línea para el ritmo cardíaco
        ritmo_chart = alt.Chart(df_filtrado).mark_line(
            color="#F18727",
            strokeWidth=2
        ).encode(
            x='timestamp:T',
            y=alt.Y('Ritmo Cardíaco:Q', title='Ritmo Cardíaco (lpm)', scale=alt.Scale(zero=False)),
            tooltip=['timestamp', 'Ritmo Cardíaco']
        )
        
        # Superponer los gráficos
        contextual_chart = (actividad_chart + ritmo_chart).interactive()
        st.altair_chart(contextual_chart, use_container_width=True, theme="streamlit")

        # --- 3. GRÁFICO DEDICADO DE PRESIÓN ARTERIAL ---
        st.header("Análisis de Presión Arterial", divider="rainbow")
        
        # Dataframe para las bandas de rangos
        rangos_pa = pd.DataFrame([
            {"rango": "Hipertensión", "inicio": 130, "fin": 180},
            {"rango": "Normal", "inicio": 90, "fin": 130},
            {"rango": "Hipotensión", "inicio": 60, "fin": 90}
        ])
        
        # Bandas de fondo
        bandas_chart = alt.Chart(rangos_pa).mark_rect(opacity=0.2).encode(
            y=alt.Y('inicio:Q', title="Presión (mmHg)"),
            y2='fin:Q',
            color=alt.Color('rango:N', 
                scale=alt.Scale(domain=["Hipertensión", "Normal", "Hipotensión"], range=["#FF4B4B", "#28A745", "#5276A7"]),
                legend=alt.Legend(title="Rangos Sistólica"))
        )
        
        # Líneas de Sistólica y Diastólica
        base_pa = alt.Chart(df_filtrado).encode(x=alt.X('timestamp:T', title='Fecha y Hora'))
        sistolica_line = base_pa.mark_line(color='red').encode(
            y=alt.Y('Presión Sistólica:Q', scale=alt.Scale(domain=[50, 180])),
            tooltip=['timestamp', 'Presión Sistólica']
        )
        diastolica_line = base_pa.mark_line(color='blue').encode(
            y='Presión Diastólica:Q',
            tooltip=['timestamp', 'Presión Diastólica']
        )
        
        pa_chart = (bandas_chart + sistolica_line + diastolica_line).interactive()
        st.altair_chart(pa_chart, use_container_width=True, theme="streamlit")

        # --- 4. ANÁLISIS DE DISTRIBUCIÓN (BOX PLOT) ---
        st.header("Análisis de Distribución por Hora", divider="rainbow")
        df_filtrado['hora_del_dia'] = df_filtrado['timestamp'].dt.hour
        
        metric_options_dist = ['Ritmo Cardíaco', 'Saturación Oxígeno', 'Presión Sistólica', 'Presión Diastólica']
        hist_metric = st.selectbox("Seleccione una métrica para ver su distribución horaria:", metric_options_dist)
        
        st.info(f"Mostrando la distribución de '{hist_metric}' por hora. Use esto para detectar patrones diarios (ej. picos matutinos).")

        boxplot_chart = alt.Chart(df_filtrado).mark_boxplot(
            extent='min-max'
        ).encode(
            x=alt.X('hora_del_dia:O', title='Hora del Día (0-23)'),
            y=alt.Y(f'{hist_metric}:Q', title=hist_metric),
            tooltip=[
                alt.Tooltip('hora_del_dia:O', title='Hora'),
                alt.Tooltip(f'q1({hist_metric}):Q', title='Cuartil 1'),
                alt.Tooltip(f'median({hist_metric}):Q', title='Mediana'),
                alt.Tooltip(f'q3({hist_metric}):Q', title='Cuartil 3'),
            ]
        ).interactive()
        
        st.altair_chart(boxplot_chart, use_container_width=True, theme="streamlit")