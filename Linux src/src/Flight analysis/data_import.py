import pandas as pd

def read_excel_to_list(file_path):
    # Read the Excel file
    df = pd.read_excel(file_path)

    # Convert the DataFrame to a list of dictionaries
    data_list = df.to_dict('records')

    return data_list

file_path = r'Shared/Data/Inspection data/inspection_data.xlsx'
data_list = read_excel_to_list(file_path)

#pilot_name = input("Enter the pilot's name: ")
#count = 0
#for record in data_list:
    #if record['Pilot: Full Name'] == pilot_name:
        #print(record['Site ID'])
        #count +=1
#print(count)
        