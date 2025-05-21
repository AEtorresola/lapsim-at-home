from car_tester import ev
from motor_tester import emrax_208
from logger import setup_logger
import pandas as pd


# Example usage
logger = setup_logger()
logger.info("Starting Acceleration.py Script")

# Simulate Lap
def accelerate_straightline(length): # Removed car=ev default argument
    """
    Simulates straight-line acceleration for a given length using the imported 'ev' car object.

    Args:
        length (float): The target distance to cover (meters).
    """
    logger.info(f"Starting straight-line acceleration simulation for {length}m.")
    # Assuming 'ev' might have state from previous runs, consider resetting if necessary
    # ev.reset_state() # If you implement a reset method in Car

    # Ensure simulation starts from t=0 if needed, or use ev.current_time as is
    # initial_time = ev.current_time # Capture start time for logging if needed

    # Simulation loop
    while -1*ev.position[0] < length:
        # Get current time for this step
        current_sim_time = ev.current_time

        logger.debug(f"--- Simulating Timestep t={current_sim_time} ms ---")

        # 1. Calculate dynamic vertical loads based on forces from previous step (t - lag)
        #    This updates the vertical_load column for 'current_sim_time'
        ev.get_vertical_load(time=current_sim_time)

        # 2. Apply Controls: Request maximum acceleration in a straight line
        #    Uses the new method, replacing accelerate_tires
        ev.apply_control_inputs(
            target_lateral_accel=0.0,       # Straight line
            longitudinal_mode='accelerate', # Accelerate
            longitudinal_intensity=1.0,     # Maximum effort
            time=current_sim_time
        )

        # 3. Integrate Physics: Use forces at 'current_sim_time' to calculate
        #    acceleration at 'current_sim_time' and update velocity/position
        #    for 'current_sim_time + timestep'. Also updates master dataframe for 'current_sim_time'.
        ev.calculate_timestep(time=current_sim_time)

        # 4. Advance Time for the next iteration
        ev.current_time += ev.timestep

        # Safety break / Check for stall (optional but recommended)
        if ev.velocity[0] < 0.01 and current_sim_time > 10000: # Example: If stuck for 10s
             logger.warning(f"Simulation potentially stalled at t={current_sim_time} ms. Velocity near zero. Stopping.")
             break
        if current_sim_time > 60000: # Example: Max simulation time 60s
             logger.warning(f"Simulation time limit exceeded at t={current_sim_time} ms. Stopping.")
             break

    logger.info(f"Simulation finished at time {ev.current_time} ms. Final position: {ev.position[0]:.2f} m.")
    # Export the results using the imported ev object
    ev.export_dataset('75m-acceleration')


if __name__ == "__main__":
    # No need to initialize 'ev' here, as it's imported from car_tester
    logger.info("Running simulation using 'ev' object imported from car_tester.py")
    try:
        accelerate_straightline(75)
    except AttributeError as e:
         logger.error(f"AttributeError: Does the imported 'ev' object have all required methods/attributes? Error: {e}")
         print(f"Error: The imported 'ev' object might be missing expected methods (like apply_control_inputs) or attributes. Check car_tester.py. Details: {e}")
    except Exception as e:
         logger.exception("An unexpected error occurred during the simulation:")
         print(f"An unexpected error occurred: {e}")









































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
       
