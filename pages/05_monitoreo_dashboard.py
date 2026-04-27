import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
from sqlalchemy import text
from core.auth import require_auth
from core.sidebar import render_sidebar
from core.theme import apply_global_theme
from utils import breadcrumb_nav

# --- PROTECCIÓN DE RUTA ---
require_auth(allowed_roles=['administrador', 'medico'])
render_sidebar()
apply_global_theme()

st.set_page_config(page_title="Visualización en Vivo", page_icon="❤️", layout="wide")
breadcrumb_nav(["Home", "Análisis", "Visualización"])

# --- CONEXIÓN ---
try:
    conn = st.connection("postgresql", type="sql")
except Exception:
    st.error("No se pudo establecer conexión con la base de datos.")
    st.stop()

st.title("Visualización en Vivo")
st.markdown("---")

# --- RANGOS CLÍNICOS ---
RANGOS = {
    'frecuencia_cardiaca': {'min': 60, 'max': 100, 'unit': 'bpm', 'label': 'Frecuencia Cardíaca', 'base': 75, 'var': 8},
    'saturacion_oxigeno': {'min': 95, 'max': 100, 'unit': '%', 'label': 'SpO2', 'base': 97.5, 'var': 1.2},
    'presion_sistolica': {'min': 90, 'max': 140, 'unit': 'mmHg', 'label': 'PA Sistólica', 'base': 120, 'var': 8},
    'presion_diastolica': {'min': 60, 'max': 90, 'unit': 'mmHg', 'label': 'PA Diastólica', 'base': 78, 'var': 5},
    'temperatura': {'min': 36.1, 'max': 37.5, 'unit': '°C', 'label': 'Temperatura', 'base': 36.7, 'var': 0.3},
}

def clasificar(val, tipo):
    r = RANGOS.get(tipo, {})
    if not r:
        return 'Normal', '#10B981'
    if r['min'] <= val <= r['max']:
        return 'Normal', '#10B981'
    if r['min'] * 0.9 <= val <= r['max'] * 1.1:
        return 'Alerta', '#F59E0B'
    return 'Crítico', '#EF4444'

def gen_value(tipo, prev=None):
    """Generate a realistic simulated value with smooth transitions."""
    r = RANGOS[tipo]
    if prev is None:
        return r['base'] + np.random.uniform(-r['var'], r['var'])
    # Smooth random walk with mean reversion
    drift = (r['base'] - prev) * 0.05  # Pull toward baseline
    noise = np.random.normal(0, r['var'] * 0.3)
    new_val = prev + drift + noise
    # Clamp to realistic bounds
    lo = r['min'] * 0.85
    hi = r['max'] * 1.15
    return max(lo, min(hi, new_val))

# --- OBTENER PACIENTES CON MONITOREO ACTIVO ---
try:
    pacientes_mon = conn.query("""
        SELECT DISTINCT p.id, p.nombre, p.apellido_paterno, p.apellido_materno,
               p.diagnostico, d.modelo, d.mac_address, m.motivo,
               m.fecha_inicio
        FROM public.monitoreos m
        JOIN public.pacientes p ON m.paciente_id = p.id
        LEFT JOIN public.dispositivos d ON p.id = d.paciente_id AND d.activo = true
        WHERE m.activo = true
        ORDER BY p.nombre
    """, ttl="10s")
except Exception as e:
    st.error(f"Error al cargar monitoreos: {e}")
    pacientes_mon = pd.DataFrame()

if pacientes_mon.empty:
    st.info("No hay monitoreos activos en este momento.")
    st.stop()

# --- CONTROLES ---
col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    opciones_pac = {
        f"{p['nombre']} {p['apellido_paterno']} {p.get('apellido_materno', '') or ''}".strip(): idx
        for idx, p in pacientes_mon.iterrows()
    }
    pac_sel_name = st.selectbox("Paciente", options=list(opciones_pac.keys()))
    pac_row = pacientes_mon.iloc[opciones_pac[pac_sel_name]]

with col2:
    intervalo = st.selectbox("Actualizar cada", options=[5, 10, 20],
                             format_func=lambda x: f"{x} segundos")

