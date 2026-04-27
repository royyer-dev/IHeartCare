import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sqlalchemy import text
from core.auth import require_auth
from core.sidebar import render_sidebar
from core.theme import apply_global_theme
from utils import breadcrumb_nav

# --- PROTECCIÓN DE RUTA ---
require_auth(allowed_roles=['administrador', 'medico'])
render_sidebar()
apply_global_theme()

st.set_page_config(page_title="Análisis Clínico", page_icon="❤️", layout="wide")
breadcrumb_nav(["Home", "Análisis", "Análisis Clínico"])

# --- CONEXIÓN ---
try:
    conn = st.connection("postgresql", type="sql")
except Exception:
    st.error("No se pudo establecer conexión con la base de datos.")
    st.stop()

st.title("Análisis Clínico")
st.markdown("---")

# --- RANGOS CLÍNICOS DE REFERENCIA ---
RANGOS_CLINICOS = {
    'frecuencia_cardiaca': {'min': 60, 'max': 100, 'unidad': 'bpm', 'label': 'Frecuencia Cardíaca'},
    'saturacion_oxigeno': {'min': 95, 'max': 100, 'unidad': '%', 'label': 'Saturación de Oxígeno'},
    'presion_sistolica': {'min': 90, 'max': 140, 'unidad': 'mmHg', 'label': 'Presión Sistólica'},
    'presion_diastolica': {'min': 60, 'max': 90, 'unidad': 'mmHg', 'label': 'Presión Diastólica'},
    'temperatura': {'min': 36.1, 'max': 37.5, 'unidad': '°C', 'label': 'Temperatura'},
}

def clasificar_valor(valor, tipo):
    """Clasifica un valor como Normal, Alerta o Crítico según rangos clínicos."""
    rango = RANGOS_CLINICOS.get(tipo)
    if not rango:
        return 'Normal', '#10B981'
    if rango['min'] <= valor <= rango['max']:
        return 'Normal', '#10B981'
    margen_min = rango['min'] * 0.9
    margen_max = rango['max'] * 1.1
    if margen_min <= valor <= margen_max:
        return 'Alerta', '#F59E0B'
    return 'Crítico', '#EF4444'

# --- OBTENER PACIENTES ---
try:
    pacientes_df = conn.query("""
        SELECT DISTINCT p.id, p.nombre, p.apellido_paterno, p.apellido_materno,
               p.diagnostico, MAX(med.timestamp) as ultima_medicion
        FROM public.pacientes p
        JOIN public.dispositivos d ON p.id = d.paciente_id
        JOIN public.mediciones med ON d.id = med.dispositivo_id
        GROUP BY p.id
        ORDER BY p.nombre
    """, ttl="10s")
except Exception as e:
    st.error(f"Error al cargar pacientes: {e}")
    pacientes_df = pd.DataFrame()

if pacientes_df.empty:
    st.warning("No hay datos de mediciones disponibles en el sistema.")
    st.stop()

# --- SELECTORES ---
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    st.markdown("**Paciente**")
    pacientes_opciones = {
        f"{p['nombre']} {p['apellido_paterno']} {p.get('apellido_materno', '') or ''}".strip(): p['id']
        for _, p in pacientes_df.iterrows()
    }
    paciente_nombre = st.selectbox("Paciente", options=list(pacientes_opciones.keys()), label_visibility="collapsed")
    paciente_id = pacientes_opciones[paciente_nombre]

with col2:
    st.markdown("**Período**")
    rango_tipo = st.radio("Período", options=["Todo", "30 días", "7 días", "Personalizado"],
                          horizontal=True, label_visibility="collapsed")

with col3:
    st.write("")
    if st.button("Refrescar", use_container_width=True):
        st.rerun()

# --- CALCULAR RANGO ---
ahora = datetime.now()
if rango_tipo == "7 días":
    fecha_inicio, fecha_fin = ahora - timedelta(days=7), ahora
elif rango_tipo == "30 días":
    fecha_inicio, fecha_fin = ahora - timedelta(days=30), ahora
elif rango_tipo == "Todo":
    fecha_inicio, fecha_fin = None, ahora
else:
    c1, c2 = st.columns(2)
    with c1:
        fi = st.date_input("Desde", value=ahora - timedelta(days=7))
    with c2:
        ff = st.date_input("Hasta", value=ahora)
    fecha_inicio = datetime.combine(fi, datetime.min.time())
    fecha_fin = datetime.combine(ff, datetime.max.time())

