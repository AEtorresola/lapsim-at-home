
from car import Car # Assuming your Car class is in car.py
# Assuming PacejkaTireRefactored, TimeSeriesStorage etc. are also available
# either in car.py or imported within car.py
import math # Needed for math.radians

# Define the path to your tire parameter file
# Make sure this file exists where the script can find it
TIRE_PARAM_FILE = 'tires/hoosier_r20.par'

# Define the static camber angles for each wheel (in radians)
# Adjust these values based on your car's setup
STATIC_CAMBERS = {

    'front_left': math.radians(0),
    'front_right': math.radians(0),
    'rear_left': math.radians(0),
    'rear_right': math.radians(0)
}

# --- Updated Car Initialization ---
ev = Car(
    mass=250,                       # 550lbs
    dist_f= 0.762,                  # 30in
    dist_r= 0.762,                  # 30in
    h_cog=0.2794,                   # 11in
    track_width=1.1176,             # 44in
    tire_parameter_filepath=TIRE_PARAM_FILE, # <<< ADDED
    static_cambers=STATIC_CAMBERS,           # <<< ADDED
    # return_tire_errors=False # Optional: Keep default or set True if needed
)

# Now you can proceed with using the 'ev' object
# Example:
# ev.apply_control_inputs(...)
# ev.calculate_timestep(...)
# ... etc ...

print("Car object initialized successfully.")
# You can add more testing code here

