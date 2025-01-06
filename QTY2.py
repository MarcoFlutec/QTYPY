import matplotlib.pyplot as plt
import math  # Importar la librería math para usar ceil
import pyodbc
import pandas as pd  # Asegúrate de importar pandas
from sqlalchemy import create_engine
import openpyxl
from openpyxl.drawing.image import Image

# Configuración de la conexión a la base de datos
SERVER = '192.168.30.184'
DATABASE = 'DavidDB'
USERNAME = 'Admin'
PASSWORD = 'Root123'
connectionString = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}'

# Crear una conexión de SQLAlchemy usando pyodbc
engine = create_engine(f'mssql+pyodbc:///?odbc_connect={connectionString}')

# Cargar datos desde la base de datos
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

    # Crear un diccionario con los galones y los diámetros
    # Asumimos que la columna 'Normal Pipe Size' tiene los diámetros y las demás columnas tienen los GPM correspondientes.
    gpm_diameters = {
        row['GPM at 4ft/sec']: row['Normal Pipe Size'] for _, row in df.iterrows()
    }

except Exception as e:
    print(f"Error al conectar a la base de datos: {e}")

# Pedir coordenadas de inicio y final
inicio_x = int(input("Introduce la coordenada x del punto de Inicio: "))
inicio_y = int(input("Introduce la coordenada y del punto de Inicio: "))
final_x = int(input("Introduce la coordenada x del punto Final: "))
final_y = int(input("Introduce la coordenada y del punto Final: "))

# Obtener el número de nodos
num_nodos = int(input("¿Cuántos nodos quieres? "))

# Pedir las coordenadas de los nodos
nodos = {}
for i in range(1, num_nodos + 1):
    nodo_x = int(input(f"Introduce la coordenada x del Nodo {i}: "))
    nodo_y = int(input(f"Introduce la coordenada y del Nodo {i}: "))
    nodos[f"Nodo {i}"] = (nodo_x, nodo_y)

# Obtener el número de equipos
num_equipos = int(input("¿Cuántos equipos quieres? "))

# Pedir las coordenadas de los equipos
equipos = {}
for i in range(1, num_equipos + 1):
    equipo_x = int(input(f"Introduce la coordenada x del Equipo {i}: "))
    equipo_y = int(input(f"Introduce la coordenada y del Equipo {i}: "))
    equipos[f"Equipo {i}"] = (equipo_x, equipo_y)

# Graficar puntos y conexiones
plt.figure(figsize=(10, 8))

# Graficar puntos y conexiones
plt.figure(figsize=(10, 8))

# Graficar el punto de inicio y final
plt.scatter(inicio_x, inicio_y, color='red', label='Inicio', zorder=5)
plt.text(inicio_x, inicio_y, 'Inicio', fontsize=12, ha='right')
plt.scatter(final_x, final_y, color='red', label='Fin', zorder=5)
plt.text(final_x, final_y, 'Fin', fontsize=12, ha='right')

# Conectar nodos con inicio y final usando líneas rectas y calcular distancias
distancias = []
prev_x, prev_y = inicio_x, inicio_y

for nombre, (nodo_x, nodo_y) in nodos.items():
    plt.scatter(nodo_x, nodo_y, color='red', label='Nodo', zorder=5)
    plt.text(nodo_x, nodo_y, nombre, fontsize=12, ha='right')
    plt.plot([prev_x, nodo_x], [prev_y, prev_y], color='black')
    plt.plot([nodo_x, nodo_x], [prev_y, nodo_y], color='black')
    distancia = abs(nodo_x - prev_x) + abs(nodo_y - prev_y)
    distancias.append(distancia)
    prev_x, prev_y = nodo_x, nodo_y

# Línea final hasta el punto final
plt.plot([prev_x, final_x], [prev_y, prev_y], color='black')
plt.plot([final_x, final_x], [prev_y, final_y], color='black')
distancia_final = abs(final_x - prev_x) + abs(final_y - prev_y)
distancias.append(distancia_final)

# Conectar nodos con equipos usando líneas rectas y calcular distancias
distancias_nodo_equipo = []
for nombre_equipo, (equipo_x, equipo_y) in equipos.items():
    plt.scatter(equipo_x, equipo_y, color='blue', label='Equipo', zorder=5)
    plt.text(equipo_x, equipo_y, nombre_equipo, fontsize=12, ha='right')
    nodo_seleccionado = input(f"¿Con qué nodo quieres conectar el {nombre_equipo}? ")
    if f"Nodo {nodo_seleccionado}" in nodos:
        nodo_x, nodo_y = nodos[f"Nodo {nodo_seleccionado}"]
        plt.plot([nodo_x, equipo_x], [nodo_y, nodo_y], color='black')
        plt.plot([equipo_x, equipo_x], [nodo_y, equipo_y], color='black')
        distancia_equipo = abs(nodo_x - equipo_x) + abs(nodo_y - equipo_y)
        distancias_nodo_equipo.append(distancia_equipo)

# Guardar el gráfico como imagen PNG
grafico_path = 'grafico_conexiones.png'
plt.savefig(grafico_path)

