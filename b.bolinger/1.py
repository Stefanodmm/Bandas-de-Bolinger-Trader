import pandas as pd
import requests
import time
import json
import os
from datetime import datetime

def obtener_precio_binance(par, temporalidad):
    url = f'https://api.binance.com/api/v3/klines?symbol={par}&interval={temporalidad}&limit=100'
    response = requests.get(url)
    data = response.json()
    precios = [float(kline[4]) for kline in data]  # Precio de cierre
    return pd.Series(precios)

def cargar_configuracion():
    config_path = 'b.bolinger/configuracion.json'  # Ruta del archivo de configuración
    if not os.path.exists(config_path):
        # Crear archivo JSON con valores predeterminados
        configuracion = {
            "periodo": 20,
            "num_desviaciones": 2
        }
        os.makedirs(os.path.dirname(config_path), exist_ok=True)  # Crear la carpeta si no existe
        with open(config_path, 'w') as json_file:
            json.dump(configuracion, json_file)
    else:
        with open(config_path, 'r') as json_file:
            configuracion = json.load(json_file)
    return configuracion

def calcular_bandas_bollinger(precios, periodo=20, num_desviaciones=2):
    media_movil = precios.rolling(window=periodo).mean()
    desviacion_estandar = precios.rolling(window=periodo).std()
    banda_superior = media_movil + (desviacion_estandar * num_desviaciones)
    banda_inferior = media_movil - (desviacion_estandar * num_desviaciones)
    return banda_superior, media_movil, banda_inferior

def guardar_accion(fecha_hora, precio_actual, accion):
    pass  # Esta función ya no es necesaria

def analizar_bandas_bollinger_en_tiempo_real(par, temporalidad, tiempo_espera):
    configuracion = cargar_configuracion()
    periodo = configuracion['periodo']
    num_desviaciones = configuracion['num_desviaciones']
    
    while True:
        precios = obtener_precio_binance(par, temporalidad)
        banda_superior, media_movil, banda_inferior = calcular_bandas_bollinger(precios, periodo, num_desviaciones)
        precio_actual = precios.iloc[-1]
        fecha_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Determinar si comprar o vender
        if precio_actual > banda_superior.iloc[-1]:
            decision = "Sobrecompra - Considerar vender"
            accion = "Vender"
        elif precio_actual < banda_inferior.iloc[-1]:
            decision = "Sobreventa - Considerar comprar"
            accion = "Comprar"
        else:
            decision = "En rango normal - Mantener posición"
            accion = "Mantener"
        
        # Imprimir información de precios y bandas en forma de columnas
        print(f'[{fecha_hora}]')
        print(f'{"Precio":<10} {"Decisión":<30} {"Banda Superior":<20} {"Media Móvil":<20} {"Banda Inferior":<20}')
        print(f'{precio_actual:<10.2f} {decision:<30} {banda_superior.iloc[-1]:<20.2f} {media_movil.iloc[-1]:<20.2f} {banda_inferior.iloc[-1]:<20.2f}')
        print('-' * 100)
        
        time.sleep(tiempo_espera)  # Esperar el tiempo especificado antes de la siguiente consulta

# Configuración inicial
par = 'BTCUSDT'  # Par de criptomonedas
temporalidad = '1m'  # Temporalidad de 1 minuto
tiempo_espera = 60  # Esperar 60 segundos entre consultas

# Iniciar análisis
analizar_bandas_bollinger_en_tiempo_real(par, temporalidad, tiempo_espera)
