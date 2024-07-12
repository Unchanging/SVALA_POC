from openai import OpenAI
import os
import shutil
import time


def create_controller(requirement_specification, run_path, iteration, thread = None):
    
    client = OpenAI()
    
    if thread == None:
        thread = client.beta.threads.create()

    # Remove previous controller
    remove_previous_controller()

    input_message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=requirement_specification
    )

    # TODO: Provide assistant_id 
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id="TODO_ADD_ID",
    )
    
    while run.status in ['queued', 'in_progress', 'cancelling']:
        time.sleep(1) # Wait for 1 second
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
    )

    if run.status == 'completed': 
        messages = client.beta.threads.messages.list(
            thread_id=thread.id, 
            order='asc'
        )
    else:
        print(run.status)

    # Save the entire messagelist
    save_messages_to_file(messages, run_path, iteration)


    # Accumulator for the text-part of the reponse.
    text = ""

    file_number = 0
    for message in messages:
        message_content = message.content[0].text
        annotations = message_content.annotations

        text += message_content.value

        for annotation in annotations:
            file_path = getattr(annotation, 'file_path', None) 

            if file_path:
                file_number += 1

                contentHpptx = client.files.content(file_path.file_id)
                content = contentHpptx.read()

                with open("./custom_controller.py", "wb") as file:
                    file.write(content)

    correctNumberOfFiles = True
    if file_number != (iteration+1):
        print("Warning: No new file was created")
        correctNumberOfFiles = False



    custom_controller_path = './custom_controller.py'
    if os.path.exists(custom_controller_path):
        # Create or ensure the "controller" subdirectory exists
        controller_subdir = os.path.join(run_path, "controller")
        if not os.path.exists(controller_subdir):
            os.makedirs(controller_subdir)
        
        # Copy the custom_controller.py file to the "controller" subdirectory
        shutil.copy(custom_controller_path, os.path.join(controller_subdir, f'{iteration}_custom_controller.py'))
        
    return thread, text, correctNumberOfFiles


def remove_previous_controller():
    custom_controller_path = './custom_controller.py'
    if os.path.exists(custom_controller_path):
        os.remove(custom_controller_path)

def save_messages_to_file(objects, path, subdir):

    # Construct the directory path including the subdir
    dir_path = os.path.join(path, str(subdir))
    
    # Ensure the directory exists, create it if it doesn't
    os.makedirs(dir_path, exist_ok=True)
    
    # Construct the full file path
    full_file_path = os.path.join(dir_path, "controllerCreatorMessages.txt")
    
    with open(full_file_path, 'w') as file:
        for i, obj in enumerate(objects):

            file.write(f"Message number: {i}")
            
            # Attempt to get the string representation of the object
            string_representation = str(obj)
            
            # Write the string representation to the file
            file.write(string_representation)
            
            # Write a dashed line to separate objects
            file.write('\n' + '-' * 20 + '\n')

