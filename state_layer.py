import ctypes as ct



class State:
    def __init__(self, simulator):
        self.simulator = simulator

        # Create structs for the vehicles
        number_of_vehicles = self.simulator.SE_GetNumberOfObjects()
        self.vehicle_structs = {}
        for vehicle_number in range(number_of_vehicles):
            vehicle_id = simulator.SE_GetId(vehicle_number)
            vehicle_state_struct = SE_ScenarioObjectState()
            self.vehicle_structs[vehicle_id] = vehicle_state_struct
        self.vehicles = []

        # Create structs for the different actions
        scenarioActionManager = ScenarioActionManager()
        self.lane_offset_action = scenarioActionManager.create_lane_offset_action()
        self.lane_change_action = scenarioActionManager.create_lane_change_action()        
        self.speed_action = scenarioActionManager.create_speed_action()

    def update(self):
        # Remove previous vehicle objects, update the vehicle information structs and create new vehicles based on the new information.
        self.vehicles = []
        for vehicle_id, vehicle_state_struct in self.vehicle_structs.items():
            return_code = self.simulator.SE_GetObjectState(vehicle_id, ct.byref(vehicle_state_struct))
            if return_code != 0:
                print("Something went wrong when vehicle struct was refreshed.")

            vehicle = Vehicle(
                identity=vehicle_id,
                position=(vehicle_state_struct.x, vehicle_state_struct.y, vehicle_state_struct.z),
                speed=vehicle_state_struct.speed,
                lane_id=vehicle_state_struct.laneId,
                s=vehicle_state_struct.s,
                t=vehicle_state_struct.t,
                heading=vehicle_state_struct.h
            )
            self.vehicles.append(vehicle)

    def set_offset(self, offset):
        self.lane_offset_action.offset = offset
        self.simulator.SE_InjectLaneOffsetAction(ct.byref(self.lane_offset_action))

    def switch_lane(self, lane_id):
        if not self.simulator.SE_InjectedActionOngoing(5):
            self.lane_change_action.target = lane_id
            self.simulator.SE_InjectLaneChangeAction(ct.byref(self.lane_change_action))

    def set_speed(self, speed):
        self.speed_action.speed = float(speed)
        self.speed_action.transition_value = 10.0
        self.simulator.SE_InjectSpeedAction(ct.byref(self.speed_action))

    def brake(self):
        self.speed_action.speed = 0
        self.speed_action.transition_value = 50.0
        self.simulator.SE_InjectSpeedAction(ct.byref(self.speed_action))

class Vehicle:
    def __init__(self, identity, position, speed, lane_id, s, t, heading):
        self.id = identity # Int
        self.position = position  # Tuple of (x, y, z) Floats
        self.speed = speed # Float
        self.lane_id = lane_id # Integer
        self.s = s  # Longitudinal position along the lane - Float
        self.t = t  # Lateral position from the centre of the road - Float
        self.heading = heading # The direction of travel for the vehicle compared to an absolute North. Radians float. 

    def __repr__(self):
        return (f"Vehicle ID: {self.id}, Position: {self.position}, "
                f"Speed: {self.speed}, Lane ID: {self.lane_id}, "
                f"S: {self.s}, T: {self.t}")


"""Structs for communicating with Esmini via ctypes"""

class SESpeedActionStruct(ct.Structure):
    _fields_ = [
        ("id", ct.c_int),                # id of object to perform action
        ("speed", ct.c_float),
        ("transition_shape", ct.c_int),  # 0 = cubic, 1 = linear, 2 = sinusoidal, 3 = step
        ("transition_dim", ct.c_int),    # 0 = distance, 1 = rate, 2 = time
        ("transition_value", ct.c_float),
    ]

class SELaneChangeActionStruct(ct.Structure):
    _fields_ = [
        ("id", ct.c_int),                # id of object to perform action
        ("mode", ct.c_int),              # 0 = absolute, 1 = relative (own vehicle)
        ("target", ct.c_int),            # target lane id (absolute or relative)
        ("transition_shape", ct.c_int),  # 0 = cubic, 1 = linear, 2 = sinusoidal, 3 = step
        ("transition_dim", ct.c_int),    # 0 = distance, 1 = rate, 2 = time
        ("transition_value", ct.c_float),
    ]

class SELaneOffsetActionStruct(ct.Structure):
    _fields_ = [
        ("id", ct.c_int),                # id of object to perform action
        ("offset", ct.c_float),
        ("max_lateral_acc", ct.c_float),
        ("transition_shape", ct.c_int),  # 0 = cubic, 1 = linear, 2 = sinusoidal, 3 = step
    ]

class SE_ScenarioObjectState(ct.Structure):
    _fields_ = [
        ("id", ct.c_int),
        ("model_id", ct.c_int),
        ("ctrl_type", ct.c_int),
        ("timestamp", ct.c_float),
        ("x", ct.c_float),
        ("y", ct.c_float),
        ("z", ct.c_float),
        ("h", ct.c_float),  # heading/yaw
        ("p", ct.c_float),  # pitch
        ("r", ct.c_float),  # roll
        ("roadId", ct.c_int),
        ("junctionId", ct.c_int),
        ("t", ct.c_float),  # lateral position
        ("laneId", ct.c_int),
        ("laneOffset", ct.c_float),
        ("s", ct.c_float),  # longitudinal position
        ("speed", ct.c_float),
        ("centerOffsetX", ct.c_float),
        ("centerOffsetY", ct.c_float),
        ("centerOffsetZ", ct.c_float),
        ("width", ct.c_float),
        ("length", ct.c_float),
        ("height", ct.c_float),
        ("objectType", ct.c_int),
        ("objectCategory", ct.c_int),
        ("wheel_angle", ct.c_float),
        ("wheel_rot", ct.c_float),
        ("visibilityMask", ct.c_int),
    ]

"""Initializations of structs"""

class ScenarioActionManager:
    def create_lane_offset_action(self):
        action = SELaneOffsetActionStruct()
        action.id = 0
        action.offset = -0.45
        action.max_lateral_acc = 0.5
        action.transition_shape = 0
        return action

    def create_lane_change_action(self):
        action = SELaneChangeActionStruct()
        action.id = 0  # Id of the vehicle
        action.mode = 1  # Relative lane change
        action.target = 1  # Target lane to change to (can be relative)
        action.transition_shape = 2
        action.transition_dim = 2
        action.transition_value = 3.0
        return action

    def create_speed_action(self):
        action = SESpeedActionStruct()
        action.id = 0  # Id of the vehicle
        action.speed = 0.0  # New speed 
        action.transition_shape = 1  # Linear transition
        action.transition_dim = 1  # Rate change
        action.transition_value = 20.0
        return action