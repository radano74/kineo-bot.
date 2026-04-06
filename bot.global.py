import datetime
import time
import yfinance as yf
import alpaca_trade_api as tradeapi

# === CONFIGURACIÓN DE ACCESO ===
API_KEY = 'TU_API_KEY_AQUI'  # Pon tu Key de Paper Trading
SECRET_KEY = 'TU_SECRET_KEY_AQUI' # Pon tu Secret Key de Paper Trading
BASE_URL = 'https://paper-api.alpaca.markets'


# Conexión con la API de Alpaca
alpaca = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL, api_version='v2')

class AlpacaGlobalBot:
    def __init__(self):
        self.objetivo_capital = 2000.0
        # --- TUS PROTECCIONES DE SEGURIDAD ---
        self.stop_loss_pct = 0.025  # 2.5%
        self.take_profit_pct = 0.05   # 5.0%
        
        print(f"--- Robot KINEO-ALGO Iniciado ---")
        print(f"Protección: SL {self.stop_loss_pct*100}% | TP {self.take_profit_pct*100}%")

    def obtener_mercado_actual(self):
        """Detecta bolsa activa - Versión Halal"""
        ahora = datetime.datetime.now(datetime.UTC).time()
        
        if datetime.time(0, 0) <= ahora < datetime.time(7, 0):
            return "ASIA", ["7203.T", "6758.T"]
        elif datetime.time(7, 0) <= ahora < datetime.time(13, 30):
            return "EUROPA", ["ASML", "SAP"]
        elif datetime.time(13, 30) <= ahora < datetime.time(21, 0):
            return "AMERICA", ["NVDA", "AAPL", "MSFT"]
            
        return "CERRADO", []

    def ejecutar_ciclo(self):
        sesion, activos = self.obtener_mercado_actual()
        hora_actual = datetime.datetime.now().strftime('%H:%M:%S')

        if sesion == "CERRADO":
            print(f"[{hora_actual}] Mercados cerrados. Robot esperando...")
            return

        print(f"[{hora_actual}] Sesión activa: {sesion}. Vigilando: {activos}")

        # Revisar posiciones abiertas para no duplicar
        try:
            posiciones = [p.symbol for p in alpaca.list_positions()]
        except Exception as e:
            print(f"Error al listar posiciones: {e}")
            return

        for ticker in activos:
            if ticker in posiciones:
                continue 

            # Descargar precio real
            try:
                datos = yf.Ticker(ticker).history(period="1d", interval="1m")
                if datos.empty: continue
                precio_crudo = datos['Close'].iloc[-1]
                
                # --- REDONDEO DE SEGURIDAD ---
                precio_actual = round(float(precio_crudo), 2)
                cantidad = int(self.objetivo_capital // precio_actual)
                
                if cantidad > 0:
                    p_tp = round(precio_actual * (1 + self.take_profit_pct), 2)
                    p_sl = round(precio_actual * (1 - self.stop_loss_pct), 2)

                    print(f"[{hora_actual}] LANZANDO ORDEN: {cantidad} de {ticker} a ${precio_actual}")

                    alpaca.submit_order(
                        symbol=ticker,
                        qty=cantidad,
                        side='buy',
                        type='market',
                        time_in_force='day',
                        order_class='bracket',
                        take_profit={'limit_price': p_tp},
                        stop_loss={'stop_price': p_sl}
                    )
                    print(f"[OK] Orden enviada correctamente para {ticker}")

            except Exception as e:
                print(f"[!] Error con {ticker}: {e}")

# --- INICIO DEL PROGRAMA ---
bot = AlpacaGlobalBot()

while True:
    try:
        bot.ejecutar_ciclo()
        time.sleep(300)  # Espera 5 minutos entre revisiones
    except Exception as e:
        print(f"Error crítico en el bucle: {e}")
        time.sleep(60)
