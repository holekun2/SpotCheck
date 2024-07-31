# flight_requirements.py

from typing import Dict, List, Optional
import json

class FlightRequirementsLibrary:
    def __init__(self, file_path: str = r'Shared\Data\Inspection data\flight_requirements.json'):
        self.file_path = file_path
        self.requirements: Dict[str, List[str]] = self.load_requirements()

    def load_requirements(self) -> Dict[str, List[str]]:
        try:
            with open(self.file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def save_requirements(self) -> None:
        with open(self.file_path, 'w') as file:
            json.dump(self.requirements, file, indent=2)

    def get_requirements(self, scope_package: str) -> Optional[List[str]]:
        return self.requirements.get(scope_package)

    def add_requirement(self, scope_package: str, flight_types: List[str]) -> None:
        self.requirements[scope_package] = flight_types
        self.save_requirements()

    def update_requirement(self, scope_package: str, flight_types: List[str]) -> None:
        if scope_package in self.requirements:
            self.requirements[scope_package] = flight_types
            self.save_requirements()

    def remove_requirement(self, scope_package: str) -> None:
        if scope_package in self.requirements:
            del self.requirements[scope_package]
            self.save_requirements()

# Example usage:
library = FlightRequirementsLibrary()
library.add_requirement('Tower Form W/ Center Out_V1.1', ['access, top down, cable anchor, tower flight Type 2, compound flight upper, compound flight lower, center in, uplook'])
print(library.get_requirements('Tower Form W/ Center Out_V1.1'))