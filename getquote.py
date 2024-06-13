import json
import requests
import argparse
import telegram
import keys
import os
import pytz
import yfinance as yf
from datetime import datetime, time, timedelta
from decimal import Decimal
from twilio.rest import Client
from yahoo_fin.stock_info import get_live_price
from telegram.ext import Updater, MessageHandler, Filters

holidays = ["26-Jan-24", "8-Mar-24", "25-Mar-24", "29-Mar-24", "11-Apr-24",
            "17-Apr-24", "1-May-24", "17-Jun-24", "17-Jul-24", "15-Aug-24",
            "2-Oct-24", "1-Nov-24", "15-Nov-24", "26-Dec-24"]

dirpath = "/root/stockdata/"

# Load data from the JSON file
with open('/root/stockTicker/stock-options-update/india_data.json', 'r') as f:
    data = json.load(f)

holdings = data.get("holdings", [])
target_profit = data.get("target_profit", [])
target_stocks = data.get("target_stocks", [])
new_plan = data.get("new_plan", [])

# Create a Twilio client
client = Client(keys.account_sid, keys.auth_token)

def is_current_time_greater_than(target_hour, target_minute, timezone_name):
    current_time = datetime.now(pytz.timezone(timezone_name)).time()
    target_time = time(target_hour, target_minute)
    return current_time > target_time

def is_current_time_lesser_than(target_hour, target_minute, timezone_name):
    current_time = datetime.now(pytz.timezone(timezone_name)).time()
    target_time = time(target_hour, target_minute)
    return current_time < target_time

def get_change(symbol):
    ticker = yf.Ticker(symbol)
    todays_data = ticker.history(period='2d')
    return round(todays_data['Close'].pct_change()[1] * 100, 1), round(todays_data['Close'][1] - todays_data['Close'][0], 1)

def get_current_price(symbol, which_day):
    ticker = yf.Ticker(symbol)
    todays_data = ticker.history(period='2d')
    return round(todays_data['Close'][1], 1) if which_day == 0 else round(todays_data['Close'][0], 1)

def send(msg, chat_id, token):
    bot = telegram.Bot(token=token)
    bot.sendMessage(chat_id=chat_id, text=msg, parse_mode=telegram.ParseMode.HTML)

def track_stocks(list_stocks):
    statement = ''
    twilio_statement = []
    if not list_stocks:
        return
    today_date = datetime.today().strftime('%d-%m-%Y')
    nifty_file_name_full = os.path.join(dirpath, "NIFTY_CALL_" + today_date)
    if not os.path.exists(nifty_file_name_full):
        last_price = get_current_price("^NSEI", 0)
        perc_change, change = get_change("^NSEI")
        if abs(change) > 200:
            twilio_statement.append(f"NIFTY moved by:{change} lastprice:{last_price}")
            os.mknod(nifty_file_name_full)

    for stock_data in list_stocks:
        stock_name = stock_data[0].rstrip('.NS').rstrip('.BO')
        file_name_full = os.path.join(dirpath, stock_name + "_CALL_" + today_date)
        file_name_perc_hit = os.path.join(dirpath, stock_name + "_PERC_" + today_date)

        if not os.path.exists(file_name_perc_hit):
            last_price = get_current_price(stock_data[0], 0)
            perc_change, _ = get_change(stock_data[0])
            if abs(perc_change) > 5:
                statement += f"<b>{stock_name}</b> just changed by <b>{perc_change}%</b>, last_price:{last_price}."
                twilio_statement.append(f"{stock_name} just changed by {perc_change} percent, last_price:{last_price}.")
                os.mknod(file_name_perc_hit)

        if not os.path.exists(file_name_full):
            last_price = get_current_price(stock_data[0], 0)
            stock_name = stock_data[0].rstrip('.NS').rstrip('.BO')
            condition = (stock_data[2] == 0 and last_price > stock_data[1]) or (stock_data[2] == 1 and last_price < stock_data[1])
            if condition:
                action = "went above" if stock_data[2] == 0 else "broke below"
                twilio_statement.append(f"{stock_name} just {action} the tracking price:{stock_data[1]} lastprice:{last_price}.")
                statement += f"<b>{stock_name}</b> just {action} the tracking price:<b>{stock_data[1]}</b> lastprice:<b>{last_price}</b>."
                os.mknod(file_name_full)

    if statement:
        send(f"<b>Tracking Alert\n</b>{statement}", keys.chat_id, keys.token)
        make_twilio_call(twilio_statement)

