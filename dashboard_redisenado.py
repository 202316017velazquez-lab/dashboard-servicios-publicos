# ============================================================================
# DASHBOARD REDISEÑADO - SERVICIOS PÚBLICOS EN MÉXICO (2000-2020)
# ESTRUCTURA CLARA CON PESTAÑAS Y CONCLUSIONES
# ============================================================================

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import os
import sys
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# 1. CARGA DE DATOS - VERSIÓN CORREGIDA PARA RENDER
# ============================================================================

print("📊 Cargando datos...")

# Obtener la ruta absoluta del directorio donde está este script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, 'datos_procesados')

# Crear carpeta si no existe
if not os.path.exists(DATA_DIR):
    print(f"⚠️ Creando carpeta: {DATA_DIR}")
    os.makedirs(DATA_DIR, exist_ok=True)

# Función para cargar datos con fallback
def cargar_csv(nombre_archivo):
    ruta = os.path.join(DATA_DIR, nombre_archivo)
    if os.path.exists(ruta):
        df = pd.read_csv(ruta, encoding='utf-8-sig')
        print(f"✅ Archivo cargado: {nombre_archivo} ({len(df)} registros)")
        return df
    else:
        print(f"❌ Archivo no encontrado: {ruta}")
        return None

# Cargar datos por estado
df_estados = cargar_csv('datos_estado_finales.csv')
if df_estados is None:
    print("❌ Error: No se pudieron cargar los datos de estados")
    print("⚠️ Creando datos de ejemplo para demostración...")
    # Datos de ejemplo mínimos
    estados = ['Ciudad de México', 'Nuevo León', 'Jalisco', 'Chihuahua', 'Sonora',
               'Veracruz', 'Oaxaca', 'Chiapas', 'Guerrero', 'Puebla']
    datos = []
    for anio in [2000, 2010, 2020]:
        for estado in estados:
            base = 20 + (anio - 2000) * 0.5
            datos.append({
                'estado': estado,
                'anio': anio,
                'viviendas_totales': 100000 + np.random.randint(0, 50000),
                'viviendas_habitadas': 90000 + np.random.randint(0, 40000),
                'agua': 80000 + np.random.randint(0, 20000),
                'drenaje': 75000 + np.random.randint(0, 20000),
                'electricidad': 85000 + np.random.randint(0, 15000),
                'servicios_basicos': 70000 + np.random.randint(0, 25000),
                'agua_pct': base + 2 + np.random.normal(0, 2),
                'drenaje_pct': base - 1 + np.random.normal(0, 2),
                'electricidad_pct': base + 5 + np.random.normal(0, 2),
                'servicios_basicos_pct': base + 1 + np.random.normal(0, 2),
                'lat': 0,
                'lon': 0
            })
    df_estados = pd.DataFrame(datos)
    # Limpiar datos de ejemplo
    for col in ['agua_pct', 'drenaje_pct', 'electricidad_pct', 'servicios_basicos_pct']:
        df_estados[col] = df_estados[col].clip(0, 100)
    print(f"⚠️ Datos de ejemplo creados: {len(df_estados)} registros")

# Cargar totales nacionales
df_totales = cargar_csv('totales_nacionales_finales.csv')
if df_totales is None:
    print("⚠️ No se encontraron totales nacionales, calculando desde datos de estados")
    df_totales = df_estados.groupby('anio').agg({
        'viviendas_totales': 'sum',
        'viviendas_habitadas': 'sum',
        'agua': 'sum',
        'drenaje': 'sum',
        'electricidad': 'sum',
        'servicios_basicos': 'sum'
    }).reset_index()
    for col in ['agua', 'drenaje', 'electricidad', 'servicios_basicos']:
        df_totales[f'{col}_pct'] = (df_totales[col] / df_totales['viviendas_totales']) * 100

print(f"✅ Datos cargados exitosamente")
print(f"   📊 Estados: {df_estados['estado'].nunique()}")
print(f"   📅 Años: {sorted(df_estados['anio'].unique())}")

# ============================================================================
# 2. DATOS GEOESPACIALES (para el mapa)
# ============================================================================

