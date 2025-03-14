# enhanced_tire.py
import numpy as np
from magic_formula_tire import MagicFormulaTire

class EnhancedTire:
    def __init__(self, magic_formula_tire, position, radius, inertia, smoothing_factor=0.2):
        """
        Enhanced tire model with force allocation and smoothing capabilities.
        
        Args:
            magic_formula_tire: MagicFormulaTire instance
            position: Tire position (e.g., "front_left")
            radius: Tire radius (m)
            inertia: Tire rotational inertia (kg·m²)
            smoothing_factor: Factor for smoothing force transitions (0-1)
        """
        self.mf_tire = magic_formula_tire
        self.position = position
        self.radius = radius
        self.inertia = inertia
        self.smoothing_factor = smoothing_factor
        
        # Initialize state dictionary
        self.state = {
            'angular_velocity': 0.0,
            'slip_ratio': 0.0,
            'slip_angle': 0.0,
            'Fz': 0.0,
            'Vx': 0.0,
            'Fx': 0.0,
            'Fy': 0.0,
            'Mz': 0.0,
            'max_Fx': 0.0,        # Maximum available longitudinal force
            'desired_Fx': 0.0,    # Desired longitudinal force
            'desired_Fy': 0.0,    # Desired lateral force
            'previous_Fx': 0.0,   # Previous longitudinal force (for smoothing)
            'previous_Fy': 0.0    # Previous lateral force (for smoothing)
        }
        
        # Check if lookup table has been generated
        if not self.mf_tire.lookup_table_generated:
            # Default lookup table generation with reasonable ranges
            Fz_values = np.array([4000])  # Single vertical load for now
            Fx_values = np.linspace(-5000, 5000, 21)  # Longitudinal force range
            Fy_values = np.linspace(-5000, 5000, 21)  # Lateral force range
            self.mf_tire.generate_force_to_slip_table(Fz_values, Fx_values, Fy_values)

    def _smooth_force(self, desired_force, previous_force, dt):
        """
        Apply smoothing to force transitions to avoid abrupt changes.
        
        Args:
            desired_force: Target force value (N)
            previous_force: Previous force value (N)
            dt: Time step (s)
            
        Returns:
            Smoothed force value
        """
        # Simple exponential smoothing
        alpha = min(1.0, self.smoothing_factor / dt)  # Scale by dt for time-consistent behavior
        return previous_force + alpha * (desired_force - previous_force)
    
    def allocate_forces(self, Fy_desired, Fz, Vx, longitudinal_mode, target_speed=None, current_speed=None, speed_buffer=1.0, dt=0.01):
        """
        Allocate forces based on desired lateral force, velocity profile, and tire limits.
        
        Args:
            Fy_desired: Desired lateral force (N)
            Fz: Vertical load (N)
            Vx: Longitudinal velocity (m/s)
            longitudinal_mode: One of "accelerate", "brake", "maintain", or "match_speed"
            target_speed: Target speed from velocity profile (m/s), required if mode is "match_speed"
            current_speed: Current vehicle speed (m/s), required if mode is "match_speed"
            speed_buffer: Allowed deviation from target speed (m/s)
            dt: Time step (s)
            
        Returns:
            Dictionary with allocated forces and slip values
        """
        # Store the desired lateral force
        self.state['desired_Fy'] = Fy_desired
        
        # Apply smoothing to lateral force transition
        smoothed_Fy = self._smooth_force(Fy_desired, self.state['previous_Fy'], dt)
        
        # Calculate maximum available longitudinal force given the desired lateral force
        # First, we need to estimate the slip angle that would produce this lateral force
        estimated_slip_angle = 0.0
        if self.mf_tire.lookup_table_generated:
            # Use lookup table to find slip angle for this lateral force
            try:
                point = np.array([[0.0, smoothed_Fy]])  # Assume no longitudinal force for initial estimate
                estimated_slip_angle = float(self.mf_tire.alpha_interp(point)[0])
            except Exception as e:
                print(f"Warning: Error in slip angle interpolation: {e}")
        
        # Calculate maximum available longitudinal force
        max_fx_info = self.mf_tire.calculate_max_longitudinal_force(
            Fz, estimated_slip_angle)
        self.state['max_Fx'] = max_fx_info['max_fx']
        
        # Determine desired longitudinal force based on mode
        Fx_desired = 0.0
        
        if longitudinal_mode == "accelerate":
            # Use maximum available acceleration
            Fx_desired = self.state['max_Fx']
        elif longitudinal_mode == "brake":
            # Use maximum available braking (negative force)
            Fx_desired = -self.state['max_Fx']
        elif longitudinal_mode == "maintain":
            # No longitudinal force (coasting)
            Fx_desired = 0.0
        elif longitudinal_mode == "match_speed":
            if target_speed is None or current_speed is None:
                raise ValueError("Target and current speed required for match_speed mode")
            
            # Determine if we need to accelerate, brake, or maintain
            if current_speed < target_speed - speed_buffer:
                # Accelerate
                accel_factor = min(1.0, (target_speed - current_speed) / speed_buffer)
                Fx_desired = self.state['max_Fx'] * accel_factor
            elif current_speed > target_speed + speed_buffer:
                # Brake
                brake_factor = min(1.0, (current_speed - target_speed) / speed_buffer)
                Fx_desired = -self.state['max_Fx'] * brake_factor
            else:
                # Within buffer, maintain speed
                Fx_desired = 0.0
        else:
            raise ValueError(f"Unknown longitudinal mode: {longitudinal_mode}")
        
        # Store the desired longitudinal force
        self.state['desired_Fx'] = Fx_desired
        
        # Apply smoothing to longitudinal force transition
        smoothed_Fx = self._smooth_force(Fx_desired, self.state['previous_Fx'], dt)
        
        # Ensure we don't exceed the maximum available longitudinal force
        if abs(smoothed_Fx) > abs(self.state['max_Fx']):
            smoothed_Fx = np.sign(smoothed_Fx) * abs(self.state['max_Fx'])
            
        # Update the tire with the allocated forces
        self.update(smoothed_Fx, smoothed_Fy, Fz, Vx, dt)
        
        # Store current forces as previous for next iteration
        self.state['previous_Fx'] = self.state['Fx']
        self.state['previous_Fy'] = self.state['Fy']
        
        # Return the allocated forces and slip values
        return {
            'Fx': self.state['Fx'],
            'Fy': self.state['Fy'],
            'max_Fx': self.state['max_Fx'],
            'slip_ratio': self.state['slip_ratio'],
            'slip_angle': self.state['slip_angle']
        }
    
    def update(self, Fx_desired, Fy_desired, Fz, Vx, dt):
        """
        Update the tire state based on desired forces and conditions.
        
        Args:
            Fx_desired: Desired longitudinal force (N)
            Fy_desired: Desired lateral force (N)
            Fz: Vertical load (N)
            Vx: Longitudinal velocity (m/s)
            dt: Time step (s)
        """
        # Update state variables
        self.state['Fz'] = Fz
        self.state['Vx'] = Vx
        
        # Get slip ratios and angles from the lookup table
        if self.mf_tire.lookup_table_generated:
            point = np.array([[Fx_desired, Fy_desired]])
            try:
                kappa = float(self.mf_tire.kappa_interp(point)[0])
                alpha = float(self.mf_tire.alpha_interp(point)[0])
                
                # Calculate forces and moments using Magic Formula with the determined slip values
                forces = self.mf_tire.calculate_steady_state_forces(Fz, kappa, alpha)
                
                # Update the state with the calculated forces and slip values
                self.state['Fx'] = forces['Fx']
                self.state['Fy'] = forces['Fy']
                self.state['Mz'] = forces['Mz']
                self.state['slip_ratio'] = kappa
                self.state['slip_angle'] = alpha
            except Exception as e:
                print(f"Warning: Error in slip interpolation: {e}")
                # Fall back to direct calculation
                direct_forces = self.mf_tire.calculate_steady_state_forces(Fz, self.state['slip_ratio'], self.state['slip_angle'])
                self.state['Fx'] = direct_forces['Fx']
                self.state['Fy'] = direct_forces['Fy']
                self.state['Mz'] = direct_forces['Mz']
        else:
            # If lookup table is not available, use current slip values
            # This is not ideal, but better than failing
            direct_forces = self.mf_tire.calculate_steady_state_forces(Fz, self.state['slip_ratio'], self.state['slip_angle'])
            self.state['Fx'] = direct_forces['Fx']
            self.state['Fy'] = direct_forces['Fy']
            self.state['Mz'] = direct_forces['Mz']
        
        # Update wheel dynamics based on resulting forces
        # Calculate torque on the wheel (T = Fx * r)
        wheel_torque = self.state['Fx'] * self.radius
        
        # Calculate angular acceleration (α = T / I)
        angular_acceleration = wheel_torque / self.inertia
        
        # Update angular velocity (ω = ω₀ + α * dt)
        self.state['angular_velocity'] += angular_acceleration * dt    

    def get_forces(self):
        """
        Get the current forces and moments.
        
        Returns:
            Dictionary containing Fx, Fy, Mz, max_Fx
        """
        return {
            'Fx': self.state['Fx'],
            'Fy': self.state['Fy'],
            'Mz': self.state['Mz'],
            'max_Fx': self.state['max_Fx'],
            'desired_Fx': self.state['desired_Fx'],
            'desired_Fy': self.state['desired_Fy']
        }

    def get_slip(self):
        """
        Get the current slip ratio and slip angle.
        
        Returns:
            Dictionary containing slip ratio and slip angle
        """
        return {
            'slip_ratio': self.state['slip_ratio'],
            'slip_angle': self.state['slip_angle']
        }

    def get_wheel_state(self):
        """
        Get the current wheel state.
        
        Returns:
            Dictionary containing angular velocity
        """
        return {
            'angular_velocity': self.state['angular_velocity'],
            'radius': self.radius
        }

