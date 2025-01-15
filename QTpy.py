import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import pyodbc
from sqlalchemy import create_engine
import math

# Configuración de la conexión a la base de datos
SERVER = '192.168.30.184'
DATABASE = 'DavidDB'
USERNAME = 'Admin'
PASSWORD = 'Root123'
connectionString = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}'

# Crear una conexión de SQLAlchemy usando pyodbc
engine = create_engine(f'mssql+pyodbc:///?odbc_connect={connectionString}')

# Función para cargar datos desde la base de datos
@st.cache_data
def cargar_datos():
    try:
        conn = pyodbc.connect(connectionString)
        query = '''
        SELECT [Normal Pipe Size],
               [GPM at 1ft/Sec],
               [GPM at 2ft/sec],
               [GPM at 4ft/sec],
               [GPM at 8ft/sec],
               [GPM at 10ft/sec],
               [GPM at 12ft/sec]
        FROM [DavidDB].[dbo].[VelToGPM]
        '''

        # Leer los datos en un DataFrame
        df = pd.read_sql(query, conn)
        conn.close()

        # Crear un diccionario con los GPM en 'GPM at 4ft/sec' y sus correspondientes diámetros
        gpm_diameters = {
            row['GPM at 4ft/sec']: row['Normal Pipe Size'] for _, row in df.iterrows()
        }

        return gpm_diameters

    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        return {}

# Cargar los datos y almacenar el diccionario de GPM a diámetros
gpm_diameters = cargar_datos()

# Verificar si el diccionario no está vacío
if gpm_diameters:
    print("Datos cargados exitosamente.")
else:
    print("No se pudieron cargar los datos.")

# Función para graficar conexiones ortogonales
def graficar_conexiones(inicio, final, nodos, equipos, conexiones):
    plt.figure(figsize=(10, 8))

    # Puntos de inicio y final
    inicio_x, inicio_y = inicio
    final_x, final_y = final

    plt.scatter(inicio_x, inicio_y, color='red', label='Inicio', zorder=5)
    plt.text(inicio_x, inicio_y, 'Inicio', fontsize=12, ha='right')
    plt.scatter(final_x, final_y, color='red', label='Fin', zorder=5)
    plt.text(final_x, final_y, 'Fin', fontsize=12, ha='right')

    # Conexiones de nodos
    prev_x, prev_y = inicio
    for nombre, (nodo_x, nodo_y) in nodos.items():
        plt.scatter(nodo_x, nodo_y, color='orange', label='Nodo', zorder=5)
        plt.text(nodo_x, nodo_y, nombre, fontsize=12, ha='right')
        plt.plot([prev_x, nodo_x], [prev_y, prev_y], color='black')
        plt.plot([nodo_x, nodo_x], [prev_y, nodo_y], color='black')
        prev_x, prev_y = nodo_x, nodo_y

    plt.plot([prev_x, final_x], [prev_y, prev_y], color='black')
    plt.plot([final_x, final_x], [prev_y, final_y], color='black')

    # Conexiones de equipos
    for equipo, nodo in conexiones.items():
        equipo_x, equipo_y = equipos[equipo]
        nodo_x, nodo_y = nodos[nodo]

        plt.scatter(equipo_x, equipo_y, color='blue', label='Equipo', zorder=5)
        plt.text(equipo_x, equipo_y, equipo, fontsize=12, ha='right')

        plt.plot([nodo_x, equipo_x], [nodo_y, nodo_y], color='black')
        plt.plot([equipo_x, equipo_x], [nodo_y, equipo_y], color='black')

    # Configuración del gráfico
    plt.xlabel('Coordenada X')
    plt.ylabel('Coordenada Y')
    plt.title('Conexiones Ortogonales')
    plt.grid()
    plt.legend()
    st.pyplot(plt)

# Inicio de la aplicación Streamlit
st.title("Conexiones Ortogonales y Cálculo de Diámetros")
st.sidebar.title("Configuración")

# Entrada de coordenadas
inicio_x = st.sidebar.number_input("Coordenada X del inicio", value=0.0)
inicio_y = st.sidebar.number_input("Coordenada Y del inicio", value=0.0)
final_x = st.sidebar.number_input("Coordenada X del final", value=10.0)
final_y = st.sidebar.number_input("Coordenada Y del final", value=10.0)

