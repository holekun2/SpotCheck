# prompts.py

TOWER_TOP_SYSTEM_INSTRUCTION = """
You are an expert in analyzing drone imagery, particularly for infrastructure inspection. 
Your task is to determine if an image shows the top of a tower or not. 
Consider features like antennas, platforms, or other structures typically found at the top of towers. 
Also, consider the perspective - a view from above or a clear horizontal view of the uppermost part of a structure would indicate the top of a tower.
"""

TOWER_TOP_PROMPT = """
Analyze this drone image and determine if it shows the top of a tower. 
Consider the following:
1. Are there visible antennas, satellite dishes, or other communication equipment?
2. Is there a platform or flat surface that could be the top of a tower?
3. Does the perspective suggest this is a view of the uppermost part of a structure?
4. Are there any signs of a tower structure ending or tapering off?
5. If the image shows the top of a tower, the top portion of the photo should contain view of the sky and possibly horizon.
Based on these considerations, respond with exactly one of the following in one word format:
PASS - if the image clearly shows the top of a tower
FAIL - if the image clearly does not show the top of a tower
INDETERMINATE - if you cannot confidently determine whether the image shows the top of a tower
"""

CABLE_ANCHOR_SYSTEM_INSTRUCTION = """
You are an expert in analyzing drone imagery, particularly for infrastructure inspection. 
Your task is to determine if an image shows a cable anchor or not. 
Compare the given image to the reference image provided.
"""

CABLE_ANCHOR_PROMPT = """
Analyze this drone image and determine if it shows a cable anchor. 
Compare it to the reference image. 
Does the image being analyzed look similar to the example? 
A cable anchor is a safety cable anchor attached to the cable anchor. 
It should look like a hook or a loop connected to a wire. 
Based on these considerations and the comparison to the reference image, respond with exactly one of the following in one word format:
PASS - if the image clearly shows the cable anchor similar to the example
FAIL - if the image clearly does not show the cable anchor or is significantly different from the example
INDETERMINATE - if you cannot confidently determine whether the image matches
"""

#error

# Unmatched right curly bracket at /loader/HASH(0x26b8f04)/PAR/Dist.pm line 62, at end of line
# syntax error at /loader/HASH(0x26b8f04)/PAR/Dist.pm line 62, near "}"
# syntax error at /loader/HASH(0x26b8f04)/PAR/Dist.pm line 76, near "}"
# syntax error at /loader/HASH(0x26b8f04)/PAR/Dist.pm line 593, near "}"
# Can't use global $! in "my" at /loader/HASH(0x26b8f04)/PAR/Dist.pm line 607, near "$! "
# syntax error at /loader/HASH(0x26b8f04)/PAR/Dist.pm line 609, near "}"
# Can't redeclare "my" in "my" at /loader/HASH(0x26b8f04)/PAR/Dist.pm line 636, near ""
# syntax error at /loader/HASH(0x26b8f04)/PAR/Dist.pm line 644, near "croak "First argument to merge_par() must be the .par archive to modify.""
# syntax error at /loader/HASH(0x26b8f04)/PAR/Dist.pm line 648, near "croak "'$base_par' is not a file or you do not have enough permissions to read and modify it.""
# /loader/HASH(0x26b8f04)/PAR/Dist.pm has too many errors.
# Compilation failed in require at -e line 165.
# Condition not met for Shared\photos4\DJI_0001.JPG. Missing keys in metadata: ['File Name', 'Create Date', 'Exposure Time', 'F Number', 'Exposure Program', 'ISO', 'Sensitivity Type', 'Components Configuration', 'Shutter Speed Value', 'Aperture Value', 'Exposure Compensation', 'Max Aperture Value', 'Light Source', 'Focal Length', 'Custom Rendered', 'Exposure Mode', 'White Balance', 'Digital Zoom Ratio', 'Focal Length In 35mm Format', 'Scene Capture Type', 'Gain Control', 'Contrast', 'Saturation', 'Sharpness', 'GPS Version ID', 'Relative Altitude', 'Gimbal Pitch Degree', 'Gimbal Yaw Degree', 'Flight Yaw 
# Degree', 'Flight X Speed', 'Flight Y Speed', 'GPS Latitude', 'GPS Longitude', 'Preview Image', 'Circle Of Confusion', 'Field Of View', 'GPS Position', 'Hyperfocal Distance', 'Light Value', 'Exif Image Width', 'Exif Image Height']
# Processing files:   0%|▏                                            | 2/491 [00:08<29:43,  3.65s/it]Condition not met for Shared\photos4\DJI_0002.JPG. Missing keys in metadata: ['File Name', 'Create Date', 'Exposure Time', 'F Number', 'Exposure Program', 'ISO', 'Sensitivity Type', 'Components Configuration', 'Shutter Speed Value', 'Aperture Value', 'Exposure Compensation', 'Max Aperture Value', 'Light Source', 'Focal Length', 'Custom Rendered', 'Exposure Mode', 'White Balance', 'Digital Zoom Ratio', 'Focal Length In 35mm Format', 'Scene Capture Type', 'Gain Control', 'Contrast', 'Saturation', 'Sharpness', 'GPS Version ID', 'Relative Altitude', 'Gimbal Pitch Degree', 'Gimbal Yaw Degree', 'Flight Yaw Degree', 'Flight X Speed', 'Flight Y Speed', 'GPS Latitude', 'GPS Longitude', 'Preview Image', 'Circle Of Confusion', 'Field Of View', 'GPS Position', 'Hyperfocal Distance', 'Light Value', 'Exif Image Width', 'Exif Image Height']