# velocity_profile.py
import numpy as np

class VelocityProfile:
    """
    Class to represent a velocity profile for a track.
    The actual implementation will be added later.
    """
    def __init__(self, track_data=None):
        """
        Initialize the velocity profile.
        
        Args:
            track_data: Data describing the track (will be implemented later)
        """
        self.track_data = track_data
        self.profile = None  # Will hold the velocity profile data
    
    def get_target_speed(self, position, direction=None):
        """
        Get the target speed at a specific position on the track.
        
        Args:
            position: Position along the track (m) or (x, y) coordinates
            direction: Optional direction vector for the car
            
        Returns:
            Target speed (m/s)
        """
        # This is a placeholder implementation
        # Will be replaced with actual calculation based on track curvature and tire grip
        if self.profile is not None:
            # If we have a profile, do a simple lookup or interpolation
            return self.profile.get(position, 30.0)  # Default to 30 m/s if not found
        else:
            # Return a default value for now
            return 30.0
    
    def calculate_profile(self, vehicle_params, tire_model):
        """
        Calculate the velocity profile for the track based on vehicle parameters and tire model.
        This method will be implemented later.
        
        Args:
            vehicle_params: Vehicle parameters (mass, dimensions, etc.)
            tire_model: Tire model to use for grip calculations
            
        Returns:
            None (updates self.profile)
        """
        # Placeholder implementation
        self.profile = {}  # Will be a mapping from position to speed
        print("Velocity profile calculation will be implemented later.")

