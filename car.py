import pandas as pd
import math
import numpy as np
from tires.new_magic_formula_tire import PacejkaTireRefactored
from tires.tire_class import PhysicalTire
from motor import *
from helper_functions import TimeSeriesStorage, combine_dataframes, append_new_rows

from logger import setup_logger
        
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
            # Tire Model Parameters
            tire_parameter_filepath: str, # Path to the .par file
            # Setup Parameters
            static_cambers: dict,       # {'fl': rad, 'fr': rad, 'rl': rad, 'rr': rad}
            # Simulation Settings
            return_tire_errors: bool = False # Added setting for tire error handling
        ):
            self.mass = mass
            self.vehicle_weight = self.mass*9.81
            self.drivetrain = "RWD" # Default, can be changed
            # Location Parameters
            self.h_cog = h_cog
            self.wheelbase = dist_f+dist_r
            self.track_width = track_width
            self.loc = position(track_width, dist_f, dist_r, h_cog)
            self.dist_f = dist_f
            self.dist_r = dist_r
            # Physical Parameters
            self.z_inertia = 1/12*self.mass*(self.wheelbase**2+self.track_width**2)
            # Program Parameters
            self.force_lag = 5          # Milliseconds
            self.timestep = 5           # Milliseconds
            self.current_time= 0
            # --- ADDED: Store tire param file path and error setting ---
            self.tire_parameter_filepath = tire_parameter_filepath
            self.return_errors_setting = return_tire_errors # Used by force_point init

            # Store static cambers
            self._static_cambers = static_cambers
            if not all(k in self._static_cambers for k in ['front_left', 'front_right', 'rear_left', 'rear_right']):
                raise ValueError("static_cambers dictionary must contain keys 'front_left', 'front_right', 'rear_left', 'rear_right'")

            # --- REMOVED: Direct tire model initialization here ---
            # self.tire_models = { ... }

            # Transient Parameters
            self.acceleration = (0.0, 0.0, 0.0)
            self.velocity = (0.0, 0.0, 0.0)
            self.position = (0.0, 0.0, 0.0)
            self.yaw_angle = 0.0
            self.yaw_velocity = 0.0

            # Initialize Data Storage & Force Points
            # Vehicle details storage needs to be initialized first
            self.vehicle_details = TimeSeriesStorage({"time": [0], "acceleration": [(0.0,0.0,0.0)], "velocity": [(0.0,0.0,0.0)], "position": [(0.0,0.0,0.0)]}, 'vehicle_dataframe', col_types={"acceleration": 'object', "velocity": 'object', "position": 'object'})
            # Now initialize force points, which will create their own tire models
            self.initialize_forces() # This now passes the file path

            # List of force points (ensure this is done AFTER initialize_forces)
            self.all_force_points = [self.front_right, self.front_left, self.rear_right, self.rear_left, self.cnt_grav]
            # List for combining dataframes
            self.all_dataframes_for_update = [(self.vehicle_details, "car"), (self.front_right.forces, "front_right"),(self.front_left.forces, "front_left"),(self.rear_right.forces, "rear_right"),(self.rear_left.forces, "rear_left"), (self.cnt_grav.forces, "cnt_grav")]
            # Initialize combined dataset
            self.full_dataset = combine_dataframes(self.all_dataframes_for_update)

            # Update initial state (t=0)
            self.vehicle_details.update({"velocity": self.velocity, "position": self.position, "acceleration": self.acceleration}, 0)
            self.update_master_dataframe(0)
            logger.info("Car model initialized.")

    def initialize_forces(self):
         # --- CHANGED: Pass tire parameter file path ---
         # Force Points - Now instantiate their own tires using the path
        self.front_right = force_point(self,"front_right",self.loc.front_right, {"vertical_load":['z'], "x_friction":['x'], "y_friction":['y'], "rolling_resistance":['x']}, is_tire=True, tire_param_file=self.tire_parameter_filepath)
        self.front_left =  force_point(self,"front_left",self.loc.front_left, {"vertical_load":['z'], "x_friction":['x'], "y_friction":['y'], "rolling_resistance":['x']}, is_tire=True, tire_param_file=self.tire_parameter_filepath)
        self.rear_right =  force_point(self,"rear_right", self.loc.rear_right, {"vertical_load":['z'], "x_friction":['x'], "y_friction":['y'], "rolling_resistance":['x']}, is_tire=True, tire_param_file=self.tire_parameter_filepath)
        self.rear_left = force_point(self,"rear_left", self.loc.rear_left, {"vertical_load":['z'], "x_friction":['x'], "y_friction":['y'], "rolling_resistance":['x']}, is_tire=True, tire_param_file=self.tire_parameter_filepath)

        self.cnt_grav = force_point(self,"cnt_grav", self.loc.cog, {"inertial_z":['z'], "inertial_x":['x'], "inertial_y":['y']})

        # Initialize Forces at t=0
        self.get_vertical_load(time=0) # Calculate loads for t=0

        initial_forces = {"x_friction":0.0, "y_friction":0.0, "rolling_resistance":0.0}
        self.front_right.forces.update(initial_forces, 0)
        self.front_left.forces.update(initial_forces, 0)
        self.rear_right.forces.update(initial_forces, 0)
        self.rear_left.forces.update(initial_forces, 0)

        cnt_grav_initial = {"inertial_z":0.0, "inertial_x":0.0, "inertial_y":0.0}
        self.cnt_grav.forces.update(cnt_grav_initial, 0)

        # Calculate initial resultants and update motion (should be zero)
        resultants = self.get_resultant_force_and_torque(0)
        self.update_linear_motion(resultants['forces'])
        self.update_rotational_motion(resultants['torques'])
        logger.debug(f"Initial state (t=0): Position = {self.position} -- Velocity = {self.velocity} --")

    def get_vertical_load(self, time=None):

        time = int(self.current_time) if time is None else time
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
        try:
            rear_tire_force = self.rear_right.total_force('x', force_time) + self.rear_left.total_force('x', force_time)
            front_tire_force = self.front_right.total_force('x', force_time) + self.front_left.total_force('x', force_time)
        except Exception as e:
            print(e)
            __import__('pdb').set_trace()
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
        self.front_right.forces.update({"vertical_load":front_right}, time)
        self.front_left.forces.update({"vertical_load":front_left}, time)
        self.rear_right.forces.update({"vertical_load":rear_right}, time)
        self.rear_left.forces.update({"vertical_load":rear_left}, time)

    def calculate_timestep(self,time):

        """"
This portion has the purpose of calculating the next timestep based on the current information. 
This involves determining the current conditions, and using them to calculate the next conditions. 
So basically, we current have a given velocity, acceleration, yaw_angle, etc. For now, we will focus
on the basics of velocity and acceleration and forces since we are focusing on straightline acceleration.
However, for the future this will be expanded to include the more complicated ones

        """

        logger.info(f"Calculating resultants at time : {time}")
        
        for force_points in self.all_force_points:
            try: 
                if force_points.forces_incomplete(time):
                    raise ValueError(f"Incomplete forces for force point {force_points.name}")
                    return
            except: 
                import pdb; pdb.set_trace()
        resultants = self.get_resultant_force_and_torque(time)
        
        self.update_linear_motion(resultants['forces'])
        self.update_rotational_motion(resultants['torques'])
        logger.debug(f"After forces are applied; Position = {self.position} -- Velocity = {self.velocity} --")
        
        self.update_master_dataframe(self.current_time)

    # Linear motion updates
    def update_linear_motion(self, forces):
        # Calculate new acceleration
        a_x = forces[0] / self.mass
        a_y = forces[1] / self.mass
        a_z = forces[2] / self.mass
        self.acceleration = (a_x, a_y, a_z)
        dt = self.timestep / 100
        # Update velocity: v_new = v_old + a_new * dt
        v_x = self.velocity[0] + a_x * dt
        v_y = self.velocity[1] + a_y * dt
        v_z = self.velocity[2] + a_z * dt
        v_z = 0
        self.velocity = (v_x, v_y, v_z)
        
        # Update position: p_new = p_old + v_new * dt + 0.5 * a_new * dt²
        p_x = self.position[0] + v_x * dt + 0.5 * a_x * dt**2
        p_y = self.position[1] + v_y * dt + 0.5 * a_y * dt**2
        # p_z = self.position[2] + v_z * dt + 0.5 * a_z * dt**2
        p_z = 0
        self.position = (p_x, p_y, p_z)
        # Keep in mind that velocity and position are updated for the next timestep, whereas acceleration is for the current timestep
            # Updating current timestep acceleration
        self.vehicle_details.update({"acceleration":self.acceleration}, self.current_time)
            # Updating next timesteps' velocity and position
        self.vehicle_details.update({"velocity": self.velocity, "position": self.position}, self.current_time+self.timestep)

    def update_rotational_motion(self, torques):
        # Calculate angular acceleration: α = τ/I
        torque_z = torques[2]
        angular_acceleration = torque_z / self.z_inertia
        
        dt = self.timestep/100
        # Update angular velocity: ω_new = ω_old + α * dt
        self.yaw_velocity = self.yaw_velocity + angular_acceleration * dt
        
        # Update yaw angle: θ_new = θ_old + ω_new * dt + 0.5 * α * dt²
        self.yaw_angle = self.yaw_angle + self.yaw_velocity * dt + 0.5 * angular_acceleration * dt**2
        
        # Optional: normalize angle to keep it between 0 and 360 degrees
        self.yaw_angle = self.yaw_angle % 360

    def get_resultant_force_and_torque(self, time, reference_point=None):

        """
        Calculate the resultant force and torque acting on the car at a given time.

        Args:
            time (float): The time at which to calculate the resultant force and torque.
            reference_point (tuple, optional): The reference point (x, y, z) for calculating torque.
                                              Defaults to the center of gravity (cog).

        Returns:
            tuple: A tuple containing:
                - The resultant force in the x, y, and z directions.
                - The resultant torque about the reference point in the x, y, and z directions.
        """
        # Default reference point is the center of gravity
        if reference_point is None:
            reference_point = self.loc.cog

        # Initialize the resultant force and torque components
        resultant_force = [0, 0, 0]  # x, y, z
        resultant_torque = [0, 0, 0]  # x, y, z

        # List of all force points
        force_points = [
            self.front_right,
            self.front_left,
            self.rear_right,
            self.rear_left,
            self.cnt_grav
        ]

        # Sum up the forces and torques
        for point in force_points:
            # Get the force components
            force_x = point.total_force('x', time)
            force_y = point.total_force('y', time)
            force_z = point.total_force('z', time)

            # Add to the resultant force
            resultant_force[0] += force_x
            resultant_force[1] += force_y
            resultant_force[2] += force_z

            # Calculate the position vector from the reference point to the force point
            r_x = point.loc[0] - reference_point[0]
            r_y = point.loc[1] - reference_point[1]
            r_z = point.loc[2] - reference_point[2]

            # Calculate the torque contribution using the cross product: τ = r × F
            torque_x = r_y * force_z - r_z * force_y
            torque_y = r_z * force_x - r_x * force_z
            torque_z = r_x * force_y - r_y * force_x

            # Add to the resultant torque
            resultant_torque[0] += torque_x
            resultant_torque[1] += torque_y
            resultant_torque[2] += torque_z
        
        logger.info(f"Timestep {time} had resultant forces of {resultant_force} And resultant torques of {resultant_torque}")
        return {'forces':tuple(resultant_force), 'torques':tuple(resultant_torque)}

    def accelerate_tires(self, 
                         acceleration_proportion=None, 
                         longitudinal_mode=None
                         ):

        if self.drivetrain == "RWD":
            
            if acceleration_proportion:

                # Going first to just assume maximum acceleration

                # Lets go step by step for calculating a timestep. 

                # First, the vertical load on the driven tires.
                rr_vertical_load = self.rear_right.forces.get_value('vertical_load', self.current_time)
                rl_vertical_load = self.rear_left.forces.get_value('vertical_load', self.current_time)
                
                # What if vertical load doesnt exist? WJKJ
                try:
                    a = rr_vertical_load/2
                    b = rl_vertical_load/2
                except:
                    import pdb; pdb.set_trace()
                # Using this vertical load, we calculate the amount of longitudinal force the tire can provide. 
                rear_right_force = self.rear_right.tire.allocate_forces(0,rr_vertical_load, self.velocity[0], longitudinal_mode, self.current_time)
                rear_left_force = self.rear_left.tire.allocate_forces(0,rl_vertical_load, self.velocity[0], longitudinal_mode, self.current_time)
                # Through this method, the force points themselves should be properly updated.
                rear_right = {'x_friction':rear_right_force['Fx'], 'y_friction':rear_right_force['Fy'], "rolling_resistance":-100} 
                rear_left= {'x_friction':rear_left_force['Fx'], 'y_friction':rear_left_force['Fy'], "rolling_resistance":-100} 
                # import pdb; pdb.set_trace()
                # I will fill the rest of the forces with 0 (to make sure it is at least included)
                # THIS IS NOT HOW ROLLING RESISTANCE IS ACTUALLY CALCULATED!

                null_forces = {"x_friction":0, "y_friction":0, "rolling_resistance":-100}
                self.front_right.forces.update(null_forces, self.current_time)
                self.front_left.forces.update(null_forces, self.current_time)

                
                self.rear_right.forces.update(rear_right, self.current_time)
                self.rear_left.forces.update(rear_left, self.current_time)


                self.cnt_grav.forces.update({'inertial_z':0, 'inertial_x':0,  'inertial_y':0}, self.current_time)
                # Now lets real quick just update all the force info in the Car object itself. 
                # Now, I have to get the resultant force of this. For now, will exclude rolling resistance
                    # The resultant force of the rear tires (acting on the CoG) will be applied.
                # I will add this vertical force to the tire force point itself now
    
                # 

                # OKay im so close. just need to implement the right functions to the force point class and then figure out how to 
                # ensure that the forces are actually passed on to the force object

    def update_master_dataframe(self,time):
        # This joins all the sub dataframes into the larger overall one.
        update_list = []

        # print("\n".join([i[0].data.to_string() for i in self.all_dataframes_for_update]))
        try: 
            for force_point, force_name in self.all_dataframes_for_update:
                myvals = (force_point.get_time_series(time), force_name)
                update_list.append(myvals)
            self.full_dataset = append_new_rows(self.full_dataset, update_list, time)

        except Exception as e:
            print(e)
            __import__('pdb').set_trace()
            print("Failed to update master dataframe")
        
        logger.info(f"Master Dataframe has been updated for timestep {self.current_time}")

    def export_dataset(self, export_name=None):
        import time
        date_str = time.asctime()
        export_name= f'dataset-export-{date_str}.csv' if export_name is None else f"{export_name}-{date_str}.csv"
        
        export_path = f"data_export/{export_name}"

        with open(export_path, 'w') as file:
            self.full_dataset.to_csv(file)
        
    def apply_control_inputs(self, target_lateral_accel, longitudinal_mode, longitudinal_intensity, time):
        """
        Translates high-level control targets into tire forces for the current timestep.

        Args:
            target_lateral_accel (float): Desired lateral acceleration (m/s^2). Positive is right turn force.
            longitudinal_mode (str): 'accelerate', 'brake', or 'coast'.
            longitudinal_intensity (float): 0.0 to 1.0 fraction of longitudinal capacity.
            time (int): The current simulation time (ms).
        """
        time = int(time) # Ensure integer time
        logger.info(f"Applying controls at t={time}: TargetLatAcc={target_lateral_accel:.2f} m/s^2, Mode='{longitudinal_mode}', Intensity={longitudinal_intensity:.2f}")

        # 1. Calculate Total Target Fy
        # Positive Fy = force pushing car CoG to the right (for a left turn usually)
        target_total_fy = self.mass * target_lateral_accel

        # 2. Distribute Target Fy (Simplified: Assume front axle handles it via steering)
        target_fy_front_axle = target_total_fy
        target_fy_rear_axle = 0.0 # Assume rear follows straight initially
        target_fy_fl = target_fy_front_axle / 2.0
        target_fy_fr = target_fy_front_axle / 2.0
        target_fy_rl = target_fy_rear_axle / 2.0
        target_fy_rr = target_fy_rear_axle / 2.0
        target_fy_map = {'front_left': target_fy_fl, 'front_right': target_fy_fr, 'rear_left': target_fy_rl, 'rear_right': target_fy_rr}

        # 3. Loop through wheels, find slips, calculate actual forces
        rolling_resistance_force = -50 # N, Simple constant placeholder per tire

        # Iterate using the defined list of force points
        for tire_point in self.all_force_points:
             if not tire_point.is_tire: continue # Skip non-tire points like CoG

             key = tire_point.name # Get the key ('fl', 'fr', etc.)

             # Get current dynamic load and static camber for this tire
             fz = tire_point.forces.get_value('vertical_load', time)
             if fz is None or fz <= 0:
                 logger.warning(f"Skipping tire {key} at t={time} due to zero or missing vertical load ({fz}). Updating forces to zero.")
                 tire_point.forces.update({'x_friction': 0.0, 'y_friction': 0.0, 'rolling_resistance': 0.0}, time)
                 continue

             gamma = self._static_cambers[key] # Get static camber
             target_fy_wheel = target_fy_map[key]

             # Determine longitudinal mode for this wheel
             wheel_longitudinal_mode = 'coast' # Default
             is_driven = ( (self.drivetrain == "FWD" and key in ['front_left', 'front_right']) or \
                           (self.drivetrain == "RWD" and key in ['rear_left', 'rear_rightr']) or \
                            self.drivetrain == "AWD" )
             is_braking = (longitudinal_mode.lower() == 'brake')

             if is_braking:
                 wheel_longitudinal_mode = 'brake'
             elif is_driven and longitudinal_mode.lower() == 'accelerate':
                 wheel_longitudinal_mode = 'accelerate'

             # Find target slips using the new tire method
             # Access the tire model via the force_point instance
             target_slips = tire_point.tire.find_slips_for_combined_target(
                 target_fy_wheel, fz, gamma, wheel_longitudinal_mode, longitudinal_intensity
             )

             alpha_cmd = target_slips['alpha']
             kappa_cmd = target_slips['kappa']

             # Handle cases where slips couldn't be found
             if np.isnan(alpha_cmd) or np.isnan(kappa_cmd):
                 logger.warning(f"Could not find valid slips for tire {key} at t={time}. Applying zero friction.")
                 actual_fx = 0.0
                 actual_fy = 0.0
             else:
                 # Calculate ACTUAL forces generated by the tire with these commanded slips
                 # Store result in tire history
                 actual_forces = tire_point.tire.calculate_forces(
                     fz, alpha_cmd, kappa_cmd, gamma, time, store_history=True
                 )
                 actual_fx = actual_forces['Fx']
                 actual_fy = actual_forces['Fy']
                 logger.debug(f"  Tire {key} @ t={time}: Cmd Slips(a={math.degrees(alpha_cmd):.2f}deg, k={kappa_cmd:.3f}) -> Forces(Fx={actual_fx:.1f}, Fy={actual_fy:.1f})")

             # Update the force_point's TimeSeriesStorage for the CURRENT time
             # Add rolling resistance here
             # Simple RR model: Apply only if moving forward significantly
             current_rr = rolling_resistance_force if self.velocity[0] > 0.1 else 0.0
             applied_fx = actual_fx + current_rr
             applied_fy = actual_fy

             tire_point.forces.update({
                 'x_friction': applied_fx, # Store net longitudinal force including RR
                 'y_friction': applied_fy,
                 'rolling_resistance': current_rr # Store RR separately for analysis if needed
             }, time)

        # Update CoG inertial forces (placeholder)
        # Ensure the row exists for this timestep, even if forces are zero
        self.cnt_grav.forces.update({'inertial_z':0.0, 'inertial_x':0.0, 'inertial_y':0.0}, time)



