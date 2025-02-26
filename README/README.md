# Venmito Data Engineering Project (Raul Rivera Solution)

- Name: Raul A. Rivera Rodriguez
- Email: raularmandoriv@gmail.com

## Approach Description

This approach took pandas data frames as the data type to use to get all the data into a same format. We first passed all different files into five data frames. After that the normalization of the data was done while merging and creating new csv files to permanently store all data. 

- Merged_people.csv was creating by merging both people.js and people.yml
- Merged_promotions.csv was creating by merging promotions.csv with Merged_people.csv
- Merged_transactions.csv was created by merging transactions.xml with Merged_people.csv
- transfers_filled.csv was created by merging transfers.csv with Merged_people.csv

This ensured all the data was well stored and conected to start our analysis. We did analysis on promotions, transactions and transfers, using the general data frames variable of each csv file on the code. 

- For Transactions we got the next analysis:

    1. Store Performance Analysis
    2. Product Performance Analysis
    3. Price & Profit Analysis
    4. Customer Analysis
    5. Transaction Analysis

- For Promotions we got the next analysis:

    1. General Response Analysis
    2. Promotions Performance Per Item
    3. Promotions by City
    4. Promotions by Device
    5. Response Rate Per City
    6. Response Rate Per Device
    7. Response Rate Per Promotion
    8. Most & Least Successful Promotions
    9. Yes Responses Based on Device Count

- For Transfers we got the next analysis:

    1. Most & Least Expensive Transfers
    2. Total Transfer Amounts by Person
    3. Transfer Frequency by Person
    4. Transfers by City

Then with this information we created two ways to consume the data. The first one is a CLI (Command Line Interface) that can be run in any code runner such as VS Code. The other is a GUI (Graphical User Interface) using Streamlit

## Technologies Used

- Libraries used were: pandas, yml, xml.etree.ElementTree, and streamlit
- For coding it was used VS Code, an evironment of Python 3.12.9.

## How to run

1. Download and import the repo into any IDE of your choice (Used was VS Code)
2. Make sure Python is on 3.12 at least, and download the libraries previously mentioned.
3. To run the code for the CLI, you will need to check that the line (610) is uncomment and run the file Solution.py as any other file.
4. To run the GUI you will need to comment the line (610) and go to the command prompt. There you will need to run
    - streamlit run (Solution.py file path)
    - In case it gives any error saying that streamlit is not found as a python command use (py -m) before the actual command.