# --- CARGAR MEDICIONES ---
try:
    if fecha_inicio:
        mediciones_df = conn.query(f"""
            SELECT m.timestamp, m.tipo_medicion, m.valor, m.unidad_medida
            FROM public.mediciones m
            JOIN public.dispositivos d ON m.dispositivo_id = d.id
            WHERE d.paciente_id = {paciente_id}
                AND m.timestamp >= '{fecha_inicio}' AND m.timestamp <= '{fecha_fin}'
            ORDER BY m.timestamp
        """, ttl="5s")
    else:
        mediciones_df = conn.query(f"""
            SELECT m.timestamp, m.tipo_medicion, m.valor, m.unidad_medida
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
    st.stop()

st.markdown("---")

paciente_sel = pacientes_df[pacientes_df['id'] == paciente_id].iloc[0]

# --- CABECERA DEL PACIENTE ---
st.markdown(f"## {paciente_nombre}")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**Diagnóstico**")
    st.write(paciente_sel.get('diagnostico', 'No especificado') or 'No especificado')
with col2:
    st.markdown("**Total de registros**")
    st.write(f"{len(mediciones_df)} mediciones")
with col3:
    st.markdown("**Última medición**")
    ultima = pd.to_datetime(paciente_sel.get('ultima_medicion'))
    st.write(ultima.strftime('%d/%m/%Y %H:%M') if pd.notna(ultima) else 'N/A')

st.markdown("---")

# --- PIVOTEAR ---
mediciones_pivot = mediciones_df.pivot_table(
    index='timestamp', columns='tipo_medicion', values='valor', aggfunc='first'
).reset_index()

# ==================== TABS ====================
tab_resumen, tab_tendencias, tab_heatmap, tab_datos, tab_simulador = st.tabs([
    "Resumen Clínico", "Tendencias", "Mapa de Calor", "Datos", "Simulador"
])

# ==================== TAB 1: RESUMEN CLÍNICO ====================
with tab_resumen:
    st.subheader("Estado Actual de Signos Vitales")

    metricas_lista = [col for col in mediciones_pivot.columns if col != 'timestamp']

    # Tarjetas de signos vitales
    cols = st.columns(min(len(metricas_lista), 4))
    for idx, tipo in enumerate(metricas_lista[:4]):
        valores = mediciones_pivot[tipo].dropna()
        if valores.empty:
            continue
        ultimo_valor = valores.iloc[-1]
        promedio = valores.mean()
        rango = RANGOS_CLINICOS.get(tipo, {})
        label = rango.get('label', tipo.replace('_', ' ').title())
        unidad = rango.get('unidad', '')
        estado, color = clasificar_valor(ultimo_valor, tipo)

        with cols[idx % len(cols)]:
            with st.container(border=True):
                st.markdown(f"**{label}**")
                st.markdown(f"<div style='font-size:2rem; font-weight:700; color:{color};'>{ultimo_valor:.1f} <span style='font-size:1rem;'>{unidad}</span></div>", unsafe_allow_html=True)
                st.caption(f"Estado: {estado}")

                rango_min = rango.get('min', '-')
                rango_max = rango.get('max', '-')
                st.caption(f"Rango normal: {rango_min} – {rango_max} {unidad}")

    # Si hay más de 4 métricas, segunda fila
    if len(metricas_lista) > 4:
        cols2 = st.columns(min(len(metricas_lista) - 4, 4))
        for idx, tipo in enumerate(metricas_lista[4:]):
            valores = mediciones_pivot[tipo].dropna()
            if valores.empty:
                continue
            ultimo_valor = valores.iloc[-1]
            rango = RANGOS_CLINICOS.get(tipo, {})
            label = rango.get('label', tipo.replace('_', ' ').title())
            unidad = rango.get('unidad', '')
            estado, color = clasificar_valor(ultimo_valor, tipo)
            with cols2[idx % len(cols2)]:
                with st.container(border=True):
                    st.markdown(f"**{label}**")
                    st.markdown(f"<div style='font-size:2rem; font-weight:700; color:{color};'>{ultimo_valor:.1f} <span style='font-size:1rem;'>{unidad}</span></div>", unsafe_allow_html=True)
                    st.caption(f"Estado: {estado}")

    st.markdown("---")

    # --- RESUMEN ESTADÍSTICO ---
    st.subheader("Resumen Estadístico")
    for i in range(0, len(metricas_lista), 2):
        col1, col2 = st.columns(2)
        for j, col in enumerate([col1, col2]):
            if i + j >= len(metricas_lista):
                break
            tipo = metricas_lista[i + j]
            valores = mediciones_pivot[tipo].dropna()
            if valores.empty:
                continue
            rango = RANGOS_CLINICOS.get(tipo, {})
            label = rango.get('label', tipo.replace('_', ' ').title())
            unidad = rango.get('unidad', '')
            with col:
                with st.container(border=True):
                    st.markdown(f"**{label}**")
                    m1, m2, m3, m4 = st.columns(4)
                    with m1:
                        st.metric("Promedio", f"{valores.mean():.1f}")
                    with m2:
                        st.metric("Mínimo", f"{valores.min():.1f}")
                    with m3:
                        st.metric("Máximo", f"{valores.max():.1f}")
                    with m4:
                        st.metric("Desv. Est.", f"{valores.std():.1f}")

    st.markdown("---")

    # --- INTERPRETACIÓN CLÍNICA ---
    st.subheader("Interpretación Clínica")
    for tipo in metricas_lista:
        valores = mediciones_pivot[tipo].dropna()
        if valores.empty:
            continue
        promedio = valores.mean()
        rango = RANGOS_CLINICOS.get(tipo, {})
        label = rango.get('label', tipo.replace('_', ' ').title())
        estado, color = clasificar_valor(promedio, tipo)

        if estado == 'Normal':
            st.success(f"**{label}:** Promedio {promedio:.1f} — dentro de rangos normales ({rango.get('min', '?')}–{rango.get('max', '?')}).")
        elif estado == 'Alerta':
            st.warning(f"**{label}:** Promedio {promedio:.1f} — fuera de rango normal ({rango.get('min', '?')}–{rango.get('max', '?')}). Se recomienda seguimiento.")
        else:
            st.error(f"**{label}:** Promedio {promedio:.1f} — valor crítico. Rango esperado: {rango.get('min', '?')}–{rango.get('max', '?')}. Requiere atención inmediata.")

# ==================== TAB 2: TENDENCIAS ====================
with tab_tendencias:
    st.subheader("Evolución Temporal")

    for tipo in [c for c in mediciones_pivot.columns if c != 'timestamp']:
        valores_col = mediciones_pivot[['timestamp', tipo]].dropna()
        if len(valores_col) == 0:
            continue

        rango = RANGOS_CLINICOS.get(tipo, {})
        label = rango.get('label', tipo.replace('_', ' ').title())

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=valores_col['timestamp'], y=valores_col[tipo],
            mode='lines+markers', name=label,
            line=dict(color='#1E40AF', width=2), marker=dict(size=3)
        ))

        # Banda de rango normal
        if 'min' in rango and 'max' in rango:
            fig.add_hrect(
                y0=rango['min'], y1=rango['max'],
                fillcolor="#10B981", opacity=0.08, layer="below", line_width=0,
                annotation_text="Rango normal", annotation_position="top left",
                annotation=dict(font_size=10, font_color="#6B7280")
            )

        fig.update_layout(
            title=label,
            xaxis_title="Fecha",
            yaxis_title=f"Valor ({rango.get('unidad', '')})",
            height=350, hovermode='x unified', template='simple_white',
            margin=dict(t=40, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)

# ==================== TAB 3: MAPA DE CALOR ====================
with tab_heatmap:
    st.subheader("Mapa de Calor — Patrones por Hora")
    st.caption("Visualiza cómo varían los valores a lo largo del día. Colores más intensos indican valores más altos.")

    mediciones_df['fecha'] = pd.to_datetime(mediciones_df['timestamp']).dt.date
    mediciones_df['hora'] = pd.to_datetime(mediciones_df['timestamp']).dt.hour

    metricas_disponibles = mediciones_df['tipo_medicion'].unique()
    metrica_heatmap = st.selectbox("Métrica", options=metricas_disponibles,
        format_func=lambda x: RANGOS_CLINICOS.get(x, {}).get('label', x.replace('_',' ').title()))

    mediciones_hm = mediciones_df[mediciones_df['tipo_medicion'] == metrica_heatmap]

    if not mediciones_hm.empty:
        heatmap_data = mediciones_hm.pivot_table(index='hora', columns='fecha', values='valor', aggfunc='mean')

        anotaciones = []
        for i, hora in enumerate(heatmap_data.index):
            for j, fecha in enumerate(heatmap_data.columns):
                val = heatmap_data.iloc[i, j]
                if not pd.isna(val):
                    anotaciones.append(dict(x=fecha, y=hora, text=f"{val:.0f}", showarrow=False,
                                            font=dict(color="black", size=10)))

        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values, x=heatmap_data.columns, y=heatmap_data.index,
            colorscale='YlOrRd', colorbar=dict(title="Valor", thickness=15, len=0.7),
            hoverongaps=False,
            hovertemplate='<b>Fecha:</b> %{x}<br><b>Hora:</b> %{y}:00<br><b>Valor:</b> %{z:.1f}<extra></extra>'
        ))

        label_hm = RANGOS_CLINICOS.get(metrica_heatmap, {}).get('label', metrica_heatmap.replace('_',' ').title())
        fig.update_layout(
            annotations=anotaciones,
            title=f"{label_hm} — Patrón por hora y fecha",
            xaxis_title="Fecha", yaxis_title="Hora del día",
            height=550, template='simple_white',
            xaxis=dict(side='bottom', tickangle=-45),
            yaxis=dict(autorange='reversed'),
            margin=dict(b=100)
        )
        st.plotly_chart(fig, use_container_width=True)

        promedio_general = heatmap_data.values[~np.isnan(heatmap_data.values)].mean()
        st.info(f"**Promedio general:** {promedio_general:.1f} — Los colores más intensos indican horas con valores más elevados.")

# ==================== TAB 4: DATOS ====================
with tab_datos:
    st.subheader("Registro Detallado")

    mediciones_tabla = mediciones_df.copy()
    mediciones_tabla['timestamp'] = pd.to_datetime(mediciones_tabla['timestamp']).dt.strftime('%d/%m/%Y %H:%M:%S')

    tipos_med = st.multiselect("Filtrar por tipo", options=mediciones_tabla['tipo_medicion'].unique(),
        default=mediciones_tabla['tipo_medicion'].unique(),
        format_func=lambda x: RANGOS_CLINICOS.get(x, {}).get('label', x.replace('_',' ').title()))

    mediciones_filtrada = mediciones_tabla[mediciones_tabla['tipo_medicion'].isin(tipos_med)]

    st.dataframe(
        mediciones_filtrada.sort_values('timestamp', ascending=False),
        use_container_width=True, hide_index=True, height=500
    )

    csv = mediciones_filtrada.to_csv(index=False)
    st.download_button(
        label="Descargar CSV",
        data=csv,
        file_name=f"analisis_{paciente_nombre}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv", use_container_width=True
    )

# ==================== TAB 5: SIMULADOR ====================
with tab_simulador:
    st.subheader("Simulador de Eventos")
    st.caption("Simula eventos médicos y observa cómo cambiarían las métricas.")

    if 'simulador_activo' not in st.session_state:
        st.session_state.simulador_activo = False

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        evento_tipo = st.selectbox("Evento", options=[
            "Actividad Física - Correr", "Actividad Física - Caminar",
            "Descanso - Dormir", "Actividad Cotidiana - Comer",
            "Estrés", "Arritmia Cardíaca", "Posible Paro Cardíaco",
            "Crisis de Pánico", "Recuperación Normal"
        ])
    with col2:
        duracion_evento = st.slider("Duración (min)", 1, 120, 30, step=5)
    with col3:
        intensidad = st.slider("Intensidad", 1.0, 3.0, 1.5, step=0.1)
    with col4:
        st.write("")
        st.write("")
        if st.button("Iniciar Simulación", use_container_width=True, type="primary"):
            st.session_state.simulador_activo = True
            st.session_state.evento_seleccionado = evento_tipo

    st.markdown("---")

    if st.session_state.simulador_activo:
        datos_sim = mediciones_pivot.tail(100).copy().reset_index()
        timestamps_nuevos = pd.date_range(
            start=datos_sim['timestamp'].max() + timedelta(seconds=1),
            periods=duracion_evento * 2, freq='30S'
        )

        evento = st.session_state.evento_seleccionado
        deltas = {
            'Correr': (50, 20, 1.0), 'Caminar': (25, 10, 0.5),
            'Dormir': (-15, -10, -0.3), 'Comer': (10, 5, 0.2),
            'Estrés': (30, 15, 0.5), 'Arritmia': (40, 25, 0.3),
            'Paro': (-80, -40, -0.5), 'Pánico': (60, 30, 1.0),
        }

        fc_d, pa_d, temp_d = 0, 0, 0
        for key, vals in deltas.items():
            if key in evento:
                fc_d, pa_d, temp_d = [v * intensidad for v in vals]
                break

        nuevos = []
        for t in timestamps_nuevos:
            prog = min(1.0, len(nuevos) / max(len(timestamps_nuevos) * 0.5, 1))
            fc = datos_sim.get('frecuencia_cardiaca', pd.Series([75])).iloc[-1] + fc_d * prog
            pa_s = datos_sim.get('presion_sistolica', pd.Series([120])).iloc[-1] + pa_d * prog
            pa_dia = datos_sim.get('presion_diastolica', pd.Series([80])).iloc[-1] + pa_d * 0.5 * prog
            o2 = datos_sim.get('saturacion_oxigeno', pd.Series([98])).iloc[-1] - (0.5 if 'Paro' in evento else 0) * prog
            temp = datos_sim.get('temperatura', pd.Series([37])).iloc[-1] + temp_d * prog

            nuevos.append({
                'timestamp': t,
                'frecuencia_cardiaca': max(40, min(180, fc)),
                'presion_sistolica': max(70, min(200, pa_s)),
                'presion_diastolica': max(40, min(120, pa_dia)),
                'saturacion_oxigeno': max(85, min(100, o2)),
                'temperatura': max(35, min(39.5, temp))
            })

        sim_df = pd.DataFrame(nuevos)

        st.info(f"**Simulando:** {evento}")

        col1, col2, col3, col4, col5 = st.columns(5)
        sim_metrics = [
            ('frecuencia_cardiaca', 'FC', 'bpm'),
            ('presion_sistolica', 'PA Sist.', 'mmHg'),
            ('presion_diastolica', 'PA Diast.', 'mmHg'),
            ('saturacion_oxigeno', 'SpO2', '%'),
            ('temperatura', 'Temp', '°C'),
        ]
        for (tipo, label, unidad), c in zip(sim_metrics, [col1, col2, col3, col4, col5]):
            val = sim_df[tipo].iloc[-1]
            estado, color = clasificar_valor(val, tipo)
            with c:
                st.markdown(f"<div style='text-align:center;'><span style='font-size:0.8rem;color:#6B7280;'>{label}</span><br><span style='font-size:1.5rem;font-weight:700;color:{color};'>{val:.1f}</span><br><span style='font-size:0.75rem;color:#9CA3AF;'>{unidad} — {estado}</span></div>", unsafe_allow_html=True)

        st.markdown("---")

        # Gráfica de simulación
        if 'frecuencia_cardiaca' in datos_sim.columns:
            combinados = pd.concat([
                datos_sim[['timestamp', 'frecuencia_cardiaca']].tail(50),
                sim_df[['timestamp', 'frecuencia_cardiaca']]
            ], ignore_index=True)

            fig_sim = go.Figure()
            fig_sim.add_trace(go.Scatter(
                x=combinados['timestamp'], y=combinados['frecuencia_cardiaca'],
                mode='lines+markers', name='FC',
                line=dict(color='#DC2626', width=2), marker=dict(size=4)
            ))
            fig_sim.add_hrect(y0=60, y1=100, fillcolor="#10B981", opacity=0.08, layer="below", line_width=0)
            fig_sim.update_layout(
                title=f"Simulación: {evento}",
                xaxis_title="Tiempo", yaxis_title="FC (bpm)",
                height=350, hovermode='x unified', template='simple_white'
            )
            st.plotly_chart(fig_sim, use_container_width=True)

        st.subheader("Datos Simulados")
        st.dataframe(sim_df.head(20), use_container_width=True, hide_index=True, height=300)

        if st.button("Detener Simulación", use_container_width=True, type="secondary"):
            st.session_state.simulador_activo = False
            st.rerun()
    else:
        st.caption("Selecciona un evento y presiona 'Iniciar Simulación' para ver cómo cambiarían las métricas.")