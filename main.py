import hashlib
import hmac
import logging
import os
import time
import warnings
from datetime import datetime, timedelta
from urllib.parse import urlencode
import pytz

import pandas as pd
import requests
from binance.client import Client
from dotenv import load_dotenv

from Strategy import PairsTradingStrategy

warnings.filterwarnings("ignore")

# logging configuration
logging.basicConfig(
    format='%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("pairs_trading.txt"),
        logging.StreamHandler()
    ]
)

# URLs
BASE_URL = 'https://testnet.binancefuture.com'

def get_credentials():
    dotenv_path = './.env.py'
    load_dotenv(dotenv_path=dotenv_path)
    # return api key and secret as tuple
    return os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET')


def sign_url(secret: str, api_url, params: {}):
    # Create query string
    query_string = urlencode(params)

    # Signature
    signature = hmac.new(secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256).hexdigest()

    # URL
    return BASE_URL + api_url + "?" + query_string + "&signature=" + signature


def send_market_order(key: str, secret: str, sym: str, quantity: float, side: bool):
    # Order parameters
    timestamp = int(time.time() * 1000)
    side_str = "BUY" if side else "SELL"
    order_params = {
        "symbol": sym,
        "side": side_str,
        "type": "MARKET",
        "quantity": quantity,
        'timestamp': timestamp
    }

    logging.info(
        'Sending market order: Symbol: {}, Side: {}, Quantity: {}'.
        format(sym, side_str, quantity)
    )

    # New order URL
    url = sign_url(secret, '/fapi/v1/order', order_params)

    # POST order request
    session = requests.Session()
    session.headers.update(
        {"Content-Type": "application/json;charset=utf-8", "X-MBX-APIKEY": key}
    )
    post_response = session.post(url=url, params={})
    post_response_data = post_response.json()

    return post_response_data


def get_credentials():
    dotenv_path = './.env.py'
    load_dotenv(dotenv_path=dotenv_path)
    return os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET')

def extract_sp(assets, pairs):
    # 获取API key和secret
    api_key, api_secret = get_credentials()

    # 初始化Binance客户端
    client = Client(api_key, api_secret)

    # 获取当前时间，并将其调整到最近的整点小时 (使用UTC时间)
    now = datetime.now(pytz.utc)
    now = now.replace(minute=0, second=0, microsecond=0)

    # 获取pairs数据框中最后一个时间点并本地化为UTC
    last_time = pairs.index.max().tz_convert('UTC')

    # 计算需要获取数据的开始时间
    start_time = last_time + timedelta(hours=1)
    start_time_str = start_time.strftime('%d %b, %Y %H:%M:%S')
    end_time_str = now.strftime('%d %b, %Y %H:%M:%S')

    def data(ticker):
        klines = client.get_historical_klines(ticker, Client.KLINE_INTERVAL_1HOUR, start_time_str, end_time_str)
        df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close',
                                           'volume', 'close_time', 'quote_asset_volume',
                                           'number_of_trades', 'taker_buy_base_asset_volume',
                                           'taker_buy_quote_asset_volume', 'ignore']
                          )
        df['close'] = df['close'].astype(float)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        df = df[['timestamp', 'close']].set_index('timestamp')
        df.columns = [ticker]
        return df

    new_crypto_data = [data(ticker) for ticker in assets]
    new_data = pd.concat(new_crypto_data, axis=1)

    # 合并新的数据到pairs数据框中
    pairs_updated = pairs.append(new_data).drop_duplicates(keep='last').sort_index()

    return pairs_updated

    new_crypto_data = [data(ticker) for ticker in assets]
    new_data = pd.concat(new_crypto_data, axis=1)

    # 合并新的数据到pairs数据框中
    pairs_updated = pairs.append(new_data).drop_duplicates(keep='last').sort_index()

    return pairs_updated

if __name__ == '__main__':
    # strategy parameters
    z_signal_in = 1.96
    z_signal_out = 0.25
    min_spread = 0.005
    MA_window = 90
    OLS_window = 365 * 24
    boll_window = 15
    std_multiplier = 1.96

    # 读取CSV文件
    pairs = pd.read_csv("pairs.csv")
    pairs.set_index('Date', inplace=True)
    pairs.index = pd.to_datetime(pairs.index)
    pairs.index = pairs.index.tz_localize('UTC')

    # 获取API密钥和秘钥
    api_key, api_secret = get_credentials()

    # 创建头寸数据框
    positions = pd.DataFrame(columns=['position_Y', 'position_X'], index=pairs.index)

    while True:
        # print program condition
        logging.info('Starting a new iteration of the trading loop.')

        # update and fill pairs
        assets = ['XRPUSDT', 'BCHUSDT']
        pairs = extract_sp(assets, pairs)

        print(pairs.tail())


        # calculate position using module "Strategy"
        strategy = PairsTradingStrategy(pairs,'XRPUSDT','BCHUSDT', z_signal_in, z_signal_out, min_spread, MA_window,
                                        OLS_window, 'cumpnl', boll_window, std_multiplier)
        results = strategy.pairs_trading_strategy()
        results_with_stop_loss = strategy.bollinger_band_stop_loss()

        print(results_with_stop_loss.head())
        # get our new position
        new_position_Y = results_with_stop_loss['position_Y'].iloc[-1]
        new_position_X = results_with_stop_loss['position_X'].iloc[-1]

        # get our previous position (if any)
        if len(positions) > 1:
            prev_position_Y = positions['position_Y'].iloc[-1]
            prev_position_X = positions['position_X'].iloc[-1]
        else:
            prev_position_Y = 0
            prev_position_X = 0

        # calculate order quantity
        order_qty_Y = new_position_Y - prev_position_Y
        order_qty_X = new_position_X - prev_position_X


        order_qty_Y = order_qty_Y*1000
        order_qty_X = order_qty_X*1000
        order_qty_Y = order_qty_Y.round(4)
        order_qty_X = order_qty_X.round(4)


        # ensure hte order quantity is not null
        if pd.isna(order_qty_Y):
            order_qty_Y = 0
        if pd.isna(order_qty_X):
            order_qty_X = 0

        # trade using our new position
        if order_qty_Y != 0:
            is_buy = order_qty_Y > 0
            filled_price_Y = send_market_order(api_key, api_secret, 'XRPUSDT', abs(order_qty_Y), is_buy)
            logging.info('Filled price for XRPUSDT: {}'.format(filled_price_Y))
        else:
            logging.info('No change in position for XRPUSDT. No order sent.')

        if order_qty_X != 0:
            is_buy = order_qty_X > 0
            filled_price_X = send_market_order(api_key, api_secret, 'BCHUSDT', abs(order_qty_X), is_buy)
            logging.info('Filled price for BCHUSDT: {}'.format(filled_price_X))
        else:
            logging.info('No change in position for BCHUSDT. No order sent.')

        # update our position
        new_index = pairs.index[-1]
        positions.loc[new_index] = [new_position_Y, new_position_X]

        # output our updated position and pairs to help to check
        positions.to_csv("./positions.csv")
        pairs.to_csv("./pairs_updated.csv")

        # print program condition and wait for 1 hour
        logging.info('Iteration complete. Sleeping for 1hr.')
        time.sleep(3600)