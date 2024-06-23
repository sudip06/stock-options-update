import json
import readline
from datetime import datetime
import os

# Function to load data from JSON file
def load_data(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return json.load(file)
    else:
        return {
            "holdings": [],
            "target_profit": [],
            "target_stocks": [],
            "new_plan": []
        }

# Function to save data to JSON file
def save_data(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

def bold(text):
    return f"\033[1m{text}\033[0m"

# Autocomplete function for stock names
def complete(text, state):
    options = [stock[0][0] for stock in data['holdings'] if stock[0][0].startswith(text.upper())]
    if state < len(options):
        return options[state]
    else:
        return None

# Function to get input with autocomplete feature
def input_with_autocomplete(prompt):
    readline.set_completer(complete)
    readline.parse_and_bind("tab: complete")
    return input(prompt).strip().upper()

# Function to calculate default values for profit, loss, target price, and stop loss price
def calculate_default_values(number_of_shares, cost_price):
    total_cost = number_of_shares * cost_price
    default_profit = int(0.3 * total_cost)
    default_loss = int(-0.1 * total_cost)
    default_target_price = round(cost_price * 1.3, 2)
    default_stop_loss_price = round(cost_price * 0.9, 2)
    return default_profit, default_loss, default_target_price, default_stop_loss_price

# Function to add a new stock to the portfolio
def add_stock(data):
    name = input_with_autocomplete("Enter the name of the stock to add: ")

    number_of_shares_input = input("Enter the number of shares: ")
    number_of_shares = int(number_of_shares_input) if number_of_shares_input else 0

    cost_price_input = input("Enter the cost price: ")
    cost_price = float(cost_price_input) if cost_price_input else 0.0

    date = input("Enter the date: ").strip()

    default_profit, default_loss, default_target_price, default_stop_loss_price = calculate_default_values(number_of_shares, cost_price)

    profit_input = input(f"Enter the profit (default 30% of total cost ie {default_profit}): ")
    if '%' in profit_input:
        profit_percentage = float(profit_input.strip('%')) / 100
        profit = int(profit_percentage * number_of_shares * cost_price)
    else:
        profit = int(profit_input) if profit_input else default_profit

    loss_input = input(f"Enter the loss (default -10% of total cost ie {default_loss}): ")
    if '%' in loss_input:
        loss_percentage = float(loss_input.strip('%')) / 100
        loss = -int(abs(loss_percentage) * number_of_shares * cost_price)
    else:
        loss = -int(abs(loss_input)) if loss_input else -abs(default_loss)

    target_price_input = input(f"Enter the target price (default 30% above cost price ie {default_target_price}): ")
    if '%' in target_price_input:
        target_price_percentage = float(target_price_input.strip('%')) / 100
        target_price = round((1 + target_price_percentage) * cost_price, 1)
    else:
        target_price = float(target_price_input) if target_price_input else default_target_price

    stop_loss_price_input = input(f"Enter the stop loss price (default -10% below cost price ie {default_stop_loss_price}): ")
    if '%' in stop_loss_price_input:
        stop_loss_price_percentage = float(stop_loss_price_input.strip('%')) / 100
        stop_loss_price = round((1 - abs(stop_loss_price_percentage)) * cost_price, 1)
    else:
        stop_loss_price = float(stop_loss_price_input) if stop_loss_price_input else default_stop_loss_price

    # Add to holdings
    data['holdings'].append([(name, number_of_shares, cost_price, date)])

    # Add to target_profit
    data['target_profit'].append([profit, loss])

    # Add to target_stocks for target_price and stop_loss_price
    data['target_stocks'].append([name, target_price, 0])
    data['target_stocks'].append([name, stop_loss_price, 1])

    print(f"Stock {name} added successfully.")

# Function to delete a stock from the portfolio
def delete_stock(data):
    name = input_with_autocomplete("Enter the name of the stock to delete: ")

    # Find and remove from holdings and target_profit
    holdings_index = None
    for i, holding in enumerate(data['holdings']):
        if holding[0][0] == name:
            holdings_index = i
            break

    if holdings_index is not None:
        del data['holdings'][holdings_index]
        del data['target_profit'][holdings_index]

        # Remove from target_stocks
        target_stocks_indices = [i for i, stock in enumerate(data['target_stocks']) if stock[0] == name]
        for index in sorted(target_stocks_indices, reverse=True):
            del data['target_stocks'][index]

        print(f"Stock {name} deleted successfully.")
    else:
        print(f"Stock {name} not found.")

def modify_stock(data):
    name = input_with_autocomplete("Enter the name of the stock to modify: ")

    holdings_index = None
    for i, holding in enumerate(data['holdings']):
        if holding[0][0] == name:
            holdings_index = i
            break

    if holdings_index is None:
        print(f"Stock {name} not found.")
        return

    # Modify holdings
    number_of_shares_input = input(f"Enter the number of shares (current: {data['holdings'][holdings_index][0][1]}): ")
    number_of_shares = int(number_of_shares_input) if number_of_shares_input else data['holdings'][holdings_index][0][1]

    cost_price_input = input(f"Enter the cost price (current: {data['holdings'][holdings_index][0][2]}): ")
    cost_price = float(cost_price_input) if cost_price_input else data['holdings'][holdings_index][0][2]

    current_date = data['holdings'][holdings_index][0][3]
    date_input = input(f"Enter the date (current: {current_date}): ").strip()
    date = date_input if date_input else current_date

    default_profit, default_loss, default_target_price, default_stop_loss_price = calculate_default_values(number_of_shares, cost_price)

    profit_current = data['target_profit'][holdings_index][0]
    profit_percentage_current = round((profit_current / (number_of_shares * cost_price)) * 100, 1)
    profit_input = input(f"Enter the profit (current: {profit_current} ({profit_percentage_current}%), default 30% of total cost ie {default_profit}): ")
    if '%' in profit_input:
        profit_percentage = float(profit_input.strip('%')) / 100
        profit = int(profit_percentage * number_of_shares * cost_price)
    else:
        profit = int(profit_input) if profit_input else profit_current

    loss_current = data['target_profit'][holdings_index][1]
    loss_percentage_current = round((loss_current / (number_of_shares * cost_price)) * 100, 1)
    loss_input = input(f"Enter the loss (current: {loss_current} ({loss_percentage_current}%), default -10% of total cost ie {default_loss}): ")
    if '%' in loss_input:
        loss_percentage = float(loss_input.strip('%')) / 100
        loss = -int(abs(loss_percentage) * number_of_shares * cost_price)
    else:
        loss = -int(abs(loss_input)) if loss_input else -abs(loss_current)

    # Find the correct indices for target_price and stop_loss_price
    target_price_index = None
    stop_loss_price_index = None
    for i, stock in enumerate(data['target_stocks']):
        if stock[0] == name:
            if stock[2] == 0:
                target_price_index = i
            elif stock[2] == 1:
                stop_loss_price_index = i

    target_price_current = data['target_stocks'][target_price_index][1] if target_price_index is not None else default_target_price
    target_price_percentage_current = round(((target_price_current / cost_price) - 1) * 100, 1)
    stop_loss_price_current = data['target_stocks'][stop_loss_price_index][1] if stop_loss_price_index is not None else default_stop_loss_price
    stop_loss_percentage_current = round(((stop_loss_price_current / cost_price) - 1) * 100, 1)

    target_price_input = input(f"Enter the target price (current: {target_price_current} ({target_price_percentage_current}%), default 30% above cost price ie {default_target_price}): ")
    if '%' in target_price_input:
        target_price_percentage = float(target_price_input.strip('%')) / 100
        target_price = round((1 + target_price_percentage) * cost_price, 1)
    else:
        target_price = float(target_price_input) if target_price_input else default_target_price

    stop_loss_price_input = input(f"Enter the stop loss price (current: {stop_loss_price_current} ({stop_loss_percentage_current}%), default -10% below cost price ie {default_stop_loss_price}): ")
    if '%' in stop_loss_price_input:
        stop_loss_price_percentage = float(stop_loss_price_input.strip('%')) / 100
        stop_loss_price = round((1 - abs(stop_loss_price_percentage)) * cost_price, 1)
    else:
        stop_loss_price = float(stop_loss_price_input) if stop_loss_price_input else default_stop_loss_price

    # Update holdings
    data['holdings'][holdings_index][0][1] = number_of_shares
    data['holdings'][holdings_index][0][2] = cost_price
    data['holdings'][holdings_index][0][3] = date

    # Update target_profit
    data['target_profit'][holdings_index][0] = profit
    data['target_profit'][holdings_index][1] = loss

    if target_price_index is not None:
        data['target_stocks'][target_price_index][1] = target_price
    if stop_loss_price_index is not None:
        data['target_stocks'][stop_loss_price_index][1] = stop_loss_price

    print(f"Stock {name} modified successfully.")

# Function to show details of a stock in the portfolio
def show_stock(data):
    name = input_with_autocomplete("Enter the name of the stock to view (or press Enter to view all stocks): ")
    if name == "":
        # Show details for all stocks
        if not data['holdings']:
            print("No stocks in the portfolio.")
            return
        for i, holding in enumerate(data['holdings']):
            name = holding[0][0]
            number_of_shares = holding[0][1]
            cost_price = holding[0][2]
            date = holding[0][3]
            profit = data['target_profit'][i][0]
            loss = data['target_profit'][i][1]
            target_price = None
            stop_loss_price = None
            print()
            for stock in data['target_stocks']:
                if stock[0] == name:
                    if stock[2] == 0:
                        target_price = stock[1]
                    elif stock[2] == 1:
                        stop_loss_price = stock[1]
            print(f"{bold('Stock name:')} {name}")
            print(f"{bold('Number of shares:')} {number_of_shares}")
            print(f"{bold('Cost price:')} {cost_price}")
            print(f"{bold('Date:')} {date}")
            print(f"{bold('Profit:')} {profit}")
            print(f"{bold('Loss:')} {loss}")
            print(f"{bold('Target price:')} {target_price}")
            print(f"{bold('Stop loss price:')} {stop_loss_price}")
            print()
    else:
        # Show details for a specific stock
        holdings_index = None
        for i, holding in enumerate(data['holdings']):
            if holding[0][0] == name:
                holdings_index = i
                break

        if holdings_index is None:
            print(f"Stock {name} not found.")
            return

        number_of_shares = data['holdings'][holdings_index][0][1]
        cost_price = data['holdings'][holdings_index][0][2]
        date = data['holdings'][holdings_index][0][3]
        profit = data['target_profit'][holdings_index][0]
        loss = data['target_profit'][holdings_index][1]
        target_price = None
        stop_loss_price = None
        for stock in data['target_stocks']:
            if stock[0] == name:
                if stock[2] == 0:
                    target_price = stock[1]
                elif stock[2] == 1:
                    stop_loss_price = stock[1]

        print()
        print(f"{bold('Stock name:')} {name}")
        print(f"{bold('Number of shares:')} {number_of_shares}")
        print(f"{bold('Cost price:')} {cost_price}")
        print(f"{bold('Date:')} {date}")
        print(f"{bold('Profit:')} {profit}")
        print(f"{bold('Loss:')} {loss}")
        print(f"{bold('Target price:')} {target_price}")
        print(f"{bold('Stop loss price:')} {stop_loss_price}")
        print()


def sell_stock(data):
    name = input_with_autocomplete("Enter the name of the stock to sell: ")

    holdings_index = None
    for i, holding in enumerate(data['holdings']):
        if holding[0][0] == name:
            holdings_index = i
            break

    if holdings_index is None:
        print(f"Stock {name} not found.")
        return

    # Find the open sub-block with number of entries equal to 4
    open_sub_block_index = None
    for j, sub_block in enumerate(data['holdings'][holdings_index]):
        if len(sub_block) == 4:
            open_sub_block_index = j
            break

    if open_sub_block_index is None:
        # No open section found, delete target_stocks for the stock
        data['target_stocks'] = [stock for stock in data['target_stocks'] if stock[0] != name]
        print(f"No open section found for {name}. Target stocks for {name} removed.")
        return

    # Ask for number of shares to sell from the open sub-block
    current_shares = data['holdings'][holdings_index][open_sub_block_index][1]
    number_of_shares_input = input(f"Enter the number of shares to sell (current: {current_shares}): ")
    number_of_shares = int(number_of_shares_input) if number_of_shares_input else current_shares

    # Ask for selling price
    selling_price_input = input("Enter the selling price: ").strip()
    if not selling_price_input:
        print("Selling price cannot be blank.")
        return
    selling_price = float(selling_price_input)

    # Ask for the date
    today_date = datetime.now().strftime('%d-%m-%Y')
    date_input = input(f"Enter the date (default {today_date}): ").strip()
    date = date_input if date_input else today_date

    if number_of_shares >= current_shares:
        # Sell all shares in the open sub-block
        data['holdings'][holdings_index][open_sub_block_index].append(selling_price)
        data['holdings'][holdings_index][open_sub_block_index].append(date)
        print(f"All shares of {name} sold at {selling_price} on {date}.")

        # Check if there are any remaining open sub-blocks
        remaining_open_sub_blocks = [sub_block for sub_block in data['holdings'][holdings_index] if len(sub_block) == 4]
        if not remaining_open_sub_blocks:
            # No remaining open sub-blocks, remove target stocks
            data['target_stocks'] = [stock for stock in data['target_stocks'] if stock[0] != name]
            print(f"No remaining open sections for {name}. Target stocks for {name} removed.")
    else:
        # Sell part of the shares in the open sub-block
        data['holdings'][holdings_index][open_sub_block_index][1] -= number_of_shares
        data['holdings'][holdings_index].append([name, number_of_shares, data['holdings'][holdings_index][open_sub_block_index][2],
                                                 data['holdings'][holdings_index][open_sub_block_index][3], selling_price, date])
        print(f"{number_of_shares} shares of {name} sold at {selling_price} on {date}.")

# Main function to manage the portfolio
def main():
    global data
    filename = 'india_data.json'

    while True:
        print("Enter 'add' to add a stock, 'delete' to delete a stock,")
        action = input(" 'modify' to modify a stock, 'show' to show details of a stock, 'sell' to sell a stock (or 'exit' to quit): ").strip().lower()
        #action = input("Enter 'add' to add a stock, 'delete' to delete a stock, 'modify' to modify a stock, 'show' to show details of a stock, 'sell' to sell a stock (or 'exit' to quit): ").strip().lower()
        if action == 'add':
            data = load_data(filename)
            add_stock(data)
            print("Changes saved to file.")
            save_data(filename, data)
        elif action == 'delete':
            data = load_data(filename)
            delete_stock(data)
            save_data(filename, data)
            print("Changes saved to file.")
        elif action == 'modify':
            data = load_data(filename)
            modify_stock(data)
            save_data(filename, data)
            print("Changes saved to file.")
        elif action == 'show':
            data = load_data(filename)
            show_stock(data)
        elif action == 'sell':
            data = load_data(filename)
            sell_stock(data)
            save_data(filename, data)
            print("Changes saved to file.")
        elif action == 'exit':
            break
        else:
            print("Invalid option. Please try again.")


if __name__ == "__main__":
    main()

