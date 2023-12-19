import requests
import argparse
import telegram
from nsetools import Nse
from datetime import datetime
import functools
import keys
import time
from datetime import datetime
import os
from decimal import Decimal
from yahoo_fin.stock_info import get_live_price
import yfinance as yf
from yahoo_fin.stock_info import get_live_price
from twilio.rest import Client
from twilio.twiml.voice_response import Gather, VoiceResponse

dirpath = "/root/stockdata/"

# Create a Twilio client
client = Client(keys.account_sid, keys.auth_token)

#holdings list should be ex: [['ASHOKLEY', 130, '26-May-2022', 'PE', -9000, 6.25], ['ASHOKLEY', 127.5, '26-May-2022', 'PE', 9000, 4.5]]
holdings = [
                [['HLVLTD.NS', 20000, 29.3 ]],
                [['SATINDLTD.NS', 6000, 116.75 ]],
                [['SYNCOMF.NS', 40000, 12.15 ]]
           ]

#target list ex: [[10000, -3000],[14000,-4000]] for 2 contracts. Each list contains profit and loss of each block for effective tractarget_profit = [[130000, -30000], [200000, -40000],  [90000, -22500], [65000, -15000], [156000, 31000],  [110000, -20000]]
target_profit = [[80000, -20000], [40000, -10000], [70000, -17000]]
#tracking list ex: [['POWERGRID.NS', 228, 0], ['SBIN.NS', 460, 1]]  #0 for going up, 1 for going down
target_stocks = [
                    ['HLVLTD.NS', 27.55, 1], ['SYNCOMF.NS', 11.2 1], ['SATINDLTD.NS', 105, 1],
                    ['HLVLTD.NS', 34, 0], ['SYNCOMF.NS', 15.0, 0], ['SATINDLTD.NS', 125, 0]
                ]

new_plan = [
              [
                ['ASHOKLEY', 130, '26-May-2022', 'PE', -9000],
                ['ASHOKLEY', 127.5, '26-May-2022', 'PE', 9000]
              ]
           ]

#return perc change in beginning, absolute value later
def get_change(symbol):
    ticker = yf.Ticker(symbol)
    todays_data = ticker.history(period='2d')
    return round(todays_data['Close'].pct_change()[1]*100,1), round(todays_data['Close'][1]-todays_data['Close'][0],1)

#which_day is 0 for today else 1 for yesterday
def get_current_price(symbol, which_day):
    ticker = yf.Ticker(symbol)
    todays_data = ticker.history(period='2d')
    return round(todays_data['Close'][1],1) if which_day == 0 else round(todays_data['Close'][0],1)


def send(msg, chat_id, token):
        """
        Send a message to a telegram user or group specified on chatId
        chat_id must be a number!
        """
        bot = telegram.Bot(token=token)
        bot.sendMessage(chat_id=chat_id, text=msg, parse_mode=telegram.ParseMode.HTML)



def track_stocks(list_stocks):
    statement = ''
    twilio_statement = []
    if not len(list_stocks):
        return
    today_date = datetime.today().strftime('%d-%m-%Y')
    for index, stock_data in enumerate(list_stocks):
        file_name_full = os.path.join(dirpath, stock_data[0]+"_CALL_"+today_date)
 
        if not os.path.exists(file_name_full):
            last_price = get_current_price(stock_data[0], 0)
            stock_name = stock_data[0].rstrip('.NS').rstrip('.BO')
            if (stock_data[2]==0) and (last_price > stock_data[1]):
                statement += "<b>{}</b> just went above the tracking price:<b>{}</b> lastprice:<b>{}</b>".format(stock_name, stock_data[1], last_price)
                twilio_statement.append("{} just went above the tracking price:{} lastprice:{}".format(stock_name, stock_data[1], last_price))
                #create file
                os.mknod(file_name_full)
            elif (stock_data[2]==1) and (last_price < stock_data[1]):
                twilio_statement.append("{} just broke below the tracking price:{} lastprice:{}".format(stock_name, stock_data[1], last_price))
                statement += "<b>{}</b> just broke below the tracking price:<b>{}</b> lastprice:<b>{}</b>".format(stock_name, stock_data[1], last_price)
                os.mknod(file_name_full)
    if statement:
        init_string = "<b>Tracking Alert\n</b>"
        statement = init_string + statement
        send(statement, keys.chat_id, keys.token)
        # Your Twilio phone number and the recipient's phone number (in E.164 format)
        from_number = keys.from_number
        to_number = keys.to_number  # Replace with the recipient's phone number

        twiml_content = "<Response>\n"
	# Iterate over the list of strings
        for message in twilio_statement:
            twiml_content += f"    <Say voice=\"alice\">{message}</Say>\n"
            twiml_content += "    <Pause length=\"2\"/>\n"
        twiml_content += "</Response>"
        # Make a phone call with TwiML content
        call = client.calls.create(
                       to=to_number,
                       from_=from_number,
                       twiml=twiml_content
                       )


