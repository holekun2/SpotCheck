import os
import unittest
from unittest.mock import patch
from data_extraction import dms_to_dd, get_detailed_metadata, parse_metadata_to_dict, extract_data
import tempfile
from datetime import datetime, timezone

class TestDataExtraction(unittest.TestCase):
    def test_dms_to_dd(self):
        # Test case 1: Valid DMS format
        self.assertAlmostEqual(dms_to_dd("40°26'46.302\"N"), 40.446195, places=6)
        
        # Test case 2: Valid DMS format with direction
        self.assertAlmostEqual(dms_to_dd("73°59'25.747\"W"), -73.99048611111111, places=5)
        
        # Test case 3: Invalid DMS format
        self.assertIsNone(dms_to_dd("invalid"))
        
        # Test case 4: Empty string
        self.assertIsNone(dms_to_dd(""))

    @patch('subprocess.run')
    def test_get_detailed_metadata(self, mock_run):
        # Test case 1: ExifTool installed and metadata retrieved successfully
        mock_run.return_value.stdout = "Metadata output"
        self.assertEqual(get_detailed_metadata("image.jpg"), "Metadata output")
        
        # Test case 2: ExifTool not installed or not found in PATH
        mock_run.side_effect = FileNotFoundError
        self.assertEqual(get_detailed_metadata("image.jpg"), "ExifTool is not installed or not found in PATH.")

    def test_parse_metadata_to_dict(self):
        # Test case 1: Valid metadata string
        metadata = "Key1: Value1\nKey2: Value2"
        expected_dict = {"Key1": "Value1", "Key2": "Value2"}
        self.assertEqual(parse_metadata_to_dict(metadata), expected_dict)
        
        # Test case 2: Empty metadata string
        self.assertEqual(parse_metadata_to_dict(""), {})

    @patch('data_extraction.get_detailed_metadata')
    def test_extract_data(self, mock_get_detailed_metadata):
        # Create a temporary directory with sample image files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create sample image files
            image_file1 = os.path.join(temp_dir, "image1.jpg")
            image_file2 = os.path.join(temp_dir, "image2.jpg")
            image_file3 = os.path.join(temp_dir, "invalid.txt")
            open(image_file1, 'a').close()
            open(image_file2, 'a').close()
            open(image_file3, 'a').close()

            # Mock the metadata for each image file
            mock_get_detailed_metadata.side_effect = [
                "Relative height: 100.0 m\nFlight Roll Degree: +0.0\nFlight Yaw Degree: -18.5\nFlight Pitch Degree: -1.6\nFlight X speed: 0.0 m/s\nFlight Y speed: -0.3 m/s\nFlight Z speed: -0.5 m/s\nFile Modification Date/Time: 2023:05:12 10:00:00+0000",
                "Relative height: 200.0 m\nFlight Roll Degree: +0.0\nFlight Yaw Degree: -20.0\nFlight Pitch Degree: -2.0\nFlight X speed: 0.1 m/s\nFlight Y speed: -0.4 m/s\nFlight Z speed: -0.6 m/s\nFile Modification Date/Time: 2023:05:12 11:00:00+0000",
            ]

            # Call the extract_data function
            data_list = extract_data(temp_dir)

            # Check the extracted data
            self.assertEqual(len(data_list), 2)
            self.assertAlmostEqual(data_list[0]['Relative height'], 100.0)
            self.assertAlmostEqual(data_list[0]['Flight Roll Degree'], 0.0)
            self.assertAlmostEqual(data_list[0]['Flight Yaw Degree'], -18.5)
            self.assertAlmostEqual(data_list[0]['Flight Pitch Degree'], -1.6)
            self.assertAlmostEqual(data_list[0]['Flight X speed'], 0.0)
            self.assertAlmostEqual(data_list[0]['Flight Y speed'], -0.3)
            self.assertAlmostEqual(data_list[0]['Flight Z speed'], -0.5)
            self.assertEqual(data_list[0]['File Modification Date/Time'], datetime(2023, 5, 12, 10, 0, tzinfo=timezone.utc))

if __name__ == '__main__':
    unittest.main()