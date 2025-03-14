# visualization.py
import matplotlib.pyplot as plt
import numpy as np


def plot_velocity_profile(times, velocities):
    plt.plot(times, velocities)
    plt.xlabel("Time (s)")
    plt.ylabel("Velocity (m/s)")
    plt.title("Velocity Profile on Straight Track")
    plt.grid()
    plt.show()


def plot_velocity_map(x_positions, y_positions, accelerations):
    # Normalize acceleration for color mapping
    norm_acc = (accelerations - np.min(accelerations)) / (np.max(accelerations) - np.min(accelerations))
    
    # Create a scatter plot of the track
    plt.figure(figsize=(10, 6))
    plt.scatter(x_positions, y_positions, c=norm_acc, cmap='viridis', s=10)
    plt.colorbar(label='Normalized Acceleration')
    plt.title('Velocity Profile as a Map of a Single Lap')
    plt.xlabel('X Position (m)')
    plt.ylabel('Y Position (m)')
    plt.grid()
    plt.show()





# visualization.py
from matplotlib.patches import Arc


import matplotlib.pyplot as plt

def plot_track(x_points, y_points):
    plt.figure(figsize=(10, 6))
    plt.plot(x_points, y_points, 'b-', linewidth=2, label='Track Centerline')
    plt.scatter(x_points[0], y_points[0], color='green', label='Start', zorder=3)
    plt.scatter(x_points[-1], y_points[-1], color='red', label='End', zorder=3)
    plt.xlabel('X Position (m)')
    plt.ylabel('Y Position (m)')
    plt.title('Track Layout')
    plt.grid()
    plt.axis('equal')  # Ensure aspect ratio is 1:1
    plt.legend()
    plt.show()