class force_point:

    def __init__(self,
                 Car_obj: Car, # Changed type hint for clarity
                 name: str,
                 origin_location: tuple,
                 force_name_direction: dict,
                 is_tire = False,
                 # tire_model: PacejkaTireRefactored = None # <<< REMOVED: No longer passed in
                 tire_param_file: str = None # <<< ADDED: File path for tire params
                 ):

        self.Car = Car_obj # Use different name to avoid confusion with Car class
        forces_at_point = {"time":[0]}
        # Use float for initial force values
        forces_at_point.update({name:[0.0] for name in force_name_direction.keys()})
        self.name = name
        self.loc = origin_location
        self.force_directions = force_name_direction
        self.is_tire = is_tire
        # Define column types for TimeSeriesStorage
        col_types = {k:float for k in force_name_direction.keys()}
        # Create the Pandas DataFame
        self.forces = TimeSeriesStorage(forces_at_point, name, col_types=col_types)

        # --- CHANGED: Instantiate tire model here ---
        self.tire = None
        if self.is_tire:
            if tire_param_file is None:
                raise ValueError(f"Tire parameter file path must be provided for tire force point '{name}'")
            try:
                # Instantiate the Pacejka tire model, passing the file path
                # Use the force_point name for the tire history name
                self.tire = PacejkaTireRefactored(tire_param_file,
                                                  return_errors=self.Car.return_errors_setting, # Get setting from Car
                                                  history_name=f"{self.name}_TireData")
                logger.info(f"Pacejka tire model initialized for force point '{name}'")
            except Exception as e:
                logger.error(f"Failed to initialize Pacejka tire model for '{name}': {e}")
                raise # Re-raise the exception to halt simulation if tire fails

    def total_force(self, direction, time):
        # --- Ensure this method handles None/NaN correctly as modified previously ---
        time = int(time)
        total_force = 0.0
        forces_in_direction = []
        try:
            for force_name, directions in self.force_directions.items():
                if isinstance(directions, (list, tuple)) and direction in directions:
                    forces_in_direction.append(force_name)
                    value = self.forces.get_value(force_name, time)
                    if value is not None and not np.isnan(value):
                        total_force += value
                    else:
                        logger.warning(f"Force '{force_name}' is None or NaN for point '{self.name}' at time {time} when calculating total force in '{direction}'.")

            logger.debug(f"Total force in '{direction}' for point '{self.name}' at t={time}: {total_force:.2f} N (from {forces_in_direction})")
            return total_force
        except Exception as e:
            logger.error(f"Error calculating total force for point '{self.name}', direction '{direction}', time {time}: {e}")
            return 0.0

    def forces_incomplete(self, time):
        # --- Ensure this method handles None correctly as modified previously ---
        time = int(time)
        time_row = self.forces.get_time_series(time)
        if time_row is None:
            logger.warning(f"Force data row for point '{self.name}' does not exist at t={time}.")
            return True
        has_nans = time_row.isnull().any()
        if has_nans:
             logger.warning(f"Force data row for point '{self.name}' at t={time} contains NaN values.")
        return has_nans

    def make_tire(self):
        if self.is_tire:

            # Create the Magic Formula tire model
            mf_tire = MagicFormulaTire("Racing Tire")

            # Create the tire object
            self.tire= PhysicalTire(mf_tire, position=self.name, radius=0.33, inertia=1.5, force_point_parent=self)
            time=0
            # Simulate a braking event
            # F_input = -2000  # Braking force (N)
            self.force_input = 0                # Braking force (N) 
            self.tire_angle = 0                 # Tire angle (rad)
            self.tire_vertical_load = self.forces.get_value("vertical_load", self.Car.current_time)        # Vertical load (N)
            self.tire_longitudinal_vel = 0      # Longitudinal velocity (m/s)

            self.dt = self.Car.timestep                  # Time step (s)

            # Update the tire state
            self.tire.update(self.force_input, self.tire_angle, self.tire_vertical_load, self.tire_longitudinal_vel, self.dt)

            # Get the resulting forces and moments
            forces = self.tire.get_forces()
            logger.debug("Forces and Moments:", forces)

            # Get the slip ratio and slip angle
            slip = self.tire.get_slip()
            logger.debug("Slip Ratio and Angle:", slip)
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


