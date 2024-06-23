import json
import readline
from datetime import datetime

# Function to load data from JSON file
def load_data(filename):
    with open(filename, 'r') as file:
        return json.load(file)

# Function to save data to JSON file
def save_data(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

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
    name = input_with_autocomplete("Enter the name of the stock: ")
    number_of_shares = int(input("Enter the number of shares: "))
    cost_price = float(input("Enter the cost price: "))

    today_date = datetime.now().strftime('%d-%m-%Y')
    date_input = input(f"Enter the date (default {today_date}): ").strip()
    date = date_input if date_input else today_date

    default_profit, default_loss, default_target_price, default_stop_loss_price = calculate_default_values(number_of_shares, cost_price)

    profit_input = input(f"Enter the profit (default 30% of total cost {default_profit}): ")
    profit = int(profit_input) if profit_input else default_profit

    loss_input = input(f"Enter the loss (default -10% of total cost {default_loss}): ")
    loss = int(loss_input) if loss_input else default_loss

    target_price_input = input(f"Enter the target price (default 30% above cost price {default_target_price}): ")
    target_price = float(target_price_input) if target_price_input else default_target_price

    stop_loss_price_input = input(f"Enter the stop loss price (default -10% below cost price {default_stop_loss_price}): ")
    stop_loss_price = float(stop_loss_price_input) if stop_loss_price_input else default_stop_loss_price

    # Check if there's an existing open position for the stock
    existing_position = None
    for holding in data['holdings']:
        if holding[0][0] == name:
            existing_position = holding
            break

    if existing_position:
        # Update existing position
        existing_shares = existing_position[0][1]
        existing_cost_price = existing_position[0][2]
        existing_profit = data['target_profit'][data['holdings'].index(existing_position)][0]
        existing_loss = data['target_profit'][data['holdings'].index(existing_position)][1]

        # Calculate new values
        total_shares = existing_shares + number_of_shares
        new_cost_price = (existing_cost_price * existing_shares + cost_price * number_of_shares) / total_shares
        new_profit = existing_profit + profit
        new_loss = existing_loss + loss

        # Update data
        existing_position[0][1] = total_shares
        existing_position[0][2] = new_cost_price
        data['target_profit'][data['holdings'].index(existing_position)] = [new_profit, new_loss]
        for target in data['target_stocks']:
            if target[0] == name:
                if target[2] == 0:
                    target[1] = target_price
                elif target[2] == 1:
                    target[1] = stop_loss_price

        print(f"Stock {name} updated successfully.")
    else:
        # Add to holdings
        data['holdings'].append([[name, number_of_shares, cost_price, date]])

        # Add to target_profit
        data['target_profit'].append([profit, loss])

        # Add to target_stocks
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
        data['target_stocks'] = [stock for stock in data['target_stocks'] if stock[0] != name]

        print(f"Stock {name} deleted successfully.")
    else:
        print(f"Stock {name} not found.")

# Function to modify details of a stock in the portfolio
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

    profit_input = input(f"Enter the profit (current: {data['target_profit'][holdings_index][0]}, default 30% of total cost {default_profit}): ")
    profit = int(profit_input) if profit_input else data['target_profit'][holdings_index][0]

    loss_input = input(f"Enter the loss (current: {data['target_profit'][holdings_index][1]}, default -10% of total cost {default_loss}): ")
    loss = int(loss_input) if loss_input else data['target_profit'][holdings_index][1]

    # Find current target and stop loss prices
    target_price = None
    stop_loss_price = None
    for stock in data['target_stocks']:
        if stock[0] == name:
            if stock[2] == 0:
                target_price = stock[1]
            elif stock[2] == 1:
                stop_loss_price = stock[1]

    target_price_input = input(f"Enter the target price (current: {target_price}, default 30% above cost price {default_target_price}): ")
    target_price = float(target_price_input) if target_price_input else target_price

    stop_loss_price_input = input(f"Enter the stop loss price (current: {stop_loss_price}, default -10% below cost price {default_stop_loss_price}): ")
    stop_loss_price = float(stop_loss_price_input) if stop_loss_price_input else stop_loss_price

    # Update holdings
    data['holdings'][holdings_index][0][1] = number_of_shares
    data['holdings'][holdings_index][0][2] = cost_price
    data['holdings'][holdings_index][0][3] = date

    # Update target_profit
    data['target_profit'][holdings_index][0] = profit
    data['target_profit'][holdings_index][1] = loss

    # Update target_stocks
    for stock in data['target_stocks']:
        if stock[0] == name:
            if stock[2] == 0:
                stock[1] = target_price
            elif stock[2] == 1:
                stock[1] = stop_loss_price

    print(f"Stock {name} modified successfully.")

# Function to show details of a stock in the portfolio
def show_stock(data):
    name = input_with_autocomplete("Enter the name of the stock to show details: ")
    # Current date
    today = datetime.now().date()
    holdings_found = False
    for holding in data['holdings']:
        if holding[0][0] == name:
            holdings_found = True
            open_sub_blocks = [sub_block for sub_block in holding if len(sub_block) == 4]
            closed_sub_blocks = [sub_block for sub_block in holding if len(sub_block) == 6]

            print(f"Stock: {holding[0][0]}")

            print("\nOpen Sub-blocks:")
            for sub_block in open_sub_blocks:
                entry_date = datetime.strptime(sub_block[3], '%d-%m-%Y').date()
                days_held = (today - entry_date).days
                print(f"  Number of Shares: {sub_block[1]}")
                print(f"  Cost Price: {sub_block[2]}")
                print(f"  Date: {sub_block[3]} (days held: {days_held})")
            if closed_sub_blocks:
                print("\nClosed Sub-blocks:")
            for sub_block in closed_sub_blocks:
                entry_date = datetime.strptime(sub_block[3], '%d-%m-%Y').date()
                closed_date = datetime.strptime(sub_block[5], '%d-%m-%Y').date()
                days_held = (closed_date - entry_date).days
                print(f"  Number of Shares: {sub_block[1]}")
                print(f"  Cost Price: {sub_block[2]}")
                print(f"  Selling Price: {sub_block[4]}")
                print(f"  Buying Date: {sub_block[3]}")
                print(f"  Selling Date: {sub_block[5]} (days held: {days_held})")
                profit=(sub_block[4]-sub_block[2])*sub_block[1]
                print(f"  Profit/Loss: {profit}")

            break

    if not holdings_found:
        print(f"Stock {name} not found in holdings.")

    target_stocks_found = False
    for stock in data['target_stocks']:
        if stock[0] == name:
            if stock[2] == 0:
                print(f"  Target Price: {stock[1]}")
            elif stock[2] == 1:
                print(f"  Stop Loss Price: {stock[1]}")
            target_stocks_found = True

    if not target_stocks_found:
        print(f"No target price or stop loss price found for stock {name}.")

# Function to sell a stock from the portfolio
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

    # Ask for number of shares to sell
    current_shares = data['holdings'][holdings_index][0][1]
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
        # Sell all shares
        data['holdings'][holdings_index][0].append(selling_price)
        data['holdings'][holdings_index][0].append(date)
        print(f"All shares of {name} sold at {selling_price} on {date}.")
    else:
        # Sell part of the shares
        data['holdings'][holdings_index][0][1] -= number_of_shares
        data['holdings'][holdings_index].append([name, number_of_shares, data['holdings'][holdings_index][0][2],
                                                 data['holdings'][holdings_index][0][3], selling_price, date])
        print(f"{number_of_shares} shares of {name} sold at {selling_price} on {date}.")

# Main function to manage the portfolio
def main():
    global data
    filename = 'india_data.json'
    data = load_data(filename)

    while True:
        action = input("Enter 'add' to add a stock, 'delete' to delete a stock, 'modify' to modify a stock, 'show' to show details of a stock, 'sell' to sell a stock (or 'exit' to quit): ").strip().lower()
        if action == 'add':
            add_stock(data)
        elif action == 'delete':
            delete_stock(data)
        elif action == 'modify':
            modify_stock(data)
        elif action == 'show':
            show_stock(data)
        elif action == 'sell':
            sell_stock(data)
        elif action == 'exit':
            break
        else:
            print("Invalid option. Please try again.")

    save_data(filename, data)
    print("Changes saved to file.")

if __name__ == "__main__":
    main()

