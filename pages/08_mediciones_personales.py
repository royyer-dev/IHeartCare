import streamlit as st
import pandas as pd
import altair as alt
from sqlalchemy import text
from auth import require_auth
from sidebar import render_sidebar
from theme import apply_global_theme

require_auth(allowed_roles=['paciente'])
render_sidebar()
apply_global_theme()

st.set_page_config(page_title="Mis Mediciones", page_icon=None, layout="wide")
st.title("Mis Mediciones Biométricas")
st.markdown("---")

try:
    conn = st.connection("postgresql", type="sql")
    
    with conn.session as s:
        query = text("""
            SELECT m.timestamp, m.tipo_medicion, m.valor, m.unidad_medida
            FROM public.mediciones m
            INNER JOIN public.dispositivos d ON m.dispositivo_id = d.id
            WHERE d.paciente_id = :paciente_id
            ORDER BY m.timestamp DESC
            LIMIT 1000
        """)
        df = pd.read_sql(query, s.connection(), params={"paciente_id": st.session_state.paciente_id})
    
    if df.empty:
        st.info("Aún no tienes mediciones registradas")
    else:
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            tipo_seleccionado = st.selectbox("Tipo de Medición", df['tipo_medicion'].unique())
        
        df_filtrado = df[df['tipo_medicion'] == tipo_seleccionado]
        
        # Gráfica con Altair
        chart = alt.Chart(df_filtrado).mark_line(
            point=alt.OverlayMarkDef(color="red", size=25),
            tooltip=True
        ).encode(
            x=alt.X('timestamp:T', title='Fecha y Hora'),
            y=alt.Y('valor:Q', title=f'{tipo_seleccionado} ({df_filtrado["unidad_medida"].iloc[0]})'),
            tooltip=['timestamp:T', 'valor:Q']
        ).interactive()
        
        st.altair_chart(chart, use_container_width=True)
        
        # Tabla de últimas mediciones
        st.subheader("Últimas 10 Mediciones")
        st.dataframe(df_filtrado.head(10), use_container_width=True)
        
except Exception as e:
    st.error(f"Error: {e}")