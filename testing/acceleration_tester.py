from car_tester import ev
from motor_tester import emrax_208
from logger import setup_logger
import pandas as pd


# Example usage
logger = setup_logger()

# # Now you can use logger throughout your script:
# logger.debug("Detailed debug information (file only)")
logger.info("Starting Acceleration.py Script")
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


def accelerate_straightline(length, car=ev):
    
    while ev.position[0] < 75:
    # Basic logic is as follows:
        # For each timestep, attempt to allocate the maximum amount of acceleration

        ev.get_vertical_load(ev.current_time)

        ev.accelerate_tires(acceleration_proportion=1, longitudinal_mode='accelerate')
        # import pdb; pdb.set_trace()
        ev.calculate_timestep(ev.current_time)
        
        ev.current_time = ev.timestep+ev.current_time

    ev.export_dataset('75m-acceleration')


if __name__ == "__main__":
    accelerate_straightline(75)











































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
 #
       
