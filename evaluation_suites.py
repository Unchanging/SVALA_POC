from report_gen_log import *

"""Instruction objects for SVALA. """

# test_evaluation_suite = {
#     'task':,                      - String:   Name of the ADAS function
#     'requirement_specification':, - String:   Description of the ADAS function
#     'correction_template' : ,     - String:   Template for feedback for iterative loop 
#     'create_new_controller': ,    - Bool:     Whether to generate a controllers (debug)
#     'use_vision_api': ,           - Bool:     Whether to generate commentary based on screenshots
#     'number_of_iterations': ,     - Int       Max number of corrections during iterative improvements
#     'scenarios_tests': [          - List      Scenarios and associated test cases used for evluation 
#         ('cut-in_high.xosc', [    - String    File name of scenario
#             test1,                - Function  Test case function
#             test2]
#             ),
#     ]
# }

test_evaluation_suite = {
    'task': 'CAEM',
    'requirement_specification': """Make a custom_controller.py file that implments the ADAS function Collision Avoidance by Evasive Maneuver for the Ego car. Prioritize evasive maneuvers to the left if possible rather than to the right. Do not drive off the road at any cost. lane_id -2, -3 and -4 are on the road.

CAEM attempts to avoid collisons by lateral movments. It identifies hazards in its path and changes lanes to avoid them.

General safety requirements:
- Assume that all vehicles only occupy one lane at the time, and that threaths to the ego primarily occurres in the same lane as ego. 
- A good meassure for how critical a situation is, is the time to collision (TTC) defined as: the distance divided the relative velocitiy. This is a better meassure than distance alone.   
- Remeber that the max deceleration of the vehicle is limited to 10m/^2 in the simulation. 
- Check if the lane you are changing to is safe before transition. 
- Remeber that lane transitions are not instantanious and require some time before completed.  
- Depending on the traffic scenario cars might come from behind or from ahead in the lane transitioned to. 

Suggestions and considerations for implementation:
- The controller should find the lane id for the Ego car. 
- The controller should determine if there are other vehicles further ahead (higher s value) in that lane. 
- The controller should calculate the time to collision, (TTC), by dividing the distance between Ego and the closest vehicle ahead of it with their relative velocity. Keep in mind that the difference in s value does not take the length of the vehicles into account, which can be up to four meters. Also note that the speed value is a scalar and does not take direction of travel into account. The controller should consider the heading of the vehicles to accurately calculate TTC using trigonometry. 
- If the TTC value indicates that a collision is likely to happen then the controller should try to avoid this by changing lanes. 
- The controller must ensure that the lane it moves Ego into is safe and on the road. 
- Ensure that the lane is safe by the same TTC calculations used to evaluate the initial lane.
- The valid lanes are -2, -3 and -4. The controller must not make Ego leave these three lanes.

Planning and explicit assumptions:
The generated code should begin with a set of comments that shows the planning you performed before writing the code. It should outline the intended functionality of the new or updated controller and explicitly state assumptions you made. """,
    'correction_template' : """
Unfortunately, the controller failed {} out of {} tests. 
\nStatic code analysis resulted in this report: 
\n{}.
\nTests run on log data generated from simulations of the different scenarios: 
\n{}.
\nPlease include the tag "version {}" as a comment in the new file
\nYou are now going to try to correct the code based on these reports. 
\nFirst try to understand what has happened during the tests which were perfomed. Try to explicitly describe the issues that the controller might have had.
\nEnumerate explicit changes you will make to the controller and how they will address previous shortcommings. 
\nFinally generate a new controller file. 
""",    
    'create_new_controller': False,
    'use_vision_api': False,
    'number_of_iterations': 0,
    'scenarios_tests': [
        ('cut-in_high.xosc', [
            detect_collisions_dynamic(),
            closest_distance_to_any_vehicle(7), 
            greatest_road_offset(9.7),
            smallest_road_offset(3.425)]
            ),
        # ('cut-in_middle.xosc', [
        #     detect_collisions_dynamic(),
        #     closest_distance_to_any_vehicle(7), 
        #     greatest_road_offset(97),
        #     smallest_road_offset(3.425)]
        #     ),
        # ('cut-in_low.xosc', [
        #     detect_collisions_dynamic(),
        #     closest_distance_to_any_vehicle(7), 
        #     greatest_road_offset(9.7),
        #     smallest_road_offset(3.425)]
        #     ),
        # ('cut-in_double_EM.xosc', [
        #     detect_collisions_dynamic(),
        #     closest_distance_to_any_vehicle(7), 
        #     greatest_road_offset(9.7),
        #     smallest_road_offset(3.425)]
        #     ),
        # ('cut-in_block_EM.xosc', [
        #     detect_collisions_dynamic(),
        #     closest_distance_to_any_vehicle(7), 
        #     greatest_road_offset(12.7),
        #     smallest_road_offset(6.425)]
        #     ),
        # ('cut-in_empty_commission.xosc', [
        #     min_ego_speed(28), 
        #     greatest_road_offset(9.7),
        #     smallest_road_offset(6.425)]
        #     ),
        # ('cut-in_meeting_commission.xosc', [
        #     detect_collisions_dynamic(),
        #     min_ego_speed(28), 
        #     greatest_road_offset(6.7),
        #     smallest_road_offset(3.425)]
        #     ),
    ]
}