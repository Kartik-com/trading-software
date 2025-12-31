import ccxt
import config

def check_kraken():
    exchange = ccxt.kraken()
    print("Kraken markets loaded...")
    # symbols = exchange.load_markets()
    # Check if BTC/USD is in symbols
    options = ["BTC/USD", "XBT/USD", "BTC/USDT", "ETH/USD"]
    for sym in options:
        try:
            print(f"Checking {sym}: {exchange.market(sym)['id']}")
        except:
            print(f"Checking {sym}: NOT FOUND")

if __name__ == "__main__":
    check_kraken()
