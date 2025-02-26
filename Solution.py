import pandas as pd
import yaml
import xml.etree.ElementTree as ET
import streamlit as st

## =================================
# Parsing the data to pandas dataframes
## =================================

def parse_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    transactions = []
    for transaction in root.findall("transaction"):
        transaction_id = transaction.get("id")
        phone = transaction.find("phone").text
        store = transaction.find("store").text
        
        for item in transaction.find("items").findall("item"):
            transactions.append({
                "transaction_id": transaction_id,
                "phone": phone,
                "store": store,
                "item_name": item.find("item").text,
                "price": float(item.find("price").text),
                "price_per_item": float(item.find("price_per_item").text),
                "quantity": int(item.find("quantity").text)
            })
    
    return pd.DataFrame(transactions)

def format_location(row):
    if pd.notna(row["city"]):
        return row["city"]
    elif isinstance(row["location"], dict):
        return f"{row['location'].get('City', '')}, {row['location'].get('Country', '')}".strip(', ')
    return None

def update_devices(row):
    devices = set(row["devices"]) if isinstance(row["devices"], list) else set()
    for device in ["Android", "Desktop", "Iphone"]:
        if row.get(device, 0) == 1:
            devices.add(device)
    return list(devices)

transaction_xml = parse_xml("Venmito-FrHend-Raul/data/transactions.xml")
people_js = pd.read_json("Venmito-FrHend-Raul/data/people.json")
promotions_csv = pd.read_csv("Venmito-FrHend-Raul/data/promotions.csv")
transfers_csv = pd.read_csv("Venmito-FrHend-Raul/data/transfers.csv")

with open("Venmito-FrHend-Raul/data/people.yml", "r") as file:
    people_yml = pd.DataFrame(yaml.safe_load(file))

## =================================
# Normalazing the data and merging
# people_js with people_yml
## =================================

# Normalize people js
people_js["name"] = people_js["first_name"] + " " + people_js["last_name"]
people_js.drop(columns=["first_name", "last_name"], inplace=True)
people_js.rename(columns={"telephone": "phone"}, inplace=True)

# Merge people data
merged_people = pd.merge(people_js, people_yml, on="email", how="outer")
merged_people["phone"] = merged_people.pop("phone_x").combine_first(merged_people.pop("phone_y"))
merged_people["id"] = merged_people.pop("id_x").combine_first(merged_people.pop("id_y"))
merged_people["name"] = merged_people.pop("name_x").combine_first(merged_people.pop("name_y"))

# Standardize city column
merged_people["city"] = merged_people.apply(format_location, axis=1)
merged_people.drop(columns=["location"], inplace=True, errors="ignore")

# Update devices column
merged_people["devices"] = merged_people.apply(update_devices, axis=1)
merged_people.drop(columns=["Android", "Desktop", "Iphone"], inplace=True, errors="ignore")

merged_people.to_csv("Venmito-FrHend-Raul/csv_data/Merged_people.csv", index=False)

## =================================
# Normalazing the data and merging
# merged_people to promotions_csv
## =================================

# Rename columns for consistency
promotions_csv.rename(columns={"client_email": "email", "telephone": "phone"}, inplace=True)

# Drop id from promotions
promotions_csv.drop(columns=["id"], inplace=True, errors="ignore")

# Fill missing values in email and phone by looking for matches in merged_people
promotions_csv['email'] = promotions_csv['email'].fillna(promotions_csv['phone'].map(merged_people.set_index('phone')['email']))
promotions_csv['phone'] = promotions_csv['phone'].fillna(promotions_csv['email'].map(merged_people.set_index('email')['phone']))

# Merge separately on email and phone
merge_email = promotions_csv.merge(merged_people, on="phone", how="left")
merge_phone = promotions_csv.merge(merged_people, on="email", how="left")

# Combine both merges, prioritizing non-null values
merged_promotions = merge_email.combine_first(merge_phone)
final_columns = ["id", "name", "phone", "email", "city", "devices", "promotion", "responded"]
final_promotions = merged_promotions[final_columns]

final_promotions.to_csv("Venmito-FrHend-Raul\csv_data\merged_promotions.csv", index=False)

