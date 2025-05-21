
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ast
import re
from matplotlib.gridspec import GridSpec

# Function to safely convert string representations of numpy arrays/tuples to actual values
def parse_numpy_tuple(value):
    # Handle potential non-string inputs (like NaN) gracefully
    if not isinstance(value, str):
        return None # Return None or np.nan if input is not a string

    if "np.float64" in value:
        # Extract the numeric values using regex
        # This regex specifically looks for np.float64(...)
        numbers = re.findall(r'np\.float64\(([-+]?\d*\.?\d+|[-+]?\d+\.?\d*[eE][-+]?\d+)\)', value)
        if numbers:
            try:
                return [float(num) for num in numbers]
            except ValueError:
                 # Handle cases where conversion to float fails
                 return None
        else:
            # If no np.float64 found, maybe try ast.literal_eval as a fallback?
            # Be cautious with literal_eval on potentially complex/unsafe strings
            # For now, let's return None if regex fails for simplicity and safety
            # try:
            #     # Attempt to evaluate the tuple structure directly, removing np.float64 text
            #     # This is less robust and might fail on varied formats
            #     cleaned_value = value.replace('np.float64', '')
            #     evaluated = ast.literal_eval(cleaned_value)
            #     if isinstance(evaluated, tuple):
            #         return list(evaluated) # Convert tuple to list
            #     else:
            #         return None # Or handle single values if needed
            # except (ValueError, SyntaxError, TypeError):
            #     return None # Failed to parse
            return None # Return None if regex finds nothing
    # If "np.float64" is not in the string, return None or handle differently
    return None

# Load the CSV file
def load_data(file_path):
    df = pd.read_csv(file_path)

    # Convert time from centaseconds to seconds
    df['time_seconds'] = df['time'] / 100.0

    # Parse the numpy tuples safely
    for col in ['car_acceleration', 'car_velocity', 'car_position']:
        if col in df.columns:
            # Apply the parsing function once
            parsed_col = df[col].apply(parse_numpy_tuple)

            # Safely extract components, checking list length
            df[f'{col}_x'] = parsed_col.apply(
                lambda lst: lst[0] if isinstance(lst, list) and len(lst) > 0 else np.nan
            )
            df[f'{col}_y'] = parsed_col.apply(
                lambda lst: lst[1] if isinstance(lst, list) and len(lst) > 1 else np.nan
            )
            df[f'{col}_z'] = parsed_col.apply(
                lambda lst: lst[2] if isinstance(lst, list) and len(lst) > 2 else np.nan
            )

            # Optional: Drop the original string column if no longer needed
            # df = df.drop(columns=[col])

    return df

