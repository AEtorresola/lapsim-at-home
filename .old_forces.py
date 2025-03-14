# forces.py
import numpy as np

# Constants
AIR_DENSITY = 1.225  # kg/m³
GRAVITY = 9.81  # m/s²

def calculate_aerodynamic_drag(car, velocity):
    return 0.5 * AIR_DENSITY * car.drag_coeff * car.frontal_area * velocity**2

def calculate_rolling_resistance(car):
    return car.rolling_resistance * car.mass * GRAVITY

def calculate_downforce(car, velocity):
    return 0.5 * AIR_DENSITY * car.downforce_coeff * car.frontal_area * velocity**2

def calculate_normal_forces(car, acceleration, downforce):
    # Weight transfer due to acceleration
    normal_force_front = (car.mass * GRAVITY * car.cg_rear / car.wheelbase) - (car.mass * acceleration * car.cg_height / car.wheelbase)
    normal_force_rear = (car.mass * GRAVITY * car.cg_front / car.wheelbase) + (car.mass * acceleration * car.cg_height / car.wheelbase)
    
    # Add downforce (distributed 50/50)
    normal_force_front += 0.5 * downforce
    normal_force_rear += 0.5 * downforce
    
    return normal_force_front, normal_force_rear

def calculate_traction_limits(car, normal_force_front, normal_force_rear):
    return car.tire_grip * normal_force_front, car.tire_grip * normal_force_rear


