"""
Prototipo BI - Empresa agroexportadora de flores (Caso 6)
=========================================================
Tablero web hecho en Python con Streamlit. Lee el modelo estrella que genera
el ETL (carpeta salida/) y calcula los indicadores con pandas.

Ejecutar:   streamlit run app.py
Se abre en: http://localhost:8501
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Prototipo BI Florícola", page_icon="🌹", layout="wide")

CARPETA = Path(__file__).parent / "salida"
META = 0.90
VERDE, ROSA, GRIS = "#127ABF", "#C0212A", "#B7C6D8"
ORDEN_TEMP = ["San Valentin", "Dia de la Madre", "Regular"]


# --------------------------------------------------------------------------- #
# 1. CARGA DEL MODELO ESTRELLA
# --------------------------------------------------------------------------- #
@st.cache_data
def cargar_modelo() -> pd.DataFrame:
    leer = lambda n: pd.read_csv(CARPETA / f"{n}.csv", encoding="utf-8-sig")
    fact = leer("fact_produccion_despacho")
    tiempo = leer("dim_tiempo")
    tiempo["fecha"] = pd.to_datetime(tiempo["fecha"])
    df = (fact
          .merge(tiempo[["id_tiempo", "fecha", "anio_mes", "temporada", "es_temporada_pico"]], on="id_tiempo")
          .merge(leer("dim_finca")[["id_finca", "codigo_finca"]], on="id_finca")
          .merge(leer("dim_variedad")[["id_variedad", "nombre_variedad"]], on="id_variedad")
          .merge(leer("dim_mercado")[["id_mercado", "nombre_mercado"]], on="id_mercado")
          .merge(leer("dim_causa")[["id_causa", "nombre_causa"]], on="id_causa"))
    return df


# --------------------------------------------------------------------------- #
# 2. MEDIDAS (siempre cociente de sumas, igual que en SQL y DAX)
# --------------------------------------------------------------------------- #
def medidas(g: pd.DataFrame) -> pd.Series:
    cos, merma = g.tallos_cosechados.sum(), g.merma.sum()
    ped, desp, ing = g.tallos_pedidos.sum(), g.tallos_despachados.sum(), g.ingreso_estimado.sum()
    dias = g.id_tiempo.nunique()
    return pd.Series({
        "cosechados": cos, "merma": merma, "pct_merma": merma / cos if cos else 0,
        "pedidos": ped, "despachados": desp, "cumplimiento": desp / ped if ped else 0,
        "ingreso": ing, "precio": ing / desp if desp else 0,
        "no_despachados": ped - desp,
        "ingreso_no_capturado": (g.tallos_no_despachados * g.precio_tallo).sum(),
        "pedidos_dia": ped / dias if dias else 0, "despachados_dia": desp / dias if dias else 0,
    })


def por(df: pd.DataFrame, col) -> pd.DataFrame:
    return df.groupby(col).apply(medidas, include_groups=False).reset_index()


usd = lambda v: f"${v:,.0f}".replace(",", ".")
pct = lambda v: f"{v:.1%}".replace(".", ",")
num = lambda v: f"{v:,.0f}".replace(",", ".")


def interp(lugar, texto: str):
    """Cuadro de interpretación debajo de cada gráfico."""
    lugar.markdown(
        f"<div style='border-left:3px solid #127ABF;background:#F4F7FB;padding:10px 12px;border-radius:0 8px 8px 0;font-size:0.92rem;line-height:1.5;margin-bottom:12px'>"
        f"<b style='color:#127ABF'>Interpretación:</b> {texto}</div>", unsafe_allow_html=True)


PICO_MES = ("01", "02", "04", "05")
MESES_TXT = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
mes_txt = lambda m: f"{MESES_TXT[int(m[5:]) - 1]} {m[:4]}"
miles = lambda v: f"{v / 1e6:.1f} millones".replace(".", ",") if v >= 1e6 else f"{round(v / 1000)} mil"
dinero = lambda v: "$" + miles(v)


def unir(xs):
    return ", ".join(xs[:-1]) + " y " + xs[-1] if len(xs) > 1 else "".join(xs)


CAUSA_ART = {"Botritis": "la botritis", "Tallo corto": "el tallo corto", "Dano mecanico": "el daño mecánico", "Plaga": "la plaga"}
TEMP_TXT = {"San Valentin": "San Valentín", "Dia de la Madre": "el Día de la Madre"}


df_total = cargar_modelo()

# --------------------------------------------------------------------------- #
# 3. FILTROS (barra lateral)
# --------------------------------------------------------------------------- #
st.sidebar.title("🌹 Filtros")
fincas = st.sidebar.multiselect("Finca", sorted(df_total.codigo_finca.unique()), default=sorted(df_total.codigo_finca.unique()))
variedades = st.sidebar.multiselect("Variedad", sorted(df_total.nombre_variedad.unique()), default=sorted(df_total.nombre_variedad.unique()))
mercados = st.sidebar.multiselect("Mercado", ["Estados Unidos", "Europa", "Asia", "Nacional"], default=["Estados Unidos", "Europa", "Asia", "Nacional"])
temporadas = st.sidebar.multiselect("Temporada", ORDEN_TEMP, default=ORDEN_TEMP)
f_min, f_max = df_total.fecha.min().date(), df_total.fecha.max().date()
periodo = st.sidebar.date_input("Período", value=(f_min, f_max), min_value=f_min, max_value=f_max)
desde, hasta = (periodo if len(periodo) == 2 else (f_min, f_max))
st.sidebar.caption("Fuente: produccion_flores.csv → ETL en Python → modelo estrella (salida/).")

df = df_total[df_total.codigo_finca.isin(fincas) & df_total.nombre_variedad.isin(variedades)
              & df_total.nombre_mercado.isin(mercados) & df_total.temporada.isin(temporadas)
              & df_total.fecha.dt.date.between(desde, hasta)]

# ---- Encabezado: escudo UCE + título + rosa ----
ROSA_SVG = """<svg viewBox="0 0 120 140" width="84" height="98" role="img" aria-label="Ilustración de una rosa">
<path d="M60 76 C57 98 63 116 60 134" stroke="#3E9B5F" stroke-width="5" fill="none" stroke-linecap="round"/>
<path d="M60 106 C44 94 30 98 22 110 C38 117 52 114 60 106Z" fill="#4CAF6E"/>
<path d="M61 118 C76 106 90 110 98 121 C82 128 69 125 61 118Z" fill="#3E9B5F"/>
<path d="M60 22 C30 22 22 50 34 66 C44 79 76 79 86 66 C98 50 90 22 60 22Z" fill="#B71C2B"/>
<path d="M34 66 C25 56 25 40 36 33 C34 46 38 58 49 67Z" fill="#951523"/>
<path d="M86 66 C95 56 95 40 84 33 C86 46 82 58 71 67Z" fill="#951523"/>
<path d="M60 30 C42 32 37 52 47 62 C55 71 70 69 77 58 C84 44 76 30 60 30Z" fill="#D63447"/>
<path d="M43 31 C50 14 70 14 77 31 C68 26 52 26 43 31Z" fill="#E25563"/>
<path d="M60 38 C49 40 49 55 60 57 C69 58 73 48 66 43 C62 40 57 43 58 47" stroke="#8E1420" stroke-width="3" fill="none" stroke-linecap="round"/>
<path d="M49 74 L60 85 L71 74 C64 79 56 79 49 74Z" fill="#2E7D4F"/></svg>"""

logo, titulo, flor = st.columns([1, 8, 1], vertical_alignment="center")
LOGO = Path(__file__).parent / "assets" / "logo_uce.png"
if LOGO.exists():
    logo.image(str(LOGO), width=90)
with titulo:
    st.caption("UNIVERSIDAD CENTRAL DEL ECUADOR · PROTOTIPO DE INTELIGENCIA DE NEGOCIOS")
    st.title("Tablero de merma, cumplimiento y estacionalidad")
    st.caption("Empresa agroexportadora de rosas de la sierra ecuatoriana · 3 fincas · 5 variedades · 4 mercados · enero 2025 – junio 2026")
flor.markdown(ROSA_SVG, unsafe_allow_html=True)
st.markdown("<hr style='margin:4px 0 12px;border:none;border-top:3px solid #C0212A'>", unsafe_allow_html=True)

if df.empty:
    st.warning("Ningún registro coincide con los filtros elegidos.")
    st.stop()

T = medidas(df)
mes = por(df, "anio_mes").sort_values("anio_mes")
bajo = mes[mes.cumplimiento < META]

tabs = st.tabs(["Resumen", "Merma", "Cumplimiento e ingreso", "Pico vs regular", "Plan de mejora", "Modelo de datos"])

# --------------------------------------------------------------------------- #
# RESUMEN
# --------------------------------------------------------------------------- #
with tabs[0]:
    c = st.columns(5)
    c[0].metric("Ingreso estimado", usd(T.ingreso))
    c[1].metric("% Merma", pct(T.pct_merma))
    c[2].metric("Cumplimiento", pct(T.cumplimiento))
    c[3].metric("Meses bajo 90 %", f"{len(bajo)} de {len(mes)}")
    c[4].metric("Ingreso no capturado", usd(T.ingreso_no_capturado))

    izq, der = st.columns(2)
    fig = go.Figure(go.Scatter(x=mes.anio_mes, y=mes.cumplimiento, mode="lines+markers", line=dict(color=VERDE, width=2),
                               marker=dict(size=9, color=[ROSA if v < META else VERDE for v in mes.cumplimiento]),
                               hovertemplate="%{x}: %{y:.1%}<extra></extra>"))
    fig.add_hline(y=META, line_dash="dash", line_color="gray", annotation_text="Meta 90 %")
    fig.update_layout(title="Cumplimiento de pedidos por mes", yaxis_tickformat=".0%", height=380, margin=dict(t=50, b=10))
    izq.plotly_chart(fig, width="stretch")
    if len(bajo):
        peor = bajo.loc[bajo.cumplimiento.idxmin()]
        todos_pico = all(m[5:] in PICO_MES for m in bajo.anio_mes)
        resto = mes[mes.cumplimiento >= META]
        interp(izq, (f"Durante casi todo el año se entrega alrededor del {pct(resto.cumplimiento.mean())} de lo pedido, pero " if len(resto) else "El cumplimiento ")
               + f"en {len(bajo)} meses cae por debajo de la meta; el peor fue {mes_txt(peor.anio_mes)}, con {pct(peor.cumplimiento)}. "
               + ("Todos esos meses coinciden con San Valentín y el Día de la Madre, así que el problema aparece justo cuando más se vende." if todos_pico else "Conviene revisar qué pasó en esos meses."))
    else:
        interp(izq, "Con estos filtros, el cumplimiento se mantiene sobre el 90 % todo el período: los pedidos se entregaron prácticamente completos.")

    fig = px.line(mes, x="anio_mes", y="pct_merma", markers=True, title="% de merma por mes")
    fig.update_traces(line_color=ROSA, hovertemplate="%{x}: %{y:.2%}<extra></extra>")
    fig.update_layout(yaxis_tickformat=".1%", xaxis_title=None, yaxis_title=None, height=380, margin=dict(t=50, b=10))
    der.plotly_chart(fig, width="stretch")
    mx, mn = mes.loc[mes.pct_merma.idxmax()], mes.loc[mes.pct_merma.idxmin()]
    texto = f"La merma se mueve entre {pct(mn.pct_merma)} y {pct(mx.pct_merma)} según el mes. "
    if df.es_temporada_pico.nunique() == 2:
        mp, mr = medidas(df[df.es_temporada_pico == 1]), medidas(df[df.es_temporada_pico == 0])
        texto += (f"En las temporadas pico sube a {pct(mp.pct_merma)}, frente a {pct(mr.pct_merma)} el resto del año: con más flor cortada y más prisa por despachar, se pierde más en el camino."
                  if mp.pct_merma > mr.pct_merma else "Con estos filtros, las temporadas pico no muestran más merma que el resto del año.")
    interp(der, texto)

# --------------------------------------------------------------------------- #
# MERMA
# --------------------------------------------------------------------------- #
def barras(tabla, eje, valor, titulo, fmt=".1%"):
    t = tabla.sort_values(valor)
    colores = [GRIS] * (len(t) - 1) + [ROSA]
    fig = go.Figure(go.Bar(x=t[valor], y=t[eje], orientation="h", marker_color=colores,
                           text=t[valor], texttemplate=f"%{{text:{fmt}}}", textposition="outside"))
    fig.update_layout(title=titulo, height=320, margin=dict(t=50, b=10, r=60), xaxis_tickformat=fmt)
    return fig


with tabs[1]:
    izq, der = st.columns(2)
    fin = por(df, "codigo_finca").sort_values("pct_merma", ascending=False)
    var = por(df, "nombre_variedad").sort_values("pct_merma", ascending=False)
    izq.plotly_chart(barras(fin, "codigo_finca", "pct_merma", "% de merma por finca"), width="stretch")
    if len(fin) > 1:
        a, b = fin.iloc[0], fin.iloc[-1]
        interp(izq, f"{a.codigo_finca} es la finca que más flor pierde: {pct(a.pct_merma)} de lo que cosecha, frente a {pct(b.pct_merma)} de {b.codigo_finca}. "
                    f"Si {a.codigo_finca} trabajara al nivel de {b.codigo_finca}, se salvarían cerca de {miles(a.cosechados * (a.pct_merma - b.pct_merma))} tallos en el período.")
    else:
        interp(izq, f"Esta finca pierde el {pct(fin.iloc[0].pct_merma)} de lo que cosecha.")
    der.plotly_chart(barras(var, "nombre_variedad", "pct_merma", "% de merma por variedad"), width="stretch")
    if len(var) > 1:
        a, b = var.iloc[0], var.iloc[-1]
        interp(der, f"{a.nombre_variedad} es la variedad más delicada: se pierde el {pct(a.pct_merma)} de lo cosechado, mientras que en {b.nombre_variedad} apenas el {pct(b.pct_merma)}. "
                    f"Vale la pena revisar cómo se corta, se manipula y se empaca {a.nombre_variedad}.")
    else:
        interp(der, f"En esta variedad se pierde el {pct(var.iloc[0].pct_merma)} de lo cosechado.")

    izq, der = st.columns(2)
    causa = df.groupby(["codigo_finca", "nombre_causa"], as_index=False).merma.sum()
    causa["pct"] = causa.merma / causa.groupby("codigo_finca").merma.transform("sum")
    fig = px.bar(causa, y="codigo_finca", x="pct", color="nombre_causa", orientation="h", text_auto=".0%",
                 title="Causa de rechazo por finca (% de su merma)",
                 color_discrete_map={"Botritis": VERDE, "Dano mecanico": "#4AB6EF", "Tallo corto": ROSA, "Ninguna": "#D6E0EB", "Plaga": "#E0A100"})
    fig.update_layout(height=320, margin=dict(t=50, b=10), xaxis_title="% de la merma", xaxis_tickformat=".0%",
                      yaxis_title=None, legend_title=None)
    izq.plotly_chart(fig, width="stretch")
    dom = causa[causa.nombre_causa != "Ninguna"].sort_values("merma").groupby("codigo_finca").tail(1).sort_values("codigo_finca")
    partes = [(f"en {r.codigo_finca} pesa más " if i == 0 else f"en {r.codigo_finca}, ") + f"{CAUSA_ART.get(r.nombre_causa, r.nombre_causa)} ({pct(r.pct)})" for i, r in enumerate(dom.itertuples())]
    if partes:
        frase = unir(partes)
        interp(izq, f"Cada finca pierde flor por un motivo diferente: {frase}. Por eso una sola medida para las tres no funcionaría; cada una necesita su propia solución."
               if len(dom) > 1 and dom.nombre_causa.nunique() == len(dom) else frase[0].upper() + frase[1:] + ".")

    mapa = por(df, ["codigo_finca", "nombre_variedad"]).pivot(index="codigo_finca", columns="nombre_variedad", values="pct_merma")
    fig = px.imshow(mapa, text_auto=".1%", color_continuous_scale=["#FFFFFF", ROSA], aspect="auto",
                    title="% de merma finca × variedad")
    fig.update_layout(height=320, margin=dict(t=50, b=10), coloraxis_showscale=False, xaxis_title=None, yaxis_title=None)
    der.plotly_chart(fig, width="stretch")
    celdas = mapa.stack()
    if len(celdas) > 1:
        hi, lo = celdas.idxmax(), celdas.idxmin()
        peores = mapa.idxmax(axis=1)
        interp(der, f"El punto más crítico es {hi[1]} en {hi[0]} ({pct(celdas.max())}) y el mejor, {lo[1]} en {lo[0]} ({pct(celdas.min())}). "
                    + (f"{peores.iloc[0]} sale mal en todas las fincas, así que el problema viene más de la variedad que del lugar donde se cultiva."
                       if len(mapa) > 1 and mapa.shape[1] > 1 and peores.nunique() == 1 else ""))

# --------------------------------------------------------------------------- #
# CUMPLIMIENTO E INGRESO
# --------------------------------------------------------------------------- #
with tabs[2]:
    merc = por(df, "nombre_mercado")
    izq, der = st.columns(2)
    izq.plotly_chart(barras(merc, "nombre_mercado", "ingreso", "Ingreso estimado por mercado (USD)", ",.0f"), width="stretch")
    top, caro = merc.loc[merc.ingreso.idxmax()], merc.loc[merc.precio.idxmax()]
    interp(izq, f"{top.nombre_mercado} es el mercado más importante: deja el {pct(top.ingreso / T.ingreso)} del ingreso ({dinero(top.ingreso)}). "
                + (f"{caro.nombre_mercado}, en cambio, es el que mejor paga por tallo (${caro.precio:.3f}), un dato clave para decidir a quién atender primero cuando la flor no alcanza."
                   if caro.nombre_mercado != top.nombre_mercado else "Además, es el que mejor paga por tallo."))
    der.plotly_chart(barras(merc, "nombre_mercado", "precio", "Precio promedio por tallo (USD)", ".3f"), width="stretch")
    interp(der, (f"Aunque el precio por tallo cambia bastante de un mercado a otro, a todos se les entrega más o menos la misma parte de lo que piden ({pct(T.cumplimiento)}). "
                 "Cuando falta flor se recorta parejo, sin dar prioridad a quien paga mejor.")
                if len(merc) > 1 and merc.cumplimiento.max() - merc.cumplimiento.min() < 0.01
                else f"El cumplimiento va de {pct(merc.cumplimiento.min())} a {pct(merc.cumplimiento.max())} según el mercado.")

    st.subheader("Cumplimiento por mercado y mes (rojo = bajo 90 %)")
    matriz = por(df, ["anio_mes", "nombre_mercado"]).pivot(index="anio_mes", columns="nombre_mercado", values="cumplimiento")
    matriz["Total"] = mes.set_index("anio_mes").cumplimiento
    st.dataframe(matriz.style.format("{:.1%}").map(lambda v: f"background-color: {'#F4C7D3' if v < META else '#DCEBDF'}"),
                 width="stretch", height=680)
    rojas = int((matriz.drop(columns="Total") < META).sum().sum())
    interp(st, (f"Las celdas en rojo se repiten en los mismos {len(bajo)} meses para todos los mercados ({unir([mes_txt(m) for m in bajo.anio_mes])}). "
                "No es un cliente en particular el que queda mal atendido; es la temporada la que desborda la operación.")
           if rojas else "En ningún mes ni mercado el cumplimiento baja del 90 %.")

# --------------------------------------------------------------------------- #
# PICO VS REGULAR
# --------------------------------------------------------------------------- #
with tabs[3]:
    temp = por(df, "temporada")
    temp["temporada"] = pd.Categorical(temp.temporada, ORDEN_TEMP, ordered=True)
    temp = temp.sort_values("temporada")
    izq, der = st.columns(2)
    fig = go.Figure([go.Bar(name="Pedidos por día", x=temp.temporada, y=temp.pedidos_dia, marker_color=ROSA, texttemplate="%{y:,.0f}"),
                     go.Bar(name="Despachados por día", x=temp.temporada, y=temp.despachados_dia, marker_color=VERDE, texttemplate="%{y:,.0f}")])
    fig.update_layout(title="Tallos pedidos vs despachados por día", barmode="group", height=360, margin=dict(t=50, b=10))
    izq.plotly_chart(fig, width="stretch")
    R = temp[temp.temporada == "Regular"]
    pico_df = df[df.es_temporada_pico == 1]
    comparable = len(R) and len(pico_df)
    if comparable:
        R = R.iloc[0]; P = medidas(pico_df)
        crec = lambda x, y: f"{x / y - 1:+.0%}"
        interp(izq, f"En temporada pico se piden unos {num(P.pedidos_dia)} tallos al día, más del doble que en un día normal ({num(R.pedidos_dia)}). "
                    f"Los despachos, en cambio, apenas pasan de {num(R.despachados_dia)} a {num(P.despachados_dia)} ({crec(P.despachados_dia, R.despachados_dia)}): "
                    "la flor disponible casi no cambia, y ahí está el origen del incumplimiento.")
    else:
        interp(izq, "Para comparar las temporadas pico con el resto del año, deja seleccionadas todas las temporadas.")

    fig = go.Figure(go.Bar(x=temp.temporada, y=temp.cumplimiento, marker_color=[ROSA if v < META else VERDE for v in temp.cumplimiento],
                           texttemplate="%{y:.1%}"))
    fig.add_hline(y=META, line_dash="dash", line_color="gray", annotation_text="Meta 90 %")
    fig.update_layout(title="Cumplimiento por temporada", yaxis_tickformat=".0%", height=360, margin=dict(t=50, b=10))
    der.plotly_chart(fig, width="stretch")
    if comparable:
        picos = temp[temp.temporada != "Regular"]
        txt = unir([(f"en {TEMP_TXT[str(r.temporada)]} solo se cumple el {pct(r.cumplimiento)}" if i == 0 else f"en {TEMP_TXT[str(r.temporada)]} el {pct(r.cumplimiento)}") for i, r in enumerate(picos.itertuples())])
        interp(der, f"Fuera de temporada se entrega casi todo lo pedido ({pct(R.cumplimiento)}). " + txt[0].upper() + txt[1:] + ", muy lejos de la meta del 90 %.")

    tabla = temp[["temporada", "pedidos_dia", "despachados_dia", "precio", "cumplimiento", "pct_merma", "ingreso_no_capturado"]]
    tabla.columns = ["Temporada", "Pedidos/día", "Despachados/día", "Precio USD", "Cumplimiento", "% Merma", "Ingreso no capturado"]
    st.dataframe(tabla.style.format({"Pedidos/día": "{:,.0f}", "Despachados/día": "{:,.0f}", "Precio USD": "${:.3f}",
                                     "Cumplimiento": "{:.1%}", "% Merma": "{:.1%}", "Ingreso no capturado": "${:,.0f}"}),
                 hide_index=True, width="stretch")
    if comparable:
        perdido = temp.ingreso_no_capturado.sum()
        interp(st, f"En temporada pico cada tallo se vende a ${P.precio:.3f}, frente a ${R.precio:.3f} el resto del año, y además la merma sube de {pct(R.pct_merma)} a {pct(P.pct_merma)}. "
                   f"En total se dejaron de vender unos {dinero(perdido)} en pedidos incompletos, y casi todo "
                   f"({pct(P.ingreso_no_capturado / perdido if perdido else 0)}) se concentra en esas fechas. Ahí está la mayor oportunidad de mejora.")

# --------------------------------------------------------------------------- #
# PLAN DE MEJORA (sobre los 18 meses completos, sin filtros)
# --------------------------------------------------------------------------- #
with tabs[4]:
    st.caption("Escenario calculado con los 18 meses completos · no cambia con los filtros")
    A = df_total
    sel = lambda m: medidas(A[m])
    todo, f1, f2 = medidas(A), sel(A.codigo_finca == "F01"), sel(A.codigo_finca == "F02")
    pico, reg = sel(A.es_temporada_pico == 1), sel(A.es_temporada_pico == 0)
    nac = sel((A.es_temporada_pico == 1) & (A.nombre_mercado == "Nacional"))
    eeuu = sel((A.es_temporada_pico == 1) & (A.nombre_mercado == "Estados Unidos"))

    t1 = f2.cosechados * (f2.pct_merma - f1.pct_merma)
    t2 = pico.cosechados * (pico.pct_merma - reg.pct_merma)
    plan = pd.DataFrame([
        ["1 · Botritis en F02", "% merma F02", pct(f2.pct_merma), pct(f1.pct_merma), t1, t1 * todo.precio],
        ["2 · Merma en pico", "% merma en pico", pct(pico.pct_merma), pct(reg.pct_merma), t2, t2 * pico.precio],
        ["3 · Priorizar pedidos", "Precio tallo nacional en pico", f"${nac.precio:.3f}", f"${eeuu.precio:.3f}",
         nac.despachados, nac.despachados * (eeuu.precio - nac.precio)],
    ], columns=["Frente", "Indicador", "Actual", "Meta", "Tallos", "USD"])

    c = st.columns(4)
    for i, r in plan.iterrows():
        c[i].metric(r.Frente, usd(r.USD), f"{r.Tallos:,.0f} tallos".replace(",", "."), delta_color="off")
    c[3].metric("Potencial total", usd(plan.USD.sum()), "18 meses, sin ampliar área", delta_color="off")

    st.dataframe(plan.style.format({"Tallos": "{:,.0f}", "USD": "${:,.0f}"}), hide_index=True, width="stretch")
    mejor = plan.loc[plan.USD.idxmax()]
    interp(st, f"Si se aplican los tres frentes, la empresa podría recuperar alrededor de {dinero(plan.USD.sum())} en 18 meses sin sembrar una sola planta más. "
               f"El que más aporta es «{mejor.Frente[4:]}», con {dinero(mejor.USD)}. Las metas no son inventadas: F01 ya trabaja con menos merma, "
               "los meses normales ya pierden menos flor y Estados Unidos ya paga ese precio en temporada pico.")
    st.markdown("""