# Create visualizations (Keep your existing function)
def create_visualizations(df):
    # Set up the figure with a grid layout
    plt.style.use('ggplot')
    fig = plt.figure(figsize=(20, 24))
    gs = GridSpec(6, 2, figure=fig)

    # --- Your plotting code remains the same ---
    # Example plot (replace with your full plotting code)
    # 1. Car Dynamics Plot
    ax1 = fig.add_subplot(gs[0, :])
    # Check if columns exist before plotting (in case parsing failed entirely)
    if 'car_velocity_x' in df.columns:
        ax1.plot(df['time_seconds'], df['car_velocity_x'], 'b-', label='Velocity (x)')
    if 'car_acceleration_x' in df.columns:
        ax1.plot(df['time_seconds'], df['car_acceleration_x'], 'r-', label='Acceleration (x)')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Value (m/s or m/s²)')
    ax1.set_title('Car Velocity and Acceleration over Time')
    ax1.legend()
    ax1.grid(True)

    # 2. Position Plot
    ax2 = fig.add_subplot(gs[1, :])
    if 'car_position_x' in df.columns:
        ax2.plot(df['time_seconds'], df['car_position_x'], 'g-', label='Position (x)')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Position (m)')
    ax2.set_title('Car Position over Time')
    ax2.legend()
    ax2.grid(True)

    # 3. Vertical Load Distribution
    ax3 = fig.add_subplot(gs[2, 0])
    if 'front_right_vertical_load' in df.columns:
        ax3.plot(df['time_seconds'], df['front_right_vertical_load'], 'r-', label='Front Right')
    if 'front_left_vertical_load' in df.columns:
        ax3.plot(df['time_seconds'], df['front_left_vertical_load'], 'b-', label='Front Left')
    if 'rear_right_vertical_load' in df.columns:
        ax3.plot(df['time_seconds'], df['rear_right_vertical_load'], 'g-', label='Rear Right')
    if 'rear_left_vertical_load' in df.columns:
        ax3.plot(df['time_seconds'], df['rear_left_vertical_load'], 'y-', label='Rear Left')
    ax3.set_xlabel('Time (s)')
    ax3.set_ylabel('Vertical Load (N)')
    ax3.set_title('Tire Vertical Load Distribution')
    ax3.legend()
    ax3.grid(True)

    # 4. Front vs Rear Load Balance
    ax4 = fig.add_subplot(gs[2, 1])
    # Ensure columns exist before calculation
    if all(c in df.columns for c in ['front_right_vertical_load', 'front_left_vertical_load', 'rear_right_vertical_load', 'rear_left_vertical_load']):
        front_load = df['front_right_vertical_load'] + df['front_left_vertical_load']
        rear_load = df['rear_right_vertical_load'] + df['rear_left_vertical_load']
        total_load = front_load + rear_load
        # Avoid division by zero if total_load is 0
        front_load_pct = np.divide(front_load * 100, total_load, out=np.zeros_like(front_load), where=total_load!=0)
        rear_load_pct = np.divide(rear_load * 100, total_load, out=np.zeros_like(rear_load), where=total_load!=0)
        ax4.plot(df['time_seconds'], front_load_pct, 'b-', label='Front Load %')
        ax4.plot(df['time_seconds'], rear_load_pct, 'r-', label='Rear Load %')
    ax4.set_xlabel('Time (s)')
    ax4.set_ylabel('Load Distribution (%)')
    ax4.set_title('Front vs Rear Load Balance')
    ax4.legend()
    ax4.grid(True)

    # 5. X Friction Forces (Longitudinal)
    ax5 = fig.add_subplot(gs[3, 0])
    if 'front_right_x_friction' in df.columns:
        ax5.plot(df['time_seconds'], df['front_right_x_friction'], 'r-', label='Front Right')
    if 'front_left_x_friction' in df.columns:
        ax5.plot(df['time_seconds'], df['front_left_x_friction'], 'b-', label='Front Left')
    if 'rear_right_x_friction' in df.columns:
        ax5.plot(df['time_seconds'], df['rear_right_x_friction'], 'g-', label='Rear Right')
    if 'rear_left_x_friction' in df.columns:
        ax5.plot(df['time_seconds'], df['rear_left_x_friction'], 'y-', label='Rear Left')
    ax5.set_xlabel('Time (s)')
    ax5.set_ylabel('X Friction Force (N)')
    ax5.set_title('Longitudinal Friction Forces')
    ax5.legend()
    ax5.grid(True)

    # 6. Y Friction Forces (Lateral)
    ax6 = fig.add_subplot(gs[3, 1])
    if 'front_right_y_friction' in df.columns:
        ax6.plot(df['time_seconds'], df['front_right_y_friction'], 'r-', label='Front Right')
    if 'front_left_y_friction' in df.columns:
        ax6.plot(df['time_seconds'], df['front_left_y_friction'], 'b-', label='Front Left')
    if 'rear_right_y_friction' in df.columns:
        ax6.plot(df['time_seconds'], df['rear_right_y_friction'], 'g-', label='Rear Right')
    if 'rear_left_y_friction' in df.columns:
        ax6.plot(df['time_seconds'], df['rear_left_y_friction'], 'y-', label='Rear Left')
    ax6.set_xlabel('Time (s)')
    ax6.set_ylabel('Y Friction Force (N)')
    ax6.set_title('Lateral Friction Forces')
    ax6.legend()
    ax6.grid(True)

    # 7. Rolling Resistance
    ax7 = fig.add_subplot(gs[4, 0])
    if 'front_right_rolling_resistance' in df.columns:
        ax7.plot(df['time_seconds'], df['front_right_rolling_resistance'], 'r-', label='Front Right')
    if 'front_left_rolling_resistance' in df.columns:
        ax7.plot(df['time_seconds'], df['front_left_rolling_resistance'], 'b-', label='Front Left')
    if 'rear_right_rolling_resistance' in df.columns:
        ax7.plot(df['time_seconds'], df['rear_right_rolling_resistance'], 'g-', label='Rear Right')
    if 'rear_left_rolling_resistance' in df.columns:
        ax7.plot(df['time_seconds'], df['rear_left_rolling_resistance'], 'y-', label='Rear Left')
    ax7.set_xlabel('Time (s)')
    ax7.set_ylabel('Rolling Resistance (N)')
    ax7.set_title('Tire Rolling Resistance')
    ax7.legend()
    ax7.grid(True)

    # 8. Total Traction Force
    ax8 = fig.add_subplot(gs[4, 1])
    if all(c in df.columns for c in ['front_right_x_friction', 'front_left_x_friction', 'rear_right_x_friction', 'rear_left_x_friction']):
        total_x_friction = (df['front_right_x_friction'] + df['front_left_x_friction'] +
                            df['rear_right_x_friction'] + df['rear_left_x_friction'])
        ax8.plot(df['time_seconds'], total_x_friction, 'b-', label='Total Traction Force')
    if 'car_acceleration_x' in df.columns:
        # Assuming car mass around 1500kg - make this configurable if possible
        car_mass = 1500
        ax8.plot(df['time_seconds'], df['car_acceleration_x'] * car_mass, 'r--',
                 label=f'F=ma (m={car_mass}kg)')
    ax8.set_xlabel('Time (s)')
    ax8.set_ylabel('Force (N)')
    ax8.set_title('Total Traction Force vs F=ma')
    ax8.legend()
    ax8.grid(True)

    # 9. Gravitational and Inertial Forces
    ax9 = fig.add_subplot(gs[5, 0])
    if 'cnt_grav_inertial_x' in df.columns:
        ax9.plot(df['time_seconds'], df['cnt_grav_inertial_x'], 'r-', label='X Component')
    if 'cnt_grav_inertial_y' in df.columns:
        ax9.plot(df['time_seconds'], df['cnt_grav_inertial_y'], 'g-', label='Y Component')
    if 'cnt_grav_inertial_z' in df.columns:
        ax9.plot(df['time_seconds'], df['cnt_grav_inertial_z'], 'b-', label='Z Component')
    ax9.set_xlabel('Time (s)')
    ax9.set_ylabel('Force (N)')
    ax9.set_title('Gravitational and Inertial Forces')
    ax9.legend()
    ax9.grid(True)

    # 10. Friction Circle Visualization
    ax10 = fig.add_subplot(gs[5, 1])
    # Check if all required columns exist
    friction_cols = ['front_right_x_friction', 'front_right_y_friction',
                     'front_left_x_friction', 'front_left_y_friction',
                     'rear_right_x_friction', 'rear_right_y_friction',
                     'rear_left_x_friction', 'rear_left_y_friction']
    if all(c in df.columns for c in friction_cols):
        ax10.scatter(df['front_right_x_friction'], df['front_right_y_friction'], s=5, c='r', alpha=0.5, label='Front Right')
        ax10.scatter(df['front_left_x_friction'], df['front_left_y_friction'], s=5, c='b', alpha=0.5, label='Front Left')
        ax10.scatter(df['rear_right_x_friction'], df['rear_right_y_friction'], s=5, c='g', alpha=0.5, label='Rear Right')
        ax10.scatter(df['rear_left_x_friction'], df['rear_left_y_friction'], s=5, c='y', alpha=0.5, label='Rear Left')
    ax10.set_xlabel('X Friction (N)')
    ax10.set_ylabel('Y Friction (N)')
    ax10.set_title('Friction Circle Visualization (All Time Points)')
    ax10.legend(markerscale=2)
    ax10.grid(True)
    ax10.set_aspect('equal', adjustable='box') # Make the plot square

    plt.tight_layout(rect=[0, 0.03, 1, 0.98]) # Adjust layout slightly
    plt.suptitle('Simulation Analysis Plots', fontsize=16, y=0.995) # Add overall title
    plt.savefig('simulation_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

    # Additional analysis: Calculate and print some key statistics
    print("=== Simulation Analysis Summary ===")
    if 'time_seconds' in df.columns:
        print(f"Simulation duration: {df['time_seconds'].max():.2f} seconds")
    if 'car_velocity_x' in df.columns:
        print(f"Maximum velocity (x): {df['car_velocity_x'].max():.2f} m/s")
    if 'car_acceleration_x' in df.columns:
        print(f"Maximum acceleration (x): {df['car_acceleration_x'].max():.2f} m/s²")
        print(f"Maximum deceleration (x): {df['car_acceleration_x'].min():.2f} m/s²")
    if 'car_position_x' in df.columns:
        print(f"Total distance traveled (x): {df['car_position_x'].max() - df['car_position_x'].min():.2f} m")

    # Calculate weight transfer percentage safely
    if all(c in df.columns for c in ['front_right_vertical_load', 'front_left_vertical_load', 'rear_right_vertical_load', 'rear_left_vertical_load']):
        front_load = df['front_right_vertical_load'] + df['front_left_vertical_load']
        rear_load = df['rear_right_vertical_load'] + df['rear_left_vertical_load']
        total_load = front_load + rear_load
        # Calculate percentages safely, handling potential division by zero
        front_load_pct = np.divide(front_load * 100, total_load, out=np.full_like(front_load, np.nan), where=total_load!=0)
        rear_load_pct = np.divide(rear_load * 100, total_load, out=np.full_like(rear_load, np.nan), where=total_load!=0)
        # Use nanmin/nanmax to ignore potential NaNs from division by zero
        print(f"Front load percentage range: {np.nanmin(front_load_pct):.1f}% to {np.nanmax(front_load_pct):.1f}%")
        print(f"Rear load percentage range: {np.nanmin(rear_load_pct):.1f}% to {np.nanmax(rear_load_pct):.1f}%")
    else:
        print("Could not calculate load balance: Missing vertical load columns.")


# Main function
def main(file_path):
    print(f"Loading data from: {file_path}")
    try:
        df = load_data(file_path)
        print("Data loaded successfully. Columns:", df.columns.tolist())
        print("Data head:\n", df.head())
        # Check for NaNs after parsing
        print("\nNaN counts after parsing:")
        print(df[['car_acceleration_x', 'car_acceleration_y', 'car_acceleration_z',
                  'car_velocity_x', 'car_velocity_y', 'car_velocity_z',
                  'car_position_x', 'car_position_y', 'car_position_z']].isnull().sum())

        create_visualizations(df)
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc() # Print detailed traceback for other errors


if __name__ == "__main__":
    # Define the file path clearly
    # Make sure this path is correct relative to where you run the script
    file_path = "data_export/75m-acceleration-Wed Apr  2 09:37:49 2025.csv"
    # file_path = "75m-acceleration-Fri Mar 21 11:19:06 2025.csv" # Example of the other path

    main(file_path)

