#!/usr/bin/python
import time
from bot import Bot
from botlogger import Logger

botLogger = Logger()
logger = botLogger.init_logger()
logger.info('Fibonacci Trading system initiated')
_bot = Bot(logger)
_bot._init_session()
try:
    while 1:
        try:
            try:
                res = _bot.has_level_changed()
                if res is True:
                    logger.info('We have moved to a new fib level {}'.format(_bot.currentFibLevel))
                    _bot.apply_strategy()
                time.sleep(5)
            except Exception as e:
                logger.error('caught an error during transaction {}'.format(e))
                continue
        except KeyboardInterrupt:
            print ("Stopping...")
            break
finally:
    print ('stopped')
