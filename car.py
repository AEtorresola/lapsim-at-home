import pandas as pd
from tires.magic_formula_tire import MagicFormulaTire
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
        # Parameters
    ):
        self.mass = mass
        self.vehicle_weight = self.mass*9.81
        self.drivetrain = "RWD"
        # Location Parameters (spatial)
        self.h_cog = h_cog
        self.wheelbase = dist_f+dist_r
        self.track_width = track_width
        self.loc = position(track_width, dist_f, dist_r, h_cog)
        self.dist_f = dist_f
        self.dist_r = dist_r

        # Physical Parameters
        self.z_inertia = 1/12*self.mass*(self.wheelbase**2+self.track_width**2)
        # Program Parameters 
        self.force_lag = 5          # Changing to millisecond based time series. 
        self.timestep = 5           # Changing to millisecond based time series. 
        self.current_time= 0

        # self.all_forces = [self.front_right, self.front_left, self.rear_right, self.rear_left]
         
        # Transient Parameters (origin is cog)
        self.acceleration = (0,0,0) # x, y, z
        self.velocity = (0,0,0)     # x, y, z
        self.position = (0,0,0)     # x, y, z
        self.yaw_angle = 0          # Angle, radians?
        self.yaw_velocity = 0          # Angle, radians?

        # Initialize Forces
        self.vehicle_details = TimeSeriesStorage({"time": [0.0], "acceleration": [0], "velocity": [0], "position": [0]}, 'vehicle_dataframe', col_types={"acceleration": 'object', "velocity": 'object', "position": 'object'})
        self.vehicle_details.update({"velocity": self.velocity, "position": self.position}, self.current_time+self.timestep)
        self.initialize_forces()

        # Put all forces into a list 
        self.all_force_points = [self.front_right, self.front_left, self.rear_right, self.rear_left, self.cnt_grav]
        # Define big transient dataframe 
        self.all_dataframes_for_update = [(self.vehicle_details, "car"), (self.front_right.forces, "front_right"),(self.front_left.forces, "front_left"),(self.rear_right.forces, "rear_right"),(self.rear_left.forces, "rear_left"), (self.cnt_grav.forces, "cnt_grav")]
        self.full_dataset = combine_dataframes(self.all_dataframes_for_update)

    def initialize_forces(self):
         # Force Points 
        self.front_right = force_point(self,"front_right",self.loc.front_right, {"vertical_load":['z'], "x_friction":['x'], "y_friction":['y'], "rolling_resistance":['x']}, is_tire=True)
        self.front_left =  force_point(self,"front_left",self.loc.front_left, {"vertical_load":['z'], "x_friction":['x'], "y_friction":['y'], "rolling_resistance":['x']}, is_tire=True)
        self.rear_right =  force_point(self,"rear_right", self.loc.rear_right, {"vertical_load":['z'], "x_friction":['x'], "y_friction":['y'], "rolling_resistance":['x']}, is_tire=True)
        self.rear_left = force_point(self,"rear_left", self.loc.rear_left, {"vertical_load":['z'], "x_friction":['x'], "y_friction":['y'], "rolling_resistance":['x']}, is_tire=True)

        self.cnt_grav = force_point(self,"cnt_grav", self.loc.cog, {"inertial_z":['z'], "inertial_x":['x'], "inertial_y":['y']})


       
        # Initialize Forces
        
        self.current_time+=self.timestep
        self.get_vertical_load()

        initial_forces = {"x_friction":0, "y_friction":0, "rolling_resistance":0}
        self.front_right.forces.update(initial_forces, self.current_time)
        self.front_left.forces.update(initial_forces, self.current_time)
        self.rear_right.forces.update(initial_forces, self.current_time)
        self.rear_left.forces.update(initial_forces, self.current_time)
        
        cnt_grav_initial = {"inertial_z":0, "inertial_x":0, "inertial_y":0}
        self.cnt_grav.forces.update(cnt_grav_initial, self.current_time)

        resultants = self.get_resultant_force_and_torque(self.current_time)
        
        self.update_linear_motion(resultants['forces'])
        self.update_rotational_motion(resultants['torques'])
        logger.debug(f"After forces are applied; Position = {self.position} -- Velocity = {self.velocity} --")
        # Get combined dataframe 

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
        

class force_point:

    def __init__(self,
                 Car: Car,
                 name: str,
                 origin_location: tuple,
                 force_name_direction: dict,
                 is_tire = False
                 ):
        
        self.Car = Car
        forces_at_point = {"time":[0]}
        forces_at_point.update({name:[0] for name in force_name_direction.keys()})
        self.name = name
        self.loc = origin_location
        self.force_directions = force_name_direction
        self.is_tire = is_tire
        # Create the Pandas DataFame
        self.forces = TimeSeriesStorage(forces_at_point, name)
        # self.old_forces = pd.DataFrame(forces_at_point,dtype=float) 
        # self.old_forces.set_index("time", inplace=True)
        
        # Lets initialize the tire class, 
        if self.is_tire:
            self.make_tire()

    def total_force(self, direction, time):
        # First need to define a way to track the direction of each force. 
        # Then, just call f_t of a direction
        try:
            forces_in_direction = [force_name for force_name in self.force_directions.keys() if self.force_directions[force_name][0]==direction]
        except Exception as e:
            print(e)
            import pbd; pdb.set_trace()
        total_force = sum([self.forces.data.at[time,force] for force in forces_in_direction])
        logger.debug(f"Returning total forces in {direction} direction for point {self.name}. Forces are : {forces_in_direction}. Sum was {total_force}")
        
        return total_force

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

    def forces_incomplete(self, time):
        
        time_row = self.forces.get_time_series(time)
        if time_row is None:
            return time_row
        return time_row.hasnans

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


