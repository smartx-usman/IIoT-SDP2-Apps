import csv
import json


# Function to convert a CSV to JSON
# Takes the file paths as arguments
def make_json(csvFilePath, jsonFilePath):
    # create a dictionary
    data = {}

    # Open a csv reader called DictReader
    with open(csvFilePath, encoding='utf-8') as csvf:
        csvReader = csv.DictReader(csvf)

        with open(jsonFilePath, 'a', encoding='utf-8') as jsonf:
            jsonf.write("{")
            jsonf.write('"temperature-data.csv": [')

        # Convert each row into a dictionary
        # and add it to data

        for rows in csvReader:
            # Assuming a column named 'No' to
            # be the primary key
            with open(jsonFilePath, 'a', encoding='utf-8') as jsonf:
                key = rows['timestamp']
                #data[key] = rows
                jsonf.write('"'+key+'",')
    # Open a json writer, and use the json.dumps()
    # function to dump data
    with open(jsonFilePath, 'a', encoding='utf-8') as jsonf:
        jsonf.write("]")
        jsonf.write("}")


# Driver Code

# Decide the two file paths according to your
# computer system
csvFilePath = r'/Users/muhausma/train-anomalies.csv'
jsonFilePath = r'/Users/muhausma/train-anomalies.json'

# Call the make_json function
make_json(csvFilePath, jsonFilePath)

csvFilePath = r'/Users/muhausma/valid-anomalies.csv'
jsonFilePath = r'/Users/muhausma/valid-anomalies.json'
make_json(csvFilePath, jsonFilePath)