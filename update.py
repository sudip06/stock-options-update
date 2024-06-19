import json

def load_data(filename):
    with open(filename, 'r') as file:
        return json.load(file)

def save_data(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

def add_stock(data):
    name = input("Enter the name of the stock: ").strip().upper()
    number_of_shares = int(input("Enter the number of shares: "))
    cost_price = float(input("Enter the cost price: "))
    total_cost = number_of_shares * cost_price
    
    profit_input = input(f"Enter the profit (default 30% of total cost {total_cost}): ")
    profit = int(profit_input) if profit_input else int(0.3 * total_cost)
    
    loss_input = input(f"Enter the loss (default -10% of total cost {total_cost}): ")
    loss = int(loss_input) if loss_input else int(-0.1 * total_cost)
    
    target_price_input = input(f"Enter the target price (default 30% above cost price {cost_price}): ")
    target_price = float(target_price_input) if target_price_input else round(cost_price * 1.3, 2)
    
    stop_loss_price_input = input(f"Enter the stop loss price (default -10% below cost price {cost_price}): ")
    stop_loss_price = float(stop_loss_price_input) if stop_loss_price_input else round(cost_price * 0.9, 2)
    
    # Add to holdings
    data['holdings'].append([[name, number_of_shares, cost_price]])
    
    # Add to target_profit
    data['target_profit'].append([profit, loss])
    
    # Add to target_stocks
    data['target_stocks'].append([name, target_price, 0])
    data['target_stocks'].append([name, stop_loss_price, 1])
    
    print(f"Stock {name} added successfully.")

def delete_stock(data):
    name = input("Enter the name of the stock to delete: ").strip().upper()
    
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
    name = input("Enter the name of the stock to modify: ").strip().upper()
    
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
    
    total_cost = number_of_shares * cost_price
    
    profit_input = input(f"Enter the profit (current: {data['target_profit'][holdings_index][0]}, default 30% of total cost {total_cost}): ")
    profit = int(profit_input) if profit_input else data['target_profit'][holdings_index][0] if data['target_profit'][holdings_index][0] else int(0.3 * total_cost)
    
    loss_input = input(f"Enter the loss (current: {data['target_profit'][holdings_index][1]}, default -10% of total cost {total_cost}): ")
    loss = int(loss_input) if loss_input else data['target_profit'][holdings_index][1] if data['target_profit'][holdings_index][1] else int(-0.1 * total_cost)
    
    target_price_input = input(f"Enter the target price (current: {(data['target_stocks'][2*holdings_index][1] if 2*holdings_index < len(data['target_stocks']) else 'N/A')}, default 30% above cost price {cost_price}): ")
    target_price = float(target_price_input) if target_price_input else round(cost_price * 1.3, 2)
    
    stop_loss_price_input = input(f"Enter the stop loss price (current: {(data['target_stocks'][2*holdings_index + 1][1] if 2*holdings_index + 1 < len(data['target_stocks']) else 'N/A')}, default -10% below cost price {cost_price}): ")
    stop_loss_price = float(stop_loss_price_input) if stop_loss_price_input else round(cost_price * 0.9, 2)
    
    # Update holdings
    data['holdings'][holdings_index][0][1] = number_of_shares
    data['holdings'][holdings_index][0][2] = cost_price
    
    # Update target_profit
    data['target_profit'][holdings_index][0] = profit
    data['target_profit'][holdings_index][1] = loss
    
    # Update target_stocks
    if 2*holdings_index < len(data['target_stocks']):
        data['target_stocks'][2*holdings_index][1] = target_price
        data['target_stocks'][2*holdings_index + 1][1] = stop_loss_price
    else:
        data['target_stocks'].append([name, target_price, 0])
        data['target_stocks'].append([name, stop_loss_price, 1])
    
    print(f"Stock {name} modified successfully.")

def main():
    filename = 'india_data.json'
    data = load_data(filename)
    
    while True:
        action = input("Enter 'add' to add a stock, 'delete' to delete a stock, 'modify' to modify a stock (or 'exit' to quit): ").strip().lower()
        if action == 'add':
            add_stock(data)
        elif action == 'delete':
            delete_stock(data)
        elif action == 'modify':
            modify_stock(data)
        elif action == 'exit':
            break
        else:
            print("Invalid option. Please try again.")
    
    save_data(filename, data)
    print("Changes saved to file.")

if __name__ == "__main__":
    main()

