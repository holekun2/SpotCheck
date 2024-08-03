from google.cloud import storage
import pandas as pd
import io
from typing import List, Dict, Any
import json

class InspectionDataReader:
    @staticmethod
    def read_inspection_data() -> List[Dict[str, Any]]:
        # Initialize the Google Cloud Storage client
        storage_client = storage.Client()

        # Replace with your actual bucket name
        bucket_name = "excel-updater"
        bucket = storage_client.bucket(bucket_name)

        # List all blobs (files) in the bucket
        blobs = list(bucket.list_blobs())

        # Filter for Excel files and sort by creation time (most recent first)
        excel_blobs = [blob for blob in blobs if blob.name.endswith('.xlsx')]
        excel_blobs.sort(key=lambda x: x.time_created, reverse=True)

        if not excel_blobs:
            raise FileNotFoundError("No Excel files found in the bucket.")

        # Get the most recent Excel file
        most_recent_blob = excel_blobs[0]

        # Download the contents of the blob as bytes
        content = most_recent_blob.download_as_bytes()

        # Use pandas to read the Excel content
        df = pd.read_excel(io.BytesIO(content))

        # Convert to list of dictionaries
        inspection_data = df.to_dict('records')

        return inspection_data
    



    def load_flight_requirements():
        # Initialize the Google Cloud Storage client
        storage_client = storage.Client()


        bucket_name = "excel-updater"
        bucket = storage_client.bucket(bucket_name)

        # Specify the name of your JSON file in the bucket
        blob_name = "flight_requirements.json"
        blob = bucket.blob(blob_name)

        # Download the contents of the blob as string
        json_string = blob.download_as_text()

        # Parse the JSON string
        flight_requirements = json.loads(json_string)

        return flight_requirements