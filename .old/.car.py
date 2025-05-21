# car.py
import numpy as np
from abc import ABC, abstractmethod

class EngineCharacteristics(ABC):
    """
    Abstract base class for engine characteristics.
    """
    @abstractmethod
    def calculate_torque(self, rpm):
        """
        Calculates the engine torque at a given RPM.

        Args:
            rpm: The engine's RPM (revolutions per minute).

        Returns:
            The engine torque in Newton-meters (Nm).
        """
        pass

class ElectricEngineCharacteristics(EngineCharacteristics):
    """
    Represents the torque characteristics of an electric motor.
    """
    def __init__(self, torque_curve):
        """
        Initializes an ElectricEngineCharacteristics object.

        Args:
            torque_curve: A list of (RPM, Torque) tuples representing the motor's torque curve.
        """
        self.torque_curve = torque_curve

    def calculate_torque(self, rpm):
        """
        Calculates the motor torque based on the RPM and the torque curve using linear interpolation.
        """
        if rpm < self.torque_curve[0][0]:
            return 0  # Below minimum RPM

        for i in range(len(self.torque_curve) - 1):
            rpm_low, torque_low = self.torque_curve[i]
            rpm_high, torque_high = self.torque_curve[i+1]

            if rpm_low <= rpm <= rpm_high:
                # Linear interpolation
                torque = torque_low + (rpm - rpm_low) * (torque_high - torque_low) / (rpm_high - rpm_low)
                return torque

        return 0  # Above maximum RPM

class CombustionEngineCharacteristics(EngineCharacteristics):
    """
    Represents the torque characteristics of a combustion engine.
    (This is a simplified example and can be expanded with more complex models)
    """
    def __init__(self, peak_torque, rpm_at_peak_torque):
        """
        Initializes a CombustionEngineCharacteristics object.

        Args:
            peak_torque: The engine's peak torque (Nm).
            rpm_at_peak_torque: The RPM at which the engine produces peak torque.
        """
        self.peak_torque = peak_torque
        self.rpm_at_peak_torque = rpm_at_peak_torque

    def calculate_torque(self, rpm):
        """
        Calculates the engine torque based on a simplified combustion engine model.
        (This is a placeholder and can be replaced with a more accurate model)
        """
        # A simple parabolic approximation
        torque = self.peak_torque * (1 - ((rpm - self.rpm_at_peak_torque) / self.rpm_at_peak_torque)**2)
        return max(0, torque)  # Ensure torque is not negative

class Car:
    """
    Represents a vehicle with its physical and performance characteristics.
    """
    def __init__(self, mass, wheelbase, cg_front, cg_rear, cg_height, track_width, tire_radius, drag_coeff, downforce_coeff, frontal_area, rolling_resistance, tire_grip, engine_characteristics, gear_ratio, drivetrain_efficiency, braking_force_distribution):
        """
        Initializes a Car object.

        Args:
            mass: Mass of the car (kg).
            wheelbase: Distance between front and rear axles (m).
            cg_front: Distance from front axle to center of gravity (m).
            cg_rear: Distance from rear axle to center of gravity (m).
            cg_height: Height of the center of gravity (m).
            track_width: Distance between left and right wheels (m).
            tire_radius: Radius of the tires (m).
            drag_coeff: Coefficient of aerodynamic drag.
            downforce_coeff: Coefficient of aerodynamic downforce.
            frontal_area: Frontal area of the car (m^2).
            rolling_resistance: Rolling resistance coefficient.
            tire_grip: Tire grip coefficient.
            engine_characteristics: An EngineCharacteristics object representing the engine's torque characteristics.
            gear_ratio: Gear ratio of the drivetrain.
            drivetrain_efficiency: Efficiency of the drivetrain.
            braking_force_distribution: Braking force distribution factor (0 to 1, front bias).
        """
        self.mass = mass
        self.wheelbase = wheelbase
        self.cg_front = cg_front
        self.cg_rear = cg_rear
        self.cg_height = cg_height
        self.track_width = track_width
        self.tire_radius = tire_radius
        self.drag_coeff = drag_coeff
        self.downforce_coeff = downforce_coeff
        self.frontal_area = frontal_area
        self.rolling_resistance = rolling_resistance
        self.tire_grip = tire_grip
        self.engine_characteristics = engine_characteristics
        self.gear_ratio = gear_ratio
        self.drivetrain_efficiency = drivetrain_efficiency
        self.braking_force_distribution = braking_force_distribution

        # Driver inputs
        self.throttle_input = 0.0  # Throttle input (0.0 to 1.0)
        self.brake_input = 0.0      # Brake input (0.0 to 1.0)

    def set_driver_inputs(self, throttle, brake):
        """
        Sets the driver inputs for throttle and brake.

        Args:
            throttle: Throttle input (0.0 to 1.0).
            brake: Brake input (0.0 to 1.0).
        """
        self.throttle_input = throttle
        self.brake_input = brake

    def calculate_motor_torque(self, rpm):
        """
        Calculates the motor torque based on the RPM and the torque curve using linear interpolation.
        """
        if rpm < self.engine_characteristics.torque_curve[0][0]:
            return 0  # Below minimum RPM

        for i in range(len(self.engine_characteristics.torque_curve) - 1):
            rpm_low, torque_low = self.engine_characteristics.torque_curve[i]
            rpm_high, torque_high = self.engine_characteristics.torque_curve[i+1]

            if rpm_low <= rpm <= rpm_high:
                # Linear interpolation
                torque = torque_low + (rpm - rpm_low) * (torque_high - torque_low) / (rpm_high - rpm_low)
                return torque

        return 0  # Above maximum RPM

    def calculate_traction_force(self, velocity, acceleration):
        """
        Calculates the traction force based on motor torque, gear ratio, tire radius, and drivetrain efficiency,
        considering weight transfer and RWD configuration.
        """
        # Calculate normal force on rear tires with weight transfer
        Nr = (self.mass * 9.81 * self.cg_front / self.wheelbase) + (self.mass * acceleration * self.cg_height / self.wheelbase)
        
        # Calculate motor force at the wheels
        rpm = (velocity * self.gear_ratio * 60) / (2 * np.pi * self.tire_radius)
        motor_torque = self.engine_characteristics.calculate_torque(rpm)
        wheel_torque = motor_torque * self.gear_ratio
        motor_force = (wheel_torque * self.drivetrain_efficiency) / self.tire_radius

        # Limit traction force by tire grip and motor force
        traction_force = min(motor_force * self.throttle_input, self.tire_grip * Nr)
        return traction_force

    def calculate_brake_force(self, acceleration):
        """
        Calculates the braking force, considering weight transfer and braking force distribution.
        """
        # Calculate normal forces with weight transfer
        Nf = (self.mass * 9.81 * self.cg_rear / self.wheelbase) - (self.mass * acceleration * self.cg_height / self.wheelbase)
        Nr = (self.mass * 9.81 * self.cg_front / self.wheelbase) + (self.mass * acceleration * self.cg_height / self.wheelbase)

        # Calculate total braking force
        total_brake_force = self.brake_input * self.tire_grip * self.mass * 9.81

        # Distribute braking force
        braking_force_front = self.braking_force_distribution * total_brake_force
        braking_force_rear = (1 - self.braking_force_distribution) * total_brake_force

        # Limit braking force by tire grip
        braking_force_front = min(braking_force_front, self.tire_grip * Nf)
        braking_force_rear = min(braking_force_rear, self.tire_grip * Nr)

        return braking_force_front, braking_force_rear