## =================================
# Normalazing the data and merging
# merged_people to transfers_csv
## =================================

transfers_csv['sender_name'] = ''
transfers_csv['sender_email'] = ''
transfers_csv['sender_phone'] = ''
transfers_csv['sender_city'] = ''
transfers_csv['recipient_name'] = ''
transfers_csv['recipient_email'] = ''
transfers_csv['recipient_phone'] = ''
transfers_csv['recipient_city'] = ''

merged_people_sender = merged_people.rename(columns={
    'name': 'sender_name',
    'email': 'sender_email',
    'phone': 'sender_phone',
    'city': 'sender_city',
    'id': 'sender_id'
})

merged_people_receiver = merged_people.rename(columns={
    'name': 'recipient_name',
    'email': 'recipient_email',
    'phone': 'recipient_phone',
    'city': 'recipient_city',
    'id': 'recipient_id'
})

# Merge the sender and receiver information into transfers_csv
transfers_csv = transfers_csv.merge(merged_people_sender[['sender_id', 'sender_name', 'sender_email', 'sender_phone', 'sender_city']], 
                                     how='left', on='sender_id')

transfers_csv = transfers_csv.merge(merged_people_receiver[['recipient_id', 'recipient_name', 'recipient_email', 'recipient_phone', 'recipient_city']], 
                                     how='left', on='recipient_id')

transfers_csv = transfers_csv.drop([col for col in transfers_csv.columns if col.endswith('_x')], axis=1)


transfers_csv = transfers_csv.rename(columns={col: col.replace('_y', '') for col in transfers_csv.columns if col.endswith('_y')})

transfers_csv.to_csv('Venmito-FrHend-Raul/csv_data/transfers_filled.csv', index=False)

## =================================
# Normalazing the data and merging
# merged_people to transactions_xml
## =================================

merged_transactions = transaction_xml.merge(merged_people[['phone', 'id', 'name', 'email']], 
                                            how='left', on='phone')

merged_transactions.to_csv('Venmito-FrHend-Raul\csv_data\merged_transactions.csv', index=False)


###ANALYSIS

## =================================
# TRANSACTIONS
## =================================

# 1. Store Performance Analysis

total_sales_per_store = merged_transactions.groupby('store')['price'].sum()
most_profitable_store = total_sales_per_store.idxmax()
most_frequent_store = merged_transactions['store'].value_counts().idxmax()

# 2. Product Performance Analysis

best_selling_product = merged_transactions.groupby('item_name')['quantity'].sum().idxmax()
least_selling_product = merged_transactions.groupby('item_name')['quantity'].sum().idxmin()
most_profitable_product = merged_transactions.groupby('item_name')['price'].sum().idxmax()

# 3. Price & Profit Analysis

most_expensive_product = merged_transactions.loc[merged_transactions['price_per_item'].idxmax(), 'item_name']
cheapest_product = merged_transactions.loc[merged_transactions['price_per_item'].idxmin(), 'item_name']
total_revenue_per_product = merged_transactions.groupby('item_name')['price'].sum()

# 4. Customer Analysis

most_frequent_customer = merged_transactions['name'].value_counts().idxmax()
highest_spending_customer = merged_transactions.groupby('id')['price'].sum().idxmax()

# 5. Transaction Analysis

largest_transaction = merged_transactions.groupby('transaction_id')['price'].sum().idxmax()
largest_transaction_amount = merged_transactions.groupby('transaction_id')['price'].sum().max()
largest_transaction_details = merged_transactions[merged_transactions['transaction_id'] == largest_transaction]

## =================================
# PROMOTIONS
## =================================

# Convert 'devices' column from string to actual lists
final_promotions = final_promotions.copy()
final_promotions.loc[:, 'devices'] = final_promotions['devices'].apply(lambda x: eval(x) if isinstance(x, str) else x)

# Create numeric response column
final_promotions.loc[:, 'responded_numeric'] = final_promotions['responded'].map({'Yes': 1, 'No': 0})

# Explode the devices column
df_exploded = final_promotions.explode('devices').copy()

# Create numeric response column for df_exploded
df_exploded.loc[:, 'responded_numeric'] = df_exploded['responded'].map({'Yes': 1, 'No': 0})

