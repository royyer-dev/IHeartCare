"""
Simulador de coordenadas GPS para dispositivos de monitoreo cardíaco.
Genera ubicaciones realistas con pequeñas variaciones basadas en el dispositivo.
"""

import random
from typing import Dict, Tuple
from datetime import datetime


# Coordenadas base por defecto (Centro de la Ciudad de México)
DEFAULT_LAT = 19.4326
DEFAULT_LON = -99.1332

# Precisión del simulador (rango de variación en grados)
# ±0.0005 grados ≈ 55 metros
PRECISION_RADIUS = 0.0005


def generar_coordenadas_base(dispositivo_id: int) -> Tuple[float, float]:
    """
    Genera coordenadas base consistentes para un dispositivo.
    Usa el dispositivo_id como seed para reproducibilidad.
    
    Args:
        dispositivo_id: ID del dispositivo para seeding
        
    Returns:
        Tupla (latitude, longitude) base para el dispositivo
    """
    random.seed(dispositivo_id)
    
    # Variación de base por dispositivo (±0.01 grados ≈ 1.1 km)
    lat_offset = random.uniform(-0.01, 0.01)
    lon_offset = random.uniform(-0.01, 0.01)
    
    base_lat = DEFAULT_LAT + lat_offset
    base_lon = DEFAULT_LON + lon_offset
    
    return (base_lat, base_lon)


def generar_coordenadas_actuales(
    dispositivo_id: int, 
    base_lat: float = None, 
    base_lon: float = None
) -> Dict[str, float]:
    """
    Genera coordenadas actuales simuladas para un dispositivo.
    Simula movimiento pequeño alrededor de la ubicación base.
    
    Args:
        dispositivo_id: ID del dispositivo
        base_lat: Latitud base (si None, usa DEFAULT_LAT)
        base_lon: Longitud base (si None, usa DEFAULT_LON)
        
    Returns:
        Dict con keys:
            - lat: Latitud actual (float)
            - lon: Longitud actual (float)
            - precision: Precisión en metros (float)
            - timestamp: Timestamp de generación (str ISO)
    """
    
    if base_lat is None:
        base_lat = DEFAULT_LAT
    if base_lon is None:
        base_lon = DEFAULT_LON
    
    # Seed basado en dispositivo_id + hora (para cambios cada minuto)
    timestamp = datetime.now()
    minute_bucket = int(timestamp.timestamp() / 60)
    seed = dispositivo_id + minute_bucket
    random.seed(seed)
    
    # Generar pequeña variación alrededor de la base
    lat_variation = random.uniform(-PRECISION_RADIUS, PRECISION_RADIUS)
    lon_variation = random.uniform(-PRECISION_RADIUS, PRECISION_RADIUS)
    
    current_lat = base_lat + lat_variation
    current_lon = base_lon + lon_variation
    
    # Calcular precisión aproximada en metros
    # 1 grado ≈ 111 km en el ecuador
    precision_meters = abs(lat_variation) * 111000  # Aproximación simple
    
    return {
        "lat": round(current_lat, 8),
        "lon": round(current_lon, 8),
        "precision": round(precision_meters, 2),
        "timestamp": timestamp.isoformat()
    }


def validar_coordenadas(lat: float, lon: float) -> bool:
    """
    Valida que las coordenadas sean válidas.
    
    Args:
        lat: Latitud (-90 a 90)
        lon: Longitud (-180 a 180)
        
    Returns:
        True si son válidas, False en caso contrario
    """
    return -90 <= lat <= 90 and -180 <= lon <= 180


def calcular_distancia_haversine(
    lat1: float, 
    lon1: float, 
    lat2: float, 
    lon2: float
) -> float:
    """
    Calcula la distancia entre dos coordenadas usando la fórmula de Haversine.
    
    Args:
        lat1, lon1: Primera coordenada
        lat2, lon2: Segunda coordenada
        
    Returns:
        Distancia en kilómetros
    """
    from math import radians, cos, sin, asin, sqrt
    
    # Convertir a radianes
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Fórmula de Haversine
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radio de la tierra en kilómetros
    
    return c * r


if __name__ == "__main__":
    # Pruebas básicas
    print("=== Prueba de Geo Simulator ===\n")
    
    # Probar 3 dispositivos
    for device_id in [1, 2, 3]:
        base_coords = generar_coordenadas_base(device_id)
        current_coords = generar_coordenadas_actuales(device_id, base_coords[0], base_coords[1])
        
        print(f"Dispositivo {device_id}:")
        print(f"  Base: {base_coords[0]:.6f}, {base_coords[1]:.6f}")
        print(f"  Actual: {current_coords['lat']:.6f}, {current_coords['lon']:.6f}")
        print(f"  Precisión: {current_coords['precision']:.2f}m")
        print()
