# Tire Object for Racing Simulation

This document provides a guide to using the Tire class, which works with the Magic Formula tire model to store state information and historical data during simulations.

## How the Tire Object Works

The Tire class serves as a state container that works with the MagicFormulaTire model. While the Magic Formula model handles the physics calculations, the Tire object maintains the current state of the tire (slip angles, forces, velocities, etc.) and records a history of these values throughout the simulation. This separation allows for clean data management while leveraging the physics-based Magic Formula model.

### Key Concepts

- **State Management**: The Tire object maintains the current state of all relevant tire parameters in a single dictionary.

- **History Tracking**: All state changes are automatically recorded in a pandas DataFrame for later analysis.

- **Delegation Pattern**: The Tire object delegates physics calculations to the MagicFormulaTire model rather than implementing them directly.

- **Position Awareness**: Each tire knows its position on the vehicle (e.g., "front_left"), allowing for position-specific behavior.

- **Physical Properties**: Beyond just the parameters needed for the Magic Formula, the Tire object tracks physical properties like mass, width, and rotational inertia.

### Tire Object-Specific Features

- **State Continuity**: Maintains continuous state between time steps for realistic simulation
- **Data Logging**: Automatically logs all tire states for post-simulation analysis
- **Simplified API**: Provides a clean interface to the more complex Magic Formula calculations
- **Stateful Design**: Preserves the transient state between simulation steps
- **Easy Visualization**: The pandas DataFrame format makes plotting tire behavior straightforward

## How to Use the Tire Object

Here's how to use the `Tire` class in your racing simulations:

1. **First Create a Magic Formula Tire Model**:
  ```python
  from magic_formula_tire import MagicFormulaTire
  
  # Create the tire model that handles physics calculations
  mf_tire = MagicFormulaTire("Racing Tire")
  ```

2. **Create a Tire Instance**:
  ```python
  from tire import Tire
  
  # Create the tire object that will store state
  tire = Tire(
      magic_formula_tire=mf_tire,
      position="front_left",
      initial_radius=0.33,    # Optional: override default radius
      initial_width=0.225,    # Optional: specify tire width
      initial_mass=15.0,      # Optional: specify tire mass
      initial_inertia=1.5     # Optional: specify rotational inertia
  )
  ```

3. **During Each Simulation Step**:
  - Update the tire state with new vehicle dynamics information
  - Calculate forces based on the current state
  - Use the calculated forces in your vehicle dynamics model
  
  ```python
  # Example of a single simulation step
  dt = 0.01  # Time step [s]
  time = simulation_time
  
  # Update tire state with current vehicle dynamics
  tire.update_state(
      time=time,
      angular_velocity=wheel_speed,   # [rad/s]
      slip_angle=current_slip_angle,  # [rad]
      Fz=vertical_load,               # [N]
      Vx=longitudinal_velocity,       # [m/s]
      Vy=lateral_velocity             # [m/s]
  )
  
  # Calculate forces for this state (includes Magic Formula calculations)
  forces = tire.calculate_forces(dt)
  
  # Apply these forces to your vehicle dynamics model
  Fx = forces['Fx']  # Longitudinal force [N]
  Fy = forces['Fy']  # Lateral force [N]
  Mz = forces['Mz']  # Aligning moment [Nm]
  ```

4. **Accessing Tire History**:
  After simulation, access the complete tire history or specific variables:
  ```python
  # Get complete history
  full_history = tire.get_history()
  
  # Get specific variables
  forces_history = tire.get_history(['time', 'Fx', 'Fy', 'Fz'])
  
  # Plot results
  import matplotlib.pyplot as plt
  plt.figure(figsize=(10, 6))
  plt.plot(forces_history['time'], forces_history['Fx'])
  plt.xlabel('Time [s]')
  plt.ylabel('Longitudinal Force [N]')
  plt.title('Tire Longitudinal Force vs Time')
  plt.grid(True)
  plt.show()
  ```

5. **Calculating Optimal Slip**:
  Find the optimal slip ratio for maximum longitudinal force:
  ```python
  # Calculate optimal slip for current conditions
  optimal_slip_info = tire.calculate_optimal_slip()
  
  # Access optimal slip information
  optimal_slip_ratio = optimal_slip_info['optimal_slip']
  max_available_force = optimal_slip_info['max_fx']
  
  print(f"For maximum acceleration, target {optimal_slip_ratio:.3f} slip ratio")
  print(f"Maximum available force: {max_available_force:.1f} N")
  ```

6. **Resetting the Tire State**:
  For a new simulation run, reset the tire:
  ```python
  tire.reset()  # Resets state and clears history
  ```

## Example: Full Simulation Loop

