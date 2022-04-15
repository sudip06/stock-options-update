import requests
import argparse
import telegram
from nsetools import Nse
from datetime import datetime
import functools
import keys
import time

holdings = [
            [17600, '21-Apr-2022', 'PE', -350, 169.41],
            [17600, '28-Apr-2022', 'PE', 350, 238.0],
            [17700, '21-Apr-2022', 'CE', -350, 68.16],
            [17700, '28-Apr-2022', 'CE', 350, 149.24],
            ]

target_profit = 1000*13

new_plan = [
            [17700, '28-Apr-2022', 'PE', 400],
            [17700, '07-Apr-2022', 'PE', -400],
            [17800, '13-Apr-2022', 'CE', -300],
            [17800, '28-Apr-2022', 'CE', 300]
            ]


def send(msg, chat_id, token):
        """
        Send a message to a telegram user or group specified on chatId
        chat_id must be a number!
        """
        bot = telegram.Bot(token=token)
        bot.sendMessage(chat_id=chat_id, text=msg)


def initial_payout(d, which_plan):
    payout = 0
    statement = ""
    nse = Nse()
    if int(which_plan) == 1:
        dataset = holdings
        statement = "Holdings:\n"
    else:
        statement = "New Plan:\n"
        dataset = new_plan
   
    statement += "Nifty:{}, change:{}\n".format(nse.get_index_quote("nifty 50").get('lastPrice'), nse.get_index_quote("nifty 50").get('change'))
    for index, element in enumerate(dataset):
        # print(round(element[3]*element[4],1))
        profit_step = round(([x[element[2]]['lastPrice'] for x in d if
                              (x['strikePrice'] == element[0] and x['expiryDate'] == element[1])][0])*element[3],1)
        implied_volatility = ([x[element[2]]['impliedVolatility'] for x in d if
                              (x['strikePrice'] == element[0] and x['expiryDate'] == element[1])][0])
        last_price = round([x[element[2]]['lastPrice'] for x in d if (x['strikePrice']==element[0] and x['expiryDate']==element[1])][0])
        statement+="{}>strike:{} qty:{} p/unit:{} expiry:{} type:{} payout:{}, IV:{}\n".format(index, element[0], element[3], last_price, datetime.strftime(datetime.strptime(element[1], "%d-%b-%Y"), "%d-%b"), element[2], -profit_step, implied_volatility)
        payout += profit_step
    statement+="Payout:"+str(-payout)
    send(statement, keys.chat_id, keys.token)
    print("payout:{}".format(-payout))


def calculate_profit(d):
    profit = 0
    statement=""
    nse = Nse()
    profit_closed = 0
    statement = "Nifty:{}, change:{}\n".format(nse.get_index_quote("nifty 50").get('lastPrice'), nse.get_index_quote("nifty 50").get('change'))
    for index, element in enumerate(holdings):
        #print(round(element[3]*element[4],1))
        if len(element)==6:
            profit_step = round(((element[5] - element[4])*element[3]),1)
            statement+="strike:{} qty:{} exp:{} profit:{} (F)\n".format(element[0], element[3], datetime.strftime(datetime.strptime(element[1], "%d-%b-%Y"), "%d-%b"), profit_step)
            profit_closed += profit_step
        else:
            profit_step = round(([x[element[2]]['lastPrice'] for x in d if (x['strikePrice']==element[0] and x['expiryDate']==element[1])][0] - element[4])*element[3],1)
            last_price = round([x[element[2]]['lastPrice'] for x in d if (x['strikePrice']==element[0] and x['expiryDate']==element[1])][0])
            implied_volatility = ([x[element[2]]['impliedVolatility'] for x in d if
                                  (x['strikePrice'] == element[0] and x['expiryDate'] == element[1])][0])
            statement+="{}>strike:{} qty:{} p/unit:{} expiry:{} type:{} profit:{}, IV:{}\n".format(index, element[0], element[3], last_price, datetime.strftime(datetime.strptime(element[1], "%d-%b-%Y"), "%d-%b"), element[2], profit_step, implied_volatility)
        profit += profit_step
    statement+="Total Profit:{}\n".format(str(profit))
    print("Total profit:", profit)
    if profit_closed and (profit_closed > 0):
        statement += "profit in open positions:{}".format(str(profit-profit_closed))

    if not all(len(x)==6 for x in holdings):
        send(statement, keys.chat_id, keys.token)

        if abs(profit-profit_closed)>0.9*target_profit:
            profit_loss = "target" if profit > 0 else "max loss"
            target_profit_loss = target_profit
            closure_statement = "Near {}:{}, profit in open positions:{}".format(profit_loss, target_profit_loss, (profit-profit_closed))
            for i in range(3):
                send(closure_statement, keys.chat_id, keys.token)
                time.sleep(5)

def main():
    headers = { 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; '
                'x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36'}
    main_url = "https://www.nseindia.com/"
    response = requests.get(main_url, headers=headers)
    print(response.status_code)
    cookies = response.cookies

    url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
    nifty_data = requests.get(url, headers=headers, cookies=cookies)
    p=nifty_data.text
    import json
    s=json.loads(nifty_data.text)
    d=s['records']['data']
    parser = argparse.ArgumentParser()
    parser.add_argument("--payout", "-p", help="Initial payout")
    args = parser.parse_args()
    if args.payout:
        initial_payout(d, args.payout)
    else:
        calculate_profit(d)

if __name__ == "__main__":
    main()
