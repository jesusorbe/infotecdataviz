
import duckdb
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json

# --- CONFIGURACIÓN INICIAL ---

# Crear la aplicación FastAPI
app = FastAPI(
    title="Dashboard de Análisis Territorial",
    description="Una API para servir datos sociodemográficos y económicos de México.",
    version="1.0.0"
)

# Montar el directorio 'static' para servir archivos CSS y JS
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configurar Jinja2 para renderizar plantillas HTML
templates = Jinja2Templates(directory="templates")

# Conectarse a la base de datos DuckDB en modo de solo lectura
try:
    con = duckdb.connect(database='censo_denue.duckdb', read_only=True)
except Exception as e:
    print(f"Error al conectar a la base de datos: {e}")
    # Salir o manejar el error como sea apropiado
    exit()


# --- ENDPOINTS DE LA APLICACIÓN ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Endpoint principal que renderiza el dashboard.
    Obtiene la lista de estados de la base de datos para poblar el menú desplegable.
    """
    try:
        # Consultar los nombres de los estados para el menú desplegable
        estados_query = "SELECT DISTINCT NOM_ENT FROM censo_manzanas ORDER BY NOM_ENT"
        estados = con.execute(estados_query).fetchall()
        # Extraer el primer elemento de cada tupla
        lista_estados = [estado[0] for estado in estados]
    except Exception as e:
        print(f"Error al obtener la lista de estados: {e}")
        lista_estados = []

    # Renderizar la plantilla HTML, pasando la lista de estados
    return templates.TemplateResponse("index.html", {"request": request, "estados": lista_estados})


@app.get("/api/data/{estado}")
async def get_dashboard_data(estado: str):
    """
    Endpoint de la API que devuelve los datos del dashboard para un estado específico.
    """
    
    # --- 1. KPIs (Población, Viviendas, Negocios) ---
    try:
        pob_viv_query = """
        SELECT SUM(POBTOT), SUM(VIVTOT) 
        FROM censo_manzanas 
        WHERE NOM_ENT = ?
        """
        poblacion_total, viviendas_totales = con.execute(pob_viv_query, [estado]).fetchone()

        negocios_query = "SELECT COUNT(id) FROM denue WHERE entidad = ?"
        numero_negocios = con.execute(negocios_query, [estado]).fetchone()[0]
        
        kpis = {
            "poblacion_total": f"{poblacion_total:,.0f}" if poblacion_total else "0",
            "viviendas_totales": f"{viviendas_totales:,.0f}" if viviendas_totales else "0",
            "numero_negocios": f"{numero_negocios:,.0f}" if numero_negocios else "0"
        }
    except Exception as e:
        print(f"Error al calcular KPIs: {e}")
        kpis = {"poblacion_total": "Error", "viviendas_totales": "Error", "numero_negocios": "Error"}

    # --- 2. Actividades Económicas Dominantes (Top 5) ---
    try:
        actividades_query = """
        SELECT nombre_act, COUNT(*) AS total 
        FROM denue 
        WHERE entidad = ? 
        GROUP BY nombre_act 
        ORDER BY total DESC 
        LIMIT 5
        """
        actividades_economicas_raw = con.execute(actividades_query, [estado]).fetchall()
        
        # Acortar etiquetas largas para mejor visualización
        actividades_economicas = []
        for nombre, total in actividades_economicas_raw:
            if len(nombre) > 45:
                nombre = nombre[:42] + "..."
            actividades_economicas.append((nombre, total))

    except Exception as e:
        print(f"Error al obtener actividades económicas: {e}")
        actividades_economicas = []

    # --- 3. Perfil Educativo (Población > 15 años) ---
    try:
        educacion_query = """
        SELECT 
            SUM(P15YM_SE) AS sin_escolaridad,
            SUM(P15PRI_IN + P15PRI_CO) AS primaria,
            SUM(P15SEC_IN + P15SEC_CO) AS secundaria,
            SUM(P18YM_PB) AS pos_basica
        FROM censo_manzanas 
        WHERE NOM_ENT = ?
        """
        perfil_educativo = con.execute(educacion_query, [estado]).fetchone()
        
        # Mapeo de resultados a un formato más amigable para el frontend
        if perfil_educativo:
            sin_escolaridad, primaria, secundaria, pos_basica = perfil_educativo
            # Estimación: Se divide el valor de "pos_basica" en dos para representar "Media Superior" y "Superior"
            media_superior = (pos_basica / 2) if pos_basica else 0
            superior = (pos_basica / 2) if pos_basica else 0
            
            educacion_data = {
                "labels": ["Sin Escolaridad", "Primaria", "Secundaria", "Media Superior", "Superior"],
                "values": [sin_escolaridad, primaria, secundaria, media_superior, superior]
            }
        else:
            educacion_data = {
                "labels": ["Sin Escolaridad", "Primaria", "Secundaria", "Media Superior", "Superior"],
                "values": [0, 0, 0, 0, 0]
            }
    except Exception as e:
        print(f"Error al obtener perfil educativo: {e}")
        educacion_data = {"labels": [], "values": []}

    # --- 4. Perfil de Edad y Género (Pirámide Poblacional) ---
    # Nota: Se usan los grupos de edad disponibles en la base de datos.
    try:
        piramide_query = """
        SELECT
            SUM(P_0A2_M), SUM(P_0A2_F),
            SUM(P_3A5_M), SUM(P_3A5_F),
            SUM(P_6A11_M), SUM(P_6A11_F),
            SUM(P_12A14_M), SUM(P_12A14_F),
            SUM(P_15A17_M), SUM(P_15A17_F),
            SUM(P_18A24_M), SUM(P_18A24_F),
            SUM(P_60YMAS_M), SUM(P_60YMAS_F)
        FROM censo_manzanas
        WHERE NOM_ENT = ?
        """
        piramide_data_raw = con.execute(piramide_query, [estado]).fetchone()
        
        hombres = [-val if val else 0 for val in piramide_data_raw[0::2]] # Negativo para la pirámide
        mujeres = [val if val else 0 for val in piramide_data_raw[1::2]]
        
        piramide_data = {
            "labels": ["0-2", "3-5", "6-11", "12-14", "15-17", "18-24", "60+"],
            "hombres": hombres,
            "mujeres": mujeres
        }
    except Exception as e:
        print(f"Error al obtener datos de la pirámide poblacional: {e}")
        piramide_data = {"labels": [], "hombres": [], "mujeres": []}

    # --- Ensamblar y devolver todos los datos ---
    return {
        "kpis": kpis,
        "actividades_economicas": {
            "labels": [row[0] for row in actividades_economicas],
            "values": [row[1] for row in actividades_economicas]
        },
        "perfil_educativo": educacion_data,
        "piramide_poblacional": piramide_data
    }

# --- Cierre de la conexión ---
@app.on_event("shutdown")
def shutdown_event():
    """
    Cierra la conexión a la base de datos cuando la aplicación se detiene.
    """
    con.close()
