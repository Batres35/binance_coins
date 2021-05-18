# Binance Coins
A binance correlated coins finder

## Setup

### Binance setup

-   Create a [Binance account](https://www.binance.com/en/register?ref=93017299) (Includes my referral link, I'll be super grateful if you use it).
-   Enable Two-factor Authentication.
-   Create a new API key.
-   Save it to use it later.

### CoinMarketCap Developers setup

-   Create a [CoinMarketCap Developer account](https://coinmarketcap.com/api/).
-   Create a new API key.
-   Save it to use it later.

### Install Python dependencies

Run the following line in the terminal: `pip3 install -r requirements.txt`.

### Create configuration

Copy file `config_example.ini` and rename it as `config.ini`, then add your API keys.

The configuration file consists of the following fields:

-   **binance_api_key** - Binance API key generated in the Binance account setup stage.
-   **binance_api_secret_key** - Binance secret key generated in the Binance account setup stage.
-   **coinmarketcap_api_key** - CoinMarketCap Developers key generated in the CoinMarketCap asetup stage.
-   **history_start** - Time from which coins history data will be fetched.
-   **paired_coin** - Coin that will be paired with all existing coins on Binance in the process of downloading the history data.
-   **top_n_ranked_coins** - Number of top coins that will be fetched from CoinMarketCap.
-   **first_n_coins** - Coins number on 'used_coins' file that will be used in process.
-   **correlation_greater_than** - Condition to show the coins that have a bigger correlation value that this parameter (from -1 to 1).
-   **correlation_less_than** - Condition to show the coins that have a less correlation value that this parameter (from -1 to 1).


## Usage

### Download Coins History

Run this code to retrieve all the coins history that are paired with the currency set in `paired_coin` field of the configuration file:

```shell
python3 binance_coins.py --update-coins-history 
```

### Download Top Coins in CoinMarketCap

Run this code to fetch the top coins listed in CoinMarketCap, the number of coins is set in the field `top_n_ranked_coins` filed of the configuration file.

```shell
python3 binance_coins.py --update-top-coins 
```

### Functionality

The program will calculate the correlation of all the coins listed in the `used_coins` file and will show the ones that the correlation are bigger that the `correlation_greater_than` filed and less than the `correlation_less_than` field, based on the pearson correlation values in a scale of -1 and 1.
Also you can hide the coins that you dont want to be showed creating a file called `ignored_coins` and put in there the coins in the same format that `used_coins` file.

### Options

You have the following options to run this program:

        --all-correlated-values                 Correlation values of all coins in 'used_coins' file.
        --one-correlated-values <coin>          Correlation values of all coins in 'used_coins' file with one.
        --all-correlated-list                   List of all correlated coins in 'used_coins' file.
        --one-correlated-list <coin>            List of all correlated coins in 'used_coins' file with one.
        --all-correlated-grouped                List of all correlated coins in 'used_coins' file grouped by their relationship.