```python
# Setup
mf_tire = MagicFormulaTire("Racing Tire")
tire = Tire(mf_tire, position="front_left")

# Simulation parameters
sim_time = 10.0  # seconds
dt = 0.01        # time step
steps = int(sim_time / dt)

# Simulation loop
for step in range(steps):
    time = step * dt
    
    # Example: Car accelerating from stop
    Vx = min(30.0, time * 3.0)  # Accelerate to 30 m/s 
    wheel_speed = (Vx + 1.0) / tire.radius  # Slight wheelspin
    
    # Update tire state
    tire.update_state(
        time=time,
        angular_velocity=wheel_speed,
        Fz=4000.0,  # Constant load for simplicity
        Vx=Vx,
        slip_angle=0.02  # Small constant slip angle
    )
    
    # Calculate forces
    forces = tire.calculate_forces(dt)
    
    # Print progress every second
    if step % 100 == 0:
        print(f"Time: {time:.1f}s, Vx: {Vx:.1f} m/s, Fx: {forces['Fx']:.1f} N")

# After simulation, analyze results
history = tire.get_history(['time', 'Vx', 'Fx', 'slip_ratio', 'temperature'])
```

## Integration with Vehicle Dynamics

The Tire object is designed to interface seamlessly with vehicle dynamics models:

1. **Vehicle Dynamics → Tire**: The vehicle model provides velocities, wheel speeds, and loads to the tire through `update_state()`

2. **Tire → Magic Formula**: The tire passes these inputs to the Magic Formula model through `calculate_forces()`

3. **Magic Formula → Tire**: The Magic Formula returns forces and moments which are stored in the tire's state

4. **Tire → Vehicle Dynamics**: The vehicle dynamics model reads these forces to update the vehicle's motion

This clean separation of concerns allows for modular development and testing of vehicle dynamics models.

## Data Analysis Capabilities

The Tire object's history tracking facilitates comprehensive post-simulation analysis:

- **Performance Analysis**: Track how tire forces evolve during maneuvers
- **Temperature Studies**: Analyze how tire temperature affects grip over a stint
- **Wear Modeling**: Study long-term tire degradation effects
- **Setup Optimization**: Compare different setup changes on tire performance

The pandas DataFrame format makes it easy to perform complex analyses and create visualizations to gain insights into tire behavior throughout your simulation.

## Question 

Yeah F_input should be the force I apply to the wheel. It doesnt necessarily have to be this, it could be a torque or something else. Regardless, the intention is to easily be able to apply a force to the tire that causes acceleration (elsewhere in the implementation though). I think the same applies to lateral force. I know the track, and i think in some other part of the code I will be calculating the required forces in order to turn the car at the rate the track requires. Using the forces then, I can see what the tire itself is able to provide, and at what slip angle for example. And then also how much I can do longitudinal acceleration at the same time (for in case i want to be doing both at the same time). 

I do think an inverse mapping would be better. If we can figure out a way, something ideal would be for this inverse mapping to be calculated as an "initial" part of the program that is then referenced as a lookup table (so it does not have to be calculated each time). Let me know how good we can make this, and what the pros and cons of it are. 

Lastly, no. I would like to use the magic formula as completely as possible. what i am looking to do is not necessarily simplify, but to convert my inputs into something that makes more sense and is more manageable with the current simulation. 

## NExt steps;

the tire model is a magic formula one. It does take into account tire wear and temperature but road conditions were overkill for me. 

Yes, I like that constraint optimization, that sounds good. 
The "requested lateral force" will be based on a given track. Depending on our discussions is how I will fully implement this. My first thought was just putting the car to go through tiny timesteps I will implement elsewhere. Throughout each of these time-steps, the car has to determine what combination of lateral loads it needs from the tire to reach the next point in the given timestep. Transitions are something I have been trying to think of. I think that ideally, we figure out a way to smoothly transition from one to the other, because fundamentally the purpose is to create the fastest possible lap.  However, both of these parts specifically are what I am most unsure about since getting the lateral force really is one of the most important things to determine, and if its not the right direction Id like to figure that out sooner rather than later. 

The outputs are correct. I mostly just want to be able to know what my tire needs in order to provide what I need (in terms of forces). The validation for now is not too much. For all of this, I am currently using the magic tire formula implementation in a script. I simply want to add an extra layer of abstraction to simplify it for the script even more (while maintaining it logically cohesive)

So, the acceleration threshold is a great question. One of the thoughts i had was to calculate a velocity profile for a track. This is so that for each segment of the track I can calculate the optimal speed it should be at. For straights there really isnt a limit, which is what causes the turns to limit it. I think my intention would be such that each time theres a 
