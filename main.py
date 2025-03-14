# main.py
import numpy as np
from car import Car, ElectricEngineCharacteristics
from track import *
from simulation import simulate_lap
from forces import calculate_aerodynamic_drag, calculate_rolling_resistance

# Define car parameters
motor_torque_curve = [(0, 100), (1000, 95), (2000, 90), (3000, 80), (4000, 70), (5000, 60)]
engine_characteristics = ElectricEngineCharacteristics(motor_torque_curve)

car = Car(
    mass=204,
    wheelbase=1.6,
    cg_front=0.7,
    cg_rear=0.9,
    cg_height=0.3,
    track_width=1.2,
    tire_radius=0.178,
    drag_coeff=1.2,
    downforce_coeff=0.1,
    frontal_area=1.5,
    rolling_resistance=0.02,
    tire_grip=1.5,
    engine_characteristics=engine_characteristics,
    gear_ratio=4.0,
    drivetrain_efficiency=0.95,
    braking_force_distribution=0.7
)

# Define a straight track segment
straight_segment = TrackSegment(length=1000, curvature=0, slope=0)  # Long straight

# Set driver inputs (full braking)
car.set_driver_inputs(throttle=0.0, brake=1.0)

# Simulate the lap
initial_velocity = 20  # m/s
times, distances, velocities, accelerations = simulate_lap(car, [straight_segment], initial_velocity)

# Find the index where the car stops
stopping_index = next((i for i, v in enumerate(velocities) if v <= 0), len(velocities) - 1)

# Calculate stopping distance and time
stopping_distance = distances[stopping_index]
stopping_time = times[stopping_index]

# Print results
print("Stopping Distance:", stopping_distance, "m")
print("Stopping Time:", stopping_time, "s")
print("Final Velocity:", velocities[stopping_index], "m/s")
print("Final Acceleration:", accelerations[stopping_index], "m/s^2")

# Print normal forces (example: at the start of braking)
acceleration = accelerations[0]
Nf = (car.mass * 9.81 * car.cg_rear / car.wheelbase) - (car.mass * acceleration * car.cg_height / car.wheelbase)
Nr = (car.mass * 9.81 * car.cg_front / car.wheelbase) + (car.mass * acceleration * car.cg_height / car.wheelbase)
print("Initial Normal Force Front:", Nf, "N")
print("Initial Normal Force Rear:", Nr, "N")

# Print braking forces (example: at the start of braking)
braking_force_front, braking_force_rear = car.calculate_brake_force(acceleration)
print("Initial Braking Force Front:", braking_force_front, "N")
print("Initial Braking Force Rear:", braking_force_rear, "N")