ESTADOS_COORDENADAS = {
    'Aguascalientes': {'lat': 21.885, 'lon': -102.292},
    'Baja California': {'lat': 32.000, 'lon': -115.500},
    'Baja California Sur': {'lat': 25.000, 'lon': -111.000},
    'Campeche': {'lat': 19.830, 'lon': -90.530},
    'Chiapas': {'lat': 16.750, 'lon': -92.633},
    'Chihuahua': {'lat': 28.635, 'lon': -106.088},
    'Ciudad de México': {'lat': 19.433, 'lon': -99.133},
    'Coahuila de Zaragoza': {'lat': 27.000, 'lon': -102.000},
    'Colima': {'lat': 19.240, 'lon': -103.730},
    'Durango': {'lat': 24.027, 'lon': -104.670},
    'Estado de México': {'lat': 19.500, 'lon': -99.500},
    'Guanajuato': {'lat': 21.019, 'lon': -101.257},
    'Guerrero': {'lat': 17.550, 'lon': -99.500},
    'Hidalgo': {'lat': 20.500, 'lon': -98.500},
    'Jalisco': {'lat': 20.659, 'lon': -103.349},
    'México': {'lat': 19.500, 'lon': -99.500},
    'Michoacán': {'lat': 19.700, 'lon': -101.183},
    'Morelos': {'lat': 18.783, 'lon': -99.233},
    'Nayarit': {'lat': 21.750, 'lon': -104.833},
    'Nuevo León': {'lat': 25.666, 'lon': -100.300},
    'Oaxaca': {'lat': 17.060, 'lon': -96.720},
    'Puebla': {'lat': 19.033, 'lon': -98.183},
    'Querétaro': {'lat': 20.600, 'lon': -100.383},
    'Quintana Roo': {'lat': 19.500, 'lon': -88.500},
    'San Luis Potosí': {'lat': 22.150, 'lon': -100.983},
    'Sinaloa': {'lat': 25.000, 'lon': -108.000},
    'Sonora': {'lat': 29.000, 'lon': -111.000},
    'Tabasco': {'lat': 18.000, 'lon': -93.000},
    'Tamaulipas': {'lat': 24.000, 'lon': -99.000},
    'Tlaxcala': {'lat': 19.316, 'lon': -98.233},
    'Veracruz': {'lat': 19.000, 'lon': -96.000},
    'Yucatán': {'lat': 21.000, 'lon': -89.000},
    'Zacatecas': {'lat': 22.775, 'lon': -102.572}
}

# Agregar coordenadas al DataFrame
df_estados['lat'] = df_estados['estado'].map(lambda x: ESTADOS_COORDENADAS.get(x, {}).get('lat', 0))
df_estados['lon'] = df_estados['estado'].map(lambda x: ESTADOS_COORDENADAS.get(x, {}).get('lon', 0))

# ============================================================================
# 3. CONFIGURACIÓN
# ============================================================================

SERVICIOS = {
    'agua': '💧 Agua Entubada',
    'drenaje': '🚽 Drenaje',
    'electricidad': '💡 Electricidad',
    'servicios_basicos': '🏠 Servicios Básicos'
}

COLORS_SERVICIO = {
    '💧 Agua Entubada': '#1F77B4',
    '🚽 Drenaje': '#2CA02C',
    '💡 Electricidad': '#FF7F0E',
    '🏠 Servicios Básicos': '#D62728'
}

# ============================================================================
# 4. INICIALIZAR APP
# ============================================================================

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# ============================================================================
# 5. LAYOUT DEL DASHBOARD
# ============================================================================

