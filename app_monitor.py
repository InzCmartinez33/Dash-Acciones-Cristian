import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go  # <-- NUEVA LIBRERÍA PARA EL GRÁFICO
import time

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Monitor de Mercado", page_icon="📈", layout="wide")

# 1. Definir la lista de acciones
tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "NVDA", "META"]

# 2. Función para calcular el RSI
def calcular_rsi(datos_precio, periodos=14):
    delta = datos_precio['Close'].diff()
    ganancias = delta.clip(lower=0)
    perdidas = -1 * delta.clip(upper=0)
    
    ema_ganancias = ganancias.ewm(com=periodos-1, adjust=False).mean()
    ema_perdidas = perdidas.ewm(com=periodos-1, adjust=False).mean()
    
    rs = ema_ganancias / ema_perdidas
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

# 3. Interfaz Visual: Título
st.title("📈 Monitor Algorítmico de Acciones")
st.markdown("Analizador en tiempo real basado en **Fuerza Relativa (RSI)**, **Volumen** y **Fibonacci**.")

# 4. Botón interactivo para ejecutar el escaneo
if st.button("🚀 Escanear Mercado Ahora"):
    resultados = []
    barra_progreso = st.progress(0)
    estado_texto = st.empty()
    
    for i, ticker in enumerate(tickers):
        estado_texto.text(f"Analizando {ticker}... ({i+1}/{len(tickers)})")
        try:
            accion = yf.Ticker(ticker)
            historial = accion.history(period="3mo")
            
            if len(historial) < 14:
                continue
                
            precio_actual = historial['Close'].iloc[-1]
            rsi_actual = calcular_rsi(historial)
            
            # --- TENDENCIA Y VOLUMEN ---
            estado_vol = "N/A"
            if len(historial) >= 10:
                precio_semana_pasada = historial['Close'].iloc[-6]
                cambio_precio = ((precio_actual - precio_semana_pasada) / precio_semana_pasada) * 100
                volumen_reciente = historial['Volume'].iloc[-5:].mean()
                volumen_previo = historial['Volume'].iloc[-10:-5].mean()
                
                if cambio_precio < 0: 
                    estado_vol = "🟢 Compra (Cae sin fuerza)" if volumen_reciente < volumen_previo else "🔴 Peligro (Cae con pánico)"
                elif cambio_precio > 0: 
                    estado_vol = "🟢 Alcista (Sube con fuerza)" if volumen_reciente > volumen_previo else "🔴 Falsa subida (Poco vol)"

            # --- DECISIÓN ---
            decision = "⚪ Mantener"
            if rsi_actual <= 30:
                decision = "🟢 FUERTE COMPRA" if "Compra" in estado_vol else "🟢 COMPRAR"
            elif rsi_actual >= 70:
                decision = "🔴 FUERTE VENTA" if "Falsa subida" in estado_vol or "Peligro" in estado_vol else "🔴 VENDER"

            # --- FIBONACCI ---
            maximo_3m = historial['High'].max()
            minimo_3m = historial['Low'].min()
            diferencia = maximo_3m - minimo_3m
            precio_objetivo = 0.0
            potencial = 0.0
            
            if diferencia > 0:
                if precio_actual < (minimo_3m + (diferencia / 2)):
                    precio_objetivo = minimo_3m + (diferencia * 0.618)
                else:
                    precio_objetivo = maximo_3m + (diferencia * 0.618) 
                potencial = ((precio_objetivo - precio_actual) / precio_actual) * 100

            # --- FUNDAMENTALES ---
            info = accion.info
            per = info.get('trailingPE') or info.get('forwardPE')
            pb = info.get('priceToBook')
            div_yield = info.get('dividendYield')
            
            resultados.append({
                "Ticker": ticker,
                "ACCIÓN": decision,
                "Precio ($)": round(precio_actual, 2),
                "Target Fib": f"${round(precio_objetivo, 2)}",
                "Potencial": f"{round(potencial, 2)}%",
                "RSI (14)": round(rsi_actual, 2),
                "Señal Vol": estado_vol,
                "PER": round(per, 2) if per else "N/A",
                "P/B": round(pb, 2) if pb else "N/A",
                "Dividendo": f"{round(div_yield * 100, 2)}%" if div_yield else "0.0%"
            })
            
        except Exception as e:
            st.error(f"Error con {ticker}: {e}")
            
        barra_progreso.progress((i + 1) / len(tickers))
        time.sleep(2)

    estado_texto.empty()
    barra_progreso.empty()

    if resultados:
        df = pd.DataFrame(resultados)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.success("✅ Análisis completado con éxito.")

# --- 5. NUEVA SECCIÓN: GRÁFICO INTERACTIVO ---
st.markdown("---")
st.subheader("📊 Análisis Visual (Velas Japonesas)")

# Menú desplegable para elegir la acción
ticker_seleccionado = st.selectbox("Selecciona una acción para ver su gráfico:", tickers)

if ticker_seleccionado:
    # Descargamos 6 meses de datos para tener una mejor perspectiva visual
    accion_chart = yf.Ticker(ticker_seleccionado)
    historial_chart = accion_chart.history(period="6mo")
    
    # Creamos la estructura del gráfico de velas
    fig = go.Figure(data=[go.Candlestick(
        x=historial_chart.index,
        open=historial_chart['Open'],
        high=historial_chart['High'],
        low=historial_chart['Low'],
        close=historial_chart['Close'],
        name="Precio"
    )])
    
    # Personalizamos la apariencia del gráfico
    fig.update_layout(
        title=f"Evolución del Precio - {ticker_seleccionado} (Últimos 6 meses)",
        yaxis_title="Precio en USD",
        xaxis_title="Fecha",
        template="plotly_dark", # Tema oscuro, se ve mucho más profesional
        xaxis_rangeslider_visible=False, # Ocultamos una barra redundante de abajo
        height=500 # Hacemos el gráfico más grande
    )
    
    # Lo mostramos en la app
    st.plotly_chart(fig, use_container_width=True)