# Calcular la distancia total del flujo principal
distancia_total_flujo_principal = sum(distancias)

# Cálculo de la cantidad necesaria de tubos para el flujo principal (dividiendo entre 6 y redondeando hacia arriba)
cantidad_tubos_flujo_principal = [math.ceil(distancia / 6) for distancia in distancias]

# Cálculo de la cantidad necesaria de tubos para el arreglo de distancias nodo a equipo (dividiendo entre 6 y redondeando hacia arriba)
cantidad_tubos_nodo_equipo = [math.ceil(distancia / 6) for distancia in distancias_nodo_equipo]

# Leyenda y visualización
plt.xlabel('Coordenada X')
plt.ylabel('Coordenada Y')
plt.title('Conexiones Ortogonales entre Inicio, Nodos, Equipos y Final')
plt.grid()
plt.legend(['Nodo', 'Equipo'])
plt.show()

# Mostrar las distancias calculadas
print("\nDistancias entre puntos del flujo principal:")
for i, d in enumerate(distancias, 1):
    print(f"Tramo {i}: {d} unidades")

print("\nDistancias entre nodos y equipos:")
for i, d in enumerate(distancias_nodo_equipo, 1):
    print(f"Tramo {i} (Nodo a Equipo): {d} unidades")

# Mostrar los arreglos de distancias
print("\nArreglo de distancias (flujo principal):", distancias)
print("Arreglo de distancias (nodo a equipo):", distancias_nodo_equipo)

# Mostrar la distancia total del flujo principal
print("\nDistancia total del flujo principal:", distancia_total_flujo_principal, "unidades")

# Mostrar la cantidad necesaria de tubos para el flujo principal
print("\nCantidad de tubos necesarios para el flujo principal (redondeados hacia arriba):", cantidad_tubos_flujo_principal)

# Mostrar la cantidad necesaria de tubos para el nodo a equipo
print("\nCantidad de tubos necesarios para el nodo a equipo (redondeados hacia arriba):", cantidad_tubos_nodo_equipo)

#---------------------------------------------Calculo De Diametros---------------------------------------------------

# Función para calcular el diámetro basado en el GPM
def calcular_diametro(gpm):
    # Ordenar los valores de GPM en orden ascendente
    gpm_keys = sorted(gpm_diameters.keys())
    for i in range(len(gpm_keys) - 1):
        gpm_lower, gpm_upper = gpm_keys[i], gpm_keys[i + 1]
        if gpm_lower <= gpm < gpm_upper:
            return gpm_diameters[gpm_lower]
    return gpm_diameters[gpm_keys[-1]]  # Retornar el diámetro más alto

# Pedir el número de equipos
num_equipos = int(input("Introduce el número de equipos: "))

# Listas para almacenar datos de los ramales principales y secundarios
ramales_principales = []
ramales_secundarios = []

# Ingresar los galonajes de los equipos
galonajes = []
for i in range(num_equipos):
    galones = float(input(f"Introduce el galonaje del Equipo {num_equipos - i}: "))
    galonajes.append(galones)

# Calcular el galonaje total de la bomba (sumando desde el último equipo al primero)
galonaje_bomba = 0

# Calcular los resultados para cada ramal
for i, galones in enumerate(reversed(galonajes), start=1):
    galonaje_bomba += galones
    diametro = calcular_diametro(galonaje_bomba)

    # Para ramales principales, usamos la cantidad de tubos calculada para el flujo principal
    cantidad_tubos_principal = cantidad_tubos_flujo_principal[i - 1]

    # Para ramales secundarios, usamos la cantidad de tubos calculada para el nodo a equipo
    cantidad_tubos_secundario = cantidad_tubos_nodo_equipo[i - 1]

    # Añadir ramal principal
    ramales_principales.append([f"Ramal Principal {i}", diametro, cantidad_tubos_principal])

    # Añadir ramal secundario
    ramales_secundarios.append([f"Ramal Secundario {i}", calcular_diametro(galones), cantidad_tubos_secundario])

# Crear un DataFrame con los resultados
resultados = []

# Añadir los resultados de los ramales principales
for ramal in ramales_principales:
    resultados.append([ramal[0], ramal[1], ramal[2]])

# Añadir los resultados de los ramales secundarios
for ramal in ramales_secundarios:
    resultados.append([ramal[0], ramal[1], ramal[2]])

# Crear un DataFrame de pandas
df_resultados = pd.DataFrame(resultados, columns=['Ramal', 'Diametro', 'Cantidad de tubos'])

# Guardar el DataFrame en un archivo Excel
archivo_excel = 'resultados_ramales.xlsx'
df_resultados.to_excel(archivo_excel, index=False)

# Abrir el archivo Excel con openpyxl
wb = openpyxl.load_workbook(archivo_excel)
ws = wb.active

# Insertar la imagen en la hoja de trabajo
img = Image(grafico_path)
ws.add_image(img, 'E5')

# Guardar el archivo Excel con la imagen insertada
wb.save(archivo_excel)

print(f"Los resultados han sido guardados en {archivo_excel}")

