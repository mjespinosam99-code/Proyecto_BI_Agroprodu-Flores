# Prototipo BI – Empresa agroexportadora de flores (Caso 6)

Solución de inteligencia de negocios para una empresa florícola de la sierra ecuatoriana:
indicadores de **merma**, **cumplimiento de pedidos** y **estacionalidad** (San Valentín y Día de la Madre)
para 3 fincas, 5 variedades de rosa y 4 mercados de destino (enero 2025 – junio 2026).

## Contenido del repositorio

| Archivo / carpeta | Qué es |
| --- | --- |
| `index.html` | Prototipo web (tablero interactivo). Se publica con **GitHub Pages** |
| `app.py` | El mismo prototipo hecho en Python con **Streamlit** |
| `requirements.txt` | Librerías que necesita `app.py` |
| `.streamlit/config.toml` | Colores de la app de Streamlit |
| `salida/` | Modelo estrella generado por el ETL: 5 dimensiones + tabla de hechos (CSV) |
| `assets/` | Escudo de la Universidad Central del Ecuador usado en el encabezado |

## Pestañas del prototipo
1. **Resumen**: indicadores clave, cumplimiento mensual (meta 90 %) y merma mensual
2. **Merma**: por finca, por variedad, causa de rechazo y mapa finca × variedad
3. **Cumplimiento e ingreso**: ingreso y precio por mercado; cumplimiento mercado × mes
4. **Pico vs regular**: volumen, precio, cumplimiento y merma por temporada
5. **Plan de mejora**: potencial de los 3 frentes de la recomendación (≈ USD 480 mil)
6. **Modelo de datos**: esquema estrella

Filtros: finca, variedad, mercado, temporada y período.

## Ejecutar la versión Python en tu computadora
```
pip install -r requirements.txt
streamlit run app.py
```
Se abre en http://localhost:8501

## Modelo de datos
Esquema estrella con grano **día × finca × variedad × mercado**:
`fact_produccion_despacho` + `dim_tiempo`, `dim_finca`, `dim_variedad`, `dim_mercado`, `dim_causa`.

Medidas: merma = cosechados − exportables · ingreso estimado = despachados × precio ·
cumplimiento = despachados ÷ pedidos (siempre como cociente de sumas).
