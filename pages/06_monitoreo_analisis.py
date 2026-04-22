import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from sqlalchemy import text
from auth import require_auth
from sidebar import render_sidebar
from theme import apply_global_theme
from utils import breadcrumb_nav

# --- PROTECCIÓN DE RUTA ---
require_auth(allowed_roles=['administrador', 'medico'])
render_sidebar()
apply_global_theme()

st.set_page_config(page_title="Análisis Clínico", page_icon="📊", layout="wide")

# --- BREADCRUMBS ---
breadcrumb_nav(["Home", "Análisis", "Análisis Clínico"])

# --- CONEXIÓN A LA BASE DE DATOS ---
try:
    conn = st.connection("postgresql", type="sql")
except Exception:
    st.error("No se pudo establecer conexión con la base de datos.")
    st.stop()

st.title("📊 Panel de Análisis Clínico Avanzado")
st.markdown("---")

# --- ESTILOS CSS - TEMA OSCURO ---
st.markdown("""
<style>
    /* Tema oscuro para análisis */
    .metric-box-dark {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid #0891B2;
        padding: 16px;
        border-radius: 8px;
        margin: 8px 0;
        color: #E2E8F0;
    }
    
    .alert-box-dark {
        background: linear-gradient(135deg, #7F1D1D 0%, #451A1A 100%);
        border-left: 4px solid #EF4444;
        padding: 12px;
        border-radius: 6px;
        margin: 8px 0;
        color: #E2E8F0;
    }
    
    .analysis-card {
        background: #0F172A;
        border: 1px solid #0891B2;
        border-radius: 8px;
        padding: 16px;
        margin: 12px 0;
        color: #E2E8F0;
    }
    
    .analysis-header {
        color: #06B6D4;
        font-weight: 600;
        border-bottom: 1px solid #0891B2;
        padding-bottom: 8px;
        margin-bottom: 12px;
    }
    
    .trend-positive {
        color: #10B981;
        font-weight: 600;
    }
    
    .trend-negative {
        color: #EF4444;
        font-weight: 600;
    }
    
    .trend-neutral {
        color: #F59E0B;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --- OBTENER PACIENTES (ACTIVOS E HISTÓRICOS) ---
try:
    pacientes_df = conn.query("""
        SELECT DISTINCT
            p.id,
            p.nombre,
            p.apellido_paterno,
            p.apellido_materno,
            p.diagnostico,
            m.activo,
            MAX(med.timestamp) as ultima_medicion
        FROM public.pacientes p
        LEFT JOIN public.monitoreos m ON p.id = m.paciente_id
        LEFT JOIN public.dispositivos d ON p.id = d.paciente_id
        LEFT JOIN public.mediciones med ON d.id = med.dispositivo_id
        WHERE med.timestamp IS NOT NULL
        GROUP BY p.id, m.activo
        ORDER BY p.nombre
    """, ttl="10s")
except Exception as e:
    st.error(f"Error al cargar pacientes: {e}")
    pacientes_df = pd.DataFrame()

if pacientes_df.empty:
    st.warning("⚠️ No hay datos de mediciones disponibles en el sistema.")
else:
    # --- SELECTORES EN COLS ---
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.markdown("**Selecciona un Paciente**")
        pacientes_opciones = {
            f"{p['nombre']} {p['apellido_paterno']} {p.get('apellido_materno', '')}".strip(): p['id']
            for _, p in pacientes_df.iterrows()
        }
        paciente_nombre = st.selectbox(
            "Paciente",
            options=list(pacientes_opciones.keys()),
            label_visibility="collapsed"
        )
        paciente_id = pacientes_opciones[paciente_nombre]
    
    with col2:
        st.markdown("**Rango de Fechas**")
        rango_tipo = st.radio(
            "Tipo de Análisis",
            options=["Últimos 7 días", "Últimos 30 días", "Histórico completo", "Rango personalizado"],
            horizontal=True,
            label_visibility="collapsed"
        )
    
    with col3:
        st.write("")
        if st.button("🔄 Refrescar", use_container_width=True):
            st.rerun()
    
    # --- CALCULAR RANGO DE FECHAS ---
    ahora = datetime.now()
    
    if rango_tipo == "Últimos 7 días":
        fecha_inicio = ahora - timedelta(days=7)
        fecha_fin = ahora
    elif rango_tipo == "Últimos 30 días":
        fecha_inicio = ahora - timedelta(days=30)
        fecha_fin = ahora
    elif rango_tipo == "Histórico completo":
        fecha_inicio = None  # Sin límite
        fecha_fin = ahora
    else:  # Personalizado
        col1, col2 = st.columns(2)
        with col1:
            fecha_inicio = st.date_input("Fecha Inicio", value=ahora - timedelta(days=7))
        with col2:
            fecha_fin = st.date_input("Fecha Fin", value=ahora)
        fecha_inicio = datetime.combine(fecha_inicio, datetime.min.time())
        fecha_fin = datetime.combine(fecha_fin, datetime.max.time())
    
    # --- CARGAR MEDICIONES DEL PACIENTE ---
    try:
        if fecha_inicio:
            mediciones_df = conn.query(f"""
                SELECT 
                    m.timestamp,
                    m.tipo_medicion,
                    m.valor,
                    m.unidad_medida
                FROM public.mediciones m
                JOIN public.dispositivos d ON m.dispositivo_id = d.id
                WHERE d.paciente_id = {paciente_id}
                    AND m.timestamp >= '{fecha_inicio}'
                    AND m.timestamp <= '{fecha_fin}'
                ORDER BY m.timestamp
            """, ttl="5s")
        else:
            mediciones_df = conn.query(f"""
                SELECT 
                    m.timestamp,
                    m.tipo_medicion,
                    m.valor,
                    m.unidad_medida
                FROM public.mediciones m
                JOIN public.dispositivos d ON m.dispositivo_id = d.id
                WHERE d.paciente_id = {paciente_id}
                ORDER BY m.timestamp
            """, ttl="5s")
    except Exception as e:
        st.error(f"Error al cargar mediciones: {e}")
        mediciones_df = pd.DataFrame()
    
    if mediciones_df.empty:
        st.info("No hay mediciones registradas para este paciente en el rango seleccionado.")
    else:
        st.markdown("---")
        
        # Obtener paciente seleccionado
        paciente_sel = pacientes_df[pacientes_df['id'] == paciente_id].iloc[0]
        
        # --- INFORMACIÓN DEL PACIENTE ---
        st.subheader(f"📋 {paciente_nombre}")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Diagnóstico", paciente_sel.get('diagnostico', 'No especificado')[:30])
        with col2:
            st.metric("Estado", "🟢 Monitoreo Activo" if paciente_sel.get('activo') else "⏸️ Histórico")
        with col3:
            ultima_med = pd.to_datetime(paciente_sel.get('ultima_medicion'))
            st.metric("Última Medición", ultima_med.strftime('%d/%m/%Y %H:%M'))
        
        st.write("")
        
        # --- PIVOTEAR DATOS POR TIPO DE MEDICIÓN ---
        mediciones_pivot = mediciones_df.pivot_table(
            index='timestamp',
            columns='tipo_medicion',
            values='valor',
            aggfunc='first'
        ).reset_index()
        
        # --- TABS PARA DIFERENTES VISTAS ---
        tab_metricas, tab_graficas, tab_heatmap, tab_tabla, tab_simulador = st.tabs([
            "📊 Métricas",
            "📈 Gráficas",
            "🔥 Mapa de Calor",
            "📋 Tabla Detallada",
            "🎮 Simulador en Vivo"
        ])
        
        # ===================== TAB 1: MÉTRICAS =====================
        with tab_metricas:
            st.subheader("📊 Estadísticas Generales")
            
            # Calcular estadísticas por tipo de medición
            metricas_lista = [col for col in mediciones_pivot.columns if col != 'timestamp']
            
            # Mostrar en filas de 2 columnas para mejor presentación
            for i in range(0, len(metricas_lista), 2):
                col1, col2 = st.columns(2)
                
                # Primera métrica
                columna1 = metricas_lista[i]
                valores1 = mediciones_pivot[columna1].dropna()
                
                with col1:
                    with st.container(border=True):
                        st.markdown(f"### {columna1.replace('_', ' ').title()}")
                        
                        # Crear filas de 3 columnas para los valores
                        m1, m2, m3 = st.columns(3)
                        with m1:
                            st.metric("Promedio", f"{valores1.mean():.1f}")
                        with m2:
                            st.metric("Actual", f"{valores1.iloc[-1]:.1f}")
                        with m3:
                            st.metric("Estado", "🟢 Normal" if 60 <= valores1.mean() <= 100 else "🟡 Alerta" if valores1.mean() > 100 else "🔴 Crítico")
                        
                        # Fila de estadísticas en una sola línea clara
                        st.markdown(f"""
                        **Estadísticas:**
                        - **Mín:** {valores1.min():.1f}
                        - **Máx:** {valores1.max():.1f}
                        - **Desv. Est:** {valores1.std():.1f}
                        """)
                
                # Segunda métrica (si existe)
                if i + 1 < len(metricas_lista):
                    columna2 = metricas_lista[i + 1]
                    valores2 = mediciones_pivot[columna2].dropna()
                    
                    with col2:
                        with st.container(border=True):
                            st.markdown(f"### {columna2.replace('_', ' ').title()}")
                            
                            # Crear filas de 3 columnas para los valores
                            m1, m2, m3 = st.columns(3)
                            with m1:
                                st.metric("Promedio", f"{valores2.mean():.1f}")
                            with m2:
                                st.metric("Actual", f"{valores2.iloc[-1]:.1f}")
                            with m3:
                                st.metric("Estado", "🟢 Normal" if 95 <= valores2.mean() <= 100 else "🟡 Alerta" if valores2.mean() < 95 else "🔴 Crítico")
                            
                            # Fila de estadísticas en una sola línea clara
                            st.markdown(f"""
                            **Estadísticas:**
                            - **Mín:** {valores2.min():.1f}
                            - **Máx:** {valores2.max():.1f}
                            - **Desv. Est:** {valores2.std():.1f}
                            """)
            
            st.write("")
            st.markdown("---")
            st.subheader("Análisis Clínico")
            
            # Análisis simple
            if 'frecuencia_cardiaca' in mediciones_pivot.columns:
                fc = mediciones_pivot['frecuencia_cardiaca'].dropna()
                fc_promedio = fc.mean()
                
                if fc_promedio > 100:
                    st.markdown("""
                    <div class="alert-box">
                    ⚠️ <b>Taquicardia Detected</b><br>
                    La frecuencia cardíaca promedio es superior a los rangos normales.
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="normal-box">
                    ✅ <b>Frecuencia Cardíaca Normal</b><br>
                    Los valores están dentro de los rangos clínicos normales.
                    </div>
                    """, unsafe_allow_html=True)
            
            if 'saturacion_oxigeno' in mediciones_pivot.columns:
                o2 = mediciones_pivot['saturacion_oxigeno'].dropna()
                o2_promedio = o2.mean()
                
                if o2_promedio < 95:
                    st.markdown("""
                    <div class="alert-box">
                    ⚠️ <b>Saturación de Oxígeno Baja</b><br>
                    La saturación está por debajo de los niveles óptimos.
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="normal-box">
                    ✅ <b>Saturación de Oxígeno Óptima</b><br>
                    Niveles de oxigenación normales.
                    </div>
                    """, unsafe_allow_html=True)
        
        # ===================== TAB 2: GRÁFICAS =====================
        with tab_graficas:
            st.subheader("Evolución de Mediciones")
            
            # Crear gráfica interactiva con Plotly
            for columna in [col for col in mediciones_pivot.columns if col != 'timestamp']:
                valores_col = mediciones_pivot[['timestamp', columna]].dropna()
                
                if len(valores_col) > 0:
                    fig = go.Figure()
                    
                    fig.add_trace(go.Scatter(
                        x=valores_col['timestamp'],
                        y=valores_col[columna],
                        mode='lines+markers',
                        name=columna.replace('_', ' ').title(),
                        line=dict(color='#0284c7', width=2),
                        marker=dict(size=4)
                    ))
                    
                    fig.update_layout(
                        title=f"Evolución: {columna.replace('_', ' ').title()}",
                        xaxis_title="Fecha y Hora",
                        yaxis_title="Valor",
                        height=400,
                        hovermode='x unified',
                        template='simple_white'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
        
        # ===================== TAB 3: MAPA DE CALOR =====================
        with tab_heatmap:
            st.subheader("🔥 Mapa de Calor - Intensidad de Mediciones")
            st.markdown("Visualiza cómo varían los valores a lo largo del día. El color indica la intensidad: **Blanco = Bajo, Rojo = Alto/Crítico**")
            
            # Crear matriz de horas vs días
            mediciones_df['fecha'] = pd.to_datetime(mediciones_df['timestamp']).dt.date
            mediciones_df['hora'] = pd.to_datetime(mediciones_df['timestamp']).dt.hour
            
            # Seleccionar una métrica para el heatmap
            metricas_disponibles = mediciones_df['tipo_medicion'].unique()
            col1, col2 = st.columns([3, 1])
            with col1:
                metrica_heatmap = st.selectbox(
                    "Selecciona una métrica para visualizar",
                    options=metricas_disponibles,
                    label_visibility="collapsed"
                )
            
            mediciones_hm = mediciones_df[mediciones_df['tipo_medicion'] == metrica_heatmap]
            
            if not mediciones_hm.empty:
                # Crear tabla para heatmap
                heatmap_data = mediciones_hm.pivot_table(
                    index='hora',
                    columns='fecha',
                    values='valor',
                    aggfunc='mean'
                )
                
                # Crear anotaciones con los valores
                anotaciones_texto = []
                for i, hora in enumerate(heatmap_data.index):
                    for j, fecha in enumerate(heatmap_data.columns):
                        valor = heatmap_data.iloc[i, j]
                        if not pd.isna(valor):
                            anotaciones_texto.append(
                                dict(
                                    x=fecha,
                                    y=hora,
                                    text=f"{valor:.0f}",
                                    showarrow=False,
                                    font=dict(color="black", size=10)
                                )
                            )
                
                fig = go.Figure(data=go.Heatmap(
                    z=heatmap_data.values,
                    x=heatmap_data.columns,
                    y=heatmap_data.index,
                    colorscale='Reds',  # Escala de blanco a rojo
                    colorbar=dict(
                        title="Valor",
                        thickness=20,
                        len=0.7
                    ),
                    hoverongaps=False,
                    hovertemplate='<b>Fecha:</b> %{x}<br><b>Hora:</b> %{y}:00<br><b>Valor:</b> %{z:.1f}<extra></extra>'
                ))
                
                # Agregar anotaciones con valores en las celdas
                fig.update_layout(
                    annotations=anotaciones_texto,
                    title=dict(
                        text=f"<b>Mapa de Calor: {metrica_heatmap.replace('_', ' ').title()}</b><br><sub>Patrón de valores por hora y fecha</sub>",
                        x=0.5,
                        xanchor='center'
                    ),
                    xaxis_title="📅 Fecha",
                    yaxis_title="🕐 Hora del Día",
                    height=600,
                    width=1000,
                    template='simple_white',
                    xaxis=dict(
                        side='bottom',
                        tickangle=-45
                    ),
                    yaxis=dict(
                        autorange='reversed'
                    ),
                    margin=dict(b=120)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Información adicional
                st.info(f"""
                **Interpretación:**
                - **Rojo intenso**: Valores altos/críticos en esa hora
                - **Rosa claro**: Valores moderados
                - **Blanco**: Valores bajos o sin datos
                
                **Análisis:** {metrica_heatmap.replace('_', ' ').title()} promedio: **{heatmap_data.values.mean():.1f}**
                """)
        
        # ===================== TAB 4: TABLA DETALLADA =====================
        with tab_tabla:
            st.subheader("Datos Detallados")
            
            # Mostrar tabla con scroll y filtros
            mediciones_tabla = mediciones_df.copy()
            mediciones_tabla['timestamp'] = pd.to_datetime(mediciones_tabla['timestamp']).dt.strftime('%d/%m/%Y %H:%M:%S')
            
            # Filtro por tipo de medición
            tipos_med = st.multiselect(
                "Filtrar por tipo de medición",
                options=mediciones_tabla['tipo_medicion'].unique(),
                default=mediciones_tabla['tipo_medicion'].unique()
            )
            
            mediciones_filtrada = mediciones_tabla[mediciones_tabla['tipo_medicion'].isin(tipos_med)]
            
            st.dataframe(
                mediciones_filtrada.sort_values('timestamp', ascending=False),
                use_container_width=True,
                hide_index=True,
                height=500
            )
            
            # Opción para descargar
            csv = mediciones_filtrada.to_csv(index=False)
            st.download_button(
                label="📥 Descargar datos como CSV",
                data=csv,
                file_name=f"analisis_clinico_{paciente_nombre}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        # ===================== TAB 5: SIMULADOR EN VIVO =====================
        with tab_simulador:
            st.subheader("🎮 Simulador de Eventos en Vivo")
            st.markdown("Simula eventos médicos y observa cómo cambian las métricas en tiempo real.")
            
            # Inicializar estado del simulador
            if 'simulador_activo' not in st.session_state:
                st.session_state.simulador_activo = False
                st.session_state.evento_seleccionado = None
                st.session_state.tiempo_evento = 0
                st.session_state.datos_simulados = mediciones_pivot.copy() if not mediciones_pivot.empty else pd.DataFrame()
            
            # ---- CONTROLES DEL SIMULADOR ----
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                evento_tipo = st.selectbox(
                    "Selecciona un evento",
                    options=[
                        "Actividad Física - Correr",
                        "Actividad Física - Caminar",
                        "Descanso - Dormir",
                        "Actividad Cotidiana - Comer",
                        "Estrés",
                        "Arritmia Cardíaca",
                        "Posible Paro Cardíaco",
                        "Crisis de Pánico",
                        "Recuperación Normal"
                    ]
                )
            
            with col2:
                duracion_evento = st.slider(
                    "Duración (minutos)",
                    min_value=1,
                    max_value=120,
                    value=30,
                    step=5
                )
            
            with col3:
                intensidad = st.slider(
                    "Intensidad",
                    min_value=1.0,
                    max_value=3.0,
                    value=1.5,
                    step=0.1
                )
            
            with col4:
                st.write("")
                st.write("")
                if st.button("▶️ Iniciar Simulación", use_container_width=True, type="primary"):
                    st.session_state.simulador_activo = True
                    st.session_state.evento_seleccionado = evento_tipo
                    st.session_state.tiempo_evento = duracion_evento
            
            st.markdown("---")
            
            # ---- SIMULACIÓN EN TIEMPO REAL ----
            if st.session_state.simulador_activo:
                # Crear datos simulados basados en el evento
                datos_sim = mediciones_pivot.tail(100).copy().reset_index()
                timestamps_nuevos = pd.date_range(
                    start=datos_sim['timestamp'].max() + timedelta(seconds=1),
                    periods=duracion_evento * 2,
                    freq='30S'
                )
                
                # Generar valores según el evento
                evento = st.session_state.evento_seleccionado
                
                # Parámetros base
                if 'Correr' in evento:
                    fc_delta = 50 * intensidad
                    pa_delta = 20 * intensidad
                    temp_delta = 1.0 * intensidad
                elif 'Caminar' in evento:
                    fc_delta = 25 * intensidad
                    pa_delta = 10 * intensidad
                    temp_delta = 0.5 * intensidad
                elif 'Dormir' in evento:
                    fc_delta = -15
                    pa_delta = -10
                    temp_delta = -0.3
                    o2_delta = 1.0
                elif 'Comer' in evento:
                    fc_delta = 10 * intensidad
                    pa_delta = 5 * intensidad
                    temp_delta = 0.2
                elif 'Estrés' in evento:
                    fc_delta = 30 * intensidad
                    pa_delta = 15 * intensidad
                    temp_delta = 0.5 * intensidad
                elif 'Arritmia' in evento:
                    fc_delta = 40 * intensidad
                    pa_delta = 25 * intensidad
                    temp_delta = 0.3
                elif 'Paro' in evento:
                    fc_delta = -80 * intensidad
                    pa_delta = -40 * intensidad
                    temp_delta = -0.5
                elif 'Pánico' in evento:
                    fc_delta = 60 * intensidad
                    pa_delta = 30 * intensidad
                    temp_delta = 1.0 * intensidad
                else:
                    fc_delta = 0
                    pa_delta = 0
                    temp_delta = 0
                
                # Generar valores simulados
                nuevos_datos = []
                for t in timestamps_nuevos:
                    # Progresión suave del evento
                    progreso = min(t.minute / (duracion_evento/60), 1.0)
                    
                    if 'frecuencia_cardiaca' in datos_sim.columns:
                        fc = datos_sim['frecuencia_cardiaca'].iloc[-1] + fc_delta * progreso
                        fc = max(40, min(180, fc))
                    else:
                        fc = 75
                    
                    if 'presion_sistolica' in datos_sim.columns:
                        pa_s = datos_sim['presion_sistolica'].iloc[-1] + pa_delta * progreso
                        pa_s = max(70, min(200, pa_s))
                    else:
                        pa_s = 120
                    
                    if 'presion_diastolica' in datos_sim.columns:
                        pa_d = datos_sim['presion_diastolica'].iloc[-1] + pa_delta * 0.5 * progreso
                        pa_d = max(40, min(120, pa_d))
                    else:
                        pa_d = 80
                    
                    if 'saturacion_oxigeno' in datos_sim.columns:
                        o2 = datos_sim['saturacion_oxigeno'].iloc[-1] - (0.5 if 'Paro' in evento else 0) * progreso
                        o2 = max(85, min(100, o2))
                    else:
                        o2 = 98
                    
                    if 'temperatura' in datos_sim.columns:
                        temp = datos_sim['temperatura'].iloc[-1] + temp_delta * progreso
                        temp = max(35, min(39.5, temp))
                    else:
                        temp = 37
                    
                    nuevos_datos.append({
                        'timestamp': t,
                        'frecuencia_cardiaca': fc,
                        'presion_sistolica': pa_s,
                        'presion_diastolica': pa_d,
                        'saturacion_oxigeno': o2,
                        'temperatura': temp
                    })
                
                datos_simulados_df = pd.DataFrame(nuevos_datos)
                
                # Mostrar métricas en tiempo real
                st.info(f"▶️ **Simulando:** {evento}")
                
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    fc_actual = datos_simulados_df['frecuencia_cardiaca'].iloc[-1]
                    fc_color = "🟢" if 60 <= fc_actual <= 100 else "🟡" if fc_actual > 100 else "🔴"
                    st.metric(f"{fc_color} FC", f"{fc_actual:.0f} bpm")
                
                with col2:
                    pa_s = datos_simulados_df['presion_sistolica'].iloc[-1]
                    pa_d = datos_simulados_df['presion_diastolica'].iloc[-1]
                    st.metric("PA", f"{pa_s:.0f}/{pa_d:.0f} mmHg")
                
                with col3:
                    o2_actual = datos_simulados_df['saturacion_oxigeno'].iloc[-1]
                    o2_color = "🟢" if o2_actual >= 95 else "🟡" if o2_actual >= 90 else "🔴"
                    st.metric(f"{o2_color} O₂", f"{o2_actual:.1f}%")
                
                with col4:
                    temp_actual = datos_simulados_df['temperatura'].iloc[-1]
                    temp_color = "🟢" if 36.5 <= temp_actual <= 37.5 else "🟡" if 36 <= temp_actual <= 38 else "🔴"
                    st.metric(f"{temp_color} Temp", f"{temp_actual:.1f}°C")
                
                with col5:
                    vfc_estim = np.random.randint(40, 150) if 'Dormir' in evento else np.random.randint(30, 80)
                    st.metric("VFC", f"{vfc_estim} ms")
                
                st.markdown("---")
                
                # Gráfico de evolución en vivo
                fig_simulacion = go.Figure()
                
                # Combinar datos históricos con simulados
                datos_combinados = pd.concat([
                    datos_sim[['timestamp', 'frecuencia_cardiaca']].tail(50),
                    datos_simulados_df[['timestamp', 'frecuencia_cardiaca']]
                ], ignore_index=True)
                
                fig_simulacion.add_trace(go.Scatter(
                    x=datos_combinados['timestamp'],
                    y=datos_combinados['frecuencia_cardiaca'],
                    mode='lines+markers',
                    name='Frecuencia Cardíaca',
                    line=dict(color='#ff6b6b', width=3),
                    marker=dict(size=6)
                ))
                
                # Zonas normales
                fig_simulacion.add_hrect(
                    y0=60, y1=100,
                    fillcolor="green", opacity=0.1,
                    layer="below", line_width=0,
                    annotation_text="Normal"
                )
                
                fig_simulacion.update_layout(
                    title=f"Evolución en Vivo: {evento}",
                    xaxis_title="Tiempo",
                    yaxis_title="FC (bpm)",
                    height=400,
                    hovermode='x unified',
                    template='simple_white'
                )
                
                st.plotly_chart(fig_simulacion, use_container_width=True)
                
                # Tabla de eventos simulados
                st.subheader("📊 Registro de Eventos Simulados")
                st.dataframe(
                    datos_simulados_df.head(20),
                    use_container_width=True,
                    hide_index=True,
                    height=300
                )
                
                # Botón para detener
                if st.button("⏹️ Detener Simulación", use_container_width=True, type="secondary"):
                    st.session_state.simulador_activo = False
                    st.rerun()
            else:
                st.info("👆 Selecciona un evento y presiona 'Iniciar Simulación' para ver cómo cambian las métricas en tiempo real.")