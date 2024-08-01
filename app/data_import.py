import pandas as pd

def read_excel_to_list(file_path):
    # Read the Excel file
    df = pd.read_excel(file_path)

    # Convert the DataFrame to a list of dictionaries
    data_list = df.to_dict('records')

    return data_list

file_path = r'app\Inspection data\inspection_data.xlsx'
data_list = read_excel_to_list(file_path)


        