def initial_payout(which_plan, headers, cookies):
    payout = 0
    statement = ""
    nse = Nse()
    if int(which_plan) == 1:
        dataset = holdings
        statement = "Holdings:\n"
    else:
        statement = "New Plan:\n"
        dataset = new_plan

    #nifty_quote = nse.get_index_quote("nifty 50")
    nifty_quote = yf.Ticker('^NSEI').info
    last_price = get_live_price("^NSEI")
    change = round(last_price - nifty_quote['previousClose'], 1)
    perc_change = round((Decimal(change)*100)/(Decimal(nifty_quote['previousClose'])),1)
    statement += "<b>Nifty:{}, change:{}({}\%)</b>\n\n".format(round(last_price), change, perc_change)

    for i, block in enumerate(dataset):
        statement += "Block:{}\n".format(str(i))
        payout = 0
        profit_step = 0
        for index, element in enumerate(block):
            #check if element is stock and not option
            if len(element) == 3:
                stock_quote = yf.Ticker(element[0]+'.NS').info
                last_price = stock_quote['currentPrice']
                change = round(last_price - stock_quote['previousClose'], 1)
                #quote_element = nse.get_quote(element[0])
                #last_price = quote_element.get('lastPrice')
                #change = quote_element.get('change')
                perc_change = round((Decimal(change)*100)/(Decimal(stock_quote['previousClose'])),1)
                statement += "<b>{}:{}, change:{}({}%) </b>\n".format(element[0], last_price, change, perc_change)
                payout = round(last_price*element[1],1)
                statement+="{}>qty:{} p/unit:{}, buy p/u:{} <b>debit:{}</b>\n\n".format(index, element[1], last_price, element[2], payout)
            else: #for options primarily
                if element[0] != "NIFTY":
                    url = "https://www.nseindia.com/api/option-chain-equities?symbol="+element[0]
                else:
                    url = "https://www.nseindia.com/api/option-chain-indices?symbol="+element[0]
                if index == 0:
                    quote_element = nse.get_quote(element[0])
                    last_price = quote_element.get('lastPrice')
                    change = quote_element.get('change')
                    statement += "<b>{}:{}, change:{} </b>\n".format(element[0], last_price, change)

                    option_data = requests.get(url, headers=headers, cookies=cookies)
                    p=option_data.text
                    import json
                    s=json.loads(option_data.text)
                    d=s['records']['data']
                # print(round(element[3]*element[4],1))
                profit_step = round(([x[element[3]]['lastPrice'] for x in d if
                                  (x['strikePrice'] == element[1] and x['expiryDate'] == element[2])][0])*element[4],1)
                implied_volatility = ([x[element[3]]['impliedVolatility'] for x in d if
                                  (x['strikePrice'] == element[1] and x['expiryDate'] == element[2])][0])
                last_price = round([x[element[3]]['lastPrice'] for x in d if (x['strikePrice']==element[1] and x['expiryDate']==element[2])][0], 2)
                statement += "{}>strike:{} qty:{} p/unit:{} expiry:{} type:{} payout:{}, IV:{}\n".format(index, element[1], element[4], last_price, datetime.strftime(datetime.strptime(element[2], "%d-%b-%Y"), "%d-%b"), element[3], -profit_step, implied_volatility)
                payout += profit_step
            statement += "Block:{} Payout:{}\n".format(str(i), str(-payout))
    send(statement, keys.chat_id, keys.token)


