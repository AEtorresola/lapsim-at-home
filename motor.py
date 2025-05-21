# motor.py
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from scipy import interpolate

class MotorCharacteristics(ABC):
    """
    Abstract base class for motor characteristics.
    """
    @abstractmethod
    def request_torque(self, rpm, requested_torque, timestep):
        """
        Requests a specific torque at a given RPM and timestep.

        Args:
            rpm: The motor's RPM (revolutions per minute).
            requested_torque: The requested torque in Newton-meters (Nm).
            timestep: The current time in seconds.

        Returns:
            The actual torque provided by the motor in Newton-meters (Nm).
        """
        pass

class ElectricMotorCharacteristics(MotorCharacteristics):
    """
    Represents the torque characteristics of an electric motor with continuous
    and peak torque curves.
    """
    def __init__(
        self, 
        continuous_torque_curve, 
        peak_torque_curve, 
        drivetrain_loss_percent=0, 
        timestep_delta=0.1
    ):
        """
        Initializes an ElectricMotorCharacteristics object.

        Args:
            continuous_torque_curve: A list of (RPM, Torque) tuples representing 
                                    the motor's continuous torque curve.
            peak_torque_curve: A list of (RPM, Torque) tuples representing the 
                              motor's peak torque curve.
            drivetrain_loss_percent: Percentage of torque lost in the drivetrain (default: 0).
            timestep_delta: Time interval between measurements in seconds (default: 0.1).
        """
        self.continuous_torque_curve = continuous_torque_curve
        self.peak_torque_curve = peak_torque_curve
        self.drivetrain_loss_percent = drivetrain_loss_percent
        self.timestep_delta = timestep_delta
        
        # Create interpolation functions for both curves
        self._create_interpolation_functions()
        
        # Initialize usage tracking dataframe
        self.usage_df = pd.DataFrame(columns=['torque', 'rpm', 'is_continuous'])
        self.last_timestep = None

    def _create_interpolation_functions(self):
        """
        Creates interpolation functions for continuous and peak torque curves.
        """
        cont_rpm, cont_torque = zip(*self.continuous_torque_curve)
        peak_rpm, peak_torque = zip(*self.peak_torque_curve)
        
        # Create interpolation functions
        self.continuous_interp = interpolate.interp1d(
            cont_rpm, 
            cont_torque, 
            bounds_error=False, 
            fill_value=(cont_torque[0], cont_torque[-1])
        )
        
        self.peak_interp = interpolate.interp1d(
            peak_rpm, 
            peak_torque, 
            bounds_error=False, 
            fill_value=(peak_torque[0], peak_torque[-1])
        )
        
        # Store rpm ranges
        self.min_rpm = min(min(cont_rpm), min(peak_rpm))
        self.max_rpm = max(max(cont_rpm), max(peak_rpm))

    def calculate_continuous_torque(self, rpm):
        """
        Calculates the continuous torque available at a given RPM.
        
        Args:
            rpm: The motor's RPM
            
        Returns:
            The continuous torque available in Newton-meters (Nm)
        """
        if rpm < self.min_rpm or rpm > self.max_rpm:
            return 0
        return float(self.continuous_interp(rpm))

    def calculate_peak_torque(self, rpm):
        """
        Calculates the peak torque available at a given RPM.
        
        Args:
            rpm: The motor's RPM
            
        Returns:
            The peak torque available in Newton-meters (Nm)
        """
        if rpm < self.min_rpm or rpm > self.max_rpm:
            return 0
        return float(self.peak_interp(rpm))

    def request_torque(self, rpm, requested_torque, timestep):
        """
        Requests a specific torque at a given RPM and timestep.

        Args:
            rpm: The motor's RPM (revolutions per minute).
            requested_torque: The requested torque at the wheels in Newton-meters (Nm).
            timestep: The current time in seconds.

        Returns:
            The actual torque delivered to the wheels in Newton-meters (Nm).
        """
        # Calculate motor torque needed to overcome drivetrain losses
        motor_torque_required = requested_torque / (1 - self.drivetrain_loss_percent/100)
        
        # Determine maximum available torque at this RPM
        max_available_torque = self.calculate_peak_torque(rpm)
        
        # The actual torque is the minimum of what was requested and what's available
        actual_motor_torque = min(motor_torque_required, max_available_torque)

        # Check to see if the torque is in the continuous or peak range; 
        torque_continuous = self.calculate_continuous_torque(rpm)>actual_motor_torque

        
        # Fill in any missing timesteps with zeros
        self._fill_missing_timesteps(timestep)
        
        # Record this torque request
        self.usage_df.loc[timestep] = [actual_motor_torque, rpm, torque_continuous]
        self.last_timestep = timestep
        
        # Return the torque that will be delivered to the wheels
        wheel_torque = actual_motor_torque * (1 - self.drivetrain_loss_percent/100)
        return wheel_torque

    def _fill_missing_timesteps(self, current_timestep):
        """
        Fills in any missing timesteps with zero torque and rpm.
        
        Args:
            current_timestep: The current timestep.
        """
        if self.last_timestep is None:
            # First entry, nothing to fill
            return
            
        # Calculate expected timesteps
        expected_steps = np.arange(
            self.last_timestep + self.timestep_delta, 
            current_timestep, 
            self.timestep_delta
        )
        
        # Fill in zeros for any missing timesteps
        for step in expected_steps:
            if step not in self.usage_df.index:
                self.usage_df.loc[step] = [0, 0]

