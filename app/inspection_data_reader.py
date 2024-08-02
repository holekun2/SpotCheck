import pandas as pd
from typing import List, Dict, Any

class InspectionDataReader:
    @staticmethod
    def read_inspection_data() -> List[Dict[str, Any]]:
        inspection_data = pd.read_excel(r'app\Inspection data\inspection_data.xlsx').to_dict('records')
        return inspection_data