def calculate_profit(headers, cookies):
    profit = 0
    statement=""
    #nse = Nse()
    last_price = get_current_price("^NSEI", 0)
    perc_change, change = get_change("^NSEI")
    statement += "<b>Nifty:{}, change:{}({}%)</b>\n\n".format(round(last_price), change, perc_change)
    if not len(holdings):
        return
    total_profit_in_all_positions = 0
    today_profit = 0
    for i, block in enumerate(holdings):
        profit_closed = 0
        profit_step = 0
        profit_block = 0 #profit for this block
        send_closure_statement = False
        statement += "Block:{}\n".format(str(i))
        for index, element in enumerate(block):
            profit_open_positions = 0
            #check if element is stock and not option and is open not closed
            if len(element) == 3:
                stock_quote = yf.Ticker(element[0].upper()).info
                last_price = get_current_price(element[0],0)
                perc_change, change = get_change(element[0].upper())
                perc_change_invested = round(round(Decimal(last_price)-Decimal(str(element[2])),1)*100/round(Decimal(str(element[2])),1),1)
                statement += "<b>{}:{}, change:{}(today:{}% Total:{}%)</b> Invested:{}K\n".format(element[0].replace(".NS","").replace(".BO",""), last_price, change, perc_change, perc_change_invested, int(round(element[1]*element[2], -3)/1000))
                profit_block = round(((last_price - element[2])*element[1]),1)  #(last_price-buy_price)*qt
                today_profit_this_stock = round(element[1]*Decimal(change))
                today_profit += today_profit_this_stock
                total_profit_in_all_positions += profit_block
                statement+="{}>qty:{} p/unit:{}, buy p/u:{} <b>profit:{}</b> <b>today profit:{}</b>\n\n".format(index, element[1], last_price, element[2], int(profit_block), today_profit_this_stock)
            elif len(element) == 4: #if equity has been partly profit/loss booked
                profit_step = round(((element[3] - element[2])*element[1]),1) #(sell_price-buy_price)*qt
                statement += "<b>{}</b> qty:{} <b>Invested:{}K profit:{} (F)</b>\n".format(element[0], element[1],
                                                                                   int(round(Decimal(element[1])*Decimal(element[2]), -3)/1000),
                                                                                   int(profit_step))
                profit_closed += profit_step
            else: #for option lines or for partially/fully closed equity
                if element[0] != "NIFTY": #for index options
                    url = "https://www.nseindia.com/api/option-chain-equities?symbol="+element[0]
                    if index == 0:
                        if not all(x==7 for x in list(map(lambda x:len(x), block))):
                            last_price = get_current_price(element[0],0)
                            perc_change, change = get_change(element[0].upper())
                            statement += "<b>{}:{}, change:{}({}%)</b>\n".format(element[0], last_price, change, perc_change)
                        else:
                            statement += "<b>{}</b>\n".format(element[0])
                else: #for stock options
                    url = "https://www.nseindia.com/api/option-chain-indices?symbol="+element[0]

                #for a block, get option data first line of each block
                if (index == 0) and not all(x==7 for x in list(map(lambda x:len(x), block))):
                    option_data = requests.get(url, headers=headers, cookies=cookies)
                    p=option_data.text
                    import json
                    s=json.loads(option_data.text)
                    d=s['records']['data']
                #if the line has been closed, find the part time profit
                if len(element) == 7:
                    profit_step = round(((element[6] - element[5])*element[4]),1)
                    statement+="{}>strike:{} qty:{} exp:{} profit:{} (F)\n".format(index, element[1], element[4], datetime.strftime(datetime.strptime(element[2], "%d-%b-%Y"), "%d-%b"), round(profit_step))
                    profit_closed += profit_step
                else: #for open option lines
                    profit_step = round(([x[element[3]]['lastPrice'] for x in d if (x['strikePrice']==element[1] and x['expiryDate']==element[2])][0] - element[5])*element[4],1)
                    last_price = round([x[element[3]]['lastPrice'] for x in d if (x['strikePrice']==element[1] and x['expiryDate']==element[2])][0],1)
                    implied_volatility = ([x[element[3]]['impliedVolatility'] for x in d if
                                    (x['strikePrice'] == element[1] and x['expiryDate'] == element[2])][0])
                    statement += "{}>strike:{} qty:{} p/unit:{}, holding p/u:{} expiry:{} type:{} <b>profit:{}</b>, IV:{}\n".format(index, element[1], element[4], last_price, element[5], datetime.strftime(datetime.strptime(element[2], "%d-%b-%Y"), "%d-%b"), element[3], int(profit_step), implied_volatility)

                #for option lines or for partially/fully closed equity
                profit_block += profit_step
                total_profit_in_all_positions += profit_block
                profit_open_positions = profit_block-profit_closed
        if not round(profit_open_positions, -3):
            statement+="Total profit:{}, open:{}, closed:{}\n\n".format(int(profit_block), int(profit_open_positions), int(profit_closed))
        else:
            statement+="<b>Total profit:{}</b>\n\n".format(int(profit_block))

        # check if profit/loss reaches limit for the specific day /tmp/limitreached
        import os
        today_date = datetime.today().strftime('%d-%m-%Y')
        file_to_check = os.path.join(dirpath, "limitreached"+"_"+today_date+"_"+str(i))
        if not os.path.exists(file_to_check):
            if (profit_block-profit_closed)>0.9*target_profit[i][0]:
                send_closure_statement = True
                profit_loss = "target"
                target_profit_loss = target_profit[i][0]
                stock_name = block[0][0]
                closure_statement = "Near {}:{}, profit in open positions:{}, block:{}".format(profit_loss, target_profit_loss, int(profit_block-profit_closed), i)
            elif (profit_block < profit_closed) and abs(profit_block-profit_closed)>0.9*abs(target_profit[i][1]):
                send_closure_statement = True
                profit_loss = "max loss"
                target_profit_loss = target_profit[i][1]
                stock_name = block[0][0]
                closure_statement = "Near {}:{}, profit in open positions:{}, stock:{} block:{}".format(profit_loss, target_profit_loss, int(profit_block-profit_closed), stock_name, i)
            if send_closure_statement == True:
                for i in range(3):
                    send(closure_statement, keys.chat_id, keys.token)
                    time.sleep(5)
                #create file
                os.mknod(file_to_check)

    statement += "Today profit:{} total profit:{}\n\n".format(today_profit, total_profit_in_all_positions)
    mod_holdings = [h for holding in holdings for h in holding]
    #check if min is every 5 mins
    from datetime import datetime as dt
    #if dt.now().minute in (0,1, 30,31):
    if True:
        if not all(len(x) in (7,4) for x in mod_holdings):
            send(statement, keys.chat_id, keys.token)


def main():
    #headers = { 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; '
    #            'x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36'}
    #main_url = "https://www.nseindia.com/"
    #response = requests.get(main_url, headers=headers)
    #cookies = response.cookies
    cookies = ''
    headers = ''
    parser = argparse.ArgumentParser()
    parser.add_argument("--payout", "-p", help="Initial payout")
    args = parser.parse_args()
    if args.payout in (1,2):
        initial_payout(args.payout, headers, cookies)
    else:
        from datetime import datetime as dt
        if dt.now().minute in (3, 24, 45):
        #if True:
            calculate_profit(headers=headers, cookies=cookies)

    track_stocks(target_stocks)

if __name__ == "__main__":
    main()