with col3:
    st.write("")
    auto_refresh = st.toggle("Auto-refresh", value=True)

# --- INFO DEL PACIENTE ---
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown("**Paciente**")
    st.write(pac_sel_name)
with col2:
    st.markdown("**Diagnóstico**")
    st.write(pac_row.get('diagnostico', 'N/A') or 'N/A')
with col3:
    st.markdown("**Dispositivo**")
    st.write(pac_row.get('modelo', 'N/A') or 'N/A')
with col4:
    st.markdown("**Monitoreo desde**")
    fi = pac_row.get('fecha_inicio')
    st.write(fi.strftime('%d/%m/%Y %H:%M') if pd.notna(fi) else 'N/A')

st.markdown("---")

# --- INICIALIZAR HISTORIAL SIMULADO ---
HISTORY_KEY = f"live_history_{pac_row['id']}"
TICK_KEY = "live_tick_count"

if HISTORY_KEY not in st.session_state:
    # Generate initial 60 data points (last ~5 min of simulated data)
    now = datetime.now()
    history = []
    prev = {}
    for i in range(60):
        ts = now - timedelta(seconds=(60 - i) * 5)
        point = {'timestamp': ts}
        for tipo in RANGOS:
            val = gen_value(tipo, prev.get(tipo))
            point[tipo] = round(val, 2)
            prev[tipo] = val
        history.append(point)
    st.session_state[HISTORY_KEY] = history

if TICK_KEY not in st.session_state:
    st.session_state[TICK_KEY] = 0

# --- GENERAR NUEVO PUNTO ---
st.session_state[TICK_KEY] += 1
history = st.session_state[HISTORY_KEY]
last = history[-1]
new_point = {'timestamp': datetime.now()}
for tipo in RANGOS:
    new_point[tipo] = round(gen_value(tipo, last[tipo]), 2)
history.append(new_point)

# Keep last 120 points
if len(history) > 120:
    history = history[-120:]
st.session_state[HISTORY_KEY] = history

df = pd.DataFrame(history)

# --- CURRENT VALUES HEADER ---
current = df.iloc[-1]
prev_vals = df.iloc[-2] if len(df) > 1 else current

vitals_cols = st.columns(5)
for idx, (tipo, info) in enumerate(RANGOS.items()):
    val = current[tipo]
    delta = val - prev_vals[tipo]
    estado, color = clasificar(val, tipo)
    with vitals_cols[idx]:
        st.markdown(f"""
        <div style="
            border: 2px solid {color};
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
            background: {color}0A;
        ">
            <div style="font-size: 0.8rem; color: #6B7280; font-weight: 600;">{info['label']}</div>
            <div style="font-size: 2rem; font-weight: 700; color: {color};">{val:.1f}</div>
            <div style="font-size: 0.75rem; color: #9CA3AF;">{info['unit']}</div>
            <div style="font-size: 0.7rem; margin-top: 4px; color: {'#10B981' if abs(delta) < info['var'] * 0.5 else '#F59E0B'};">
                {'▲' if delta > 0 else '▼'} {abs(delta):.1f} — {estado}
            </div>
        </div>
        """, unsafe_allow_html=True)

st.write("")

# --- GRÁFICAS EN TIEMPO REAL ---
tab_fc, tab_pa, tab_o2, tab_temp, tab_all = st.tabs([
    "Frecuencia Cardíaca", "Presión Arterial", "SpO2", "Temperatura", "Vista General"
])

with tab_fc:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['frecuencia_cardiaca'],
        mode='lines', name='FC', line=dict(color='#DC2626', width=2),
        fill='tozeroy', fillcolor='rgba(220,38,38,0.05)'
    ))
    fig.add_hrect(y0=60, y1=100, fillcolor="#10B981", opacity=0.06, layer="below", line_width=0)
    fig.update_layout(title="Frecuencia Cardíaca", yaxis_title="bpm",
                      height=400, template='simple_white', hovermode='x unified',
                      margin=dict(t=40, b=30))
    st.plotly_chart(fig, use_container_width=True)

