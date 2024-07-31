import os
from image_analyzer_gemini import ImageAnalyzerGemini
from prompts import CABLE_ANCHOR_SYSTEM_INSTRUCTION, CABLE_ANCHOR_PROMPT

class CableAnchorAnalyzer:
    def __init__(self, flight_data):
        self.flight_data = flight_data
        self.category = "cable anchor"

    def analyze_cable_anchor(self) -> bool:
        return self.category in self.flight_data['Flight Category'].values

    def interpret_result(self, result: bool) -> str:
        if result:
            return "Cable anchor flight is present in the data."
        else:
            return "Cable anchor flight is not present in the data. Consider performing a cable anchor inspection."

# def main():
#     # Set up the analyzer with the correct assets folder
#     assets_folder = r"C:\SpotCheck\SpotCheck\Shared\assets\image analyzer assets"
#     analyzer = CableAnchorAnalyzer(assets_folder)

#     # Get the user-selected image path
#     user_selected_image = r'C:\SpotCheck\SpotCheck\Shared\photos5\DJI_0953.JPG'

#     # Ensure the file exists
#     if not os.path.exists(user_selected_image):
#         print(f"Error: The file {user_selected_image} does not exist.")
#         return

#     # Analyze the image
#     result = analyzer.analyze_cable_anchor(user_selected_image)

#     # Interpret and print the result
#     interpretation = analyzer.interpret_result(result)
#     print(interpretation)
#     print(f"Raw result: {result}")

# if __name__ == "__main__":
#     main()