inicio = (inicio_x, inicio_y)
final = (final_x, final_y)

# Nodos
num_nodos = st.sidebar.number_input("Número de nodos", min_value=1, max_value=40, value=3)
nodos = {}
for i in range(1, num_nodos + 1):
    nodo_x = st.sidebar.number_input(f"Coordenada X del Nodo {i}", value=0.0, key=f"nodo_x_{i}")
    nodo_y = st.sidebar.number_input(f"Coordenada Y del Nodo {i}", value=0.0, key=f"nodo_y_{i}")
    nodos[f"Nodo {i}"] = (nodo_x, nodo_y)

# Equipos
num_equipos = st.sidebar.number_input("Número de equipos", min_value=1, max_value=40, value=2)
equipos = {}
galonajes = []
for i in range(1, num_equipos + 1):
    equipo_x = st.sidebar.number_input(f"Coordenada X del Equipo {i}", value=0.0, key=f"equipo_x_{i}")
    equipo_y = st.sidebar.number_input(f"Coordenada Y del Equipo {i}", value=0.0, key=f"equipo_y_{i}")
    galonaje = st.sidebar.number_input(f"Galonaje del Equipo {i} (GPM)", value=40.0, key=f"galonaje_{i}")
    equipos[f"Equipo {i}"] = (equipo_x, equipo_y)
    galonajes.append(galonaje)

# Conexiones entre nodos y equipos
conexiones = {}
for equipo in equipos:
    nodo_seleccionado = st.sidebar.selectbox(f"Conectar {equipo} con:", options=list(nodos.keys()), key=f"conexion_{equipo}")
    conexiones[equipo] = nodo_seleccionado

# Medida del Tubo
MedidadelTubo_input = st.sidebar.number_input("Medida que va a tener el tubo", value=0.0)

# Calcular diámetros
galonaje_total = sum(galonajes)
st.write(f"Flujo total requerido: {galonaje_total} GPM")

# Cálculo de ramales secundarios
diametros_ramal_secundario = {}
for i, (nombre_equipo, (equipo_x, equipo_y)) in enumerate(equipos.items(), 1):
    nodo_seleccionado = conexiones[nombre_equipo]
    galonaje_equipo = galonajes[i - 1]
    diametro_secundario = next((d for g, d in sorted(gpm_diameters.items()) if galonaje_equipo <= g), None)
    diametros_ramal_secundario[f"Ramal Secundario {i}"] = {
        "Equipo": nombre_equipo,
        "Nodo": nodo_seleccionado,
        "Galonaje": galonaje_equipo,
        "Diámetro": diametro_secundario,
    }

#--------------------------------------------------------------------------
# Función para obtener el diámetro basado en el galonaje
def obtener_diametro_por_galonaje(galonaje):
    # Convertimos gpm_diameters en una lista de tuplas ordenadas
    gpm_diameters_sorted = sorted(gpm_diameters.items())

    # Recorremos las filas de GPM y comprobamos el rango
    for i in range(1, len(gpm_diameters_sorted)):
        gpm_anterior, diametro_anterior = gpm_diameters_sorted[i - 1]
        gpm_actual, diametro_actual = gpm_diameters_sorted[i]

        # Comprobamos si el galonaje está entre los dos valores
        if gpm_anterior < galonaje <= gpm_actual:
            return diametro_anterior  # Tomamos el diámetro del rango inferior

    # Si el galonaje es mayor que el mayor valor de GPM, devolvemos el último valor
    return gpm_diameters_sorted[-1][1]


# Usar directamente la medida del tubo obtenida previamente
MedidadelTubo = MedidadelTubo_input