# 1. General Response Analysis
response_counts = final_promotions['responded'].value_counts()

# 2. Promotions Performance Per Item
promotion_response = final_promotions.groupby('promotion')['responded'].value_counts().unstack().fillna(0)

# 3. Promotions by City
city_response = final_promotions.groupby('city')['responded'].value_counts().unstack().fillna(0)

# 4. Promotions by Device
device_response = df_exploded.groupby('devices')['responded'].value_counts().unstack().fillna(0)

# 5. Response Rate Per City
city_response_rate = final_promotions.groupby('city')['responded_numeric'].mean().sort_values(ascending=False)

# 6. Response Rate Per Device
device_response_rate = df_exploded.groupby('devices')['responded_numeric'].mean().sort_values(ascending=False)

# 7. Response Rate Per Promotion
promotion_response_rate = final_promotions.groupby('promotion')['responded_numeric'].mean().sort_values(ascending=False)

# 8. Most & Least Successful Promotions (Based on Yes Percentage)
promotion_success_rate = (promotion_response["Yes"] / (promotion_response["Yes"] + promotion_response["No"])).sort_values(ascending=False)
city_success_rate = (city_response["Yes"] / (city_response["Yes"] + city_response["No"])).sort_values(ascending=False)
device_success_rate = (device_response["Yes"] / (device_response["Yes"] + device_response["No"])).sort_values(ascending=False)

# 9. Get the best and worst performers based on success rate
most_successful_promotion = promotion_success_rate.idxmax()
least_successful_promotion = promotion_success_rate.idxmin()

most_successful_city = city_success_rate.idxmax()
least_successful_city = city_success_rate.idxmin()

most_successful_device = device_success_rate.idxmax()
least_successful_device = device_success_rate.idxmin()

# 10. Device Count & Yes Responses
final_promotions.loc[:, 'device_count'] = final_promotions['devices'].apply(lambda x: len(set(x)) if isinstance(x, list) else 1)

# 11. Count the number of "Yes" responses for each device count
device_count_response = final_promotions[final_promotions['responded'] == 'Yes'].groupby('device_count').size()


## =================================
# TRANSFERS
## =================================

data = transfers_csv.copy()

# 1. Person who does the most transfers (sender)
top_sender = data['sender_name'].value_counts().idxmax()

# 2. Person who receives the most transfers (recipient)
top_recipient = data['recipient_name'].value_counts().idxmax()

# 3. City that sends the most transfers
top_sender_city = data['sender_city'].value_counts().idxmax()

# 4. City that receives the most transfers
top_recipient_city = data['recipient_city'].value_counts().idxmax()

# 5. City that sends the least transfers
least_sender_city = data['sender_city'].value_counts().idxmin()

# 6. City that receives the least transfers
least_recipient_city = data['recipient_city'].value_counts().idxmin()

# 7. Most expensive transfer (only amount and names)
most_expensive_transfer_amount = data['amount'].max()
most_expensive_transfer_sender = data.loc[data['amount'].idxmax()]['sender_name']
most_expensive_transfer_recipient = data.loc[data['amount'].idxmax()]['recipient_name']

# 8. Least expensive transfer (only amount and names)
least_expensive_transfer_amount = data['amount'].min()
least_expensive_transfer_sender = data.loc[data['amount'].idxmin()]['sender_name']
least_expensive_transfer_recipient = data.loc[data['amount'].idxmin()]['recipient_name']

# 9. Person with the most expensive total transfer amount (sum of their transfers)
sender_total = data.groupby('sender_name')['amount'].sum()
most_expensive_sender = sender_total.idxmax()

# 10. Person with the least expensive total transfer amount (sum of their transfers)
least_expensive_sender = sender_total.idxmin()

# 11. Person who received the most expensive total transfer amount (sum of their received transfers)
recipient_total = data.groupby('recipient_name')['amount'].sum()
most_expensive_recipient = recipient_total.idxmax()

# 12. Person who received the least expensive total transfer amount (sum of their received transfers)
least_expensive_recipient = recipient_total.idxmin()

## =================================
# CLI MENU
## =================================

