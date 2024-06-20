import json
import readline

def load_data(filename):
    with open(filename, 'r') as file:
        return json.load(file)

def save_data(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

def complete(text, state):
    options = [stock[0][0] for stock in data['holdings'] if stock[0][0].startswith(text.upper())]
    if state < len(options):
        return options[state]
    else:
        return None

def input_with_autocomplete(prompt):
    readline.set_completer(complete)
    readline.parse_and_bind("tab: complete")
    return input(prompt).strip().upper()

def calculate_default_values(number_of_shares, cost_price):
    total_cost = number_of_shares * cost_price
    default_profit = int(0.3 * total_cost)
    default_loss = int(-0.1 * total_cost)
    default_target_price = round(cost_price * 1.3, 2)
    default_stop_loss_price = round(cost_price * 0.9, 2)
    return default_profit, default_loss, default_target_price, default_stop_loss_price

def add_stock(data):
    name = input_with_autocomplete("Enter the name of the stock: ")
    number_of_shares = int(input("Enter the number of shares: "))
    cost_price = float(input("Enter the cost price: "))

    default_profit, default_loss, default_target_price, default_stop_loss_price = calculate_default_values(number_of_shares, cost_price)

    profit_input = input(f"Enter the profit (default 30% of total cost {default_profit}): ")
    profit = int(profit_input) if profit_input else default_profit

    loss_input = input(f"Enter the loss (default -10% of total cost {default_loss}): ")
    loss = int(loss_input) if loss_input else default_loss

    target_price_input = input(f"Enter the target price (default 30% above cost price {default_target_price}): ")
    target_price = float(target_price_input) if target_price_input else default_target_price

    stop_loss_price_input = input(f"Enter the stop loss price (default -10% below cost price {default_stop_loss_price}): ")
    stop_loss_price = float(stop_loss_price_input) if stop_loss_price_input else default_stop_loss_price

    # Add to holdings
    data['holdings'].append([[name, number_of_shares, cost_price]])

    # Add to target_profit
    data['target_profit'].append([profit, loss])

    # Add to target_stocks
    data['target_stocks'].append([name, target_price, 0])
    data['target_stocks'].append([name, stop_loss_price, 1])

    print(f"Stock {name} added successfully.")

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

def show_stock(data):
    name = input_with_autocomplete("Enter the name of the stock to show details: ")

    holdings_found = False
    for holding in data['holdings']:
        if holding[0][0] == name:
            print(f"Stock: {holding[0][0]}")
            print(f"Number of Shares: {holding[0][1]}")
            print(f"Cost Price: {holding[0][2]}")
            holdings_found = True
            break

    if not holdings_found:
        print(f"Stock {name} not found in holdings.")

    target_stocks_found = False
    for stock in data['target_stocks']:
        if stock[0] == name:
            if stock[2] == 0:
                print(f"Target Price: {stock[1]}")
            elif stock[2] == 1:
                print(f"Stop Loss Price: {stock[1]}")
            target_stocks_found = True

    if not target_stocks_found:
        print(f"No target price or stop loss price found for stock {name}.")

def main():
    global data
    filename = 'india_data.json'
    data = load_data(filename)

    while True:
        action = input("Enter 'add' to add a stock, 'delete' to delete a stock, 'modify' to modify a stock, 'show' to show details of a stock (or 'exit' to quit): ").strip().lower()
        if action == 'add':
            add_stock(data)
        elif action == 'delete':
            delete_stock(data)
        elif action == 'modify':
            modify_stock(data)
        elif action == 'show':
            show_stock(data)
        elif action == 'exit':
            break
        else:
            print("Invalid option. Please try again.")

    save_data(filename, data)
    print("Changes saved to file.")

if __name__ == "__main__":
    main()

