import pandas as pd
import numpy as np
from datetime import datetime
import os

def detect_collisions_dynamic():
    """Checks for collisions involving the Ego vehicle and returns pass/fail status along with a message."""
    def check(df):
        collision_frames = []
        collisions_mask = df["#1 collision_ids"].str.strip() != ""
        if collisions_mask.any():
            collision_messages = []
            latest_collision = -1  # Set this to a negative value initially to ensure the first collision is processed.
            for _, collision in df[collisions_mask].iterrows():
                collision_frames.append(collision['Index [-]'])
                time = collision["TimeStamp [s]"]
                vehicle_speed = collision["#1 Current_Speed [m/s]"]
                # Assuming there is only one colliding entity (No example found of how multiple would be represented in the csv yet)
                collision_id = int(collision["#1 collision_ids"].strip()) + 1
                colliding_name = collision[f"#{collision_id} Entity_Name [-]"].strip()
                if time > latest_collision + 1:  # Ensure at least one second has passed since the last recorded collision.
                    latest_collision = time  # Update the latest_collision time.
                    collision_messages.append(f"Ego was involved in a collision at time: {time} s with a speed of {vehicle_speed} m/s, colliding with: {colliding_name}.")

            # If collisions were detected, it's considered a fail.
            return (False, "\n".join(collision_messages), collision_frames)
        else:
            # No collisions detected, it's a pass.
            return (True, "No collisions were detected.", collision_frames)

    check.name = "detect_collisions_dynamic"
    return check
def max_ego_speed(limit):
    """Factory function to create a check function with a specified speed limit."""
    def check(df):
        """The actual check function that will be called by generate_report."""
        idx_max_speed = df["#1 Current_Speed [m/s]"].idxmax()
        max_speed = df.loc[idx_max_speed, "#1 Current_Speed [m/s]"]
        time = df.loc[idx_max_speed, "TimeStamp [s]"]
        
        # Check if the max speed exceeds the limit
        if max_speed > limit:
            return (False, f"Maximum speed of Ego: {max_speed:.2f} m/s at time: {time} s, which exceeds the limit of {limit} m/s.")
        else:
            return (True, f"Maximum speed of Ego: {max_speed:.2f} m/s at time: {time} s, within the limit of {limit} m/s.")
    check.name = "max_ego_speed"
    return check

def min_ego_speed(limit):
    """Factory function to create a check function with a specified minimum speed limit."""
    def check(df):
        """The actual check function that will be called by generate_report."""
        idx_min_speed = df["#1 Current_Speed [m/s]"].idxmin()
        min_speed = df.loc[idx_min_speed, "#1 Current_Speed [m/s]"]
        time = df.loc[idx_min_speed, "TimeStamp [s]"]
        
        # Check if the min speed is below the limit
        if min_speed < limit:
            return (False, f"Minimum speed of Ego: {min_speed:.2f} m/s at time: {time} s, which is below the minimum limit of {limit} m/s.")
        else:
            return (True, f"Minimum speed of Ego: {min_speed:.2f} m/s at time: {time} s, above the minimum limit of {limit} m/s.")
    check.name = "min_ego_speed"
    return check
    
def greatest_ego_speed_increase(min_increase):
    """Factory function to create a check function with a specified minimum speed increase limit."""
    def check(df):
        """The actual check function that will be called by generate_report."""
        speeds = df["#1 Current_Speed [m/s]"].to_numpy()
        times = df["TimeStamp [s]"].to_numpy()
        min_speed_index = np.argmin(speeds)
        
        if min_speed_index == len(speeds) - 1:
            return (False, "No increase in speed detected after reaching the minimum speed.")
        
        max_speed_after_min_index = min_speed_index + np.argmax(speeds[min_speed_index:])
        greatest_increase = speeds[max_speed_after_min_index] - speeds[min_speed_index]
        
        time_min_speed = times[min_speed_index]
        time_max_speed_after_min = times[max_speed_after_min_index]
        
        if greatest_increase < min_increase:
            return (False, f"Greatest speed increase of Ego after reaching its minimum speed is {greatest_increase:.2f} m/s, from time: {time_min_speed} s to {time_max_speed_after_min} s, which is less than the required increase of {min_increase} m/s.")
        else:
            return (True, f"Greatest speed increase of Ego after reaching its minimum speed: {greatest_increase:.2f} m/s, from time: {time_min_speed} s to {time_max_speed_after_min} s, meeting the required increase of {min_increase} m/s.")
    check.name = "greatest_ego_speed_increase"
    return check

def greatest_road_offset(max_allowed_offset):
    """Factory function to create a check function with a specified maximum allowed absolute offset from middle of the road."""
    def check(df):
        """The actual check function that will be called by generate_report."""
        # Use absolute values to find the greatest offset
        abs_offsets = df["#1 Lateral_Distance_Lanem [m]"].abs()
        idx_max_abs_offset = abs_offsets.idxmax()
        max_abs_offset = abs_offsets[idx_max_abs_offset]
        time_max_offset = df.loc[idx_max_abs_offset, "TimeStamp [s]"]
        
        if max_abs_offset > max_allowed_offset:
            return (False, f"Greatest absolute lane offset of Ego: {max_abs_offset:.2f} m at time: {time_max_offset} s, which exceeds the allowed maximum of {max_allowed_offset} m.")
        else:
            return (True, f"Greatest absolute lane offset of Ego: {max_abs_offset:.2f} m at time: {time_max_offset} s, within the allowed maximum of {max_allowed_offset} m.")
    check.name = "greatest_lane_offset"
    return check

