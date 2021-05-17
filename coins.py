from datetime import datetime
import pandas as pd
import numpy as np
import os
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceWithdrawException
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import time
import itertools as it
import json
import math
import sys
import getopt
import configparser


binance_api_key = ""
binance_api_secret_key = ""
coinmarketcap_api_key = ""
first_n_coins = 100
top_n_ranked_coins = 100
correlation_greater_than = 0.90
correlation_less_than = 1
paired_coin = "USDT"
history_start = "90 day ago UTC"
history_interval = Client.KLINE_INTERVAL_12HOUR
coin_history_file = 'historical_klines.json'
all_coins_file = 'all_coins'
ignored_coins_file = 'ignored_coins'

client = Client()


def get_coins_from_file(file):
    supported_coin_list = []

    if os.path.exists(file):
        with open(file) as rfh:
            for line in rfh:
                line = line.strip()
                if not line or line.startswith("#") or line in supported_coin_list:
                    continue
                supported_coin_list.append(line)
    else:
        raise Exception("Coin list not found")

    return supported_coin_list


def get_all_tickers(bridge):
    coins = []
    for ticker in client.get_all_tickers():
        if(bridge in ticker['symbol']):
            coins.append(ticker['symbol'].replace(bridge, ''))
    return coins


def klines_to_df(klines):
    df = pd.DataFrame.from_records(klines, columns=['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time',
                                   'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    df['change'] = df.apply(lambda row: (
        (float(row.close) - float(row.open))/float(row.open))*100, axis=1)
    df['normalized'] = (df['close'].astype('float') - df['close'].astype('float').min()) / \
        (df['close'].astype('float').max()-df['close'].astype('float').min())
    return df


def pearson_correlation(x, y):
    lenght = len(x) if len(x) <= len(y) else len(y)
    meanx = sum(x)/lenght
    meany = sum(y)/lenght

    num = 0
    for i in range(lenght):
        num += ((x[i]-meanx)*(y[i]-meany))

    denx = 0
    deny = 0
    for i in range(lenght):
        denx += pow(x[i]-meanx, 2)
        deny += pow(y[i]-meany, 2)

    den = math.sqrt(denx*deny)

    return num/den


def get_all_coins_combinations(coin_list):
    filtered_coin_list = []
    combinations = []

    for coin in coin_list:
        filtered_coin_list.append(coin)

    for combination in list(it.product(filtered_coin_list, repeat=2)):
        if(combination[0] != combination[1]):
            combinations.append(combination)

    output = set(map(lambda x: tuple(sorted(x)), combinations))

    return output


def get_one_coin_combinations(coin_list, coin):
    combinations = []
    for c in coin_list:
        if(c != coin):
            combinations.append((c, coin))

    return combinations


def get_coins_history(coin_list, bridge):
    klines = {}

    count = 0
    for coin in coin_list:

        print("Getting "+coin+bridge+" history data... " +
              str(round((count*100)/len(coin_list))) + "%")
        try:
            coin_klines = client.get_historical_klines(
                coin+bridge, history_interval, history_start)
            klines[coin] = coin_klines
        except BinanceAPIException as e:
            pass
        count = count + 1

    return klines


def get_existing_coins(coin_list, coins_history):
    existing_coins = []
    for coin in coin_list:
        if coin in coins_history:
            existing_coins.append(coin)
    return existing_coins


def get_one_correlated_values(correlated_coin):
    verify_coins_files()

    coins_history = read_coins_history_file()
    ignored_coins = get_coins_from_file(ignored_coins_file)

    coin_list = []
    [coin_list.append(x) for x in get_coins_from_file(
        all_coins_file)[:first_n_coins] if x in coins_history and x not in ignored_coins]

    if correlated_coin not in coins_history:
        raise Exception("Coin not found")

    correlations = []
    sorted_correlations = {}

    combinations = get_one_coin_combinations(
        coin_list, correlated_coin)

    for coins in combinations:
        correlations.append({"coin_a": coins[0], "coin_b": coins[1], "correlation": pearson_correlation(
            coins_history[coins[0]]['normalized'].tolist(), coins_history[coins[1]]['normalized'].tolist())})

    filtered_correlations = [
        c for c in correlations if c['correlation'] > correlation_greater_than and c['correlation'] < correlation_less_than]
    sorted_correlations = sorted(
        filtered_correlations, key=lambda i: i['correlation'])

    for c in sorted_correlations:
        print(c['coin_a']+"/"+c['coin_b']+": "+str(round(c['correlation'], 2)))


