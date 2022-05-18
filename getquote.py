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

dirpath = "/tmp/stockdata/"

#holdings list should be ex: [['ASHOKLEY', 130, '26-May-2022', 'PE', -9000, 6.25], ['ASHOKLEY', 127.5, '26-May-2022', 'PE', 9000, 4.5]]
holdings = [
           ]

#target list ex: [[10000, -3000],[14000,-4000]] for 2 contracts. Each list contains profit and loss of each block for effective tracking
target_profit = []

target_stocks = [['SBIN', 458.5, 0]]

new_plan = [
              [
                ['ASHOKLEY', 130, '26-May-2022', 'PE', -9000],
                ['ASHOKLEY', 127.5, '26-May-2022', 'PE', 9000]
              ]
           ]


def send(msg, chat_id, token):
        """
        Send a message to a telegram user or group specified on chatId
        chat_id must be a number!
        """
        bot = telegram.Bot(token=token)
        bot.sendMessage(chat_id=chat_id, text=msg, parse_mode=telegram.ParseMode.HTML)



def track_stocks(list_stocks):
    nse = Nse()
    statement = ''
    if not len(list_stocks):
        return
    today_date = datetime.today().strftime('%d-%m-%Y')
    for index, stock_data in enumerate(list_stocks):
        file_name_full = os.path.join(dirpath, stock_data[0]+"_"+today_date)
 
        if not os.path.exists(file_name_full):
            last_price = nse.get_quote(stock_data[0]).get('lastPrice')
            if (stock_data[2] == 1) and (last_price > stock_data[1]):
                statement += "<b>{}</b> just went above the tracking price:<b>{}</b> lastprice:<b>{}</b>".format(stock_data[0], stock_data[1], last_price)
                #create file
                os.mknod(file_name_full)
            elif (stock_data[2] == 0) and (last_price < stock_data[1]):
                statement += "<b>{}</b> just broke the tracking price:<b>{}</b> lastprice:<b>{}</b>".format(stock_data[0], stock_data[1], last_price)
                os.mknod(file_name_full)
    if statement:
        init_string = "<b>Tracking Alert\n</b>"
        statement = init_string + statement
        send(statement, keys.chat_id, keys.token)


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
   
    statement += "<b>Nifty:{}, change:{}</b>\n".format(nse.get_index_quote("nifty 50").get('lastPrice'), nse.get_index_quote("nifty 50").get('change'))
    for i, block in enumerate(dataset):
        statement += "Block:{}\n".format(str(i))
        payout = 0
        profit_step = 0
        for index, element in enumerate(block):
            #check if element is stock and not option
            if len(element) == 3:
                last_price = nse.get_quote(element[0]).get('lastPrice')
                statement += "<b>{}:{}, change:{}</b>\n".format(element[0], last_price, nse.get_quote(element[0]).get('change'))
                payout = round(last_price*element[1],1)
                statement+="{}>qty:{} p/unit:{}, buy p/u:{} <b>debit:{}</b>\n\n".format(index, element[1], last_price, element[2], payout)
            else:
                if element[0] != "NIFTY":
                    url = "https://www.nseindia.com/api/option-chain-equities?symbol="+element[0]
                else:
                    url = "https://www.nseindia.com/api/option-chain-indices?symbol="+element[0]
                if index == 0:
                    statement += "{}:{}, change:{}\n".format(element[0], nse.get_quote(element[0]).get('lastPrice'), nse.get_quote(element[0]).get('change'))
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
    nse = Nse()
    statement = "<b>Nifty:{}, change:{}</b>\n".format(nse.get_index_quote("nifty 50").get('lastPrice'), nse.get_index_quote("nifty 50").get('change'))
    if not len(holdings):
        return

    for i, block in enumerate(holdings):
        profit_closed = 0
        profit_step = 0
        profit = 0
        send_closure_statement = False
        statement += "Block:{}\n".format(str(i))
        for index, element in enumerate(block):
            #check if element is stock and not option
            if len(element) == 3:
                last_price = nse.get_quote(element[0]).get('lastPrice')
                statement += "<b>{}:{}, change:{}</b>\n".format(element[0], last_price, nse.get_quote(element[0]).get('change'))
                profit = round(((last_price - element[2])*element[1]),1)
                statement+="{}>qty:{} p/unit:{}, buy p/u:{} <b>profit:{}</b>\n\n".format(index, element[1], last_price, element[2], profit)

            else:
                if element[0] != "NIFTY":
                    url = "https://www.nseindia.com/api/option-chain-equities?symbol="+element[0]
                    if index == 0:
                        if not all(x==7 for x in list(map(lambda x:len(x), block))):
                            statement += "<b>{}:{}, change:{}</b>\n".format(element[0], nse.get_quote(element[0]).get('lastPrice'), nse.get_quote(element[0]).get('change'))
                        else:
                            statement += "<b>{}</b>\n".format(element[0])
                else:
                    url = "https://www.nseindia.com/api/option-chain-indices?symbol="+element[0]
                if (index == 0) and not all(x==7 for x in list(map(lambda x:len(x), block))):
                    option_data = requests.get(url, headers=headers, cookies=cookies)
                    p=option_data.text
                    import json
                    s=json.loads(option_data.text)
                    d=s['records']['data']
                #print(round(element[3]*element[4],1))
                if len(element)==7:
                    profit_step = round(((element[6] - element[5])*element[4]),1)
                    statement+="{}>strike:{} qty:{} exp:{} profit:{} (F)\n".format(index, element[1], element[4], datetime.strftime(datetime.strptime(element[2], "%d-%b-%Y"), "%d-%b"), profit_step)
                    profit_closed += profit_step
                else:
                    profit_step = round(([x[element[3]]['lastPrice'] for x in d if (x['strikePrice']==element[1] and x['expiryDate']==element[2])][0] - element[5])*element[4],1)
                    last_price = round([x[element[3]]['lastPrice'] for x in d if (x['strikePrice']==element[1] and x['expiryDate']==element[2])][0],1)
                    implied_volatility = ([x[element[3]]['impliedVolatility'] for x in d if
                                    (x['strikePrice'] == element[1] and x['expiryDate'] == element[2])][0])
                    statement+="{}>strike:{} qty:{} p/unit:{}, holding p/u:{} expiry:{} type:{} <b>profit:{}</b>, IV:{}\n".format(index, element[1], element[4], last_price, element[5], datetime.strftime(datetime.strptime(element[2], "%d-%b-%Y"), "%d-%b"), element[3], profit_step, implied_volatility)
                profit += profit_step
                profit_open_positions = profit-profit_closed
        if profit_open_positions != 0:
            statement+="Total profit:{}, open:{}, closed:{}\n\n".format(str(profit), str(profit_open_positions), str(profit_closed))
        else:
            statement+="<b>Total profit:{}</b>\n\n".format(str(profit))

        # check if /tmp/limitreached
        import os
        file_to_check = os.path.join(dirpath, "limitreached"+"_"+i)
        if not os.path.exists(file_to_check):
            if (profit-profit_closed)>0.9*target_profit[i][0]:
                send_closure_statement = True
                profit_loss = "target"
                target_profit_loss = target_profit[i][0]
                closure_statement = "Near {}:{}, profit in open positions:{}, block:{}".format(profit_loss, target_profit_loss, (profit-profit_closed), i)
            elif (profit < profit_closed) and abs(profit-profit_closed)>0.9*abs(target_profit[i][1]):
                send_closure_statement = True
                profit_loss = "max loss"
                target_profit_loss = target_profit[i][1]
                closure_statement = "Near {}:{}, profit in open positions:{}, block:{}".format(profit_loss, target_profit_loss, (profit-profit_closed), i)
            if send_closure_statement == True:
                for i in range(3):
                    send(closure_statement, keys.chat_id, keys.token)
                    time.sleep(5)
                #create file
                os.mknod(file_to_check)

    mod_holdings = [h for holding in holdings for h in holding]
    #check if min is every 5 mins
    from datetime import datetime as dt
    if dt.now().minute % 10 == 0:
        if not all(len(x) in (7,4) for x in mod_holdings):
            send(statement, keys.chat_id, keys.token)


def main():
    headers = { 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; '
                'x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36'}
    main_url = "https://www.nseindia.com/"
    response = requests.get(main_url, headers=headers)
    cookies = response.cookies

    parser = argparse.ArgumentParser()
    parser.add_argument("--payout", "-p", help="Initial payout")
    args = parser.parse_args()
    if args.payout in (1,2):
        initial_payout(args.payout, headers, cookies)
    else:
        calculate_profit(headers=headers, cookies=cookies)

    track_stocks(target_stocks)

if __name__ == "__main__":
    main()
