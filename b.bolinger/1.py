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
            "num_desviaciones": 2,
            "temporalidad": "1h",  # Agregar temporalidad
            "tiempo_espera": 60,   # Agregar tiempo de espera
            "par": "BTCUSDT"       # Agregar par de criptomonedas
        }
        os.makedirs(os.path.dirname(config_path), exist_ok=True)  # Crear la carpeta si no existe
        with open(config_path, 'w') as json_file:
            json.dump(configuracion, json_file, indent=4)  # Indentar para mejor legibilidad
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

def crear_csv_si_no_existe():
    # Crear el archivo CSV si no existe
    if not os.path.exists('registro_acciones.csv'):
        with open('registro_acciones.csv', mode='w', newline='') as archivo_csv:
            writer = pd.DataFrame(columns=["fecha y hora", "precio", "banda superior", "media móvil", "banda inferior", "acción a tomar"])
            writer.to_csv(archivo_csv, header=True, index=False)

def guardar_en_csv(fecha_hora, precio_actual, banda_superior, media_movil, banda_inferior, accion):
    with open('registro_acciones.csv', mode='a', newline='') as archivo_csv:
        writer = pd.DataFrame([[fecha_hora, precio_actual, banda_superior, media_movil, banda_inferior, accion]], 
                              columns=["fecha y hora", "precio", "banda superior", "media móvil", "banda inferior", "acción a tomar"])
        writer.to_csv(archivo_csv, header=False, index=False)

espera = 0  # Variable global para almacenar los segundos

def obtener_temporalidad(config):
    global espera  # Declarar que vamos a usar la variable global
    temporalidad = config['temporalidad']
    unidad = temporalidad[-1]  # Obtener la última letra para determinar la unidad
    valor = int(temporalidad[:-1])  # Obtener el valor numérico

    # Determinar la conversión a segundos
    if unidad == 's':
        espera = valor
    elif unidad == 'm':
        espera = valor * 60
    elif unidad == 'h':
        espera = valor * 3600
    elif unidad == 'D':
        espera = valor * 86400
    elif unidad == 'S':
        espera = valor * 604800
    elif unidad == 'M':
        espera = valor * 2592000
    else:
        raise ValueError("Unidad de temporalidad no válida")

def analizar_bandas_bollinger_en_tiempo_real(par, temporalidad, tiempo_espera):
    crear_csv_si_no_existe()  # Llamar a la función para crear el CSV si no existe
    configuracion = cargar_configuracion()
    periodo = configuracion['periodo']
    num_desviaciones = configuracion['num_desviaciones']
    
    obtener_temporalidad(configuracion)  # Obtener la temporalidad y establecer la variable espera

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

        # Guardar en CSV solo si se va a comprar o vender
        if accion in ["Vender", "Comprar"]:
            guardar_en_csv(fecha_hora, precio_actual, banda_superior.iloc[-1], media_movil.iloc[-1], banda_inferior.iloc[-1], accion)
        
        time.sleep(espera)  # Esperar el tiempo especificado antes de la siguiente consulta

# Configuración inicial
configuracion = cargar_configuracion()  # Cargar configuración desde el JSON
par = configuracion['par']  # Obtener par de criptomonedas desde la configuración
temporalidad = configuracion['temporalidad']  # Obtener temporalidad desde la configuración
tiempo_espera = configuracion['tiempo_espera']  # Obtener tiempo de espera desde la configuración

# Iniciar análisis
analizar_bandas_bollinger_en_tiempo_real(par, temporalidad, tiempo_espera)
