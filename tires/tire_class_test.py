# test_enhanced_tire.py
import numpy as np
import matplotlib.pyplot as plt
from magic_formula_tire import MagicFormulaTire
from tires.tire_class import PhysicalTire
from helper_functions import TimeSeriesStorage

def test_constant_speed():
    """
    Test the enhanced tire with a constant target speed of 60 mph.
    """
    # Create a Magic Formula tire model
    mf_tire = MagicFormulaTire("Racing Tire")
    
    # Generate lookup table
    Fz_values = np.array([4000])  # Single vertical load for now
    Fx_values = np.linspace(-5000, 5000, 21)  # Longitudinal force range
    Fy_values = np.linspace(-5000, 5000, 21)  # Lateral force range
    mf_tire.generate_force_to_slip_table(Fz_values, Fx_values, Fy_values)
    
    # Create the enhanced tire with smoothing
    tire = PhysicalTire(mf_tire, position="front_left", radius=0.33, inertia=1.5, smoothing_factor=0.3)
    
    # Simulation parameters
    dt = 0.01  # Time step (s)
    sim_time = 10.0  # Total simulation time (s)
    steps = int(sim_time / dt)
    
    # Constant target speed (60 mph = 26.8224 m/s)
    target_speed = 60.0 * 0.44704  # Convert mph to m/s
    print(f"Using constant target speed: {target_speed:.2f} m/s ({60.0} mph)")
    
    # Initial conditions - start from rest
    current_speed = 0.0  # m/s (starting from rest for acceleration test)
    current_position = 0.0  # m along the track
    Fz = 4000.0  # Vertical load (N)
    
    # Arrays to store results (for backward compatibility)
    time_array = np.linspace(0, sim_time, steps)
    speed_array = np.zeros(steps)
    acceleration_array = np.zeros(steps)
    position_array = np.zeros(steps)
    
    # Vehicle parameters
    vehicle_mass = 1500.0  # kg
    
    # Run simulation
    print("Running acceleration test with constant target speed...")
    previous_speed = current_speed
    
    for i in range(steps):
        # Current time
        t = time_array[i]
        
        # For straight-line acceleration, use minimal lateral force
        Fy_desired = 0.0  # N (straight line)
        
        # Allocate forces based on desired lateral force and speed
        forces = tire.allocate_forces(
            Fy_desired=Fy_desired,
            Fz=Fz,
            Vx=current_speed,
            longitudinal_mode="match_speed",
            target_speed=target_speed,
            current_speed=current_speed,
            speed_buffer=1.0,  # 1 m/s buffer (~2.2 mph)
            dt=dt,
            time=t  # Pass current time for history tracking
        )
        
        # Update current speed based on forces
        previous_speed = current_speed
        current_speed += forces['Fx'] / vehicle_mass * dt
        
        # Update position
        current_position += current_speed * dt
        
        # Calculate acceleration
        acceleration = (current_speed - previous_speed) / dt
        
        # Store results in arrays (for backward compatibility)
        speed_array[i] = current_speed
        acceleration_array[i] = acceleration
        position_array[i] = current_position
    
    # Print results
    print(f"Initial speed: 0.00 m/s (0.00 mph)")
    print(f"Final speed: {current_speed:.2f} m/s ({current_speed/0.44704:.2f} mph)")
    print(f"Final position: {current_position:.2f} m")
    
    # Find time to reach target speed
    target_speed_index = np.argmax(speed_array >= target_speed * 0.99)
    if target_speed_index > 0:
        time_to_target = time_array[target_speed_index]
        print(f"Time to reach target speed: {time_to_target:.2f} s")
    
    # Get history dataframe
    history_df = tire.get_history()
    
    # Plot results using the tire's history
    plt.figure(figsize=(15, 10))
    
    # Plot speed
    plt.subplot(3, 1, 1)
    plt.plot(history_df.index, speed_array)  # Use stored speed array
    plt.axhline(y=target_speed, color='r', linestyle='--', label='Target Speed')
    plt.xlabel('Time (s)')
    plt.ylabel('Speed (m/s)')
    plt.title('Vehicle Speed during Acceleration Test')
    plt.legend()
    plt.grid(True)
    
    # Plot acceleration
    plt.subplot(3, 1, 2)
    plt.plot(history_df.index, acceleration_array)  # Use stored acceleration array
    plt.xlabel('Time (s)')
    plt.ylabel('Acceleration (m/s²)')
    plt.title('Vehicle Acceleration')
    plt.grid(True)
    
    # Plot forces directly from history
    plt.subplot(3, 1, 3)
    plt.plot(history_df.index, history_df['Fx'], label='Fx (Applied)')
    plt.plot(history_df.index, history_df['max_Fx'], label='Max Available Fx', linestyle='--')
    plt.plot(history_df.index, history_df['Fy'], label='Fy', color='g')
    plt.xlabel('Time (s)')
    plt.ylabel('Force (N)')
    plt.title('Tire Forces')
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()
    
    # Demonstrate the tire's built-in plotting
    print("\nPlotting additional tire history data:")
    tire.plot_history(["Fx", "Fy", "max_Fx", "slip_ratio", "slip_angle"])
    
    # Return data for further analysis
    return {
        'time': time_array,
        'speed': speed_array,
        'acceleration': acceleration_array,
        'position': position_array,
        'history_df': history_df
    }

