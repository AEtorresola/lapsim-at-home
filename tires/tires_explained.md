# Magic Formula Tire Model for Racing Applications

This document provides a guide to using the simplified Magic Formula tire model for racing tires like Hoosier.

## How the Racing Tire Model Works

The Magic Formula tire model has been adapted for racing tires, focusing on essential parameters while adding temperature and wear modeling critical for racing applications. This model remains semi-empirical but has been streamlined for better usability with racing tires.

### Key Concepts

- **Longitudinal Slip (κ)**: The difference between the tire's rolling speed and its actual speed.

$κ = (Ω * r_e - V_x) / V_x$

where `Ω` is the wheel's angular velocity, `r_e` is the effective rolling radius, and `V_x` is the longitudinal velocity.

- **Lateral Slip (α)**: The angle between the tire's heading and its direction of travel.

$α = atan(-V_y / V_x)$

where `V_y` is the lateral velocity.

- **Simplified Magic Formula Equation**: The core equation remains:

$y(x) = D * sin(C * atan(B * x - E * (B * x - atan(B * x)))))$

where `y` is the force/moment, `x` is the slip, and `B`, `C`, `D`, `E` are coefficients that shape the curve.

- **Temperature Effects**: Racing tires are highly temperature dependent, with performance following a bell curve centered on the optimal operating temperature.

- **Wear Modeling**: The model tracks tire wear based on slip energy, affecting long-term performance.

- **Transient Slip**: The Single Contact Point transient model calculates dynamic slip behavior.

### Racing Tire-Specific Features

- **Temperature Sensitivity**: Peak grip occurs at optimal temperature (~85°C for many racing tires)
- **Higher Friction Coefficients**: Racing tires have significantly higher peak friction
- **Quicker Response**: Racing tires have higher stiffness values and shorter relaxation lengths
- **Load Sensitivity**: Reduced grip coefficient at higher loads (typical for racing tires)
- **Combined Slip Performance**: Optimized friction ellipse modeling

## How to Use the Racing Tire Model

Here's how to use the `MagicFormulaTire` class for racing simulations:

1. **Import the Class**:
  ```python
  from simplified_magic_formula_tire import MagicFormulaTire
  ```

2. **Create a Tire Instance**:
  ```python
  tire = MagicFormulaTire(tire_file_path="path/to/your/hoosier.tire")  # Load from file
  # or
  tire = MagicFormulaTire()  # Use default racing tire parameters
  ```

3. **At Each Time Step**:
  - Provide the current state of the vehicle (velocities, wheel rotations, etc.).
  - Calculate the slip velocities.
  - Use the `calculate_transient_slip()` method to compute transient slip quantities.
  - Use the `calculate_steady_state_forces()` method to compute forces and moments.
  - Access temperature and wear information.
  
  ```python
  # Example
  Vx = 30.0  # Racing speed [m/s]
  Vsy = -1.5  # Lateral slip velocity [m/s]
  Vsx = 0.0  # Longitudinal slip velocity [m/s]
  omega = Vx / tire.params['R_e']  # Wheel angular velocity [rad/s]
  Fz = 4500  # Normal load [N]
  dt = 0.01  # Time step [s]

  # Calculate transient slip (includes temperature and wear updates)
  transient_slip = tire.calculate_transient_slip(Vx, Vsx, Vsy, omega, 0.0, dt)
  
  # Get forces with temperature effects automatically included
  forces = tire.calculate_steady_state_forces(Fz, 
                                              transient_slip['kappa_prime'],
                                              transient_slip['alpha_prime'])

  # Access the calculated values
  Fx = forces['Fx']
  Fy = forces['Fy']
  Mz = forces['Mz']
  current_temp = transient_slip['temperature']
  current_wear = transient_slip['wear']

  # Apply forces to your vehicle model
  ```

4. **Reset the Tire State**:
  For a new simulation, reset the tire state:
  ```python
  tire.reset_state()  # Resets deflections, temperature, and wear
  ```

5. **Loading Hoosier-Specific Parameters**:
  Create a simple file with the key parameters for your specific Hoosier tire:
  ```
  % Simplified Hoosier Racing Tire File
  % Based on available data for typical racing tires
  
  R_0 = 0.330       % unloaded tire radius [m]
  R_e = 0.315       % effective rolling radius [m]
  C_Fx = 500000     % longitudinal tire stiffness [N]
  C_Fy = 180000     % lateral tire stiffness [N]
  p_Dx1 = 1.35      % peak longitudinal friction
  p_Dy1 = -1.1      % peak lateral friction
  temp_opt = 85.0   % optimal operating temperature [°C]
  ```

## Racing Tire Temperature and Wear

The model includes simplified thermal modeling where:
- Temperature increases with slip energy (how much the tire is sliding)
- Temperature affects grip following a bell curve around the optimal temperature
- Highest grip is achieved within the optimal temperature window
- Tire performance degrades with wear accumulation

This behavior matches the typical thermal characteristics of Hoosier and other racing tires, where getting the tire into the optimal temperature window is critical for maximum performance.

## Combined Slip Performance

Racing tires exhibit a complex friction ellipse under combined longitudinal and lateral slip conditions. The model simulates this by applying weighting functions that reduce peak forces under combined slip conditions, creating the characteristic friction ellipse of racing tires.

The model is particularly useful for:
- Racing simulations requiring realistic tire behavior
- Driver training and race strategy optimization
- Lap time optimization and racing line analysis
- Understanding tire temperature effects during a race stint
