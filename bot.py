from binance.client import Client
import configparser


class Bot(object):
    API_KEY = ''
    API_SECRET = ''
    SYMBOL = 'BTCUSDT'
    FEE = 0.01

    priceMax = float()
    priceMin = float()
    fibLevels = [1, 0.786, 0.618, 0.5, 0.382, 0.236, 0]
    fibList = []

    def __init__(self, logger):
        config = configparser.ConfigParser()
        config.read('conf.ini')
        self.API_KEY = config['API_KEYS']['api_key']
        self.API_SECRET = config['API_KEYS']['api_secret']
        self.priceMax = float(config['PRICES']['high'])
        self.priceMin = float(config['PRICES']['low'])
        diff = self.priceMax - self.priceMin
        for f in self.fibLevels:
            self.fibList.append(self.priceMax - f * diff)
        self.client = Client(self.API_KEY, self.API_SECRET)
        self.logger = logger
        logger.info('bot initiated with fibonacci levels {}'.format(self.fibList))

    def get_last_price(self):
        tickers = self.client.get_ticker()
        ticker = next(
            item for item in tickers if item["symbol"] == self.SYMBOL
        )
        self.logger.info('Last price on Binance is {}'.format(ticker['lastPrice']))
        return float(ticker['lastPrice'])

    def get_closest_fib_level(self, Number):
        aux = []
        _list = self.fibList
        for valor in _list:
            aux.append(abs(Number - valor))
        i = aux.index(min(aux))
        self.logger.info('closest fib level is {}'.format({self.fibLevels[i]: self.fibList[i]}))
        return {self.fibLevels[i]: self.fibList[i]}

    def get_balance(self, lastPrice):
        return [{'overall(usdt)': float(self.client.get_asset_balance(asset='BTC')['free']) * lastPrice + float(self.client.get_asset_balance(asset='USDT')['free']),
                 'overall(btc)': float(self.client.get_asset_balance(asset='BTC')['free']) + float(self.client.get_asset_balance(asset='USDT')['free'])/lastPrice},
                self.client.get_asset_balance(asset='USDT'), self.client.get_asset_balance(asset='BTC')]

    def _init_session(self):
        self.logger.info('Initiating a new trading session')
        lastPrice = self.get_last_price()
        self.currentFibLevel = self.get_closest_fib_level(lastPrice)
        self.balance = self.get_balance(lastPrice)
        self.logger.info('Current balance {}'.format(self.balance))
        self.apply_strategy()

    def buy(self, _quantity):
        lastPrice = self.get_last_price()
        self.logger.info('Attempting to buy BTC at rate {} and quantity {}'.format(lastPrice, _quantity / lastPrice))
        result = False
        try:
            result = self.client.order_market_buy(symbol=self.SYMBOL, quantity=round(_quantity / lastPrice, 4))
        except Exception as e:
            self.logger.error('Caught an error during buy: {}'.format(e))
        self.logger.info('Result: {}'.format(result))

    def sell(self, _quantity):
        lastPrice = self.get_last_price()
        self.logger.info('Attempting to sell BTC at rate {} and quantity {}'.format(lastPrice, _quantity / lastPrice))
        result = False
        try:
            result = self.client.order_market_sell(symbol=self.SYMBOL, quantity=round(_quantity / lastPrice, 4))
        except Exception as e:
            self.logger.error('Caught an error during sell: {}'.format(e))
        self.logger.info('Result: {}'.format(result))

    def has_level_changed(self):
        lastPrice = self.get_last_price()
        self.balance = self.get_balance(lastPrice)
        self.logger.info('Current balance is: {}'.format(self.balance))
        newFibLevel = self.get_closest_fib_level(lastPrice)
        if newFibLevel == self.currentFibLevel:
            return False
        elif abs(1 - lastPrice / list(newFibLevel.values())[0]) < 0.0009:
            self.logger.info('Value of current price nearing next Fib level, thus changing level: {}'.format(newFibLevel))
            self.currentFibLevel = newFibLevel
            return True
        elif abs(list(newFibLevel.values())[0] - list(self.currentFibLevel.values())[0]) < abs(lastPrice - list(self.currentFibLevel.values())[0]):
            self.logger.info('Value of current price has passed next Fib level, thus changing level: {}'.format(newFibLevel))
            self.currentFibLevel = newFibLevel
            return True
        else:
            return False

    def apply_strategy(self):
        overAll = self.balance[0]['overall(usdt)']
        fibLevel = list(self.currentFibLevel.keys())[0]
        diff = overAll - overAll * fibLevel
        change = diff - float(self.balance[1]['free'])
        if fibLevel != 1:
            change = change - change * self.FEE
        else:
            change = change - change * (self.FEE + 0.02)
        if abs(change) < 10:
            self.logger.info('Nothing to do, Level has not been changed')
            return True
        self.logger.info('Applying strategy, balance is : {}'.format(self.balance))
        if change < 0:
            self.logger.info('Change: {} is below zero'.format(change))
            self.buy(abs(change))
            return True
        elif change > 0:
            self.logger.info('Change: {} is above zero'.format(change))
            self.sell(change)
            return True
        else:
            self.logger.error('caught unknown error when applying strategy')
            return False
