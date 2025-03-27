from discord.ext import commands
import discord
from asyncio import sleep
import ccxt
import json
import sys
import traceback
import datetime, time
import sys
import argparse

parser = argparse.ArgumentParser()

parser.add_argument('--coin', dest='coin_name', type=str, help='Set coin name (Example: BTC/USDT)')
parser.add_argument('--decimal', dest='decimal', type=str, help='Set decimal place (Example: 2)')
args = parser.parse_args()

if not args.coin_name:
    print("Please set --coin! Example: --coin=BTC/USDT")
    sys.exit()

if not args.decimal:
    print("Please set --decimal! Example --decimal=2")
    sys.exit()

coin_name = args.coin_name
decimal_places = args.decimal
try:
    decimal_places = int(decimal_places)
    if decimal_places < 0:
        print("Error with decimal value!")
        sys.exit()        
except ValueError:
    print("Error with decimal value!")
    sys.exit()

# Set the bot token directly
bot_token = 'MTEyMzUwMzcxMjEyODczMzE4NA.G9UmSd.ehyalDZmMD1yw9j0CHc9NJsO8Cxze4Q2E6Wk6E'

# Create an instance of the Binance client from ccxt
binance = ccxt.binance()

async def get_binance_price(symbol: str, timeframe: str = '5m', limit: int = 1):
    try:
        # Ensure that the symbol is correctly formatted
        if '/' not in symbol:
            raise ValueError(f"Invalid symbol format: {symbol}. It should be in the format 'BASE/QUOTE', e.g., 'BTC/USDT'.")

        ohlcv = binance.fetch_ohlcv(symbol, timeframe, limit=limit)
        if ohlcv:
            # Fetch the close price of the most recent candle
            close_price = ohlcv[-1][4]
            return close_price
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
    return None

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    async def on_ready(self):
        print("Bot is online {}.".format(self.user.name))
        print("Invite link: https://discord.com/oauth2/authorize?client_id={}&scope=bot".format(self.user.id))
    
    async def setup_hook(self) -> None:
        self.coin_name = coin_name
        self.bg_task = self.loop.create_task(self.background_task())

    async def background_task(self):
        await self.wait_until_ready()
        while not self.is_closed():
            previous_nick = {}
            previous_status = None
            try:
                # Ensure that the coin_name is in the correct format 'BASE/QUOTE'
                if '/' not in self.coin_name:
                    self.coin_name = self.coin_name.replace("-", "/")  # Replace any dashes with a slash (if needed)

                symbol = f"{self.coin_name.upper()}"
                price = await get_binance_price(symbol)
                if price is None:
                    await sleep(10.0)
                    continue

                # Format the bot's nickname and status based on the price
                nick_me = f"{self.coin_name.upper()} ${price:.{decimal_places}f}"
                percentage_24h = await self.get_24h_percentage(symbol)
                p_place = 2
                status_me = f"24h ($): {percentage_24h:.{p_place}f}% ↘️"
                if percentage_24h > 0:
                    status_me = f"24h ($): +{percentage_24h:.{p_place}f}% ↗️"

                for guild in self.guilds:
                    me = guild.me
                    try:
                        if str(guild.id) not in previous_nick or (str(guild.id) in previous_nick and previous_nick[str(guild.id)] != nick_me):
                            await me.edit(nick=nick_me)
                            print("{} Change Bot name guild {} to {}!".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), guild.name, nick_me))
                            previous_nick[str(guild.id)] = nick_me
                        if previous_status != status_me:
                            await self.change_presence(activity=discord.Game(name=status_me))
                            previous_status = status_me
                            print("{} Set status to {}!".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), previous_status))
                        await sleep(5.0)
                    except Exception as e:
                        traceback.print_exc(file=sys.stdout)
            except Exception as e:
                traceback.print_exc(file=sys.stdout)
            await sleep(90.0)

    async def get_24h_percentage(self, symbol: str):
        try:
            ticker = binance.fetch_ticker(symbol)
            percentage_24h = ticker['percentage']
            return percentage_24h
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
        return 0.0

intents = discord.Intents.default()
client = MyClient(intents=discord.Intents.default())
client.run(bot_token)