with tab_pa:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['presion_sistolica'],
        mode='lines', name='Sistólica', line=dict(color='#1E40AF', width=2)
    ))
    fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['presion_diastolica'],
        mode='lines', name='Diastólica', line=dict(color='#7C3AED', width=2)
    ))
    fig.add_hrect(y0=90, y1=140, fillcolor="#10B981", opacity=0.05, layer="below", line_width=0)
    fig.update_layout(title="Presión Arterial", yaxis_title="mmHg",
                      height=400, template='simple_white', hovermode='x unified',
                      margin=dict(t=40, b=30))
    st.plotly_chart(fig, use_container_width=True)

with tab_o2:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['saturacion_oxigeno'],
        mode='lines', name='SpO2', line=dict(color='#0891B2', width=2),
        fill='tozeroy', fillcolor='rgba(8,145,178,0.05)'
    ))
    fig.add_hrect(y0=95, y1=100, fillcolor="#10B981", opacity=0.06, layer="below", line_width=0)
    fig.update_layout(title="Saturación de Oxígeno", yaxis_title="%",
                      height=400, template='simple_white', hovermode='x unified',
                      yaxis=dict(range=[88, 102]),
                      margin=dict(t=40, b=30))
    st.plotly_chart(fig, use_container_width=True)

with tab_temp:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['temperatura'],
        mode='lines+markers', name='Temp', line=dict(color='#D97706', width=2),
        marker=dict(size=3)
    ))
    fig.add_hrect(y0=36.1, y1=37.5, fillcolor="#10B981", opacity=0.06, layer="below", line_width=0)
    fig.update_layout(title="Temperatura Corporal", yaxis_title="°C",
                      height=400, template='simple_white', hovermode='x unified',
                      margin=dict(t=40, b=30))
    st.plotly_chart(fig, use_container_width=True)

with tab_all:
    fig = make_subplots(
        rows=2, cols=2, subplot_titles=(
            "Frecuencia Cardíaca", "Presión Arterial",
            "SpO2", "Temperatura"
        ), vertical_spacing=0.12, horizontal_spacing=0.08
    )
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['frecuencia_cardiaca'],
                             mode='lines', name='FC', line=dict(color='#DC2626', width=1.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['presion_sistolica'],
                             mode='lines', name='Sist.', line=dict(color='#1E40AF', width=1.5)), row=1, col=2)
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['presion_diastolica'],
                             mode='lines', name='Diast.', line=dict(color='#7C3AED', width=1.5)), row=1, col=2)
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['saturacion_oxigeno'],
                             mode='lines', name='SpO2', line=dict(color='#0891B2', width=1.5)), row=2, col=1)
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['temperatura'],
                             mode='lines', name='Temp', line=dict(color='#D97706', width=1.5)), row=2, col=2)

    fig.update_layout(height=600, template='simple_white', showlegend=False,
                      margin=dict(t=40, b=30))
    st.plotly_chart(fig, use_container_width=True)

# --- STATS ROW ---
st.markdown("---")
st.subheader("Estadísticas de la Sesión")
stat_cols = st.columns(5)
for idx, (tipo, info) in enumerate(RANGOS.items()):
    vals = df[tipo]
    with stat_cols[idx]:
        with st.container(border=True):
            st.markdown(f"**{info['label']}**")
            m1, m2 = st.columns(2)
            with m1:
                st.metric("Promedio", f"{vals.mean():.1f}")
            with m2:
                st.metric("Actual", f"{vals.iloc[-1]:.1f}")
            st.caption(f"Min: {vals.min():.1f} | Max: {vals.max():.1f}")

# --- FOOTER ---
st.markdown("---")
col1, col2 = st.columns([3, 1])
with col1:
    st.caption(f"Última actualización: {datetime.now().strftime('%H:%M:%S')} — Punto #{st.session_state[TICK_KEY]}")
with col2:
    if st.button("Reiniciar Sesión", use_container_width=True):
        st.session_state.pop(HISTORY_KEY, None)
        st.session_state[TICK_KEY] = 0
        st.rerun()

# --- AUTO-REFRESH ---
if auto_refresh:
    time.sleep(intervalo)
    st.rerun()