document.addEventListener('DOMContentLoaded', function () {

    const estadoSelect = document.getElementById('estado-select');
    const estadoTitulo = document.getElementById('estado-titulo');

    // --- ELEMENTOS DEL UI ---
    const kpiPoblacion = document.getElementById('kpi-poblacion');
    const kpiViviendas = document.getElementById('kpi-viviendas');
    const kpiNegocios = document.getElementById('kpi-negocios');

    // --- CONFIGURACIÓN GLOBAL DE PLOTLY ---
    const plotlyConfig = {
        displayModeBar: false, // Ocultar la barra de herramientas de Plotly
        responsive: true
    };

    const plotlyLayout = {
        margin: { l: 120, r: 40, b: 40, t: 40 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: {
            family: 'Roboto, sans-serif',
            color: '#333'
        }
    };

    /**
     * Función principal para actualizar todo el dashboard.
     * @param {string} estado - El nombre del estado seleccionado.
     */
    async function updateDashboard(estado) {
        if (!estado) return;

        // Actualizar título y mostrar estado de carga
        estadoTitulo.textContent = estado;
        setLoadingState(true);

        try {
            // Realizar la petición a la API
            const response = await fetch(`/api/data/${estado}`);
            if (!response.ok) {
                throw new Error(`Error en la petición: ${response.statusText}`);
            }
            const data = await response.json();

            // Actualizar cada componente del dashboard (esto sobreescribirá el estado de carga)
            updateKPIs(data.kpis);
            renderActividadesChart(data.actividades_economicas);
            renderEducacionChart(data.perfil_educativo);
            renderPiramideChart(data.piramide_poblacional);

        } catch (error) {
            console.error('Error al actualizar el dashboard:', error);
            // Mostrar un estado de error en los KPIs si la carga falla
            kpiPoblacion.textContent = 'Error';
            kpiViviendas.textContent = 'Error';
            kpiNegocios.textContent = 'Error';
        }
    }

    /**
     * Muestra el estado de "cargando" en los KPIs.
     * @param {boolean} isLoading - Si es true, muestra "Cargando...".
     */
    function setLoadingState(isLoading) {
        if (!isLoading) return; // No hace nada si isLoading es false
        
        const kpis = [kpiPoblacion, kpiViviendas, kpiNegocios];
        kpis.forEach(kpi => {
            kpi.textContent = 'Cargando...';
        });
    }

    /**
     * Actualiza las tarjetas de KPIs.
     * @param {object} kpis - Objeto con los datos de los KPIs.
     */
    function updateKPIs(kpis) {
        kpiPoblacion.textContent = kpis.poblacion_total || '0';
        kpiViviendas.textContent = kpis.viviendas_totales || '0';
        kpiNegocios.textContent = kpis.numero_negocios || '0';
    }

    /**
     * Renderiza el gráfico de barras de actividades económicas.
     * @param {object} data - Datos para el gráfico.
     */
    function renderActividadesChart(data) {
        const trace = {
            x: data.values.reverse(),
            y: data.labels.reverse(),
            type: 'bar',
            orientation: 'h',
            marker: {
                color: '#28a745'
            },
            hovertemplate: '<b>%{y}</b><br>Negocios: %{x:,.0f}<extra></extra>'
        };
        // Se ajusta el margen izquierdo para dar espacio a las etiquetas
        const layout = { ...plotlyLayout, margin: { l: 250, r: 20, b: 40, t: 40 }, yaxis: { automargin: false } };
        Plotly.newPlot('chart-actividades', [trace], layout, plotlyConfig);
    }

    /**
     * Renderiza el gráfico de dona del perfil educativo.
     * @param {object} data - Datos para el gráfico.
     */
    function renderEducacionChart(data) {
        const trace = {
            labels: data.labels,
            values: data.values,
            type: 'pie',
            hole: .6, // Para hacerlo un gráfico de dona
            marker: {
                colors: ['#ff6384', '#36a2eb', '#ffce56', '#4bc0c0', '#9966ff']
            },
            // Mostrar porcentajes dentro de la dona
            textinfo: 'percent',
            textposition: 'inside',
            insidetextfont: { color: '#fff', size: 14 },
            hovertemplate: '<b>%{label}</b><br>Población: %{value:,.0f}<br>%{percent}<extra></extra>',
            sort: false // Asegura que los segmentos respeten el orden de los datos
        };
        const layout = { ...plotlyLayout, margin: { l: 40, r: 40, b: 40, t: 40 }, legend: {orientation: 'h', y: -0.2, yanchor: 'top'} };
        Plotly.newPlot('chart-educacion', [trace], layout, plotlyConfig);
    }

    /**
     * Renderiza la pirámide poblacional.
     * @param {object} data - Datos para el gráfico.
     */
    function renderPiramideChart(data) {
        // Preparar datos para el hover (siempre positivos)
        const hombres_text_hover = data.hombres.map(v => Math.abs(v));

        const traceHombres = {
            y: data.labels,
            x: data.hombres, // Usa valores negativos para la dirección
            text: hombres_text_hover, // Usa valores absolutos para el texto del hover
            name: 'Hombres',
            type: 'bar',
            orientation: 'h',
            marker: {
                color: '#36a2eb'
            },
            hovertemplate: 'Población: %{text:,.0f}<extra></extra>'
        };

        const traceMujeres = {
            y: data.labels,
            x: data.mujeres,
            name: 'Mujeres',
            type: 'bar',
            orientation: 'h',
            marker: {
                color: '#ff6384'
            },
            hovertemplate: 'Población: %{x:,.0f}<extra></extra>'
        };

        // Calcular el rango máximo para un eje simétrico
        const maxVal = Math.max(...data.hombres.map(Math.abs), ...data.mujeres);
        const axisRange = [-maxVal, maxVal];

        const layout = {
            ...plotlyLayout,
            barmode: 'relative',
            xaxis: {
                range: axisRange,
                tickvals: Plotly.d3.range(-maxVal, maxVal, maxVal / 3).concat([maxVal]),
                ticktext: Plotly.d3.range(-maxVal, maxVal, maxVal / 3).concat([maxVal]).map(v => `${Math.abs(v/1000).toFixed(0)}k`),
                title: 'Población',
            },
            yaxis: { automargin: true },
            legend: { x: 0.5, xanchor: 'center', y: -0.2, orientation: 'h' }
        };

        Plotly.newPlot('chart-piramide', [traceHombres, traceMujeres], layout, plotlyConfig);
    }

    // --- EVENT LISTENERS ---
    estadoSelect.addEventListener('change', (e) => {
        updateDashboard(e.target.value);
    });

    // --- INICIALIZACIÓN ---
    // Cargar datos para el primer estado en la lista al cargar la página
    if (estadoSelect.options.length > 0) {
        updateDashboard(estadoSelect.value);
    }
});