def transactions_menu():
    while True:
        print("\nTransaction Analysis:")
        print("1. Store Performance Analysis")
        print("2. Product Performance Analysis")
        print("3. Price & Profit Analysis")
        print("4. Customer Analysis")
        print("5. Transaction Analysis")
        print("6. Go Back")
        
        choice = input("Choose an option: ")
        
        if choice == "1":
            print(f"Total Sales per Store:\n{total_sales_per_store}")
            print(f"Most Profitable Store: {most_profitable_store}")
            print(f"Most Frequent Store: {most_frequent_store}")
        elif choice == "2":
            print(f"Best-Selling Product: {best_selling_product}")
            print(f"Least Selling Product: {least_selling_product}")
            print(f"Most Profitable Product: {most_profitable_product}")
        elif choice == "3":
            print(f"Most Expensive Product: {most_expensive_product}")
            print(f"Cheapest Product: {cheapest_product}")
            print(f"Total Revenue per Product:\n{total_revenue_per_product}")
        elif choice == "4":
            print(f"Most Frequent Customer: {most_frequent_customer}")
            print(f"Highest Spending Customer: {highest_spending_customer}")
        elif choice == "5":
            print(f"Largest Transaction ID: {largest_transaction}")
            print(f"Largest Transaction Amount: {largest_transaction_amount}")
            print("Transaction Details:")
            print(largest_transaction_details)
        elif choice == "6":
            break
        else:
            print("Invalid choice. Please enter a valid option.")

def promotions_menu():
    while True:
        print("\nPromotions Data - Choose an analysis category:")
        print("1. General Response Analysis")
        print("2. Promotions Performance Per Item")
        print("3. Promotions by City")
        print("4. Promotions by Device")
        print("5. Response Rate Per City")
        print("6. Response Rate Per Device")
        print("7. Response Rate Per Promotion")
        print("8. Most & Least Successful Promotions")
        print("9. Yes Responses Based on Device Count")
        print("10. Go back to main menu")

        choice = input("Enter your choice: ")

        if choice == "1":
            print("\n### General Response Analysis ###")
            print(response_counts)
        elif choice == "2":
            print("\n### Promotions Performance Per Item ###")
            print(promotion_response)
        elif choice == "3":
            print("\n### Promotions by City ###")
            print(city_response)
        elif choice == "4":
            print("\n### Promotions by Device ###")
            print(device_response)
        elif choice == "5":
            print("\n### Response Rate Per City ###")
            print(city_response_rate)
        elif choice == "6":
            print("\n### Response Rate Per Device ###")
            print(device_response_rate)
        elif choice == "7":
            print("\n### Response Rate Per Promotion ###")
            print(promotion_response_rate)
        elif choice == "8":
            print("\n### Most & Least Successful Promotions (Based on Yes Percentage) ###")
            print(f"Most successful promotion: {most_successful_promotion} ({promotion_success_rate.max():.2%} success rate)")
            print(f"Least successful promotion: {least_successful_promotion} ({promotion_success_rate.min():.2%} success rate)")
            print(f"Most successful city: {most_successful_city} ({city_success_rate.max():.2%} success rate)")
            print(f"Least successful city: {least_successful_city} ({city_success_rate.min():.2%} success rate)")
            print(f"Most successful device: {most_successful_device} ({device_success_rate.max():.2%} success rate)")
            print(f"Least successful device: {least_successful_device} ({device_success_rate.min():.2%} success rate)")
        elif choice == "9":
            print("\n### Yes Responses Based on Device Count ###")
            print(device_count_response)
        elif choice == "10":
            break  # Go back to the main menu
        else:
            print("Invalid input. Please choose a valid option.")