**Acciones del plan de temporada pico** (inicio 90 días antes de cada fecha):
1. **Botritis en F02:** control de humedad y ventilación, cadena de frío, fungicida preventivo.
2. **Merma en pico:** personal entrenado en corte y empaque (F03: daño mecánico) y protocolo para Pink Floyd.
3. **Priorizar pedidos:** comprometer solo hasta la proyección de exportables y priorizar por precio y contrato.
4. **Mediano plazo:** programación de cosecha y siembra escalonada para crecer más del 15 % en pico.
""")

# --------------------------------------------------------------------------- #
# MODELO DE DATOS
# --------------------------------------------------------------------------- #
with tabs[5]:
    st.caption("Cada fila del modelo guarda lo que pasó en un día, en una finca, con una variedad y para un mercado. Como el archivo original repetía la cosecha en los cuatro mercados, la repartimos según lo que se despachó a cada uno; así la merma se cuenta una sola vez y los totales cuadran con la realidad.")
    st.graphviz_chart("""
digraph {
  rankdir=LR; node [shape=box style="rounded,filled" fillcolor="#FDFCF8" fontname="Helvetica"];
  fact [label="fact_produccion_despacho\\n\\ntallos cosechados / exportables\\nmerma · pedidos · despachados\\nprecio · ingreso estimado" fillcolor="#DCE8E0" color="#2F6B52" penwidth=2];
  t [label="dim_tiempo\\naño ▸ mes ▸ día\\ntemporada · es_pico"];
  f [label="dim_finca\\nF01 · F02 · F03"];
  v [label="dim_variedad\\n5 variedades"];
  m [label="dim_mercado\\n4 mercados"];
  c [label="dim_causa\\ncausa de rechazo"];
  t -> fact [label="1:*"]; f -> fact [label="1:*"]; v -> fact [label="1:*"]; m -> fact [label="1:*"]; c -> fact [label="1:*"];
}
""")
interp(tabs[5], "En el centro están los números del negocio (tallos, merma, pedidos, despachos e ingreso) y alrededor, las distintas formas de mirarlos: "
                "por fecha, finca, variedad, mercado y causa. Gracias a esta estructura, cada gráfico del tablero se puede filtrar sin rehacer los cálculos.")