def test_simple_track():
    """
    Test the enhanced tire with a simple track defined by position and target speed tuples.
    The track has straights and corners with different target speeds.
    """
    # Create a Magic Formula tire model
    mf_tire = MagicFormulaTire("Racing Tire")
    
    # Generate lookup table
    Fz_values = np.array([4000])  # Single vertical load for now
    Fx_values = np.linspace(-5000, 5000, 21)  # Longitudinal force range
    Fy_values = np.linspace(-5000, 5000, 21)  # Lateral force range
    mf_tire.generate_force_to_slip_table(Fz_values, Fx_values, Fy_values)
    
    # Create the enhanced tire with smoothing
    tire = PhysicalTire(mf_tire, position="front_left", radius=0.33, inertia=1.5, smoothing_factor=0.3)
    
    # Define a simple track with [(position, target_speed, lateral_force), ...] tuples
    # Position in meters, speed in m/s, lateral force in N
    simple_track = [
        (0, 0, 0),           # Start (position 0m, 0 m/s, 0N lateral)
        (100, 30, 0),        # End of first straight (position 100m, 30 m/s, 0N lateral)
        (200, 20, 3000),     # First corner (position 200m, 20 m/s, 3000N lateral)
        (300, 30, 0),        # Second straight (position 300m, 30 m/s, 0N lateral)
        (400, 15, 3500),     # Second corner (position 400m, 15 m/s, 3500N lateral)
        (500, 30, 0)         # Final straight (position 500m, 30 m/s, 0N lateral)
    ]
    
    # Simulation parameters
    dt = 0.01  # Time step (s)
    sim_time = 30.0  # Total simulation time (s)
    steps = int(sim_time / dt)
    
    # Initial conditions
    current_speed = 0.0  # m/s (starting from rest)
    current_position = 0.0  # m along the track
    Fz = 4000.0  # Vertical load (N)
    
    # Arrays to store results (for backward compatibility)
    time_array = np.linspace(0, sim_time, steps)
    speed_array = np.zeros(steps)
    position_array = np.zeros(steps)
    target_speed_array = np.zeros(steps)
    Fy_desired_array = np.zeros(steps)
    
    # Vehicle parameters
    vehicle_mass = 1500.0  # kg
    
    # Run simulation
    print("Running simulation with simple track...")
    
    for i in range(steps):
        # Current time
        t = time_array[i]
        
        # Update position
        current_position += current_speed * dt
        position_array[i] = current_position
        
        # Find target speed and lateral force for current position by linear interpolation
        target_speed = 0
        Fy_desired = 0
        
        for j in range(len(simple_track) - 1):
            pos1, speed1, lat1 = simple_track[j]
            pos2, speed2, lat2 = simple_track[j + 1]
            
            if pos1 <= current_position <= pos2:
                # Linear interpolation
                t_interp = (current_position - pos1) / (pos2 - pos1) if pos2 != pos1 else 0
                target_speed = speed1 + t_interp * (speed2 - speed1)
                Fy_desired = lat1 + t_interp * (lat2 - lat1)
                break
        
        # If beyond the last point, use the last speed
        if current_position > simple_track[-1][0]:
            target_speed = simple_track[-1][1]
            Fy_desired = simple_track[-1][2]
        
        target_speed_array[i] = target_speed
        Fy_desired_array[i] = Fy_desired
        
        # Allocate forces based on desired lateral force and speed
        forces = tire.allocate_forces(
            Fy_desired=Fy_desired,
            Fz=Fz,
            Vx=current_speed,
            longitudinal_mode="match_speed",
            target_speed=target_speed,
            current_speed=current_speed,
            speed_buffer=2.0,  # 2 m/s buffer
            dt=dt,
            time=t  # Pass current time for history tracking
        )
        
        # Update current speed based on forces
        current_speed += forces['Fx'] / vehicle_mass * dt
        current_speed = max(0, current_speed)  # Prevent negative speed
        
        # Store results in arrays (for backward compatibility)
        speed_array[i] = current_speed
    
    # Print results
    print(f"Distance covered: {current_position:.2f} m")
    print(f"Final speed: {current_speed:.2f} m/s ({current_speed/0.44704:.2f} mph)")
    
    # Get history dataframe
    history_df = tire.get_history()
    
    # Add additional columns to history for analysis
    history_df['position'] = position_array
    history_df['target_speed'] = target_speed_array
    history_df['current_speed'] = speed_array
    history_df['Fy_desired'] = Fy_desired_array
    
    # Plot results using the tire's history
    plt.figure(figsize=(15, 12))
    
    # Plot position vs target speed and actual speed
    plt.subplot(3, 1, 1)
    plt.plot(position_array, speed_array, label='Actual Speed')
    plt.plot(position_array, target_speed_array, 'r--', label='Target Speed')
    plt.xlabel('Position (m)')
    plt.ylabel('Speed (m/s)')
    plt.title('Speed Profile along Track')
    plt.legend()
    plt.grid(True)
    
    # Plot position vs forces
    plt.subplot(3, 1, 2)
    plt.plot(position_array, history_df['Fx'], label='Fx (Applied)')
    plt.plot(position_array, history_df['max_Fx'], 'b--', label='Max Available Fx')
    plt.plot(position_array, history_df['Fy'], 'g', label='Fy (Applied)')
    plt.plot(position_array, Fy_desired_array, 'g--', label='Fy (Desired)')
    plt.xlabel('Position (m)')
    plt.ylabel('Force (N)')
    plt.title('Forces along Track')
    plt.legend()
    plt.grid(True)
    
    # Plot time vs speed
    plt.subplot(3, 1, 3)
    plt.plot(time_array, speed_array)
    plt.xlabel('Time (s)')
    plt.ylabel('Speed (m/s)')
    plt.title('Speed vs Time')
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()
    
    # Demonstrate additional history plots
    print("\nPlotting tire slip data:")
    tire.plot_history(["slip_ratio", "slip_angle", "angular_velocity"])
    
    # Return data for further analysis
    return {
        'time': time_array,
        'position': position_array,
        'speed': speed_array,
        'target_speed': target_speed_array,
        'history_df': history_df
    }

if __name__ == "__main__":
    print("Select a test to run:")
    print("1. Constant Speed Test (Pure Acceleration)")
    print("2. Simple Track Test")
    
    choice = input("Enter 1 or 2: ")
    
    if choice == "1":
        test_constant_speed()
    elif choice == "2":
        test_simple_track()
    else:
        print("Invalid choice. Running constant speed test by default.")
        test_constant_speed()