def transfers_menu():
    while True:
        print("\nTransfers Data - Choose an analysis category:")
        print("1. Most & Least Expensive Transfers")
        print("2. Total Transfer Amounts by Person")
        print("3. Transfer Frequency by Person")
        print("4. Transfers by City")
        print("5. Go back to main menu")

        choice = input("Enter your choice: ")

        if choice == "1":
            print("\n### Most & Least Expensive Transfers ###")
            print(f"Most expensive transfer: {most_expensive_transfer_amount} (Sender: {most_expensive_transfer_sender}, Recipient: {most_expensive_transfer_recipient})")
            print(f"Least expensive transfer: {least_expensive_transfer_amount} (Sender: {least_expensive_transfer_sender}, Recipient: {least_expensive_transfer_recipient})")
        elif choice == "2":
            print("\n### Total Transfer Amounts by Person ###")
            print(f"Person with the most expensive total transfer: {most_expensive_sender} with {sender_total[most_expensive_sender]}")
            print(f"Person with the least expensive total transfer: {least_expensive_sender} with {sender_total[least_expensive_sender]}")
            print(f"Person who received the most expensive total transfer: {most_expensive_recipient} with {recipient_total[most_expensive_recipient]}")
            print(f"Person who received the least expensive total transfer: {least_expensive_recipient} with {recipient_total[least_expensive_recipient]}")
        elif choice == "3":
            print("\n### Transfer Frequency by Person ###")
            print(f"Person who does the most transfers (sender): {top_sender}")
            print(f"Person who receives the most transfers (recipient): {top_recipient}")
        elif choice == "4":
            print("\n### Transfers by City ###")
            print(f"City that sends the most transfers: {top_sender_city}")
            print(f"City that receives the most transfers: {top_recipient_city}")
            print(f"City that sends the least transfers: {least_sender_city}")
            print(f"City that receives the least transfers: {least_recipient_city}")
        elif choice == "5":
            break  # Go back to the main menu
        else:
            print("Invalid input. Please choose a valid option.")

def cli_main_menu():
    while True:
        print('\nWelcome to Venmito CLI')
        print('This platform will let you see the data analyzed from our server')
        print("Please choose the area for analysis:")
        print("1. Transactions")
        print("2. Promotions")
        print("3. Transfers")
        print("4. Exit")
        
        choice = input("Choose an option: ")
        
        if choice == "1":
            transactions_menu()
        elif choice == "2":
            promotions_menu()
        elif choice == "3":
            transfers_menu()
        elif choice == "4":
            print("Exiting program. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a valid option.")

## =================================
# GUI Menu
## =================================

def show_transactions():
    st.title("Transaction Analysis")

    st.subheader("Store Performance Analysis")
    df_sales = pd.DataFrame(list(total_sales_per_store.items()), columns=["Store", "Total Sales"])
    st.write("Total Sales per Store")
    st.dataframe(df_sales)
    st.write(f"Most Profitable Store: {most_profitable_store}")
    st.write(f"Most Frequent Store: {most_frequent_store}")
    
    st.subheader("Product Performance Analysis")
    st.write(f"Best-Selling Product: {best_selling_product}")
    st.write(f"Least Selling Product: {least_selling_product}")
    st.write(f"Most Profitable Product: {most_profitable_product}")
    
    st.subheader("Price & Profit Analysis")
    st.write(f"Most Expensive Product: {most_expensive_product}")
    st.write(f"Cheapest Product: {cheapest_product}")
    df_revenue = pd.DataFrame(list(total_revenue_per_product.items()), columns=["Product", "Total Revenue"])
    st.write("### Total Revenue per Product")
    st.dataframe(df_revenue)
    
    st.subheader("Customer Analysis")
    st.write(f"Most Frequent Customer: {most_frequent_customer}")
    st.write(f"Highest Spending Customer: {highest_spending_customer}")
    
    st.subheader("Transaction Analysis")
    st.write(f"Largest Transaction ID: {largest_transaction}")
    st.write(f"Largest Transaction Amount: {largest_transaction_amount}")
    st.write("Transaction Details:")
    st.write(largest_transaction_details)