def make_twilio_call(twilio_statement):
    from_number = keys.from_number
    to_numbers = keys.to_number
    twiml_content = "<Response>\n"
    twiml_content += "    <Pause length=\"5\"/>\n"
    twiml_content += "    <Say voice=\"alice\">Listen to this carefully:</Say>\n"
    twiml_content += "    <Pause length=\"2\"/>\n"
    for message in twilio_statement:
        twiml_content += f"    <Say voice=\"alice\">{message}</Say>\n"
        twiml_content += "    <Pause length=\"2\"/>\n"
    twiml_content += "</Response>"
    for to_number in to_numbers:
        client.calls.create(to=to_number, from_=from_number, twiml=twiml_content)

def initial_payout(which_plan, headers, cookies):
    payout = 0
    statement = "Holdings:\n" if int(which_plan) == 1 else "New Plan:\n"
    dataset = holdings if int(which_plan) == 1 else new_plan

    nifty_quote = yf.Ticker('^NSEI').info
    last_price = get_live_price("^NSEI")
    change = round(last_price - nifty_quote['previousClose'], 1)
    perc_change = round((Decimal(change) * 100) / (Decimal(nifty_quote['previousClose'])), 1)
    statement += f"<b>Nifty:{round(last_price)}, change:{change}({perc_change}%)</b>\n\n"

    for i, block in enumerate(dataset):
        statement += f"Block:{i}\n"
        for index, element in enumerate(block):
            if len(element) == 3:
                stock_quote = yf.Ticker(element[0] + '.NS').info
                last_price = stock_quote['currentPrice']
                change = round(last_price - stock_quote['previousClose'], 1)
                perc_change = round((Decimal(change) * 100) / (Decimal(stock_quote['previousClose'])), 1)
                statement += f"<b>{element[0]}:{last_price}, change:{change}({perc_change}%) </b>\n"
                payout = round(last_price * element[1], 1)
                statement += f"{index}>qty:{element[1]} p/unit:{last_price}, buy p/u:{element[2]} <b>debit:{payout}</b>\n\n"
            else:
                statement += process_option_data(element, headers, cookies, index, block)
        statement += f"Block:{i} Payout:{-payout}\n"
    send(statement, keys.chat_id, keys.token)

def process_option_data(element, headers, cookies, index, block):
    if element[0] != "NIFTY":
        url = "https://www.nseindia.com/api/option-chain-equities?symbol=" + element[0]
    else:
        url = "https://www.nseindia.com/api/option-chain-indices?symbol=" + element[0]
    if index == 0:
        option_data = requests.get(url, headers=headers, cookies=cookies).json()
        d = option_data['records']['data']
    profit_step = round(([x[element[3]]['lastPrice'] for x in d if (x['strikePrice'] == element[1] and x['expiryDate'] == element[2])][0]) * element[4], 1)
    implied_volatility = ([x[element[3]]['impliedVolatility'] for x in d if (x['strikePrice'] == element[1] and x['expiryDate'] == element[2])][0])
    last_price = round([x[element[3]]['lastPrice'] for x in d if (x['strikePrice'] == element[1] and x['expiryDate'] == element[2])][0], 2)
    return f"{index}>strike:{element[1]} qty:{element[4]} p/unit:{last_price} expiry:{datetime.strftime(datetime.strptime(element[2], '%d-%b-%Y'), '%d-%b')} type:{element[3]} <b>debit:{profit_step}</b>, IV:{implied_volatility}\n"

def fetch_option_data(symbol, headers, cookies):
    url = "https://www.nseindia.com/api/option-chain-equities?symbol=" + symbol if symbol != "NIFTY" else "https://www.nseindia.com/api/option-chain-indices?symbol=" + symbol
    return requests.get(url, headers=headers, cookies=cookies).json()

def process_stock(element):
    last_price = get_current_price(element[0], 0)
    perc_change, change = get_change(element[0].upper())
    profit_block = round((last_price - element[2]) * element[1], 1)
    today_profit = round(element[1] * Decimal(change))
    target_price = next(stock[1] for stock in target_stocks if stock[0] == element[0] and stock[2] == 0)
    lower_price = next(stock[1] for stock in target_stocks if stock[0] == element[0] and stock[2] == 1)
    return last_price, perc_change, change, profit_block, today_profit, target_price, lower_price

