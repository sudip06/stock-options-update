import requests
import argparse
import telegram_send
from nsetools import Nse

holdings = [
            [17100, '31-Mar-2022', 'PE', -250, 188.5],
            [17100, '28-Apr-2022', 'PE', 250, 439.2],
            ]

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
        statement += "strike:{} expiry:{} payout:{}, IV:{}\n".format(element[0], element[1], -profit_step, implied_volatility)
        payout += profit_step
    statement+="Payout:"+str(-payout)
    telegram_send.send(messages=[statement])
    print("payout:{}".format(-payout))


def calculate_profit(d):
    profit = 0
    statement=""
    nse = Nse()
    statement = "Nifty:{}, change:{}\n".format(nse.get_index_quote("nifty 50").get('lastPrice'), nse.get_index_quote("nifty 50").get('change'))
    for index, element in enumerate(holdings):
        #print(round(element[3]*element[4],1))
        if len(element)==6:
            profit_step = round(((element[5] - element[4])*element[3]),1)
            statement+="strike:{} profit:{} (F)\n".format(element[0], profit_step)
        else:
            profit_step = round(([x[element[2]]['lastPrice'] for x in d if (x['strikePrice']==element[0] and x['expiryDate']==element[1])][0] - element[4])*element[3],1)
            implied_volatility = ([x[element[2]]['impliedVolatility'] for x in d if
                                  (x['strikePrice'] == element[0] and x['expiryDate'] == element[1])][0])
            statement+="strike:{} profit:{}, IV:{}\n".format(element[0], profit_step, implied_volatility)
        profit += profit_step
    statement+="Total Profit:"+str(profit)
    print("Total profit:", profit)
    telegram_send.send(messages=[statement])


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
