
# main.py
from car import Car
from track import *
from dynamics import *
from visualization import *

# Define car parameters
car = Car(
    mass=204,  # kg
    wheelbase=1.6,  # m
    cg_front=0.7,  # m
    cg_rear=0.9,  # m
    cg_height=0.3,  # m
    track_width=1.2,  # m
    tire_radius=0.178,  # m
    drag_coeff=1.2,
    downforce_coeff=0.1,
    frontal_area=1.5,  # m²
    rolling_resistance=0.02,
    tire_grip=1.5
)



# Define track segments (mix of straight and cornering)
# segments = [
#     TrackSegment(length=50, curvature=0, slope=0),  # Straight
#     TrackSegment(length=30, curvature=0.1, slope=0),  # Corner
#     TrackSegment(length=50, curvature=0, slope=0),  # Straight
#     TrackSegment(length=30, curvature=0.1, slope=0)   # Corner
# ]
#

from track import Track

# Load track from CSV
track = Track.from_csv("tracks/2021_michigan.csv")

# Plot the full track
track.plot_full_track()

# # Load track segments from CSV
# track_segments = TrackSegment.load_from_csv('tracks/2023_michigan.csv')
#
# x_points, y_points = generate_track_points(track_segments)
#
# plot_track(x_points, y_points)

import pdb; pdb.set_trace()

# Set driver inputs (full throttle, no braking)
car.set_driver_inputs(throttle=1.0, brake=0.0)

# Simulate the lap
times, distances, velocities, accelerations, x_positions, y_positions = simulate_lap(car, segments, initial_velocity=0)

# Visualize results
plot_velocity_map(x_positions, y_positions, accelerations)


