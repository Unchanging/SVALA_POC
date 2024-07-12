import ctypes as ct
import sys
import os
from datetime import datetime
import json
import shutil

import controller_creator
import report_gen_static
import report_gen_vision
import report_gen_log
import state_layer
from evaluation_suites import * 
import importlib

def main(evaluation_suite):

    """
    The main function of Svala. 
    The input is an evaluation suite dictionary object and the output is the creation of various files.
    Steps:
        1. Unpacks values from the evaluation suite.
        2. Creates a folder for all the resulting files.
        3. Generates a new controller file.
        4. Generates a static analysis of the new controller file.
        5. Tests the controller file in simulation with each scenario.
            5.1 Esmini is initialized with the scenario and the new controller.
            5.2 The resulting logs are analysed according to the test cases in the evaluation suite.
            5.3 The screenshots are analysed, if the visual feedback mechanism is used.
        6. Iterate if a test case failed:
            6.1 The static + log + vison feedback is submitted to LLM to update controller
            6.2 goto 4.
        7. JSON file with test cases 
    """
 
    # Config information is loaded from an evaluation suite
    # Selected scenarios 
    scenarios = [scenario[0] for scenario in evaluation_suite['scenarios_tests']]

    # The associated lists of checks for each scenario 
    checks_list_list = [scenario[1] for scenario in evaluation_suite['scenarios_tests']]

    # Toggle for controller creation (debugging and development)
    create_new_controller = evaluation_suite['create_new_controller']

    # Toggle for use of vision (debugging and development)
    use_vision_api = evaluation_suite['use_vision_api']

    # Name of the type of task (AEB, ACC, CAEM, Other)
    task = evaluation_suite['task']

    # Description of the desired vehicle behaviour. 
    requirement_specification = evaluation_suite['requirement_specification']

    # Number of times the LLM is allowed to improve the code it generated
    max_iterations = evaluation_suite['number_of_iterations']

    # Template used for giving feedback during iterative improvement
    correction_template = evaluation_suite['correction_template']

    # Create a new directory for saving information about the run
    run_path = create_run_folder(task)

    # Create a new controller
    if create_new_controller:
        print("WARNING: API CALLS. Controller Creation")
        thread, text, correctNumberOfFiles = controller_creator.create_controller(requirement_specification, run_path, 0)
        # Abort the execution if the controller creator failed to produce a new controller file.
        if not correctNumberOfFiles:
            raise Exception(f"No controller was created for iteration {0}") 

    # Perform static code analysis to begin the log_string
    static_analysis = report_gen_static.static_analysis_string("custom_controller.py", 0, task, create_new_controller, use_vision_api)
    log_string = static_analysis

    # Run the scenario with the new controller. 
    # Reports are natural language reports from scenarios where the controller failed. 
    (log_success_fail, reports, report_json_list) = run_scenario_set(scenarios, checks_list_list, use_vision_api, task, 0, run_path)

    # Formats the reports into a string with new lines and append to current log string
    log_string += format_reports(0, reports)

    # Creates a JSON object for storing information about the run. 
    evaluation_data = create_evaluation_json(evaluation_suite, log_success_fail, report_json_list)

    # Iterative Improvement of the controller if failed a test case and the number of iterations are not exceeded 
    iteration = 0
    while ((log_success_fail['fail'] > 0 or log_success_fail['error'] > 0) and iteration < max_iterations):
        correction = correction_template.format(log_success_fail['fail'], 
           log_success_fail['fail'] + log_success_fail['success'], 
           static_analysis, 
           format_reports(iteration, reports), 
           iteration + 1)

        iteration += 1

        # Generate a new controller based on the feedback
        if create_new_controller:
            print("WARNING: API CALLS. Controller Creation")
            thread, text, correctNumberOfFiles = controller_creator.create_controller(correction, run_path, iteration, thread=thread)
            # Abort the execution if the controller creator failed to produce a new controller file.
            if not correctNumberOfFiles:
                raise Exception(f"No controller was created for iteration {iteration}") 

        static_analysis = report_gen_static.static_analysis_string("custom_controller.py", iteration, task, create_new_controller, use_vision_api)
        log_string += static_analysis

        (log_success_fail, reports, report_json_list) = run_scenario_set(scenarios, checks_list_list, use_vision_api, task, iteration, run_path)
        log_string += format_reports(iteration, reports)

        evaluation_data["iterations"].append(create_iteration_json(iteration, log_success_fail, report_json_list))
    
    final_statement = f"{iteration} iterations of corrections were performed. The final controller was {'unsuccessful' if reports else 'successful'}.\n"
    log_string += final_statement

    # Saves both the log and the JSON object to the newly created test directory
    report_gen_log.create_log(f"{task}", log_string, log_directory=run_path)
    save_evaluation_data(evaluation_data, run_path)

