import requests
import argparse
import telegram_send
from nsetools import Nse
from datetime import datetime
import functools
holdings = [
            [17100, '31-Mar-2022', 'PE', -250, 188.5, 150.37],
            [17100, '28-Apr-2022', 'PE', 250, 439.2, 422.15],
            [17200, '31-Mar-2022', 'PE', -400, 212.6, 63],
            [17200, '28-Apr-2022', 'PE', 400, 485.5, 352],
            ]

target_profit = 1000*8

new_plan = [
            [17100, '31-Mar-2022', 'PE', -250 ],
            [17100, '28-Apr-2022', 'PE', 250]
            ]

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
        statement += "strike:{} expiry:{} payout:{}, IV:{}\n".format(element[0], datetime.strftime(datetime.strptime(element[1], "%d-%b-%Y"), "%d-%b"), -profit_step, implied_volatility)
        payout += profit_step
    statement+="Payout:"+str(-payout)
    telegram_send.send(messages=[statement])
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
            statement+="strike:{} profit:{} (F)\n".format(element[0], profit_step)
            profit_closed += profit_step
        else:
            profit_step = round(([x[element[2]]['lastPrice'] for x in d if (x['strikePrice']==element[0] and x['expiryDate']==element[1])][0] - element[4])*element[3],1)
            implied_volatility = ([x[element[2]]['impliedVolatility'] for x in d if
                                  (x['strikePrice'] == element[0] and x['expiryDate'] == element[1])][0])
            statement+="strike:{} expiry:{} profit:{}, IV:{}\n".format(element[0], datetime.strftime(datetime.strptime(element[1], "%d-%b-%Y"), "%d-%b"), profit_step, implied_volatility)
        profit += profit_step
    statement+="Total Profit:{}\n".format(str(profit))
    print("Total profit:", profit)
    if profit_closed and (profit_closed > 0):
        statement += "profit in open positions:{}".format(str(profit-profit_closed))

    if not all(len(x)==6 for x in holdings):
        telegram_send.send(messages=[statement])

        if abs(profit-profit_closed)>0.9*target_profit:
            closure_statement = "Near target:{}, profit:{}".format(target_profit, profit)
            for i in range(2):
                telegram_send.send(messages=[closure_statement])
                sleep(5)

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
