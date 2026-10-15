import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time

# ================== EXNESS SETTINGS ==================
LOGIN = 123456789  # <-- یہاں اپنا Exness MT5 Login ID ڈالیں
PASSWORD = "ApnaPassword" # <-- یہاں اپنا 【entity-Exness¦canonical_name=Exness】 پاسورڈ ڈالیں
SERVER = "【entity-Exness¦canonical_name=Exness】-MT5Real" # <-- آپ کا سرور، جیسے 【entity-Exness¦canonical_name=Exness】-MT5Trial یا Real
SYMBOL = "XAUUSD"  # Gold, یا EURUSD, BTCUSD جو بھی آپ ٹریڈ کرنا چاہتے ہیں
LOT_PERCENT = 2.0 # ہر ٹریڈ پر اکاؤنٹ کا 2% رسک

class ExnessTradingBot:
    def __init__(self):
        # MT5 سے کنکشن
        if not mt5.initialize(login=LOGIN, password=PASSWORD, server=SERVER):
            print("MT5 Connection Failed:", mt5.last_error())
            quit()
        print("【entity-Exness¦canonical_name=Exness】 MT5 سے کنیکٹ ہو گیا!")

    def get_data(self, symbol, timeframe=mt5.TIMEFRAME_M15, bars=300):
        rates = mt5.copy_rates(symbol, timeframe, 0, bars)
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    def analysis(self, df):
        # 1. Support & Resistance
        df['support'] = df['low'].rolling(20).min()
        df['resistance'] = df['high'].rolling(20).max()
        
        # 2. Trend Line - EMA
        df['ema50'] = df['close'].ewm(span=50).mean()
        df['ema200'] = df['close'].ewm(span=200).mean()
        
        # 3. RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        df['trend'] = np.where(df['ema50'] > df['ema200'], 'UPTREND', 'DOWNTREND')
        return df

    def risk_management(self, symbol, entry_price, stop_loss):
        account = mt5.account_info()
        balance = account.balance
        risk_money = balance * (LOT_PERCENT / 100)
        # Stop Loss کی دوری کے حساب سے Lot Size
        sl_distance = abs(entry_price - stop_loss)
        tick_value = mt5.symbol_info(symbol).trade_tick_value
        lot = risk_money / (sl_distance * tick_value * 100) # Gold کے لیے
        lot = max(0.01, round(lot, 2)) # کم سے کم 0.01 Lot
        return lot

    def place_order(self, symbol, order_type, lot, sl, tp):
        price = mt5.symbol_info_tick(symbol).ask if order_type == "BUY" else mt5.symbol_info_tick(symbol).bid
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": mt5.ORDER_TYPE_BUY if order_type == "BUY" else mt5.ORDER_TYPE_SELL,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": 123456,
            "comment": "Exness Complete System",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        print(f"Order Result: {result}")
        return result

    def run(self):
        while True:
            df = self.get_data(SYMBOL)
            df = self.analysis(df)
            last = df.iloc[-1]
            prev = df.iloc[-2]

            print(f"Price: {last['close']} | Trend: {last['trend']} | RSI: {round(last['rsi'],2)} | Support: {last['support']} | Resistance: {last['resistance']}")

            # BUY Logic - Exness کے اصول کے مطابق
            if last['trend'] == 'UPTREND' and last['close'] <= last['support']*1.01 and 35 < last['rsi'] < 60:
                sl = last['support'] * 0.997
                tp = last['close'] + (last['close'] - sl) * 2.0 # RR 1:2
                lot = self.risk_management(SYMBOL, last['close'], sl)
                print(f"BUY SIGNAL -> Lot: {lot}, SL: {sl}, TP: {tp}")
                self.place_order(SYMBOL, "BUY", lot, sl, tp)

            # SELL Logic
            elif last['trend'] == 'DOWNTREND' and last['close'] >= last['resistance']*0.99 and 40 < last['rsi'] < 70:
                sl = last['resistance'] * 1.003
                tp = last['close'] - (sl - last['close']) * 2.0 # RR 1:2
                lot = self.risk_management(SYMBOL, last['close'], sl)
                print(f"SELL SIGNAL -> Lot: {lot}, SL: {sl}, TP: {tp}")
                self.place_order(SYMBOL, "SELL", lot, sl, tp)
            
            else:
                print("No Signal - HOLD")

            time.sleep(60) # ہر 1 منٹ بعد چیک کرے گا

# بوٹ اسٹارٹ
if __name__ == "__main__":
    bot = ExnessTradingBot()
    bot.run()
