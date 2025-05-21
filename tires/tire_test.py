# tire_test.py

import math
import numpy as np
import matplotlib.pyplot as plt
from magic_formula_tire import MagicFormulaTire

def demonstration():
    """Demonstrate the usage of the simplified Magic Formula tire model."""
    # Create a tire instance with default parameters
    tire = MagicFormulaTire('test_tire')
    
    # Example 1: Steady-state lateral force at varying slip angles
    print("Example 1: Steady-state forces at varying slip angles")
    Fz = 4500  # Normal load [N]
    kappa = 0.0  # Pure lateral slip case
    
    # Create an array of slip angles to evaluate
    alpha_array = np.linspace(-0.3, 0.3, 100)  # -17° to 17° in radians
    
    # Calculate lateral force for each slip angle at different temperatures
    Fy_cold = []
    Fy_optimal = []
    Fy_hot = []
    
    for alpha in alpha_array:
        forces_cold = tire.calculate_steady_state_forces(Fz, kappa, alpha, temp=40)
        forces_optimal = tire.calculate_steady_state_forces(Fz, kappa, alpha, temp=85)
        forces_hot = tire.calculate_steady_state_forces(Fz, kappa, alpha, temp=130)
        
        Fy_cold.append(forces_cold['Fy'])
        Fy_optimal.append(forces_optimal['Fy'])
        Fy_hot.append(forces_hot['Fy'])
    
    # Plot lateral force vs slip angle at different temperatures
    plt.figure(figsize=(10, 6))
    plt.plot(np.degrees(alpha_array), Fy_cold, 'b-', label='Cold (40°C)')
    plt.plot(np.degrees(alpha_array), Fy_optimal, 'g-', label='Optimal (85°C)')
    plt.plot(np.degrees(alpha_array), Fy_hot, 'r-', label='Hot (130°C)')
    plt.xlabel('Slip Angle [deg]')
    plt.ylabel('Lateral Force [N]')
    plt.title('Hoosier Racing Tire: Lateral Force vs Slip Angle')
    plt.grid(True)
    plt.legend()
    plt.show()
    
    # Example 2: Transient response to a step input in slip angle
    print("Example 2: Transient response to a step input in slip angle")
    
    # Simulation parameters
    Vx = 30.0  # Racing speed [m/s]
    dt = 0.01  # Time step [s]
    time_steps = 500  # Number of time steps
    
    # Arrays to store results
    time_array = np.linspace(0, dt*time_steps, time_steps)
    alpha_input = np.zeros(time_steps)
    alpha_transient = np.zeros(time_steps)
    Fy_transient = np.zeros(time_steps)
    temperature = np.zeros(time_steps)
    
    # Step input in slip angle at t = 1s
    step_time_index = int(1.0 / dt)
    alpha_input[step_time_index:] = 0.1  # 5.7 degrees
    
    # Reset tire transient state
    tire.reset_state()
    
    # Run simulation
    for i in range(time_steps):
        # Calculate slip velocities from slip angle
        alpha = alpha_input[i]
        Vsy = -Vx * math.tan(alpha)  # Lateral slip velocity
        Vsx = 0.0  # No longitudinal slip
        omega = Vx / tire.params['R_e']  # Wheel angular velocity for free rolling
        
        # Calculate transient slip
        transient_slip = tire.calculate_transient_slip(Vx, Vsx, Vsy, omega, 0.0, dt)
        alpha_transient[i] = transient_slip['alpha_prime']
        temperature[i] = transient_slip['temperature']
        
        # Calculate forces using transient slip
        forces = tire.calculate_steady_state_forces(Fz, transient_slip['kappa_prime'], 
                                                  transient_slip['alpha_prime'])
        Fy_transient[i] = forces['Fy']
    
    # Plot results
    plt.figure(figsize=(12, 10))
    
    plt.subplot(3, 1, 1)
    plt.plot(time_array, np.degrees(alpha_input), 'r-', label='Input Slip Angle')
    plt.plot(time_array, np.degrees(alpha_transient), 'b-', label='Transient Slip Angle')
    plt.xlabel('Time [s]')
    plt.ylabel('Slip Angle [deg]')
    plt.legend()
    plt.grid(True)
    
    plt.subplot(3, 1, 2)
    plt.plot(time_array, Fy_transient)
    plt.xlabel('Time [s]')
    plt.ylabel('Lateral Force [N]')
    plt.grid(True)
    
    plt.subplot(3, 1, 3)
    plt.plot(time_array, temperature)
    plt.xlabel('Time [s]')
    plt.ylabel('Tire Temperature [°C]')
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()

    # Example 3: Friction Ellipse - Combined Slip Performance
    print("Example 3: Friction Ellipse - Combined Slip Performance")
    
    # Define range of slip values
    kappa_range = np.linspace(-0.15, 0.15, 31)
    alpha_range = np.linspace(-0.15, 0.15, 31)
    
    # Create mesh grid for contour plot
    kappa_grid, alpha_grid = np.meshgrid(kappa_range, alpha_range)
    resultant_force = np.zeros_like(kappa_grid)
    
    # Calculate forces at each slip combination
    for i in range(len(alpha_range)):
        for j in range(len(kappa_range)):
            forces = tire.calculate_steady_state_forces(Fz, kappa_grid[i,j], alpha_grid[i,j], temp=85)
            resultant_force[i,j] = np.sqrt(forces['Fx']**2 + forces['Fy']**2)
    
    # Plot the combined slip results
    plt.figure(figsize=(10, 8))
    
    # Contour plot of resultant force
    contour = plt.contourf(kappa_grid, alpha_grid, resultant_force, 20, cmap='viridis')
    plt.colorbar(contour, label='Resultant Force [N]')
    
    # Add force vectors at selected points
    skip = 3
    for i in range(0, len(alpha_range), skip):
        for j in range(0, len(kappa_range), skip):
            forces = tire.calculate_steady_state_forces(Fz, kappa_grid[i,j], alpha_grid[i,j], temp=85)
            plt.arrow(kappa_grid[i,j], alpha_grid[i,j], 
                     forces['Fx']/20000, forces['Fy']/20000,  # Scale down forces for visualization
                     head_width=0.005, head_length=0.01, fc='white', ec='white', alpha=0.5)
    
    plt.xlabel('Longitudinal Slip κ [-]')
    plt.ylabel('Slip Angle α [rad]')
    plt.title('Friction Ellipse: Combined Slip Performance')
    plt.grid(True)
    plt.axis('equal')
    plt.tight_layout()
    plt.show()
    
    # Example 4: Effect of Load on Lateral Force Coefficient
    print("Example 4: Effect of Load on Lateral Force Coefficient")
    
    # Range of loads to evaluate
    loads = np.linspace(2000, 7000, 6)
    
    plt.figure(figsize=(10, 6))
    
    for load in loads:
        # Calculate lateral force at different slip angles for this load
        fy_values = []
        for alpha in alpha_array:
            forces = tire.calculate_steady_state_forces(load, 0.0, alpha, temp=85)
            fy_values.append(forces['Fy'] / load)  # Normalize by load to get coefficient
            
        plt.plot(np.degrees(alpha_array), fy_values, label=f'Fz = {load:.0f} N')
    
    plt.xlabel('Slip Angle [deg]')
    plt.ylabel('Lateral Force Coefficient (Fy/Fz) [-]')
    plt.title('Load Sensitivity: Effect on Lateral Force Coefficient')
    plt.legend()
    plt.grid(True)
    plt.show()

def straight_line():

# Example usage for acceleration capability analysis
    tire = MagicFormulaTire("test_tire")

# Straight line maximum acceleration
    straight_line_max = tire.calculate_max_longitudinal_force(4500)  # 4500N vertical load
    print(f"Maximum acceleration force: {straight_line_max['max_fx']:.1f} N at {straight_line_max['optimal_slip']:.3f} slip ratio")

# During cornering with 3 degrees slip angle
    cornering_max = tire.calculate_max_longitudinal_force(4500, alpha=math.radians(3))
    print(f"Maximum acceleration while cornering: {cornering_max['max_fx']:.1f} N ({cornering_max['available_percentage']:.1f}% of straight line capability)")

# On a hot track
    hot_condition_max = tire.calculate_max_longitudinal_force(4500, temp=110)
    print(f"Maximum acceleration on hot track: {hot_condition_max['max_fx']:.1f} N")

if __name__ == "__main__":
    demonstration()
    # straight_line()

