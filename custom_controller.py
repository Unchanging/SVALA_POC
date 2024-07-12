class CustomController:
    def __init__(self, state):
        self.state = state


    def step(self):

        ego = self.state.vehicles[0]
        other = self.state.vehicles[1]

        if (ego.lane_id == other.lane_id) and (ego.s > other.s - 50):
            self.state.set_speed(0)
            print("breaking")
        else:
            self.state.set_speed(50)
            print("accelerating")

# Structure of the State and Vehicle classes:
"""
class State:
    def __init__(self, simulator):
        ...
        # a list of all the cars in the simulation.
        # car [0] is the "ego" car and it is the one this controller operates. 
        self.vehicles = [] 

    # Changes the lane which the ego car uses.
    # 1 makes the car switch one lane to the left and -1 changes one lane to the right
    def switch_lane(self, lane_id):
        ...
    
    # Sets the absolute target speed of the car. Meters per second as a float between -70 and 70.
    def set_speed(self, speed):
        ...

    # Stops the car as fast as possible.
    def brake(self):
        ...

    # Sets how far from the middle of a lane that the car drives. 
    # 0.0 is in the middle of the lane, 0.6 brings the car's left side of the car to the left edge of the lane and -0.6 mirrors this on the right side.
    # 2.8 is enough to completely leave the lane. 
    def set_offset(self, offset):
        ...

class Vehicle:
    def __init__(self, identity, position, speed, lane_id, s, t):
        self.id = identity # Int
        self.position = position  # Tuple of (x, y, z) Floats
        self.speed = speed # Float
        self.lane_id = lane_id # Integer
        self.s = s  # Longitudinal position along the lane - Float
        self.t = t  # Lateral position from the centre of the road - Float
        self.heading = heading # The direction of travel for the vehicle compared to an absolute North. Radians float. 
"""