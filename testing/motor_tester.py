# Import the motor classes
from motor import ElectricMotorCharacteristics, CombustionMotorCharacteristics


# Example 1: Electric Motor
# Define the torque curves as (RPM, Torque) tuples

peak_power_curve = [
    (0, 0),      # 0 kW at 0 RPM
    (1000, 10),  # 10 kW at 1000 RPM
    (2000, 27),  # 27 kW at 2000 RPM 
    (3000, 42),  # 42 kW at 3000 RPM
    (4000, 53),  # 53 kW at 4000 RPM
    (5000, 62),  # 62 kW at 5000 RPM
    (6000, 68)   # 68 kW at 6000 RPM
]

peak_torque_curve = [
    (0, 140),    # 140 Nm at 0 RPM
    (1000, 138), # 138 Nm at 1000 RPM
    (2000, 136), # 136 Nm at 2000 RPM
    (3000, 133), # 133 Nm at 3000 RPM
    (4000, 130), # 130 Nm at 4000 RPM
    (5000, 125), # 125 Nm at 5000 RPM
    (6000, 120)  # 120 Nm at 6000 RPM
]

continuous_power_curve = [
    (0, 0),      # 0 kW at 0 RPM
    (1000, 5),   # 5 kW at 1000 RPM
    (2000, 13),  # 13 kW at 2000 RPM
    (3000, 21),  # 21 kW at 3000 RPM
    (4000, 28),  # 28 kW at 4000 RPM
    (5000, 32),  # 32 kW at 5000 RPM
    (6000, 35)   # 35 kW at 6000 RPM
]

continuous_torque_curve = [
    (0, 60),     # 60 Nm at 0 RPM
    (1000, 66),  # 66 Nm at 1000 RPM
    (2000, 67),  # 67 Nm at 2000 RPM
    (3000, 66),  # 66 Nm at 3000 RPM
    (4000, 64),  # 64 Nm at 4000 RPM
    (5000, 58),  # 58 Nm at 5000 RPM
    (6000, 55)   # 55 Nm at 6000 RPM
]


# Create the electric motor with 5% drivetrain losses
emrax_208 = ElectricMotorCharacteristics(
    continuous_torque_curve=continuous_torque_curve,
    peak_torque_curve=peak_torque_curve,
    drivetrain_loss_percent=5,
    timestep_delta=0.1
)


