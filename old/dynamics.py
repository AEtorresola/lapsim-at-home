
# dynamics.py
from forces import calculate_aerodynamic_drag, calculate_rolling_resistance, calculate_downforce
from car import Car
from track import TrackSegment
import pandas as pd
import numpy as np


def calculate_normal_forces(car, acceleration, downforce):
    # Weight transfer due to acceleration
    normal_force_front = (car.mass * 9.81 * car.cg_rear / car.wheelbase) - (car.mass * acceleration * car.cg_height / car.wheelbase)
    normal_force_rear = (car.mass * 9.81 * car.cg_front / car.wheelbase) + (car.mass * acceleration * car.cg_height / car.wheelbase)
    
    # Add downforce (distributed 50/50)
    normal_force_front += 0.5 * downforce
    normal_force_rear += 0.5 * downforce
    
    return normal_force_front, normal_force_rear

def calculate_traction_limits(car, normal_force_front, normal_force_rear):
    return car.tire_grip * normal_force_front, car.tire_grip * normal_force_rear


def calculate_lateral_forces(car, velocity, radius):
    # Calculate lateral acceleration
    lateral_acceleration = velocity**2 / radius
    
    # Calculate normal forces during cornering
    normal_force_left = (car.mass * 9.81 / 2) - (car.mass * lateral_acceleration * car.cg_height / car.track_width)
    normal_force_right = (car.mass * 9.81 / 2) + (car.mass * lateral_acceleration * car.cg_height / car.track_width)
    
    # Calculate maximum lateral forces
    max_lateral_force_left = car.tire_grip * normal_force_left
    max_lateral_force_right = car.tire_grip * normal_force_right
    
    return max_lateral_force_left, max_lateral_force_right



def simulate_straight_segment(car, segment, initial_velocity, initial_x, initial_y, initial_angle, time_step=0.1):
    velocity = initial_velocity
    distance = 0
    time = 0
    x = initial_x
    y = initial_y
    angle = initial_angle  # Current direction of the car
    
    # Lists to store data
    times = []
    distances = []
    velocities = []
    accelerations = []
    x_positions = []
    y_positions = []
    angles = []
    
    while distance < segment.length:
        # Calculate forces
        aero_drag = calculate_aerodynamic_drag(car, velocity)
        rolling_resistance = calculate_rolling_resistance(car)
        downforce = calculate_downforce(car, velocity)
        
        # Calculate normal forces and traction limits
        normal_force_front, normal_force_rear = calculate_normal_forces(car, 0, downforce)
        traction_limit_front, traction_limit_rear = calculate_traction_limits(car, normal_force_front, normal_force_rear)
        
        # Calculate driver inputs
        throttle_force = car.calculate_throttle_force()
        brake_force = car.calculate_brake_force()
        
        # Net traction force (considering throttle and brake)
        net_traction_force = throttle_force - brake_force
        traction_force = min(net_traction_force, traction_limit_front + traction_limit_rear)
        
        # Net force
        net_force = traction_force - aero_drag - rolling_resistance
        
        # Acceleration
        acceleration = net_force / car.mass
        
        # Update velocity and distance
        velocity += acceleration * time_step
        delta_distance = velocity * time_step
        distance += delta_distance
        time += time_step
        
        # Update position (straight segment: no curvature)
        x += delta_distance * np.cos(angle)
        y += delta_distance * np.sin(angle)
        
        # Store results
        times.append(time)
        distances.append(distance)
        velocities.append(velocity)
        accelerations.append(acceleration)
        x_positions.append(x)
        y_positions.append(y)
        angles.append(angle)
    
    return times, distances, velocities, accelerations, x_positions, y_positions, angles



def simulate_cornering_segment(car, segment, initial_velocity, initial_x, initial_y, initial_angle, time_step=0.1):
    velocity = initial_velocity
    distance = 0
    time = 0
    x = initial_x
    y = initial_y
    angle = initial_angle  # Current direction of the car
    
    # Lists to store data
    times = []
    distances = []
    velocities = []
    accelerations = []
    x_positions = []
    y_positions = []
    angles = []
    
    # Corner parameters
    curvature = segment.curvature
    radius = 1 / curvature if curvature != 0 else float('inf')
    
    while distance < segment.length:
        # Calculate forces
        aero_drag = calculate_aerodynamic_drag(car, velocity)
        rolling_resistance = calculate_rolling_resistance(car)
        downforce = calculate_downforce(car, velocity)
        
        # Calculate normal forces and traction limits
        normal_force_front, normal_force_rear = calculate_normal_forces(car, 0, downforce)
        traction_limit_front, traction_limit_rear = calculate_traction_limits(car, normal_force_front, normal_force_rear)
        
        # Calculate driver inputs
        throttle_force = car.calculate_throttle_force()
        brake_force = car.calculate_brake_force()
        
        # Net traction force (considering throttle and brake)
        net_traction_force = throttle_force - brake_force
        traction_force = min(net_traction_force, traction_limit_front + traction_limit_rear)
        
        # Net force
        net_force = traction_force - aero_drag - rolling_resistance
        
        # Acceleration
        acceleration = net_force / car.mass
        
        # Update velocity and distance
        velocity += acceleration * time_step
        delta_distance = velocity * time_step
        distance += delta_distance
        time += time_step
        
        # Update position and angle (cornering)
        delta_angle = delta_distance * curvature  # Change in angle due to curvature
        angle += delta_angle
        
        # Update x and y based on the average angle during the time step
        avg_angle = angle - delta_angle / 2  # Use midpoint angle for smoother path
        x += delta_distance * np.cos(avg_angle)
        y += delta_distance * np.sin(avg_angle)
        
        # Store results
        times.append(time)
        distances.append(distance)
        velocities.append(velocity)
        accelerations.append(acceleration)
        x_positions.append(x)
        y_positions.append(y)
        angles.append(angle)
    
    return times, distances, velocities, accelerations, x_positions, y_positions, angles


def simulate_lap(car, segments, initial_velocity):
    times = []
    distances = []
    velocities = []
    accelerations = []
    x_positions = []
    y_positions = []
    angles = []
    
    # Initialize position and angle
    current_x = 0.0
    current_y = 0.0
    current_angle = 0.0  # Start facing along the positive x-axis
    
    for segment in segments:
        if segment.curvature == 0:  # Straight segment
            t, d, v, a, x, y, ang = simulate_straight_segment(
                car, segment, initial_velocity, current_x, current_y, current_angle
            )
        else:  # Cornering segment
            t, d, v, a, x, y, ang = simulate_cornering_segment(
                car, segment, initial_velocity, current_x, current_y, current_angle
            )
        
        # Append results
        times.extend(t)
        distances.extend(d)
        velocities.extend(v)
        accelerations.extend(a)
        x_positions.extend(x)
        y_positions.extend(y)
        angles.extend(ang)
        
        # Update initial conditions for the next segment
        initial_velocity = velocities[-1]
        current_x = x_positions[-1]
        current_y = y_positions[-1]
        current_angle = angles[-1]
    
    return times, distances, velocities, accelerations, x_positions, y_positions



