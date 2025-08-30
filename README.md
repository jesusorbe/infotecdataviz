# Dashboard de Análisis Territorial

Este proyecto implementa un dashboard interactivo para la visualización de datos sociodemográficos y económicos de México por estado. Utiliza FastAPI para el backend, DuckDB como base de datos y Plotly.js para la renderización de gráficos en el frontend.

---

## 1. Arquitectura de la Aplicación

La aplicación sigue una arquitectura de tres capas desacoplada, lo que facilita su mantenimiento y escalabilidad.

### a. Capa de Datos (Data Layer)

-   **Base de Datos:** Se utiliza un único archivo `censo_denue.duckdb` que contiene dos tablas principales: `censo_manzanas` (datos sociodemográficos del Censo 2020) y `denue` (unidades económicas del DENUE).
-   **Motor:** DuckDB es una base de datos analítica en proceso (in-process) que es extremadamente rápida para consultas agregadas, ideal para este tipo de dashboards.

### b. Capa de Lógica (Backend - API)

-   **Framework:** FastAPI, un moderno y rápido framework de Python para construir APIs.
-   **Responsabilidades:**
    1.  **Conexión a la Base de Datos:** Gestiona la conexión de solo lectura con `censo_denue.duckdb`.
    2.  **Servir la Interfaz de Usuario:** Expone un endpoint raíz (`/`) que renderiza la plantilla `index.html` usando Jinja2.
    3.  **Exponer la API de Datos:** Proporciona un endpoint dinámico (`/api/data/{estado}`) que recibe el nombre de un estado, ejecuta múltiples consultas SQL sobre la base de datos para agregar y calcular los indicadores, y devuelve los resultados en un formato JSON estructurado.

### c. Capa de Presentación (Frontend)

-   **Tecnologías:** HTML5, CSS3 y JavaScript moderno.
-   **Estructura (`index.html`):** Define la estructura semántica del dashboard, incluyendo los contenedores para los KPIs y los gráficos, y el menú desplegable.
-   **Estilos (`style.css`):** Proporciona el diseño visual inspirado en la imagen de referencia, con un layout responsive basado en CSS Grid.
-   **Interactividad (`dashboard.js`):**
    1.  **Renderización de Gráficos:** Utiliza la biblioteca **Plotly.js** para crear los gráficos (barras, dona, pirámide poblacional).
    2.  **Comunicación con la API:** Al seleccionar un estado del menú, el script realiza una petición `fetch` al backend para obtener los datos correspondientes a ese estado.
    3.  **Actualización Dinámica:** Una vez recibidos los datos JSON, el script actualiza los valores de los KPIs y redibuja todos los gráficos con la nueva información, sin necesidad de recargar la página.

---

## 2. Guía de Instalación y Ejecución

Sigue estos pasos para configurar y ejecutar el dashboard en tu máquina local.

### Prerrequisitos

-   Tener instalado **Python 3.8** o superior.
-   Tener el archivo `censo_denue.duckdb`.

### Paso 1: Organizar los archivos

1.  Asegúrate de tener la carpeta `dashboard_project` con todos los archivos que se han generado.
2.  **Importante:** Mueve tu archivo `censo_denue.duckdb` y colócalo en el directorio `DATAVIZ`, al mismo nivel que la carpeta `dashboard_project`.

La estructura final debe verse así:

```
/Users/jesusortiz/Infotec/2025/DATAVIZ/
├── censo_denue.duckdb
└── dashboard_project/
    ├── main.py
    ├── requirements.txt
    ├── static/
    │   ├── css/style.css
    │   └── js/dashboard.js
    └── templates/
        └── index.html
```

### Paso 2: Crear y Activar un Entorno Virtual

Es una buena práctica aislar las dependencias del proyecto. Abre tu terminal y navega dentro de la carpeta `dashboard_project`.

```bash
# Navega al directorio del proyecto
cd /Users/jesusortiz/Infotec/2025/DATAVIZ/dashboard_project

# Crea un entorno virtual llamado 'venv'
python3 -m venv venv

# Activa el entorno virtual
# En macOS/Linux:
source venv/bin/activate
# En Windows:
# .\venv\Scripts\activate
```

### Paso 3: Instalar las Dependencias

Con el entorno virtual activado, instala todas las librerías necesarias usando el archivo `requirements.txt`.

```bash
pip install -r requirements.txt
```

### Paso 4: Ejecutar la Aplicación

Usa `uvicorn` para iniciar el servidor de la aplicación FastAPI.

```bash
uvicorn main:app --reload
```

-   `main`: Se refiere al archivo `main.py`.
-   `app`: Es el objeto `FastAPI()` creado dentro de `main.py`.
-   `--reload`: Hace que el servidor se reinicie automáticamente cada vez que guardes un cambio en el código.

### Paso 5: Acceder al Dashboard

Abre tu navegador web y ve a la siguiente dirección:

[http://127.0.0.1:8000](http://127.0.0.1:8000)

Deberías ver el dashboard cargado con los datos del primer estado de la lista. Ahora puedes usar el menú desplegable para explorar los datos de otros estados.

---

## 3. Detalles de Implementación y Adaptaciones

-   **Pirámide Poblacional:** La imagen de referencia muestra la población en rangos de edad de 5 o 10 años (ej. 20-24, 30-34). La tabla `censo_manzanas` no contiene estos rangos pre-calculados. Para ser fieles a los datos disponibles, la pirámide se ha construido utilizando los grupos de edad que sí están presentes en la base de datos (ej. 0-2, 3-5, 6-11, etc.).

-   **Perfil Educativo:** De manera similar, la imagen distingue entre "Media Superior" y "Superior". La base de datos agrupa estos niveles en una sola columna (`P18YM_PB` - Población de 18 años y más con educación posbásica). El gráfico de dona refleja esta agrupación bajo la etiqueta "Educación Posbásica".

-   **Rendimiento:** Las consultas se realizan sobre la totalidad de las tablas para cada estado. DuckDB es muy eficiente, pero en máquinas con recursos limitados, la carga inicial podría tomar un instante. La conexión a la base de datos se abre en modo `read_only` para prevenir escrituras accidentales y mejorar la concurrencia.
