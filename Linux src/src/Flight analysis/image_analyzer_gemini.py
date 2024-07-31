import google.generativeai as genai
import os
from typing import List
from dotenv import load_dotenv
import PIL.Image

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if api_key is None:
    #print("api key = ", api_key)
    raise ValueError("Check API key.")

genai.configure(api_key=api_key)

class ImageAnalyzerGemini:
    def __init__(self, assets_folder: str = "assets"):
        self.model_flash = genai.GenerativeModel('gemini-1.5-flash')
        self.model_pro = genai.GenerativeModel('gemini-1.5-pro')
        self.assets_folder = assets_folder

    def get_reference_photos(self, category: str) -> List[str]:
        category_folder = os.path.join(self.assets_folder, category)
        if not os.path.exists(category_folder):
            ##print(f"Warning: Category folder {category_folder} does not exist.")
            return []
        return [
            os.path.join(category_folder, f)
            for f in os.listdir(category_folder)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        ]

    def two_step_analysis(self, model, prompt: str, image_path: str, reference_image_path: str = None) -> str:
        try:
            # Step 1: Confirm what it sees in the main image
            main_image = PIL.Image.open(image_path)
            step1_prompt = "Describe what you see in this image concisely."
            step1_response = model.generate_content([step1_prompt, main_image])
            #print(f"Main image description: {step1_response.text.strip()}")

            if reference_image_path:
                # Step 1b: Confirm what it sees in the reference image
                reference_image = PIL.Image.open(reference_image_path)
                ref_step1_prompt = "Describe what you see in this reference image concisely."
                ref_step1_response = model.generate_content([ref_step1_prompt, reference_image])
                #print(f"Reference image description: {ref_step1_response.text.strip()}")

                # Step 2: Compare the images
                step2_prompt = f"{prompt}\n\nMain image: {step1_response.text.strip()}\nReference image: {ref_step1_response.text.strip()}"
                step2_response = model.generate_content([step2_prompt, main_image, reference_image])
            else:
                # If no reference image, just analyze the main image
                step2_prompt = f"{prompt}\n\nImage description: {step1_response.text.strip()}"
                step2_response = model.generate_content([step2_prompt, main_image])

            return step2_response.text.strip().upper()
        except Exception as e:
            #print(f"Error during two_step_analysis: {e}")
            return "ERROR"

    def analyze_image(self, image_path: str, prompt: str, system_instruction: str, category: str) -> str:
        reference_photos = self.get_reference_photos(category)
        reference_image_path = reference_photos[0] if reference_photos else None
        
        full_prompt = f"{system_instruction}\n\n{prompt}"
        
        # First pass with Flash (2 instances)
        results = [self.two_step_analysis(self.model_flash, full_prompt, image_path, reference_image_path) for _ in range(2)]
        
        if all(result == "PASS" for result in results):
            #print("First pass complete: 2/2 PASS")
            return "PASS"
        elif all(result == "FAIL" for result in results):
            #print("First pass complete: 2/2 FAIL")
            return "FAIL"
        
        # Second pass with Flash (3 instances)
        additional_results = [self.two_step_analysis(self.model_flash, full_prompt, image_path, reference_image_path) for _ in range(3)]
        all_results = results + additional_results
        
        pass_count = all_results.count("PASS")
        fail_count = all_results.count("FAIL")
        
        if pass_count >= 3:
            #print("Second pass complete: majority PASS")
            return "PASS"
        elif fail_count >= 3:
            #print("Second pass complete: majority FAIL")
            return "FAIL"
        
        # Third pass with Pro (3 instances)
        pro_results = [self.two_step_analysis(self.model_pro, full_prompt, image_path, reference_image_path) for _ in range(3)]
        
        pass_count = pro_results.count("PASS")
        fail_count = pro_results.count("FAIL")
        indeterminate_count = pro_results.count("INDETERMINATE")
        
        #print(f"Third pass complete: PASS: {pass_count}, FAIL: {fail_count}, INDETERMINATE: {indeterminate_count}")
        
        if pass_count >= 2:
            return "PASS"
        elif fail_count >= 2:
            return "FAIL"
        else:
            return "INDETERMINATE"

# Example usage (unchanged)
# def main():
#     analyzer = ImageAnalyzerGemini(
#         assets_folder=r"C:\SpotCheck\SpotCheck\Shared\assets\image analyzer assets"
#     )

#     system_instruction = (
#         "You are an expert in analyzing drone imagery, particularly for infrastructure inspection. "
#         "Your task is to determine if an image shows a cable anchor or not."
#         "Focus on the center of the image as it is the most relevant part of the image"
#         "Compare the given image to the reference image provided."
#     )

#     prompt = (
#         "Analyze this drone image and determine if it shows a cable anchor. "
#         "Compare it to the reference image. "
#         "Does the image being analyzed look similar to the example? "
#         "A cable anchor is a safety cable anchor attached to the cable anchor. "
#         "It should look like a hook or a loop connected to a wire. "
#         "Based on these considerations and the comparison to the reference image, respond with exactly one of the following in one word format:\n"
#         "PASS - if the image clearly shows the cable anchor similar to the example\n"
#         "FAIL - if the image clearly does not show the cable anchor or is significantly different from the example\n"
#         "INDETERMINATE - if you cannot confidently determine whether the image matches"
#     )

#     user_selected_image = r"C:\SpotCheck\SpotCheck\Shared\photos5\DJI_0953.JPG"
#     category = "cable_anchor"

#     result = analyzer.analyze_image(
#         user_selected_image, prompt, system_instruction, category
#     )

#     if result == "PASS":
#         print("This image shows the cable anchor. You can log the height.")
#     elif result == "FAIL":
#         print("This image does not show the cable anchor. Consider adjusting the drone's position.")
#     else:
#         print("The analysis is inconclusive. Additional inspection may be required.")

#     print(result)

# if __name__ == "__main__":
#     main()