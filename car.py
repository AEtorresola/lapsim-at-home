import pandas as pd
from tires.magic_formula_tire import MagicFormulaTire
from motor import *
from helper_functions import combine_dataframes, append_new_rows

        
# Example usage
logger = setup_logger()

# # Now you can use logger throughout your script:
# logger.debug("Detailed debug information (file only)")
logger.info("Starting Car.py Script")
# logger.warning("Warning message (file and console)")
# logger.error("Error message (file and console)")
# logger.critical("Critical failure (file and console)")
#
# # Can also log exceptions with traceback
# try:
#     x = 1 / 0
# except Exception as e:
#     logger.exception("An error occurred")
#

class Car:
    def __init__(
        self,
        # Vehicle parameters
        mass: float,            # Total mass (kg)
        # Location Parameters
        dist_f: float,          # [m] x distance front axle to center of gravity
        dist_r: float,          # [m] x distance rear axle to center of gravity
        h_cog: float,           # [m] height of center of gravity
        track_width: float,     # [m] track width 
        # Parameters
    ):
        self.mass = mass
        self.vehicle_weight = self.mass*9.81
        # Location Parameters (spatial)
        self.h_cog = h_cog
        self.wheelbase = dist_f+dist_r
        self.track_width = track_width
        self.loc = position(track_width, dist_f, dist_r, h_cog)
        self.dist_f = dist_f
        self.dist_r = dist_r
        # Program Parameters 
        self.force_lag = 0.05
        self.timestep = 0.05
        self.current_time= 0
        self.initialize_forces()

        # self.all_forces = [self.front_right, self.front_left, self.rear_right, self.rear_left]
         
        # Transient Parameters (origin is cog)
        self.acceleration = (0,0,0) # x, y, z
        self.velocity = (0,0,0)     # x, y, z
        self.position = (0,0,0)     # x, y, z
        self.yaw_angle = 0          # Angle, radians?


        # Define big transient dataframe 
        car_parameters = {"time":[0],"acceleration":[0], "velocity":[0],"position":[0]}
        self.vehicle_details = pd.DataFrame()

    def initialize_forces(self):
         # Force Points 
        self.front_right = force_point(self,"front_right",self.loc.front_right, {"vertical_load":['z'], "x_friction":['x'], "y_friction":['y'], "rolling_resistance":['x']}, is_tire=True)
        self.front_left =  force_point(self,"front_left",self.loc.front_left, {"vertical_load":['z'], "x_friction":['x'], "y_friction":['y'], "rolling_resistance":['x']}, is_tire=True)
        self.rear_right =  force_point(self,"rear_right", self.loc.rear_right, {"vertical_load":['z'], "x_friction":['x'], "y_friction":['y'], "rolling_resistance":['x']}, is_tire=True)
        self.rear_left = force_point(self,"rear_left", self.loc.rear_left, {"vertical_load":['z'], "x_friction":['x'], "y_friction":['y'], "rolling_resistance":['x']}, is_tire=True)

        self.cnt_grav = force_point(self,"cnt_grav", self.loc.cog, {"vertical_load":['z'], "longitudinal_load":['x'], "lateral_load":['y'])

        # Initialize Forces
        
        self.current_time+=self.force_lag
        self.get_vertical_load()
        # Get combined dataframe 
        all_dataframes = [(self.front_right.forces, "front_right"),(self.front_left.forces, "front_left"),(self.rear_right.forces, "rear_right"),(self.rear_left.forces, "rear_left"), (self.cnt_grav.forces, "cnt_grav")]
        self.full_dataset = combine_dataframes(all_dataframes)
        
    def get_vertical_load(self, time=None):
        time = self.current_time if time is None else time
        # Lets get the basic parameters;
        # Time delta (adding a delta means that there is a lag between the force being applied at the wheel 
        # and it causing load transfer). 
        force_time = time- self.force_lag # Basically is the time that we will use for calculating forces. 
        # ie, which force are we using (if its 0.05, it means that we want to look at the time 0.05 seconds beforehand, and from there determine what the forces were)

        # Static Loads 
        
        front_tires = self.vehicle_weight*(self.dist_f/self.wheelbase)
        rear_tires = self.vehicle_weight*(self.dist_r/self.wheelbase)
        

        # Okay so, I want this function to get the vertical load on each of the four tires at a 
            # given point based on the current parameters.
        # This involves the acceleration, velocity, and position of each point. 

        # First Determine Longitudinal weight transfer
        rear_tire_force = self.rear_right.total_force('x', force_time) + self.rear_left.total_force('x', force_time)
        front_tire_force = self.front_right.total_force('x', force_time) + self.front_left.total_force('x', force_time)
        
        # This load transfer is the "delta" of how much the load moves. 
        load_transfer_accel = rear_tire_force*self.h_cog/self.wheelbase
        load_transfer_brake = front_tire_force*self.h_cog/self.wheelbase
        
        # Now determine lateral weight transfer
        left_tire_force = self.front_left.total_force('y', force_time) + self.rear_left.total_force('y', force_time)
        right_tire_force = self.front_right.total_force('y', force_time) + self.rear_right.total_force('y', force_time)
        
        # This load transfer is the "delta" of how much the load moves. 
        load_transfer_left = left_tire_force*self.h_cog/self.track_width    # This is the delta load to add to left tires (and subtract from right tires)
        load_transfer_right = right_tire_force*self.h_cog/self.track_width  # This is the delta load to add to right tires (and subtract from left tires)

        # Now getting the total per-tire
        front_right = front_tires/2 - load_transfer_accel + load_transfer_brake + right_tire_force - left_tire_force
        front_left = front_tires/2 - load_transfer_accel + load_transfer_brake - right_tire_force + left_tire_force
        rear_right = rear_tires/2 + load_transfer_accel - load_transfer_brake + right_tire_force - left_tire_force
        rear_left = rear_tires/2 + load_transfer_accel - load_transfer_brake - right_tire_force + left_tire_force
        
        # Now we have the vertical load on each of the wheels
        self.front_right.force_timestep({"vertical_load":front_right}, time)
        self.front_left.force_timestep({"vertical_load":front_left}, time)
        self.rear_right.force_timestep({"vertical_load":rear_right}, time)
        self.rear_left.force_timestep({"vertical_load":rear_left}, time)

    def calculate_timestep(self):
        """"
This portion has the purpose of calculating the next timestep based on the current information. 
This involves determining the current conditions, and using them to calculate the next conditions. 
So basically, we current have a given velocity, acceleration

        """
        print("---Starting time series calculation---")
        continue_iterating = True
        while continue_iterating:
            # First, lets calculate all the forces for this given iteration
            
            # Next, lets figure out what we want the car to do for the next timestep
            pass # This is based on the velocity profile calculated for the track based on tire and weight transfer parameters
            # Next lets figure out what forces we would need to apply to get the car to do the previous
            pass # Basically, given that we have a theoretical maximum velocity profile, we can use that as a basis for
                # determining what we should do for each timestep (not based on timestep btw, but on the distance along the track)
            # Next, we should apply the forces to the car. 
            pass # This involves calculating the resultant vector that we get based on all the forces on the car

    def get_resultant_force(self,time):

        # First, we should verify that *all* forces are defined for the timestep

        


        pass

class force_point:

    def __init__(self,
                 Car: Car,
                 point_name: str,
                 origin_location: tuple,
                 force_name_direction: dict,
                 is_tire = False
                 ):
        
        self.Car = Car
        forces_at_point = {"time":[0]}
        forces_at_point.update({name:[0] for name in force_name_direction.keys()})
        self.loc = origin_location
        self.force_directions = force_name_direction
        self.is_tire = is_tire
        # Create the Pandas DataFame
        self.forces = pd.DataFrame(forces_at_point,dtype=float) 
        self.forces.set_index("time", inplace=True)
        
        # Lets initialize the tire class, 
        if self.is_tire:
            self.make_tire()

    def total_force(self, direction, time):
        # First need to define a way to track the direction of each force. 
        # Then, just call f_t of a direcctoin
        forces_in_direction = [force_name for force_name in self.force_directions.keys() if self.force_directions[force_name][0]==direction]
        
        total_force = sum([self.forces.at[time,force] for force in forces_in_direction])
        print(f"Returning total forces in {direction} direction. Forces are : {forces_in_direction}. Sum was {total_force}")
        
        return total_force

    def force_timestep(self,input_forces, time):
        # Make sure that all forces are being updated
        
        # Makes sure that all the given forces exist
        if all([force in self.forces.columns for force in input_forces.keys()]):
            #
            
            new_row_series = pd.Series(input_forces)

            if time in self.forces.index:
                # Index already exists: Update the row, filling in provided columns
                for col, value in new_row_series.items():
                    self.forces.loc[time, col] = value  # Update specific columns
            else:
                # Index doesn't exist: Append a new row
                self.forces.loc[time] = new_row_series

        else:
            # Means that some updates for forces are missing
            missing_forces = [column for column in self.forces.columns if column not in input_forces]
            print(f"Tried updating forces at point: {point_name} but was missing forces : {missing_forces}")
 
    def f_t(self, force_name, time):  # Get force at time
        try:
            return self.forces.at[time, force_name]
        except KeyError as e:
            logger.error(f"Time index '{time}' not found for force '{force_name}'")
            return None
    def get_series_from_dataframe_row(
        time: int
    ) -> pd.Series:
        """
        Retrieves a Pandas Series representing a specific row from a DataFrame.

        Args:
            df: The Pandas DataFrame.
            time: The index (integer) of the row to retrieve.

        Returns:
            A Pandas Series representing the specified row.  Returns None if the
            time is out of bounds.
        """
        try:
            return df.iloc[time]
        except IndexError:
            print(f"Error: Row index {time} is out of bounds.")
            return None


    def get_series_from_dataframe_row(
        time: int
    ) -> pd.Series:
        """
        Retrieves a Pandas Series representing a specific row from a DataFrame.

        Args:
            df: The Pandas DataFrame.
            time: The index (integer) of the row to retrieve.

        Returns:
            A Pandas Series representing the specified row.  Returns None if the
            time is out of bounds.
        """
        try:
            return df.iloc[time]
        except IndexError:
            print(f"Error: Row index {time} is out of bounds.")
            return None

    def make_tire(self):
        if self.is_tire:

            # Create the Magic Formula tire model
            mf_tire = MagicFormulaTire("Racing Tire")

            #self.current_time
            # Create the tire object
            self.tire= Tire(mf_tire, position="front_left", radius=0.33, inertia=1.5)
            time=0
            # Simulate a braking event
            # F_input = -2000  # Braking force (N)
            self.force_input = 0                # Braking force (N) 
            self.tire_angle = 0                 # Tire angle (rad)
            self.tire_vertical_load = self.f_t("vertical_load", self.Car.current_time)        # Vertical load (N)
            self.tire_longitudinal_vel = 0      # Longitudinal velocity (m/s)

            self.dt = Car.timestep                  # Time step (s)

            # Update the tire state
            self.tire.update(self.force_input, self.tire_angle, self.tire_vertical_load, self.tire_longitudinal_vel, self.dt)

            # Get the resulting forces and moments
            forces = self.tire.get_forces()
            print("Forces and Moments:", forces)

            # Get the slip ratio and slip angle
            slip = tire.get_slip()
            print("Slip Ratio and Angle:", slip)
        else:
            pass


class position:

    def __init__(self,
                 track_width, # Currently works for same track width on both front and rear, can be changed.
                 dist_f,
                 dist_r,
                 h_cog  
                 ):
        # Coordinates in x, y, z. 
        # Coordinate system has origin at the center point between the rear wheel 
        # contact patch. ie, on the ground between the rear tires
        wheelbase = dist_f+dist_r
        self.front_right = (track_width/2, wheelbase, 0)
        self.front_left = (-track_width/2, wheelbase, 0)
        self.rear_right = (track_width/2, 0, 0)
        self.rear_left = (-track_width/2, 0, 0)
        self.cog = (dist_r, 0, h_cog)