def show_promotions():
    st.title("Promotions Data Analysis")

    st.subheader("General Response Analysis")
    st.dataframe(response_counts)

    st.subheader("Promotions Performance Per Item")
    
    st.dataframe(promotion_response)

    
    st.subheader("Promotions by City")
    
    st.dataframe(city_response)

    
    st.subheader("Promotions by Device")
    
    st.dataframe(device_response)

    
    st.subheader("Response Rate Per City")
    df_city_response_rate = pd.DataFrame(list(city_response_rate.items()), columns=["City", "Response Rate"])
    st.dataframe(df_city_response_rate)

    
    st.subheader("Response Rate Per Device")
    df_device_response_rate = pd.DataFrame(list(device_response_rate.items()), columns=["Device", "Response Rate"])
    st.dataframe(df_device_response_rate)

    
    st.subheader("Response Rate Per Promotion")
    
    most_successful_promotion = promotion_success_rate.idxmax() if promotion_success_rate is not None else None
    least_successful_promotion = promotion_success_rate.idxmin() if promotion_success_rate is not None else None

    
    most_successful_city = city_success_rate.idxmax() if city_success_rate is not None else None
    least_successful_city = city_success_rate.idxmin() if city_success_rate is not None else None

    
    most_successful_device = device_success_rate.idxmax() if device_success_rate is not None else None
    least_successful_device = device_success_rate.idxmin() if device_success_rate is not None else None

    
    if most_successful_promotion and least_successful_promotion:
        st.write(f"Most successful promotion: {most_successful_promotion} ({promotion_success_rate.max():.2%} success rate)")
        st.write(f"Least successful promotion: {least_successful_promotion} ({promotion_success_rate.min():.2%} success rate)")

    if most_successful_city and least_successful_city:
        st.write(f"Most successful city: {most_successful_city} ({city_success_rate.max():.2%} success rate)")
        st.write(f"Least successful city: {least_successful_city} ({city_success_rate.min():.2%} success rate)")

    if most_successful_device and least_successful_device:
        st.write(f"Most successful device: {most_successful_device} ({device_success_rate.max():.2%} success rate)")
        st.write(f"Least successful device: {least_successful_device} ({device_success_rate.min():.2%} success rate)")

    st.subheader("Yes Responses Based on Device Count")
    st.write(f"Device Count Responses:\n{device_count_response}")

def show_transfers():
    st.subheader("Transfers Data Analysis")

    st.write("### Most & Least Expensive Transfers")
    st.write(f"Most expensive transfer: ${most_expensive_transfer_amount} (Sender: {most_expensive_transfer_sender}, Recipient: {most_expensive_transfer_recipient})")
    st.write(f"Least expensive transfer: ${least_expensive_transfer_amount} (Sender: {least_expensive_transfer_sender}, Recipient: {least_expensive_transfer_recipient})")

    st.write("### Total Transfer Amounts by Person")
    st.write(f"Person with the most expensive total transfer: {most_expensive_sender} with ${sender_total[most_expensive_sender]}")
    st.write(f"Person with the least expensive total transfer: {least_expensive_sender} with ${sender_total[least_expensive_sender]}")
    st.write(f"Person who received the most expensive total transfer: {most_expensive_recipient} with ${recipient_total[most_expensive_recipient]}")
    st.write(f"Person who received the least expensive total transfer: {least_expensive_recipient} with ${recipient_total[least_expensive_recipient]}")

    st.write("### Transfer Frequency by Person")
    st.write(f"Person who does the most transfers (sender): {top_sender}")
    st.write(f"Person who receives the most transfers (recipient): {top_recipient}")

    st.write("### Transfers by City")
    st.write(f"City that sends the most transfers: {top_sender_city}")
    st.write(f"City that receives the most transfers: {top_recipient_city}")
    st.write(f"City that sends the least transfers: {least_sender_city}")
    st.write(f"City that receives the least transfers: {least_recipient_city}")

# Main Dashboard UI
def main():
    
    menu = ["Home", "Transactions", "Promotions", "Transfers"]
    choice = st.sidebar.selectbox("Select an Option", menu)

    
    if choice == "Home":
        st.title("Welcome to Venmito Dashboard")
        st.write("Hello, welcome to the Venmito Dashboard. Please choose a page to get started.")
    
    
    elif choice == "Transactions":
        st.empty()  
        show_transactions()
    elif choice == "Promotions":
        st.empty()  
        show_promotions()
    elif choice == "Transfers":
        st.empty()  
        show_transfers()

if __name__ == "__main__":
    main()

## =================================
# RUNNING EVERYTHING
# To run the CLI go to line 610 and uncomment the function. This should work just running the python file as any other python file
# To run the GUI comment line 610 and run streamlit run "local file path". Any issues with python write "py -m" before the command.
## =================================

cli_main_menu()