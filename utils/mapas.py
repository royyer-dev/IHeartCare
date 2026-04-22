"""
Módulo de componentes de mapas para visualización de dispositivos.
Utiliza folium para crear mapas interactivos con ubicaciones de dispositivos.
"""

import folium
from folium import plugins
from typing import List, Dict, Optional, Tuple
import streamlit as st


# Coordenadas por defecto (Centro de la Ciudad de México)
DEFAULT_CENTER = [19.4326, -99.1332]
DEFAULT_ZOOM = 12


def crear_mapa_dispositivos(
    dispositivos: List[Dict],
    zoom_inicial: int = DEFAULT_ZOOM,
    center: Optional[Tuple[float, float]] = None
) -> folium.Map:
    """
    Crea un mapa con todos los dispositivos activos.
    
    Args:
        dispositivos: Lista de dicts con keys:
            - id: ID del dispositivo
            - lat: Latitud
            - lon: Longitud
            - nombre_paciente: Nombre del paciente
            - modelo: Modelo del dispositivo
            - estado: 'activo' o 'inactivo'
        zoom_inicial: Nivel de zoom inicial (default: 12)
        center: Tupla (lat, lon) para centrar el mapa. Si None, centra en promedio
        
    Returns:
        folium.Map con marcadores de dispositivos
    """
    
    if not dispositivos:
        # Mapa vacío centrado en Ciudad de México
        mapa = folium.Map(
            location=DEFAULT_CENTER,
            zoom_start=zoom_inicial,
            tiles="OpenStreetMap"
        )
        return mapa
    
    # Calcular centro del mapa
    if center is None:
        lats = [d['lat'] for d in dispositivos if d.get('lat')]
        lons = [d['lon'] for d in dispositivos if d.get('lon')]
        
        if lats and lons:
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)
            center = [center_lat, center_lon]
        else:
            center = DEFAULT_CENTER
    
    # Crear mapa con tema oscuro
    mapa = folium.Map(
        location=center,
        zoom_start=zoom_inicial,
        tiles="CartoDB positron"  # Tema claro (CartoDB tiene opciones)
    )
    
    # Agregar marcadores para cada dispositivo
    for dispositivo in dispositivos:
        if dispositivo.get('lat') and dispositivo.get('lon'):
            lat = dispositivo['lat']
            lon = dispositivo['lon']
            
            # Determinar color según estado
            color = "#10B981" if dispositivo.get('estado') == 'activo' else "#EF4444"
            
            # Crear popup con información
            popup_text = f"""
            <b>{dispositivo.get('nombre_paciente', 'Sin asignar')}</b><br>
            Modelo: {dispositivo.get('modelo', 'N/A')}<br>
            ID: {dispositivo.get('id', 'N/A')}<br>
            Estado: {dispositivo.get('estado', 'desconocido')}
            """
            
            popup = folium.Popup(popup_text, max_width=250)
            
            # Agregar marcador al mapa
            folium.CircleMarker(
                location=[lat, lon],
                radius=8,
                popup=popup,
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
                weight=2,
                opacity=0.8
            ).add_to(mapa)
            
            # Agregar etiqueta
            folium.Marker(
                location=[lat, lon],
                popup=popup,
                icon=folium.Icon(
                    color="green" if dispositivo.get('estado') == 'activo' else "red",
                    icon="heartbeat"
                )
            ).add_to(mapa)
    
    return mapa


def crear_minimapa(
    lat: float,
    lon: float,
    nombre_paciente: str = "Paciente",
    zoom: int = 15,
    width: str = "100%",
    height: str = "300px"
) -> folium.Map:
    """
    Crea un mini mapa centrado en un punto específico.
    
    Args:
        lat: Latitud del dispositivo
        lon: Longitud del dispositivo
        nombre_paciente: Nombre del paciente para mostrar
        zoom: Nivel de zoom (default: 15, más cercano)
        width: Ancho del mapa (CSS)
        height: Alto del mapa (CSS)
        
    Returns:
        folium.Map pequeño y centrado
    """
    
    mapa = folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles="CartoDB positron",
        width=width,
        height=height
    )
    
    # Marcador centrado
    folium.CircleMarker(
        location=[lat, lon],
        radius=10,
        popup=f"<b>{nombre_paciente}</b><br>Ubicación actual",
        color="#0891B2",  # Cian
        fill=True,
        fillColor="#0891B2",
        fillOpacity=0.8,
        weight=3,
        opacity=1.0
    ).add_to(mapa)
    
    # Agregar círculo de precisión (simulado)
    folium.Circle(
        location=[lat, lon],
        radius=50,  # 50 metros
        color="#0891B2",
        fill=False,
        weight=1,
        opacity=0.5
    ).add_to(mapa)
    
    return mapa