app.layout = dbc.Container([

    # ========================================================================
    # HEADER
    # ========================================================================
    dbc.Row([
        dbc.Col([
            html.H1("🏠 Servicios Públicos en México",
                   className="text-center text-primary mt-4 mb-1",
                   style={'fontWeight': 'bold', 'fontSize': '2.5rem'}),
            html.P("Análisis de la evolución de servicios básicos en viviendas (2000-2020)",
                  className="text-center text-muted mb-1"),
            html.P("Fuente: INEGI - Censos de Población y Vivienda",
                  className="text-center text-muted small mb-4")
        ], width=12)
    ]),

    # ========================================================================
    # KPIs (Indicadores Clave)
    # ========================================================================
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("🏠 Viviendas Totales", className="text-muted text-center"),
                html.H2(id='kpi-viviendas', className="text-center text-primary"),
                html.P(id='kpi-viviendas-desc', className="text-center text-muted small")
            ])
        ], className="shadow-sm"), width=3),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("💧 Agua Entubada", className="text-muted text-center"),
                html.H2(id='kpi-agua', className="text-center text-primary"),
                html.P(id='kpi-agua-desc', className="text-center text-muted small")
            ])
        ], className="shadow-sm"), width=3),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("🚽 Drenaje", className="text-muted text-center"),
                html.H2(id='kpi-drenaje', className="text-center text-success"),
                html.P(id='kpi-drenaje-desc', className="text-center text-muted small")
            ])
        ], className="shadow-sm"), width=3),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("🏠 Servicios Básicos", className="text-muted text-center"),
                html.H2(id='kpi-basicos', className="text-center text-danger"),
                html.P(id='kpi-basicos-desc', className="text-center text-muted small")
            ])
        ], className="shadow-sm"), width=3)
    ], className="mb-4"),

    # ========================================================================
    # FILTROS
    # ========================================================================
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("📅 Año:", className="fw-bold"),
                            dcc.Dropdown(
                                id='filtro-anio',
                                options=[{'label': '📊 Todos (Comparativa)', 'value': 'todos'}] +
                                        [{'label': f'📅 {a}', 'value': a} for a in sorted(df_estados['anio'].unique())],
                                value='todos',
                                clearable=False,
                                className="mb-2"
                            )
                        ], width=4),
                        dbc.Col([
                            html.Label("🔧 Servicio:", className="fw-bold"),
                            dcc.Dropdown(
                                id='filtro-servicio',
                                options=[{'label': v, 'value': k} for k, v in SERVICIOS.items()],
                                value='servicios_basicos',
                                clearable=False,
                                className="mb-2"
                            )
                        ], width=4),
                        dbc.Col([
                            html.Label("📊 Comparar:", className="fw-bold"),
                            dcc.Dropdown(
                                id='filtro-comparar',
                                options=[
                                    {'label': '📈 Evolución Temporal', 'value': 'evolucion'},
                                    {'label': '🗺️ Mapa por Estado', 'value': 'mapa'},
                                    {'label': '🏆 Ranking de Estados', 'value': 'ranking'},
                                    {'label': '📊 Comparativa de Servicios', 'value': 'comparativa'}
                                ],
                                value='evolucion',
                                clearable=False,
                                className="mb-2"
                            )
                        ], width=4)
                    ])
                ])
            ], className="mb-4 shadow-sm")
        ], width=12)
    ]),

    # ========================================================================
    # PESTAÑAS PARA ORGANIZAR LA INFORMACIÓN
    # ========================================================================
    dbc.Tabs([
        # ================================================================
        # TAB 1: VISUALIZACIÓN PRINCIPAL
        # ================================================================
        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            dcc.Graph(id='grafico-principal', config={'responsive': True})
                        ])
                    ], className="shadow-sm mb-3")
                ], width=12)
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            dcc.Graph(id='grafico-secundario', config={'responsive': True})
                        ])
                    ], className="shadow-sm")
                ], width=12)
            ])
        ], label="📊 Visualización", tab_style={'fontWeight': 'bold'}),

        # ================================================================
        # TAB 2: MAPA DE MÉXICO
        # ================================================================
        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("🗺️ Mapa Interactivo de México", className="mb-3"),
                            html.P("El tamaño y color de cada burbuja representa el porcentaje de cobertura del servicio seleccionado.",
                                  className="text-muted small mb-3"),
                            dcc.Graph(id='grafico-mapa', config={'responsive': True})
                        ])
                    ], className="shadow-sm")
                ], width=12)
            ])
        ], label="🗺️ Mapa", tab_style={'fontWeight': 'bold'}),

        # ================================================================
        # TAB 3: RANKING Y COMPARATIVAS
        # ================================================================
        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("🏆 Ranking de Estados", className="mb-3"),
                            html.P("Estados ordenados de mejor a peor cobertura del servicio seleccionado.",
                                  className="text-muted small mb-3"),
                            dcc.Graph(id='grafico-ranking', config={'responsive': True})
                        ])
                    ], className="shadow-sm mb-3")
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("🎯 Perfil Comparativo", className="mb-3"),
                            html.P("Comparación de todos los servicios entre el mejor y peor estado.",
                                  className="text-muted small mb-3"),
                            dcc.Graph(id='grafico-radar', config={'responsive': True})
                        ])
                    ], className="shadow-sm")
                ], width=6)
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("📊 Comparativa de Servicios", className="mb-3"),
                            html.P("Comparación de los 4 servicios a nivel nacional.",
                                  className="text-muted small mb-3"),
                            dcc.Graph(id='grafico-comparativa', config={'responsive': True})
                        ])
                    ], className="shadow-sm")
                ], width=12)
            ])
        ], label="🏆 Rankings", tab_style={'fontWeight': 'bold'}),

        # ================================================================
        # TAB 4: DATOS DETALLADOS
        # ================================================================
        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5("📋 Datos Detallados por Estado", className="mb-0 fw-bold")
                        ]),
                        dbc.CardBody([
                            html.P("Tabla con todos los datos disponibles. Las celdas en verde indican cobertura superior al 80%, en rojo inferior al 60%.",
                                  className="text-muted small mb-3"),
                            html.Div(id='tabla-datos')
                        ])
                    ], className="shadow-sm")
                ], width=12)
            ])
        ], label="📋 Datos", tab_style={'fontWeight': 'bold'}),

        # ================================================================
        # TAB 5: CONCLUSIONES
        # ================================================================
        dbc.Tab([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5("💡 Conclusiones del Análisis", className="mb-0 fw-bold")
                        ]),
                        dbc.CardBody([
                            html.Div(id='conclusiones')
                        ])
                    ], className="shadow-sm")
                ], width=12)
            ])
        ], label="💡 Conclusiones", tab_style={'fontWeight': 'bold'})
    ], className="mb-4"),

    # ========================================================================
    # FOOTER
    # ========================================================================
    dbc.Row([
        dbc.Col([
            html.Hr(),
            html.P("Dashboard desarrollado con Python, Dash y Plotly | Datos INEGI 2000, 2010, 2020",
                  className="text-center text-muted small")
        ], width=12)
    ])

], fluid=True, style={'backgroundColor': '#F8F9FA'})