def process_option(element, headers, cookies, option_data):
    d = option_data['records']['data']
    profit_step = round(([x[element[3]]['lastPrice'] for x in d if (x['strikePrice'] == element[1] and x['expiryDate'] == element[2])][0] - element[5]) * element[4], 1)
    last_price = round([x[element[3]]['lastPrice'] for x in d if (x['strikePrice'] == element[1] and x['expiryDate'] == element[2])][0], 1)
    implied_volatility = ([x[element[3]]['impliedVolatility'] for x in d if (x['strikePrice'] == element[1] and x['expiryDate'] == element[2])][0])
    return profit_step, last_price, implied_volatility

def calculate_profit(headers, cookies):
    statement = ""
    last_price = get_current_price("^NSEI", 0)
    perc_change, change = get_change("^NSEI")
    statement += f"<b>Nifty:{round(last_price)}, change:{change}({perc_change}%)</b>\n\n"

    current_minute = datetime.now().minute  # Get the current minute
    allowed_minutes = [3, 33, 45]  # Define the allowed minutes

    #Check if the current minute is one of the allowed minutes
    if current_minute not in allowed_minutes:
        return

    if not holdings:
        return

    total_profit = 0
    today_profit = 0

    for i, block in enumerate(holdings):
        profit_block = 0
        profit_closed = 0
        statement += f"Block:{i}\n"

        option_data = None
        for index, element in enumerate(block):
            if len(element) == 3:  # Stock
                last_price, perc_change, change, profit, today_profit_stock, target_price, lower_price = process_stock(element)
                today_profit += today_profit_stock
                total_profit += profit
                profit_block += profit
                statement += f"<b>{element[0].replace('.NS', '').replace('.BO', '')}:{last_price}, change:{change}(today:{perc_change}% Total:{profit}%)</b> Invested:{int(round(element[1] * element[2], -3) / 1000)}K <b>target:{target_price} lower alert:{lower_price}</b>\n"
                statement += f"{index}>qty:{element[1]} p/unit:{last_price}, buy p/u:{element[2]} <b>profit:{profit}</b> <b>today profit:{today_profit_stock}</b>\n\n"

            elif len(element) == 4:  # Partially booked stock
                profit_step = round(((element[3] - element[2]) * element[1]), 1)
                profit_closed += profit_step
                total_profit += profit_step
                profit_block += profit_step
                statement += f"<b>{element[0]}</b> qty:{element[1]} <b>Invested:{int(round(Decimal(element[1]) * Decimal(element[2]), -3) / 1000)}K profit:{profit_step} (F)</b>\n"

            else:  # Option
                if index == 0 and not option_data:
                    option_data = fetch_option_data(element[0], headers, cookies)

                if len(element) == 7:  # Closed option
                    profit_step = round(((element[6] - element[5]) * element[4]), 1)
                    profit_closed += profit_step
                    statement += f"{index}>strike:{element[1]} qty:{element[4]} exp:{datetime.strftime(datetime.strptime(element[2], '%d-%b-%Y'), '%d-%b')} profit:{profit_step} (F)\n"

                else:  # Open option
                    profit_step, last_price, implied_volatility = process_option(element, headers, cookies, option_data)
                    profit_block += profit_step
                    total_profit += profit_block
                    statement += f"{index}>strike:{element[1]} qty:{element[4]} p/unit:{last_price}, holding p/u:{element[5]} expiry:{datetime.strftime(datetime.strptime(element[2], '%d-%b-%Y'), '%d-%b')} type:{element[3]} <b>profit:{profit_step}</b>, IV:{implied_volatility}\n"

        statement += f"<b>Total profit:{profit_block}</b>\n\n"

    statement += f"Today profit:{today_profit} total profit:{total_profit}\n\n"

    # Send the message only if the current minute is one of the allowed minutes
    send(statement, keys.chat_id, keys.token)


def main():
    parser = argparse.ArgumentParser(description="Script to calculate profit and alert for stocks and options.")
    parser.add_argument("action", choices=["calculate_profit", "initial_payout", "track_stocks"], help="Action to perform")
    args = parser.parse_args()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }
    cookies = {
        'bm_sv': 'randomcookievalue',
    }

    if args.action == "calculate_profit":
        calculate_profit(headers, cookies)
        track_stocks(target_stocks)
    elif args.action == "initial_payout":
        initial_payout(1, headers, cookies)
    elif args.action == "track_stocks":
        track_stocks(target_stocks)

if __name__ == "__main__":
    main()