# Tests each provided scenario with the current controller and returns reports
def run_scenario_set(scenarios, checks_list_list, use_vision_api, task, iteration, run_path):

    reports = []
    report_json_list = []
    log_success_fail = {'success':0, 'fail':0, 'error':0}
    for scenario, checks in zip(scenarios, checks_list_list):

        scenario_file = "../resources/xosc/" + scenario

        captureInterval = 10

        (run_result, message) = run_simulation(scenario_file, captureInterval)

        copy_csv_log(run_path, iteration, scenario)

        if run_result == "error":
            reports.append(f"Attempt to use the controller file resulted in a crash. Error message {message}")
            log_success_fail['error'] += 1
            report_json_list.append({"scenario":scenario, "results":"error", "vision":"N/A"}) 

        else: 
            # Generate natural language report based on the logs 
            log_report_list, crash_frames = report_gen_log.generate_report(checks, "recordings\\full_log.csv")
            log_report = report_gen_log.format_report(log_report_list)
            reports.append(f"Log based report for scenario: {scenario}: \n{log_report}")

            success = all(report_dict['success'] for report_dict in log_report_list)
            log_success_fail['success'] += sum(report_dict['success'] for report_dict in log_report_list)
            log_success_fail['fail'] += sum(not report_dict['success'] for report_dict in log_report_list)

            visual_report = "Vision function was not used"
            # Generate natural language report based on the screenshots
            if use_vision_api and not success and crash_frames:
                crash_frame = crash_frames[len(crash_frames)//2]//captureInterval
                print("WARNING: API CALLS. Vision")
                visual_report = report_gen_vision.generate_visual_report(crash_frame, task, iteration, scenario, run_path)
                reports.append(f"Vision based report for scenario {scenario}: \n{visual_report}")

            report_json_list.append(
                {
                    "scenario":scenario, 
                    "results":log_report_list,
                    "vision":visual_report
                }
            )

        # Remove the TGA screenshots from the working directory. 
        report_gen_vision.remove_TGA()
    return (log_success_fail, reports, report_json_list)

# Initializes an instance of Esmini and test the controller with the provided scenario
def run_simulation(scenario, captureInterval):

    # Reference to esmini shared library via ctypes
    if sys.platform == "linux" or sys.platform == "linux2":
        se = ct.CDLL("../bin/libesminiLib.so")
    elif sys.platform == "darwin":
        se = ct.CDLL("../bin/libesminiLib.dylib")
    elif sys.platform == "win32":
        se = ct.CDLL("../bin/esminiLib.dll")
    else:
        print("Unsupported platform: {}".format(sys.platform))
        quit()

    # specify arguments and return types of useful functions
    se.SE_StepDT.argtypes = [ct.c_float]
    se.SE_GetSimulationTime.restype = ct.c_float
    se.SE_InjectedActionOngoing.restype = ct.c_bool

    # Prepare arguments for initializing Esmin
    se.SE_InitWithArgs.argtypes = [ct.c_int, ct.POINTER(ct.c_char_p)]    
    args = [
        '--window', '80', '80', '1200', '800', 
        # '--headless',
        '--osc', scenario, 
        '--csv_logger', 'recordings\\full_log.csv', 
        '--collision', 
        '--disable_stdout', 
        '--trail_mode', '3', 
        '--info_text', '2', 
        '--custom_camera', '-70,40,50,-0.5,0.6',
        '--text_scale', '2.0'
        ]
    argc = len(args)
    argv = (ct.c_char_p * argc)(*map(lambda arg: arg.encode('utf-8'), args))
    
    # initialize Esmini
    se.SE_InitWithArgs(ct.c_int(argc), argv)
    
    # initialize and update the state object
    state = state_layer.State(se)
    state.update()

    import custom_controller
    # Reload is necessary to obtain new version when controller file is updated
    importlib.reload(custom_controller)
    
    # A try-except block is used as the controller code is not guaranteed to be syntactically correct.  
    try: 
        # Load the custom_controller file and initailize a controller
        controller = custom_controller.CustomController(state)
        
        step = 0

        # Simulation loop
        while se.SE_GetQuitFlag() == 0 and se.SE_GetSimulationTime() < 30.0:
            
            # Updates the values stored in the state object each time step
            state.update()

            # Counter of steps for screenshots 
            step += 1

            # Saves an image every captureInterval frames
            if step % captureInterval == 0:
                se.SE_SaveImagesToFile(1)

            # Let the controller take action
            controller.step()

            # Steps the simulation by a constant value
            se.SE_StepDT(0.1) 

        # Assume that Esmini did not launch correctly if there were fewer than 25 steps.
        if step < 24:
            return ("error", RuntimeError("Esmini closed earlier than expected"))
        return ("success", "")
    except Exception as e:
            # Return error and the associated message if there's a runtime error when trying to run the controller file
            return ("error", e)
    
# Takes the list of reports and combined them into a string with new line characters  
def format_reports(iteration, reports):
    log_string = f"Iteration {iteration} reports:\n"
    for i, report in enumerate(reports, start=1):
        log_string += f"{report}\n\n"
    return log_string

# Creates a JSON object and populates the first iteraton
def create_evaluation_json(evaluation_suite, log_success_fail, report_json_list):
    evaluation_data = {
        "task": evaluation_suite['task'], 
        "requirement_specification": evaluation_suite['requirement_specification'],
        "create_new_controller": ['create_new_controller'],
        "use_vision_api": evaluation_suite['use_vision_api'],
        "number_of_iterations": evaluation_suite['number_of_iterations'],
        "iterations": [create_iteration_json(0, log_success_fail, report_json_list)
        ]
    }
    return evaluation_data 

# Creates an iteration entry for the JSON
def create_iteration_json(iteration, log_success_fail, report_json_list):
    iteration_data = {
        "iteration": iteration,
        "static": report_gen_static.static_analysis_json("custom_controller.py"),
        "run_success": log_success_fail['success'],
        "run_fail": log_success_fail['fail'],
        "run_error": log_success_fail['error'],
        "scenario_checks": report_json_list
    }
    return iteration_data  

# Creates a copy of the CSV log file and places is in the run folder
def copy_csv_log(run_path, iteration, scenario):
    destination_folder = os.path.join(run_path, str(iteration), scenario)
    destination_path = os.path.join(destination_folder, 'full_log.csv')
    os.makedirs(destination_folder, exist_ok=True)
    csv_path = 'recordings\\full_log.csv'
    try:
        shutil.copy(csv_path, destination_path)  # Copy the file to the destination path
    except Exception as e:
        print(f"An error occurred: {e}")

# Saves the JSON file
def save_evaluation_data(data, run_path):
    filename = "evaluation_data.json"
    full_path = os.path.join(run_path, filename)
    with open(full_path, "w") as file:
        json.dump(data, file, indent=2)

# Creates a folder for all the data from the run
def create_run_folder(custom_str):
    # Ensure the 'runs' subfolder exists
    runs_folder_path = os.path.join(os.getcwd(), 'runs')
    if not os.path.exists(runs_folder_path):
        os.makedirs(runs_folder_path)

    # Format the current date and time
    date_time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Combine date_time_str with custom_str to form the new folder's name
    folder_name = f"{date_time_str}_{custom_str}"
    new_folder_path = os.path.join(runs_folder_path, folder_name)
    
    # Create the new folder
    os.makedirs(new_folder_path)
    
    return new_folder_path

if __name__ == "__main__":
    main(test_evaluation_suite)