# Verificar si la medida del tubo es válida (no cero o negativa)
if MedidadelTubo > 0:
    # ---------------- Ramales Secundarios ----------------
    diametros_ramal_secundario = []
    cantidad_tubos_ramal_secundario = []

    for i, (nombre_equipo, (equipo_x, equipo_y)) in enumerate(equipos.items(), 1):
        nodo_seleccionado = conexiones[nombre_equipo]  # Usar conexión almacenada
        galonaje_equipo = galonajes[i - 1]  # Galonaje correspondiente al equipo

        # Obtener el diámetro para el galonaje usando la función
        diametro_secundario = obtener_diametro_por_galonaje(galonaje_equipo)

        # Calcular la distancia entre el equipo y el nodo
        nodo_x, nodo_y = nodos[nodo_seleccionado]
        distancia_secundario = abs(equipo_x - nodo_x) + abs(equipo_y - nodo_y)

        # Calcular la cantidad de tubos necesarios para esta distancia
        cantidad_tubos = math.ceil(distancia_secundario / MedidadelTubo)

        # Guardar los resultados
        diametros_ramal_secundario.append({
            "Ramal": f"Ramal Secundario {i}",
            "Equipo": nombre_equipo,
            "Nodo": nodo_seleccionado,
            "Galonaje (GPM)": galonaje_equipo,
            "Diametro (pulg)": diametro_secundario,
            "Cantidad de Tubos": cantidad_tubos
        })

    # Crear un DataFrame para los ramales secundarios
    df_ramal_secundario = pd.DataFrame(diametros_ramal_secundario)
    st.write("### Ramales Secundarios")
    st.write(df_ramal_secundario)

    # ---------------- Ramales Principales ----------------
    st.write("### Cálculo de Ramales Principales")

    # Flujo inicial en la bomba
    flujo_restante = galonaje_total

    # Diccionario para almacenar resultados
    diametros_ramal_principal = []
    cantidad_tubos_ramal_principal = []

    # Coordenadas iniciales
    prev_x, prev_y = inicio_x, inicio_y

    for i, (nombre_nodo, (nodo_x, nodo_y)) in enumerate(nodos.items(), 1):
        # Calcular diámetro del tramo actual utilizando la función de cálculo
        diametro_principal = obtener_diametro_por_galonaje(flujo_restante)

        # Calcular la distancia entre el nodo y el nodo anterior
        distancia_principal = abs(nodo_x - prev_x) + abs(nodo_y - prev_y)

        # Calcular la cantidad de tubos necesarios para este tramo
        cantidad_tubos = math.ceil(distancia_principal / MedidadelTubo)

        # Guardar resultados en el diccionario
        diametros_ramal_principal.append({
            "Ramal": f"Ramal Principal {i}",
            "Nodo Inicio": "Inicio" if i == 1 else f"Nodo {i - 1}",
            "Nodo Fin": nombre_nodo,
            "Flujo Restante (GPM)": flujo_restante,
            "Diametro (pulg)": diametro_principal,
            "Cantidad de Tubos": cantidad_tubos
        })

        # Restar el flujo de los equipos conectados al nodo actual
        for nombre_equipo, conexion in conexiones.items():
            if conexion == nombre_nodo:  # Verificar si el equipo está conectado a este nodo
                flujo_restante -= galonajes[int(nombre_equipo.split(" ")[1]) - 1]

        # Actualizar nodo previo
        prev_x, prev_y = nodo_x, nodo_y

    # Crear un DataFrame para los ramales principales
    df_ramal_principal = pd.DataFrame(diametros_ramal_principal)
    st.write(df_ramal_principal)

    # ---------------- Calcular distancias y cantidad de tubos ----------------
    distancias = []
    prev_x, prev_y = inicio_x, inicio_y

    for nombre, (nodo_x, nodo_y) in nodos.items():
        distancia = abs(nodo_x - prev_x) + abs(nodo_y - prev_y)
        distancias.append(distancia)
        prev_x, prev_y = nodo_x, nodo_y

    # Línea final hasta el punto final
    distancia_final = abs(final_x - prev_x) + abs(final_y - prev_y)
    distancias.append(distancia_final)

    # Calcular la cantidad de tubos para el flujo principal
    cantidad_tubos_flujo_principal = [math.ceil(distancia / MedidadelTubo) for distancia in distancias]

    # Crear un DataFrame para las distancias del flujo principal
    df_flujo_principal = pd.DataFrame({
        "Tramo": [f"Tramo {i + 1}" for i in range(len(distancias))],
        "Distancia (unidades)": distancias,
        "Cantidad de Tubos": cantidad_tubos_flujo_principal
    })

    st.write("### Distancias del Flujo Principal")
    st.write(df_flujo_principal)

    # Botón para graficar
    if st.button("Generar Gráfico"):
        graficar_conexiones(inicio, final, nodos, equipos, conexiones)
else:
    st.error("La medida del tubo debe ser mayor que 0.")