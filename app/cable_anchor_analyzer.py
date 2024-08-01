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