def get_one_correlated_list(correlated_coin):
    verify_coins_files()

    coins_history = read_coins_history_file()
    ignored_coins = get_coins_from_file(ignored_coins_file)

    coin_list = []
    [coin_list.append(x) for x in get_coins_from_file(
        all_coins_file)[:first_n_coins] if x in coins_history and x not in ignored_coins]

    if correlated_coin not in coins_history:
        raise Exception("Coin not found")

    correlations = []
    sorted_correlations = {}

    combinations = get_one_coin_combinations(
        coin_list, correlated_coin)

    for coins in combinations:
        correlations.append({"coin_a": coins[0], "coin_b": coins[1], "correlation": pearson_correlation(
            coins_history[coins[0]]['normalized'].tolist(), coins_history[coins[1]]['normalized'].tolist())})

    filtered_correlations = [
        c for c in correlations if c['correlation'] > correlation_greater_than and c['correlation'] < correlation_less_than]
    sorted_correlations = sorted(
        filtered_correlations, key=lambda i: i['correlation'])

    correlated_coin_list = []
    filtered_correlated_coin_list = []

    for c in sorted_correlations:
        correlated_coin_list.append(c['coin_a'])
        correlated_coin_list.append(c['coin_b'])

    [filtered_correlated_coin_list.append(
        x) for x in correlated_coin_list if x not in filtered_correlated_coin_list]

    print(filtered_correlated_coin_list)


def get_all_correlated_values():
    verify_coins_files()

    coins_history = read_coins_history_file()
    ignored_coins = get_coins_from_file(ignored_coins_file)

    coin_list = []
    [coin_list.append(x) for x in get_coins_from_file(
        all_coins_file)[:first_n_coins] if x in coins_history and x not in ignored_coins]

    correlations = []
    sorted_correlations = {}

    combinations = get_all_coins_combinations(coin_list)

    for coins in combinations:
        correlations.append({"coin_a": coins[0], "coin_b": coins[1], "correlation": pearson_correlation(
            coins_history[coins[0]]['normalized'].tolist(), coins_history[coins[1]]['normalized'].tolist())})

    filtered_correlations = [
        c for c in correlations if c['correlation'] > correlation_greater_than and c['correlation'] < correlation_less_than]
    sorted_correlations = sorted(
        filtered_correlations, key=lambda i: i['correlation'])

    for c in sorted_correlations:
        print(c['coin_a']+"/"+c['coin_b']+": "+str(round(c['correlation'], 2)))


def get_all_correlated_grouped():
    verify_coins_files()

    coins_history = read_coins_history_file()
    ignored_coins = get_coins_from_file(ignored_coins_file)
    coin_list = []
    [coin_list.append(x) for x in get_coins_from_file(
        all_coins_file)[:first_n_coins] if x in coins_history and x not in ignored_coins]

    correlations = []

    combinations = get_all_coins_combinations(coin_list)

    for coins in combinations:
        correlations.append({"coin_a": coins[0], "coin_b": coins[1], "correlation": pearson_correlation(
            coins_history[coins[0]]['normalized'].tolist(), coins_history[coins[1]]['normalized'].tolist())})

    filtered_correlations = [
        c for c in correlations if c['correlation'] > correlation_greater_than and c['correlation'] < correlation_less_than]

    group_correlations(filtered_correlations)


def get_all_correlated_list():
    verify_coins_files()

    coins_history = read_coins_history_file()
    ignored_coins = get_coins_from_file(ignored_coins_file)
    coin_list = []
    [coin_list.append(x) for x in get_coins_from_file(
        all_coins_file)[:first_n_coins] if x in coins_history and x not in ignored_coins]

    correlations = []

    combinations = get_all_coins_combinations(coin_list)

    for coins in combinations:
        correlations.append({"coin_a": coins[0], "coin_b": coins[1], "correlation": pearson_correlation(
            coins_history[coins[0]]['normalized'].tolist(), coins_history[coins[1]]['normalized'].tolist())})

    filtered_correlations = [
        c for c in correlations if c['correlation'] > correlation_greater_than and c['correlation'] < correlation_less_than]

    correlated_coin_list = []
    filtered_correlated_coin_list = []

    for c in filtered_correlations:
        correlated_coin_list.append(c['coin_a'])
        correlated_coin_list.append(c['coin_b'])

    [filtered_correlated_coin_list.append(
        x) for x in correlated_coin_list if x not in filtered_correlated_coin_list]

    print(filtered_correlated_coin_list)


def group_correlations(correlations):
    l = [(c["coin_a"], c["coin_b"])
         for c in correlations]
    pool = set(map(frozenset, l))
    groups = []
    coin_groups = []
    while pool:
        group = set()
        groups.append([])
        while True:
            for candidate in pool:
                if not group or group & candidate:
                    group |= candidate
                    groups[-1].append(tuple(candidate))
                    pool.remove(candidate)
                    break
            else:
                break

    for g in groups:
        separated = []
        coin_list = []
        for c in g:
            separated.append(c[0])
            separated.append(c[1])
        for x in separated:
            if(x not in coin_list):
                coin_list.append(x)
        coin_groups.append(coin_list)

    for i in range(len(coin_groups)):
        print("Group "+str(i+1)+":")
        print(coin_groups[i])