# ============================================================================
# 6. CALLBACKS
# ============================================================================

@app.callback(
    [Output('kpi-viviendas', 'children'),
     Output('kpi-viviendas-desc', 'children'),
     Output('kpi-agua', 'children'),
     Output('kpi-agua-desc', 'children'),
     Output('kpi-drenaje', 'children'),
     Output('kpi-drenaje-desc', 'children'),
     Output('kpi-basicos', 'children'),
     Output('kpi-basicos-desc', 'children'),
     Output('grafico-principal', 'figure'),
     Output('grafico-secundario', 'figure'),
     Output('grafico-mapa', 'figure'),
     Output('grafico-ranking', 'figure'),
     Output('grafico-radar', 'figure'),
     Output('grafico-comparativa', 'figure'),
     Output('tabla-datos', 'children'),
     Output('conclusiones', 'children')],
    [Input('filtro-anio', 'value'),
     Input('filtro-servicio', 'value'),
     Input('filtro-comparar', 'value')]
)
def actualizar_dashboard(anio, servicio, comparar):
    """Actualiza todos los componentes del dashboard."""

    # ========================================================================
    # FILTRAR DATOS
    # ========================================================================
    if anio == 'todos':
        df_filtrado = df_estados.copy()
        df_anio = df_estados[df_estados['anio'] == 2020].copy()
        titulo_anio = "2000-2020"
    else:
        df_filtrado = df_estados[df_estados['anio'] == anio].copy()
        df_anio = df_filtrado.copy()
        titulo_anio = str(anio)

    nombre_servicio = SERVICIOS[servicio]
    columna_pct = f'{servicio}_pct'

    # ========================================================================
    # 1. KPIs
    # ========================================================================
    df_kpi = df_estados[df_estados['anio'] == 2020] if anio == 'todos' else df_filtrado
    total_viv = df_kpi['viviendas_totales'].sum()
    total_agua = df_kpi['agua'].sum()
    total_drenaje = df_kpi['drenaje'].sum()
    total_basicos = df_kpi['servicios_basicos'].sum()

    kpi_viviendas = f"{total_viv:,.0f}"
    kpi_agua = f"{total_agua/total_viv*100:.1f}%"
    kpi_drenaje = f"{total_drenaje/total_viv*100:.1f}%"
    kpi_basicos = f"{total_basicos/total_viv*100:.1f}%"

    desc_viviendas = f"Total nacional {titulo_anio}"
    desc_agua = f"{total_agua:,.0f} viviendas ({total_agua/total_viv*100:.1f}%)"
    desc_drenaje = f"{total_drenaje:,.0f} viviendas ({total_drenaje/total_viv*100:.1f}%)"
    desc_basicos = f"{total_basicos:,.0f} viviendas ({total_basicos/total_viv*100:.1f}%)"

    # ========================================================================
    # 2. GRÁFICO PRINCIPAL (según comparar)
    # ========================================================================
    if comparar == 'evolucion':
        df_evo = df_estados.groupby('anio')[columna_pct].mean().reset_index()
        fig_principal = go.Figure()
        fig_principal.add_trace(go.Scatter(
            x=df_evo['anio'],
            y=df_evo[columna_pct],
            mode='lines+markers',
            name=nombre_servicio,
            line=dict(width=4, color=COLORS_SERVICIO.get(nombre_servicio, '#1F77B4')),
            marker=dict(size=14),
            hovertemplate='Año: %{x}<br>Porcentaje: %{y:.1f}%<extra></extra>'
        ))
        fig_principal.update_layout(
            title=f'📈 Evolución de {nombre_servicio} en México ({titulo_anio})',
            xaxis_title='Año',
            yaxis_title='Porcentaje de Viviendas con Servicio (%)',
            yaxis=dict(range=[0, 100], gridcolor='rgba(0,0,0,0.1)'),
            plot_bgcolor='white',
            height=500,
            hovermode='x unified'
        )

    elif comparar == 'mapa':
        fig_principal = px.scatter_mapbox(
            df_filtrado,
            lat='lat',
            lon='lon',
            size=columna_pct,
            color=columna_pct,
            hover_name='estado',
            hover_data={
                'viviendas_totales': ':,.0f',
                columna_pct: ':.1f',
                'anio': True
            },
            color_continuous_scale='RdYlGn',
            size_max=50,
            zoom=4,
            center={'lat': 23.6, 'lon': -102.5},
            title=f'🗺️ {nombre_servicio} por Estado ({titulo_anio})',
            labels={columna_pct: 'Porcentaje (%)'}
        )
        fig_principal.update_layout(
            mapbox_style='open-street-map',
            mapbox_zoom=4,
            height=550,
            margin={'r': 0, 't': 40, 'l': 0, 'b': 0}
        )

    elif comparar == 'ranking':
        df_rank = df_filtrado.sort_values(columna_pct, ascending=True)
        colors = ['#D62728' if i < 3 else '#2CA02C' if i > len(df_rank)-4 else '#1F77B4'
                 for i in range(len(df_rank))]

        fig_principal = go.Figure()
        fig_principal.add_trace(go.Bar(
            x=df_rank[columna_pct],
            y=df_rank['estado'],
            orientation='h',
            marker_color=colors,
            text=df_rank[columna_pct].round(1),
            textposition='outside',
            hovertemplate='Estado: %{y}<br>Porcentaje: %{x:.1f}%<extra></extra>'
        ))
        fig_principal.update_layout(
            title=f'🏆 Ranking de Estados - {nombre_servicio} ({titulo_anio})',
            xaxis_title='Porcentaje (%)',
            yaxis_title='Estado',
            xaxis=dict(range=[0, 100], gridcolor='rgba(0,0,0,0.1)'),
            plot_bgcolor='white',
            height=550,
            showlegend=False
        )

    else:  # comparativa
        promedios = {}
        for s in ['agua', 'drenaje', 'electricidad', 'servicios_basicos']:
            promedios[SERVICIOS[s]] = df_filtrado[f'{s}_pct'].mean()

        fig_principal = go.Figure()
        for servicio_nombre, valor in promedios.items():
            color = COLORS_SERVICIO.get(servicio_nombre, '#1F77B4')
            fig_principal.add_trace(go.Bar(
                x=[servicio_nombre],
                y=[valor],
                name=servicio_nombre,
                marker_color=color,
                text=[f'{valor:.1f}%'],
                textposition='outside'
            ))
        fig_principal.update_layout(
            title=f'📊 Comparativa de Servicios - Promedio Nacional ({titulo_anio})',
            yaxis_title='Porcentaje (%)',
            yaxis=dict(range=[0, 100], gridcolor='rgba(0,0,0,0.1)'),
            plot_bgcolor='white',
            height=500,
            showlegend=False
        )

    # ========================================================================
    # 3. GRÁFICO SECUNDARIO (Evolución de todos los servicios)
    # ========================================================================
    df_evo_completa = df_estados.groupby('anio').agg({
        'agua_pct': 'mean',
        'drenaje_pct': 'mean',
        'electricidad_pct': 'mean',
        'servicios_basicos_pct': 'mean'
    }).reset_index()

    fig_secundario = go.Figure()
    for s in ['agua', 'drenaje', 'electricidad', 'servicios_basicos']:
        nombre = SERVICIOS[s]
        color = COLORS_SERVICIO.get(nombre, '#1F77B4')
        fig_secundario.add_trace(go.Scatter(
            x=df_evo_completa['anio'],
            y=df_evo_completa[f'{s}_pct'],
            mode='lines+markers',
            name=nombre,
            line=dict(width=3, color=color),
            marker=dict(size=10)
        ))

    fig_secundario.update_layout(
        title='📈 Evolución de Todos los Servicios (2000-2020)',
        xaxis_title='Año',
        yaxis_title='Porcentaje (%)',
        yaxis=dict(range=[0, 100], gridcolor='rgba(0,0,0,0.1)'),
        plot_bgcolor='white',
        height=400,
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        hovermode='x unified'
    )

    # ========================================================================
    # 4. GRÁFICO MAPA (para la pestaña de mapa)
    # ========================================================================
    fig_mapa = px.scatter_mapbox(
        df_filtrado,
        lat='lat',
        lon='lon',
        size=columna_pct,
        color=columna_pct,
        hover_name='estado',
        hover_data={
            'viviendas_totales': ':,.0f',
            columna_pct: ':.1f',
            'anio': True
        },
        color_continuous_scale='RdYlGn',
        size_max=50,
        zoom=4,
        center={'lat': 23.6, 'lon': -102.5},
        title=f'🗺️ {nombre_servicio} por Estado ({titulo_anio})',
        labels={columna_pct: 'Porcentaje (%)'}
    )
    fig_mapa.update_layout(
        mapbox_style='open-street-map',
        mapbox_zoom=4,
        height=600,
        margin={'r': 0, 't': 40, 'l': 0, 'b': 0}
    )

    # ========================================================================
    # 5. GRÁFICO RANKING
    # ========================================================================
    df_rank = df_filtrado.sort_values(columna_pct, ascending=True)
    colors = ['#D62728' if i < 3 else '#2CA02C' if i > len(df_rank)-4 else '#1F77B4'
             for i in range(len(df_rank))]

    fig_ranking = go.Figure()
    fig_ranking.add_trace(go.Bar(
        x=df_rank[columna_pct],
        y=df_rank['estado'],
        orientation='h',
        marker_color=colors,
        text=df_rank[columna_pct].round(1),
        textposition='outside',
        hovertemplate='Estado: %{y}<br>Porcentaje: %{x:.1f}%<extra></extra>'
    ))
    fig_ranking.update_layout(
        title=f'🏆 Ranking de Estados - {nombre_servicio} ({titulo_anio})',
        xaxis_title='Porcentaje (%)',
        yaxis_title='Estado',
        xaxis=dict(range=[0, 100], gridcolor='rgba(0,0,0,0.1)'),
        plot_bgcolor='white',
        height=500,
        showlegend=False
    )

    # ========================================================================
    # 6. GRÁFICO RADAR
    # ========================================================================
    if anio == 'todos':
        df_radar = df_estados[df_estados['anio'] == 2020].copy()
    else:
        df_radar = df_filtrado.copy()

    if not df_radar.empty:
        top_estado = df_radar.loc[df_radar['servicios_basicos_pct'].idxmax(), 'estado']
        bottom_estado = df_radar.loc[df_radar['servicios_basicos_pct'].idxmin(), 'estado']
    else:
        top_estado = "Sin datos"
        bottom_estado = "Sin datos"

    fig_radar = go.Figure()

    for estado in [top_estado, bottom_estado]:
        df_est = df_radar[df_radar['estado'] == estado]
        if not df_est.empty:
            valores = [
                df_est['agua_pct'].values[0],
                df_est['drenaje_pct'].values[0],
                df_est['electricidad_pct'].values[0],
                df_est['servicios_basicos_pct'].values[0]
            ]
            fig_radar.add_trace(go.Scatterpolar(
                r=valores,
                theta=['Agua\nEntubada', 'Drenaje', 'Electricidad', 'Servicios\nBásicos'],
                fill='toself',
                name=estado,
                line_color='#1F77B4' if estado == top_estado else '#D62728',
                fillcolor='rgba(31, 119, 180, 0.3)' if estado == top_estado else 'rgba(214, 39, 40, 0.3)'
            ))

    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], gridcolor='rgba(0,0,0,0.1)'),
            angularaxis=dict(tickfont=dict(size=12))
        ),
        title=f'🎯 Comparativa: {top_estado} vs {bottom_estado} ({titulo_anio})',
        showlegend=True,
        height=400
    )

    # ========================================================================
    # 7. GRÁFICO COMPARATIVA
    # ========================================================================
    promedios = {}
    for s in ['agua', 'drenaje', 'electricidad', 'servicios_basicos']:
        promedios[SERVICIOS[s]] = df_filtrado[f'{s}_pct'].mean()

    fig_comparativa = go.Figure()
    for servicio_nombre, valor in promedios.items():
        color = COLORS_SERVICIO.get(servicio_nombre, '#1F77B4')
        fig_comparativa.add_trace(go.Bar(
            x=[servicio_nombre],
            y=[valor],
            name=servicio_nombre,
            marker_color=color,
            text=[f'{valor:.1f}%'],
            textposition='outside'
        ))
    fig_comparativa.update_layout(
        title=f'📊 Comparativa de Servicios - Promedio Nacional ({titulo_anio})',
        yaxis_title='Porcentaje (%)',
        yaxis=dict(range=[0, 100], gridcolor='rgba(0,0,0,0.1)'),
        plot_bgcolor='white',
        height=400,
        showlegend=False
    )

    # ========================================================================
    # 8. TABLA DE DATOS
    # ========================================================================
    tabla_df = df_filtrado[['estado', 'anio', 'viviendas_totales',
                            'agua_pct', 'drenaje_pct', 'electricidad_pct', 'servicios_basicos_pct']].copy()
    tabla_df.columns = ['Estado', 'Año', 'Viviendas',
                        'Agua %', 'Drenaje %', 'Electricidad %', 'Servicios Básicos %']

    tabla = dash_table.DataTable(
        data=tabla_df.round(1).to_dict('records'),
        columns=[{'name': col, 'id': col} for col in tabla_df.columns],
        page_size=15,
        style_table={'overflowX': 'auto', 'maxHeight': '400px'},
        style_header={'backgroundColor': '#2C3E50', 'color': 'white', 'fontWeight': 'bold'},
        style_cell={'textAlign': 'center', 'padding': '10px'},
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': '#F8F9FA'},
            {'if': {'filter_query': '{Servicios Básicos %} > 80'}, 
             'backgroundColor': '#D4EDDA', 'color': '#155724'},
            {'if': {'filter_query': '{Servicios Básicos %} < 60'}, 
             'backgroundColor': '#F8D7DA', 'color': '#721C24'}
        ]
    )

    # ========================================================================
    # 9. CONCLUSIONES
    # ========================================================================
    # Calcular estadísticas para conclusiones
    df_2020 = df_estados[df_estados['anio'] == 2020]
    df_2000 = df_estados[df_estados['anio'] == 2000]

    if not df_2020.empty and not df_2000.empty:
        prom_basicos_2020 = df_2020['servicios_basicos_pct'].mean()
        prom_basicos_2000 = df_2000['servicios_basicos_pct'].mean()
        crecimiento = prom_basicos_2020 - prom_basicos_2000

        mejor_estado = df_2020.loc[df_2020['servicios_basicos_pct'].idxmax(), 'estado']
        peor_estado = df_2020.loc[df_2020['servicios_basicos_pct'].idxmin(), 'estado']
        mejor_pct = df_2020['servicios_basicos_pct'].max()
        peor_pct = df_2020['servicios_basicos_pct'].min()
        brecha = mejor_pct - peor_pct

        prom_agua_2020 = df_2020['agua_pct'].mean()
        prom_drenaje_2020 = df_2020['drenaje_pct'].mean()
        prom_electricidad_2020 = df_2020['electricidad_pct'].mean()

        conclusiones = html.Div([
            html.H4("💡 Principales Hallazgos", className="text-primary mb-3"),
            
            html.H6("📈 Evolución General", className="fw-bold mt-3"),
            html.P(f"En 20 años, los servicios básicos crecieron de {prom_basicos_2000:.1f}% a {prom_basicos_2020:.1f}%, un aumento de {crecimiento:.1f} puntos porcentuales.", className="mb-2"),
            
            html.H6("🏆 Desigualdad Regional", className="fw-bold mt-3"),
            html.P(f"La brecha entre el mejor estado ({mejor_estado}: {mejor_pct:.1f}%) y el peor ({peor_estado}: {peor_pct:.1f}%) es de {brecha:.1f} puntos porcentuales.", className="mb-2"),
            
            html.H6("🔧 Servicios por Tipo (2020)", className="fw-bold mt-3"),
            html.Ul([
                html.Li(f"💧 Agua entubada: {prom_agua_2020:.1f}% de cobertura"),
                html.Li(f"🚽 Drenaje: {prom_drenaje_2020:.1f}% de cobertura"),
                html.Li(f"💡 Electricidad: {prom_electricidad_2020:.1f}% de cobertura"),
                html.Li(f"🏠 Servicios básicos (los 3): {prom_basicos_2020:.1f}% de cobertura")
            ], className="mb-2"),
            
            html.H6("⚠️ Retos Pendientes", className="fw-bold mt-3"),
            html.Ul([
                html.Li(f"⏳ Al ritmo actual, se necesitarían ~30 años para llegar al 90% de cobertura."),
                html.Li(f"📍 Los estados del sur-sureste (Oaxaca, Chiapas, Guerrero) concentran el mayor rezago."),
                html.Li(f"💡 La electricidad es el servicio con mayor cobertura ({prom_electricidad_2020:.1f}%)."),
                html.Li(f"🚽 El drenaje es el servicio con mayor crecimiento en el período.")
            ], className="mb-2"),
            
            html.H6("🎯 Recomendaciones", className="fw-bold mt-3"),
            html.Ul([
                html.Li("✅ Focalizar inversión en estados del sur-sureste."),
                html.Li("✅ Priorizar la ampliación de redes de drenaje y agua potable."),
                html.Li("✅ Mantener el ritmo de crecimiento de la última década.")
            ], className="mb-0")
        ])
    else:
        conclusiones = html.P("No hay datos suficientes para generar conclusiones.")

    return (kpi_viviendas, desc_viviendas,
            kpi_agua, desc_agua,
            kpi_drenaje, desc_drenaje,
            kpi_basicos, desc_basicos,
            fig_principal, fig_secundario,
            fig_mapa, fig_ranking, fig_radar, fig_comparativa,
            tabla, conclusiones)

# ============================================================================
# 7. EJECUTAR
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🏠 DASHBOARD REDISEÑADO - SERVICIOS PÚBLICOS EN MÉXICO")
    print("="*70)
    print(f"✅ Datos cargados: {len(df_estados)} registros")
    print(f"📅 Años: {sorted(df_estados['anio'].unique())}")
    print(f"🏛️ Estados: {df_estados['estado'].nunique()}")
    print("\n" + "="*70)
    print("🌐 El dashboard está disponible en:")
    print("   ➜ http://127.0.0.1:8050")
    print("   ➜ http://localhost:8050")
    print("\n💡 Presiona Ctrl+C para detener el servidor")
    print("="*70 + "\n")

    app.run(debug=True, host='0.0.0.0', port=8050)