def generar_popup_dispositivo(
    dispositivo_id: int,
    paciente_nombre: str,
    modelo: str,
    mac_address: Optional[str] = None,
    estado: str = "activo"
) -> str:
    """
    Genera HTML para un popup de dispositivo.
    
    Args:
        dispositivo_id: ID del dispositivo
        paciente_nombre: Nombre del paciente
        modelo: Modelo del dispositivo
        mac_address: Dirección MAC (opcional)
        estado: Estado del dispositivo
        
    Returns:
        HTML para usar en popup de folium
    """
    
    html = f"""
    <div style="font-family: Arial; font-size: 12px; width: 200px;">
        <b style="font-size: 14px; color: #1E40AF;">{paciente_nombre}</b><br>
        <hr style="margin: 5px 0;">
        <b>Dispositivo:</b> {modelo}<br>
    """
    
    if mac_address:
        html += f"<b>MAC:</b> {mac_address}<br>"
    
    html += f"""
        <b>ID:</b> {dispositivo_id}<br>
        <b>Estado:</b> <span style="color: {'#10B981' if estado == 'activo' else '#EF4444'};">
            {estado.upper()}
        </span><br>
    </div>
    """
    
    return html


def crear_mapa_clustered(
    dispositivos: List[Dict],
    zoom_inicial: int = DEFAULT_ZOOM,
    center: Optional[Tuple[float, float]] = None
) -> folium.Map:
    """
    Crea un mapa con clustering de marcadores.
    Útil cuando hay muchos dispositivos agrupados.
    
    Args:
        dispositivos: Lista de dicts con info de dispositivos
        zoom_inicial: Nivel de zoom inicial
        center: Tupla (lat, lon) para centrar
        
    Returns:
        folium.Map con clustering
    """
    
    if not dispositivos:
        mapa = folium.Map(location=DEFAULT_CENTER, zoom_start=zoom_inicial)
        return mapa
    
    # Calcular centro
    if center is None:
        lats = [d['lat'] for d in dispositivos if d.get('lat')]
        lons = [d['lon'] for d in dispositivos if d.get('lon')]
        
        if lats and lons:
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)
            center = [center_lat, center_lon]
        else:
            center = DEFAULT_CENTER
    
    mapa = folium.Map(
        location=center,
        zoom_start=zoom_inicial,
        tiles="CartoDB positron"
    )
    
    # Agregar MarkerCluster
    marker_cluster = plugins.MarkerCluster().add_to(mapa)
    
    # Agregar dispositivos al cluster
    for dispositivo in dispositivos:
        if dispositivo.get('lat') and dispositivo.get('lon'):
            lat = dispositivo['lat']
            lon = dispositivo['lon']
            
            popup_html = generar_popup_dispositivo(
                dispositivo.get('id'),
                dispositivo.get('nombre_paciente', 'Sin asignar'),
                dispositivo.get('modelo', 'N/A'),
                dispositivo.get('mac_address'),
                dispositivo.get('estado', 'desconocido')
            )
            
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=250),
                icon=folium.Icon(
                    color="green" if dispositivo.get('estado') == 'activo' else "red",
                    icon="heartbeat"
                )
            ).add_to(marker_cluster)
    
    return mapa


if __name__ == "__main__":
    # Pruebas básicas
    print("Módulo de mapas cargado correctamente")
    print("Funciones disponibles:")
    print("- crear_mapa_dispositivos()")
    print("- crear_minimapa()")
    print("- generar_popup_dispositivo()")
    print("- crear_mapa_clustered()")
