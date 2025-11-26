import streamlit as st
import pandas as pd
from sqlalchemy import text
from auth import require_auth

require_auth(allowed_roles=['paciente'])

st.set_page_config(page_title="Mis Alertas", page_icon="⚠️", layout="wide")
st.title("⚠️ Mis Alertas Médicas")
st.markdown("---")

try:
    conn = st.connection("postgresql", type="sql")
    
    # Obtener alertas del paciente
    with conn.session as s:
        query = text("""
            SELECT 
                a.id,
                a.timestamp,
                a.tipo_alerta,
                a.mensaje,
                a.leida,
                m.tipo_medicion,
                m.valor,
                m.unidad_medida
            FROM public.alertas a
            INNER JOIN public.mediciones m ON a.medicion_id = m.id
            INNER JOIN public.dispositivos d ON m.dispositivo_id = d.id
            WHERE d.paciente_id = :paciente_id
            ORDER BY a.timestamp DESC
            LIMIT 100
        """)
        df = pd.read_sql(query, s.connection(), params={"paciente_id": st.session_state.paciente_id})
    
    if df.empty:
        st.success("✅ No tienes alertas registradas")
    else:
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            mostrar = st.radio("Mostrar:", ["Todas", "No leídas", "Leídas"])
        with col2:
            tipo_filtro = st.multiselect("Tipo de alerta:", df['tipo_alerta'].unique())
        
        # Aplicar filtros
        df_filtrado = df.copy()
        if mostrar == "No leídas":
            df_filtrado = df_filtrado[df_filtrado['leida'] == False]
        elif mostrar == "Leídas":
            df_filtrado = df_filtrado[df_filtrado['leida'] == True]
        
        if tipo_filtro:
            df_filtrado = df_filtrado[df_filtrado['tipo_alerta'].isin(tipo_filtro)]
        
        # Mostrar alertas
        st.subheader(f"📋 Alertas ({len(df_filtrado)})")
        
        for _, alerta in df_filtrado.iterrows():
            color = "🔴" if not alerta['leida'] else "🟢"
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"{color} **{alerta['tipo_alerta']}** - {alerta['timestamp']}")
                    st.write(alerta['mensaje'])
                    st.caption(f"Medición: {alerta['tipo_medicion']} = {alerta['valor']} {alerta['unidad_medida']}")
                with col2:
                    if not alerta['leida']:
                        if st.button("Marcar como leída", key=f"leer_{alerta['id']}"):
                            with conn.session as s:
                                update_query = text("UPDATE public.alertas SET leida = true WHERE id = :id")
                                s.execute(update_query, {"id": alerta['id']})
                                s.commit()
                            st.rerun()
        
        # Botón para marcar todas como leídas
        if not df_filtrado[df_filtrado['leida'] == False].empty:
            st.markdown("---")
            if st.button("✅ Marcar todas como leídas", type="primary"):
                with conn.session as s:
                    update_all = text("""
                        UPDATE public.alertas a
                        SET leida = true
                        FROM public.mediciones m
                        INNER JOIN public.dispositivos d ON m.dispositivo_id = d.id
                        WHERE a.medicion_id = m.id AND d.paciente_id = :paciente_id
                    """)
                    s.execute(update_all, {"paciente_id": st.session_state.paciente_id})
                    s.commit()
                st.success("✅ Todas las alertas marcadas como leídas")
                st.rerun()
        
except Exception as e:
    st.error(f"Error al cargar alertas: {e}")