def verify_coins_files():
    if not os.path.isfile(coin_history_file):
        raise Exception(
            "Coin history '"+coin_history_file+"' not found, please run: coin.py --update-coins-history")

    if not os.path.isfile(all_coins_file):
        raise Exception(
            "Top coins file '"+all_coins_file+"' not found, please run: coin.py --update-top-coins")


def update_coin_historical_klines():
    coins_history = get_coins_history(
        get_all_tickers(paired_coin), paired_coin)
    with open(coin_history_file, 'w') as outfile:
        json.dump(coins_history, outfile)


def read_coins_history_file():
    kline_df = {}
    data = {}

    with open(coin_history_file) as json_file:
        data = json.load(json_file)

    for coin in data:
        if(len(data[coin]) > 0):
            kline_df[coin] = klines_to_df(data[coin])

    return kline_df


def update_top_ranked_coins():
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    parameters = {
        'start': '1',
        'limit': top_n_ranked_coins,
        'convert': 'USD'
    }
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': coinmarketcap_api_key,
    }

    session = Session()
    session.headers.update(headers)

    print("Getting top "+str(top_n_ranked_coins)+" coins...")
    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        with open(all_coins_file, 'w') as writer:
            for coin in data['data']:
                writer.write(coin['symbol']+'\n')
        print("Top coin list stored successfully!")
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)


def load_configuration():
    global binance_api_key, binance_api_secret_key, coinmarketcap_api_key, client, first_n_coins, top_n_ranked_coins, correlation_greater_than, correlation_less_than, paired_coin, history_start, history_interval, coin_history_file, all_coins_file, ignored_coins_file
    config = configparser.ConfigParser()
    config.read('config.ini')

    binance_api_key = config['binance_coins']['binance_api_key']
    binance_api_secret_key = config['binance_coins']['binance_api_secret_key']
    coinmarketcap_api_key = config['binance_coins']['coinmarketcap_api_key']
    first_n_coins = int(config['binance_coins']['first_n_coins'])
    top_n_ranked_coins = int(config['binance_coins']['top_n_ranked_coins'])
    correlation_greater_than = float(
        config['binance_coins']['correlation_greater_than'])
    correlation_less_than = float(
        config['binance_coins']['correlation_less_than'])
    paired_coin = config['binance_coins']['paired_coin']
    history_start = config['binance_coins']['history_start']
    history_interval = config['binance_coins']['history_interval']
    coin_history_file = config['binance_coins']['coin_history_file']
    all_coins_file = config['binance_coins']['all_coins_file']
    ignored_coins_file = config['binance_coins']['ignored_coins_file']
    client = Client(binance_api_key, binance_api_secret_key)


def main(argv):
    load_configuration()
    try:
        opts, args = getopt.getopt(
            argv, "h", ["update-coins-history", "update-top-coins", "all-correlated-values", "one-correlated-values=", "all-correlated-list", "one-correlated-list=", "all-correlated-grouped"])
    except getopt.GetoptError:
        print("usage:\t"+"coins.py [--option]")
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print("usage: coins.py""\t[--option value]")
            print(
                "\t[--update-coins-history]\t#Updates the historical price of all the coins in Binance.")
            print(
                "\t[--update-top-coins]\t\t#Updates the list of the 100 best coins in CoinMarketCap.")
            print("\t[--all-correlated-values]\t#Correlation values of all coins.")
            print(
                "\t[--one-correlated-values coin]\t#Correlation values of all coins with one.")
            print("\t[--all-correlated-list]\t\t#List of all correlated coins.")
            print(
                "\t[--one-correlated-list coin]\t#List of all correlated coins with one.")
            print(
                "\t[--all-correlated-grouped]\t#List of all correlated coins grouped by their relationship.")
            sys.exit()
        elif opt in ("--update-coins-history"):
            update_coin_historical_klines()
        elif opt in ("--update-top-coins"):
            update_top_ranked_coins()
        elif opt in ("--all-correlated-values"):
            get_all_correlated_values()
        elif opt in ("--one-correlated-values"):
            get_one_correlated_values(arg)
        elif opt in ("--all-correlated-list"):
            get_all_correlated_list()
        elif opt in ("--one-correlated-list"):
            get_one_correlated_list(arg)
        elif opt in ("--all-correlated-grouped"):
            get_all_correlated_grouped()


if __name__ == "__main__":
    main(sys.argv[1:])
