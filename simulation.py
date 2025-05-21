# simulation.py
import numpy as np
from car import *
from forces import *

# Example usage
logger = setup_logger()

# # Now you can use logger throughout your script:
# logger.debug("Detailed debug information (file only)")
logger.info("Starting Simulation.py Script")
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
## Maximum Grip Tire model

# Simulate Lap

def accelerate_meters(track_length:int, car):
    
    
    
    while car.position[0] < track_length:
        car.current_time += car.timestep

        car.





def initial_simulation_loop():
        continue_iterating = False
        while continue_iterating:
            ev.current_time += ev.timestep
            # First, lets calculate all the forces for this given iteration
            
            # Calculate Vertical Load 
            # Get all current parameters of:
                # 

            # Next, lets figure out what we want the car to do for the next timestep
            pass # This is based on the velocity profile calculated for the track based on tire and weight transfer parameters


            # Next lets figure out what forces we would need to apply to get the car to do the previous
            pass # Basically, given that we have a theoretical maximum velocity profile, we can use that as a basis for
                # determining what we should do for each timestep (not based on timestep btw, but on the distance along the track)
            
            # We will be using the accelerate tires method for this. For now, there is not consideration of lateral forces. 

            ev.accelerate_tires(acceleration_proportion=1)
            import pdb; pdb.set_trace()
            # Next, we should apply the forces to the car. 
            pass # This involves calculating the resultant vector that we get based on all the forces on the car





def compute_acceleration_timestep(
    cornering_force: float,     # 0 to 1, ratio of how much goes to cornering
    current_velocity: float,    # Velocity the vehicle is currently going at [m/s]
    tire_state: dict,           # Current parameters that describe the angle, vertical load, etc of the tire 
                                      #  (all needed to calculate frictional forces)
    target_velocity: float=None # Velocity we are seeking to reach
) -> pd.DataFrame:
    
    speed_error = 0.5
    # Lets handle pure longitudinal first; as this is all we are actually focused on
    if cornering_force ==0:
        # For maintaining speed 
        if abs(current_velocity - target_velocity) < speed_error:
            logger.debug(f"| Maintaining Velocity |  Current Velocity: {current_velocity}  |  Target Velocity: {target_velocity}")

        elif target_velocity - current_velocity > speed_error:
            logger.debug(f"|      Accelerating    |  Current Velocity: {current_velocity}  |  Target Velocity: {target_velocity}")

    # If so, we can assume we want to accelerate
        elif target_velocity - current_velocity < speed_error:
            logger.debug(f"|         Braking      |  Current Velocity: {current_velocity}  |  Target Velocity: {target_velocity}")
            # At a speed of 1, wanting to go to 2. 
            # Add speed error (0.5), then make sure its still negative. 
            # Being negative means that 
            #2-1 > 0.5 ; 1>0.5 True ; accelerate
            #2-1 < 0.5 ; 1<0.5 not true 
    else: 
        logger.warning(f"This is only meant to simulate acceleration, yet cornering fraction of {cornering_force} provided")
      pass


def compute_longitudinal_acceleration(
    accelerate: bool,         # True = accelerate, False = Brake
    tire_state: dict
):
    


    