class CombustionMotorCharacteristics(MotorCharacteristics):
    """
    Represents the torque characteristics of a combustion engine.
    """
    def __init__(self, torque_curve, drivetrain_loss_percent=0, timestep_delta=0.1):
        """
        Initializes a CombustionMotorCharacteristics object.

        Args:
            torque_curve: A list of (RPM, Torque) tuples representing the engine's torque curve.
            drivetrain_loss_percent: Percentage of torque lost in the drivetrain (default: 0).
            timestep_delta: Time interval between measurements in seconds (default: 0.1).
        """
        self.torque_curve = torque_curve
        self.drivetrain_loss_percent = drivetrain_loss_percent
        self.timestep_delta = timestep_delta
        
        # Create interpolation function
        self._create_interpolation_function()
        
        # Initialize usage tracking dataframe
        self.usage_df = pd.DataFrame(columns=['torque', 'rpm'])
        self.last_timestep = None

    def _create_interpolation_function(self):
        """
        Creates an interpolation function for the torque curve.
        """
        rpm, torque = zip(*self.torque_curve)
        
        # Create interpolation function
        self.torque_interp = interpolate.interp1d(
            rpm, 
            torque, 
            bounds_error=False, 
            fill_value=(0, 0)
        )
        
        # Store rpm range
        self.min_rpm = min(rpm)
        self.max_rpm = max(rpm)

    def calculate_torque(self, rpm):
        """
        Calculates the torque available at a given RPM.
        
        Args:
            rpm: The engine's RPM
            
        Returns:
            The torque available in Newton-meters (Nm)
        """
        if rpm < self.min_rpm or rpm > self.max_rpm:
            return 0
        return float(self.torque_interp(rpm))

    def request_torque(self, rpm, requested_torque, timestep):
        """
        Requests a specific torque at a given RPM and timestep.

        Args:
            rpm: The engine's RPM (revolutions per minute).
            requested_torque: The requested torque at the wheels in Newton-meters (Nm).
            timestep: The current time in seconds.

        Returns:
            The actual torque delivered to the wheels in Newton-meters (Nm).
        """
        # Calculate engine torque needed to overcome drivetrain losses
        engine_torque_required = requested_torque / (1 - self.drivetrain_loss_percent/100)
        
        # Determine maximum available torque at this RPM
        max_available_torque = self.calculate_torque(rpm)
        
        # The actual torque is the minimum of what was requested and what's available
        actual_engine_torque = min(engine_torque_required, max_available_torque)
        
        # Fill in any missing timesteps with zeros
        self._fill_missing_timesteps(timestep)
        
        # Record this torque request
        self.usage_df.loc[timestep] = [actual_engine_torque, rpm]
        self.last_timestep = timestep
        
        # Return the torque that will be delivered to the wheels
        wheel_torque = actual_engine_torque * (1 - self.drivetrain_loss_percent/100)
        return wheel_torque

    def _fill_missing_timesteps(self, current_timestep):
        """
        Fills in any missing timesteps with zero torque and rpm.
        
        Args:
            current_timestep: The current timestep.
        """
        if self.last_timestep is None:
            # First entry, nothing to fill
            return
            
        # Calculate expected timesteps
        expected_steps = np.arange(
            self.last_timestep + self.timestep_delta, 
            current_timestep, 
            self.timestep_delta
        )
        
        # Fill in zeros for any missing timesteps
        for step in expected_steps:
            if step not in self.usage_df.index:
                self.usage_df.loc[step] = [0, 0]