def smallest_road_offset(min_allowed_offset):
    """Factory function to create a check function with a specified minimum allowed absolute lane offset from middle of the road."""
    def check(df):
        """The actual check function that will be called by generate_report."""
        # Use absolute values to find the offset closest to zero
        abs_offsets = df["#1 Lateral_Distance_Lanem [m]"].abs()
        idx_min_abs_offset = abs_offsets.idxmin()
        min_abs_offset = abs_offsets[idx_min_abs_offset]
        time_min_offset = df.loc[idx_min_abs_offset, "TimeStamp [s]"]
        
        if min_abs_offset < min_allowed_offset:
            return (False, f"Smallest absolute lane offset of Ego: {min_abs_offset:.2f} m at time: {time_min_offset} s, which is below the allowed minimum of {min_allowed_offset} m.")
        else:
            return (True, f"Smallest absolute lane offset of Ego: {min_abs_offset:.2f} m at time: {time_min_offset} s, above the allowed minimum of {min_allowed_offset} m.")
    check.name = "smallest_lane_offset"
    return check

import re
# This code gets the numbers of the vehicles in the dataframe
def get_vehicle_identifiers(df):
    """Extracts unique vehicle identifiers from dataframe column names using regex."""
    vehicle_cols = [col for col in df.columns if "#" in col]
    vehicle_ids = set()
    for col in vehicle_cols:
        match = re.search(r"#(\d+)", col)
        if match:
            vehicle_ids.add(int(match.group(1)))
    return sorted(list(vehicle_ids))

def calculate_distance(row, other_prefix, ego_prefix="#1",):
    """Calculate the least amount of distance in front of the Ego vehicle, considering only vehicles in the same lane."""
    # Check if both vehicles are in the same lane
    if row[f"{ego_prefix} lane_id"] == row[f"{other_prefix} lane_id"]:
        # Calculate the lateral distance from the Ego vehicle to the other vehicle
        ego_lateral_distance = row[f"{ego_prefix} Distance_Travelled_Along_Road_Segment [m]"]
        other_lateral_distance = row[f"{other_prefix} Distance_Travelled_Along_Road_Segment [m]"]
        # Calculate the distance if the other vehicle is ahead of the Ego vehicle
        if other_lateral_distance > ego_lateral_distance:
            return other_lateral_distance - ego_lateral_distance
    return float('inf')  # Return infinity if not in the same lane or not ahead


def closest_distance_to_any_vehicle(min_allowed_distance):
    """Factory function to create a check function with a specified minimum allowed distance to any vehicle."""
    def check(df):
        """The actual check function that will be called by generate_report."""
        vehicle_ids = get_vehicle_identifiers(df)
        closest_distance = float('inf')
        closest_time = None
        closest_vehicle_id = None

        for vid in vehicle_ids[1:]:  # Start from 2 to exclude Ego itself
            prefix = f"#{vid}"
            distances = df.apply(lambda row: calculate_distance(row, prefix), axis=1)
            min_distance_index = distances.idxmin()
            if distances[min_distance_index] < closest_distance:
                closest_distance = distances[min_distance_index]
                closest_time = df.loc[min_distance_index, "TimeStamp [s]"]
                closest_vehicle_id = vid

        if closest_distance == float('inf'):
            return (True, "No other vehicles present or no distances calculated.")

        if closest_distance < min_allowed_distance:
            return (False, f"Closest distance Ego comes to any vehicle is {closest_distance:.2f} m to vehicle #{closest_vehicle_id} at time: {closest_time} s, which is closer than the allowed minimum of {min_allowed_distance} m.")
        else:
            return (True, f"Closest distance Ego comes to any vehicle is {closest_distance:.2f} m to vehicle #{closest_vehicle_id} at time: {closest_time} s, respecting the minimum allowed distance of {min_allowed_distance} m.")
        
    check.name = "closest_distance_to_any_vehicle"
    return check

# Function which accepts a set of tests which it will run on the linked csv log. Returns a list of dictionaries with the reults from the tests
def generate_report(checks, file_path):
    """Executes a list of checks on the dataset and compiles the results into a list of of dictionaries (fucntion name, pass/fail, message)."""
    df = pd.read_csv(file_path, skiprows=6)
    df.columns = df.columns.str.strip()
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    crash_frames = []
    report_results = []
    for check_func in checks:
        result = check_func(df)

        if check_func.name == "detect_collisions_dynamic":
            crash_frames = result[2]

        result_dict = {"check_function": check_func.name, "success": result[0], "message": result[1]}
        report_results.append(result_dict)
    
    return report_results, crash_frames

# Function which formats the list of tests generated by generate_report into something more readable. 
def format_report(report_results):
    """Formats the list of tuples (pass/fail, message) into a pretty string."""
    formatted_results = []
    for report_dict in report_results:
        pass_fail_text = "Pass" if report_dict["success"] else "Fail"
        formatted_results.append(f"{pass_fail_text}: {report_dict['message']}")
    
    return "\n".join(formatted_results)


def create_log(file_name_descriptor, log_message, log_directory):
    # Get the current datetime
    now = datetime.now()
    
    # Format the datetime and custom string to create a filename
    file_name = now.strftime(f"%Y-%m-%d_%H-%M-%S_{file_name_descriptor}.txt")
    
    # Ensure the logs directory exists
    os.makedirs(log_directory, exist_ok=True)

    # Create the full path for the log file
    log_file_path = os.path.join(log_directory, file_name)
    
    # Write the log message to the file
    with open(log_file_path, 'w') as file:
        file.write(log_message)
