# forces.py
import numpy as np



def longitudinal_weight_transfer(
    car: Car,
    a_x: np.ndarray,  # Longitudinal acceleration array (m/s²)
    t: np.ndarray,    # Time array (s)
) -> tuple[np.ndarray, np.ndarray]:
    """
    Returns:
        delta_front: Weight transferred to front axle (N)
        delta_rear: Weight transferred to rear axle (N)
    """
    # Steady-state weight transfer (rigid-body)
    delta_front_steady = -(car.mass * a_x * car.cg_height) / car.wheelbase
    
    # Apply first-order lag for suspension dynamics
    delta_front = delta_front_steady * (1 - np.exp(-t / car.tau_long))
    delta_rear = -delta_front
    
    return delta_front, delta_rear

def lateral_weight_transfer(
    car: Car,
    a_y: np.ndarray,  # Lateral acceleration array (m/s²)
    t: np.ndarray,    # Time array (s)
) -> tuple[np.ndarray, np.ndarray]:
    """
    Returns:
        delta_left: Weight transferred to left wheels (N)
        delta_right: Weight transferred to right wheels (N)
    """
    # Steady-state weight transfer (rigid-body)
    delta_left_steady = (car.mass * a_y * car.cg_height) / car.track_width
    
    # Apply first-order lag for suspension dynamics
    delta_left = delta_left_steady * (1 - np.exp(-t / car.tau_lat))
    delta_right = -delta_left
    
    return delta_left, delta_right

def combined_weight_transfer(
    car: Car,
    a_x: np.ndarray,  # Longitudinal acceleration (m/s²)
    a_y: np.ndarray,  # Lateral acceleration (m/s²)
    t: np.ndarray,    # Time array (s)
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Returns:
        front_left: Total weight transfer on front-left wheel (N)
        front_right: Total weight transfer on front-right wheel (N)
        rear_left: Total weight transfer on rear-left wheel (N)
        rear_right: Total weight transfer on rear-right wheel (N)
    """
    # Longitudinal transfer (front/rear)
    delta_front, delta_rear = longitudinal_weight_transfer(car, a_x, t)
    
    # Lateral transfer (left/right)
    delta_left, delta_right = lateral_weight_transfer(car, a_y, t)
    
    # Combine effects for each wheel
    front_left = delta_front + delta_left
    front_right = delta_front + delta_right
    rear_left = delta_rear + delta_left
    rear_right = delta_rear + delta_right
    
    return front_left, front_right, rear_left, rear_right

def calculate_aerodynamic_drag(car, velocity):
    """
    Calculates the aerodynamic drag force acting on the car.

    Args:
        car: An object representing the car, with attributes for drag_coeff and frontal_area.
        velocity: The velocity of the car in meters per second (m/s).

    Returns:
        The aerodynamic drag force in Newtons (N).
    """
    AIR_DENSITY = 1.225  # kg/m^3
    return 0.5 * AIR_DENSITY * car.drag_coeff * car.frontal_area * velocity**2

def calculate_rolling_resistance(car):
    """
    Calculates the rolling resistance force acting on the car.

    Args:
        car: An object representing the car, with attributes for rolling_resistance and mass.

    Returns:
        The rolling resistance force in Newtons (N).
    """
    GRAVITY = 9.81  # m/s^2
    return car.rolling_resistance * car.mass * GRAVITY



