
import math
import matplotlib.pyplot as plt
import numpy as np


import os 
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Get the absolute path of the parent directory (my_project)
parent_dir = os.path.dirname(current_dir)

# 3. Add the parent directory to sys.path if it's not already there
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir) # Insert at the beginning for priority

# --- Manim Animation Scene ---
from steering import *

def run_steering_simulation_and_plot():
    """
    Runs steering simulations for different Ackermann percentages and plots
    the results.
    """
    # Vehicle Parameters (example values)
    wheelbase = 2.7  # meters
    track_width_front = 1.5  # meters
    max_inner_wheel_angle_deg = 35.0  # degrees
    max_inner_wheel_angle_rad = math.radians(max_inner_wheel_angle_deg)

    # Steering configurations to test
    steering_configurations = {
        "Ackermann (100%)": 1.0,
        "Parallel (0%)": 0.0,
        "Anti-Ackermann (-100%)": -1.0,
    }

    # Steering input percentages (1% to 100% for a right turn)
    # The function input is 0.0 to 1.0. We multiply by 100 for plotting.
    steering_input_norm = np.linspace(
        0.01, 1.0, 100
    )  # 1% to 100% input

    results_for_plotting = {}

    for name, ack_percentage in steering_configurations.items():
        system = SteeringSystem(
            wheelbase=wheelbase,
            track_width_front=track_width_front,
            max_steering_angle_inner_wheel_rad=max_inner_wheel_angle_rad,
            ackermann_percentage=ack_percentage,
        )

        inner_wheel_angles_deg_list = []
        outer_wheel_angles_deg_list = []

        for steer_norm_input in steering_input_norm:
            # Positive steer_norm_input simulates a right turn.
            # In a right turn:
            # - Right wheel is the inner wheel.
            # - Left wheel is the outer wheel.
            # get_wheel_angles returns (left_rad, right_rad)
            # All angles will be positive for a right turn.

            left_rad, right_rad = system.get_wheel_angles(
                steer_norm_input
            )

            inner_angle_rad = right_rad  # Right wheel is inner
            outer_angle_rad = left_rad  # Left wheel is outer

            inner_wheel_angles_deg_list.append(
                math.degrees(inner_angle_rad)
            )
            outer_wheel_angles_deg_list.append(
                math.degrees(outer_angle_rad)
            )

        results_for_plotting[name] = {
            "inputs_plot_percent": steering_input_norm * 100,
            "inner_deg": inner_wheel_angles_deg_list,
            "outer_deg": outer_wheel_angles_deg_list,
        }

    # Plotting
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.figure(figsize=(14, 9))

    # Define colors and line styles for clarity
    # (color for steering type, solid for inner, dashed for outer)
    colors = {
        "Ackermann (100%)": "blue",
        "Parallel (0%)": "green",
        "Anti-Ackermann (-100%)": "red",
    }

    for name, data in results_for_plotting.items():
        color = colors[name]
        plt.plot(
            data["inputs_plot_percent"],
            data["inner_deg"],
            label=f"{name} - Inner Wheel",
            color=color,
            linestyle="-",
            linewidth=2,
        )
        plt.plot(
            data["inputs_plot_percent"],
            data["outer_deg"],
            label=f"{name} - Outer Wheel",
            color=color,
            linestyle="--",
            linewidth=2,
        )

    plt.title(
        "Wheel Angles vs. Steering Input Percentage (Simulated Right Turn)",
        fontsize=16,
    )
    plt.xlabel(
        "Steering Input (% of Max Inner Wheel Angle Command)", fontsize=14
    )
    plt.ylabel("Wheel Angle (degrees)", fontsize=14)
    plt.legend(loc="upper left", fontsize="medium")
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.xlim(0, 100)
    # Adjust y-limit if necessary, but usually auto is fine
    # plt.ylim(0, max_inner_wheel_angle_deg * 1.5) # Example y-limit adjustment

    plt.tight_layout() # Adjust layout to prevent labels from overlapping
    plt.show()


if __name__ == "__main__":
    run_steering_simulation_and_plot()
