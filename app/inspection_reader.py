from google.cloud import storage
import pandas as pd
import io
from typing import List, Dict, Any
import json
from google.api_core import exceptions


class InspectionDataReader:
    def __init__(self):
        self.storage_client = storage.Client()
        
        
    @staticmethod
    def read_inspection_data() -> List[Dict[str, Any]]:
        # Initialize the Google Cloud Storage client
        storage_client = storage.Client()

        # Replace with your actual bucket name
        bucket_name = "inspection-data"
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
    
    def print_bucket_info(self):
        """Prints available buckets and their contents."""
        buckets = self.storage_client.list_buckets()
        print("Available Buckets:")
        for bucket in buckets:
            print(f"- {bucket.name}")
            print("  Contents:")
            blobs = self.storage_client.list_blobs(bucket.name)
            for blob in blobs:
                print(f"    - {blob.name}")


    @staticmethod
    def load_flight_requirements() -> Dict[str, List[str]]:
        # Initialize the Google Cloud Storage client
        storage_client = storage.Client()

        bucket_name = "inspection-data"
        bucket = storage_client.bucket(bucket_name)
        print(f"Accessing bucket: {bucket_name}")

        # Specify the name of your JSON file in the bucket
        blob_name = "flight_requirements.json"
        blob = bucket.blob(blob_name)
        print(f"Reading file: {blob_name}")
        
        try:
            # Download the contents of the blob as string
            json_string = blob.download_as_text()

            # Parse the JSON string
            flight_requirements = json.loads(json_string)

        except exceptions.NotFound:
            print(f"Warning: {blob_name} not found in {bucket_name}. Using default flight requirements.")
            # Provide a default set of flight requirements
            flight_requirements = {
                "Default": [
                    "uplook, downlook, center in, top down, cable anchor, tower flight Type 2, compound flight upper, compound flight lower"
                ]
            }
        except Exception as e:
            print(f"Error loading flight requirements: {str(e)}. Using default flight requirements.")
            flight_requirements = {
                "Default": [
                    "uplook, downlook, center in, top down, cable anchor, tower flight Type 2, compound flight upper, compound flight lower"
                ]
            }

        return flight_requirements