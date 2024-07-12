from PIL import Image
import os
from openai import OpenAI
import base64
import numpy as np


# Converts image formats and requests a report based on the them
def generate_visual_report(crash_frame, task, iteration, scenario, run_path):

    convert_TGA(crash_frame, iteration, scenario, run_path)
    
    report = analyze_images("screen_shots", task)
    return report

def convert_TGA(crash_frame, iteration, scenario, run_path):
    # Set the source folder to the current working directory
    source_folder = os.getcwd()
    screen_shots_folder = os.path.join(source_folder, 'screen_shots')
    # Ensure the screen_shots folder exists
    os.makedirs(screen_shots_folder, exist_ok=True)
    # Remove potential previous images in the folder.
    remove_PNG(screen_shots_folder)

    # Define and ensure the new structured destination folder exists
    new_destination_folder = os.path.join(run_path, str(iteration), str(scenario))
    os.makedirs(new_destination_folder, exist_ok=True)
    
    frame_number = 0
    for filename in os.listdir(source_folder):
        if filename.endswith('.tga'):
            frame_number += 1
            original_path = os.path.join(source_folder, filename)
            try:
                with Image.open(original_path) as img:
                    # Define the new filename, replacing the file extension
                    new_filename = filename[:-4] + '.png'   
                    # Check if the current frame is within the desired range
                    if abs(frame_number - crash_frame) <= 1:
                        # Save the image in the screen_shots folder
                        img.save(os.path.join(screen_shots_folder, new_filename))
                        # Additionally, save a copy in the new structured destination folder
                        img.save(os.path.join(new_destination_folder, new_filename))
            except Exception as e:
                print(f"Failed to convert {filename}. Error: {e}")

def remove_TGA():
    source_folder = os.getcwd()
    for filename in os.listdir(source_folder):
        if filename.endswith('.tga'):
            original_path = os.path.join(source_folder, filename)
            os.remove(original_path)

def remove_PNG(folder):
    for filename in os.listdir(folder):
        if filename.endswith('.png'):
            original_path = os.path.join(folder, filename)
            os.remove(original_path)

def encode_image_to_base64(image_path):
    """
    Encodes an image to a base64 string.

    :param image_path: Path to the image file.
    :return: A base64 encoded string of the image.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Sends images and text to LLM to generate commentary
def analyze_images(folder_path, task_prompt):

    vision_prompt = f"""These screenshots were captured because a collision was detected during the simulation run. 
\nPlease try to give an explanation of what might have gone wrong in the images.
\nGive details such as the positions of the vehicles, relative to each other and to the road network, and similar data. The lanes are separated by dashed lines and the edge of the lanes by continuous lines. There might also be a shoulder of the road beyond the continuous lines. Notice the text above each vehicle with its name, id number, the distance traveled (m) on the first row. 
\nSpeed (km/h), current lane / ongoing relative lane change, the distance from the start of the road (m) on the second row 
\nX and Y coordinates (m) and heading (Radians) on the third row. ignore the fourth row. 
\nThe lines on the ground trailing after the vehicles show how they have traveled. They might overlap and in that case only one line is visible. 
\nThe code controlling the white car was created by an LLM with the specification: \n{{{task_prompt}}}
\n Remember to provide explanations of what is shown in the image which the code generating LLM will use. Do not provide any suggestions of how the implementation of the code might be changed. Just try to give a good explanation of what might have gone wrong in the images. Example output based on different input images could be: \n
{{A non-controlled car drives past Ego on the left, and then cuts Ego off by changing its lane to Ego’s and decelerating. Ego maintains the same speed and remains in its initial lane which leads to a collision.}}
"""
    # List of user message and images
    content = [
            {
            "type": "text",
            "text": vision_prompt,
            }
        ]
        
    # Add all images in the folder to the message
    for file_name in os.listdir(folder_path):
        full_path = os.path.join(folder_path, file_name)
        if os.path.isfile(full_path) and file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
            base64_image = encode_image_to_base64(full_path)
            content.append({
                "type": "image_url",
                "image_url": f"data:image/jpeg;base64,{base64_image}"
            })

    system_prompt = """You are an expert at analyzing screenshots of traffic scenarios enacted in the Esmini simulator suite. The Esmini simulator is a minimalistic traffic simulator. Screenshots are captured and provided to you when there’s a fail state detected during the simulation. There is no guarantee that the failure is visible in the provided screenshot, so you should be clear if you can’t see what the issue might be. 
    You are going to provide descriptions of the scene and try to explain what it depicts. These natural language reports are going to be fed into another LLM, combined with other reports based on numerical logs, which will try to improve the code which controls the white car. Refer to the white car as “Ego” and distinguish it from the “non-controlled” car or cars. 
    """

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[{"role": "system", "content": 
                system_prompt     }, 
            {
            "role": "user",
            "content": content,
            }
        ],
        max_tokens=800,
    )
    return response.choices[0].message.content
