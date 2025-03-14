# tire_class.py
from magic_formula_tire import MagicFormulaTire


class Tire:
    def __init__(self, magic_formula_tire, position, radius, inertia):
        self.mf_tire = magic_formula_tire
        self.position = position
        self.radius = radius
        self.inertia = inertia
        self.state = {
            'angular_velocity': 0.0,
            'slip_ratio': 0.0,
            'slip_angle': 0.0,
            'Fz': 0.0,
            'Vx': 0.0,
            'Fx': 0.0,
            'Fy': 0.0,
            'Mz': 0.0
        }

    def update(self, F_input, tire_angle, Fz, Vx, dt):
        """
        Update the tire state based on inputs.
        
        Args:
            F_input: Braking/acceleration force (N)
            tire_angle: Tire angle (rad)
            Fz: Vertical load (N)
            Vx: Longitudinal velocity (m/s)
            dt: Time step (s)
        """
        # Update state variables
        self.state['Fz'] = Fz
        self.state['Vx'] = Vx

        # Calculate angular velocity
        omega_dot = F_input * self.radius / self.inertia
        self.state['angular_velocity'] += omega_dot * dt

        # Calculate slip ratio
        omega = self.state['angular_velocity']
        re = self.mf_tire.params['R_e']
        self.state['slip_ratio'] = (omega * re - Vx) / Vx if abs(Vx) > 0.01 else 0.0

        # Calculate slip angle
        self.state['slip_angle'] = tire_angle

        # Calculate forces and moments using Magic Formula
        forces = self.mf_tire.calculate_steady_state_forces(
            Fz, self.state['slip_ratio'], self.state['slip_angle']
        )
        self.state['Fx'] = forces['Fx']
        self.state['Fy'] = forces['Fy']
        self.state['Mz'] = forces['Mz']

    def get_forces(self):
        """
        Get the current forces and moments.
        
        Returns:
            Dictionary containing Fx, Fy, Mz
        """
        return {
            'Fx': self.state['Fx'],
            'Fy': self.state['Fy'],
            'Mz': self.state['Mz']
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


if __name__ == "__main__":
    
# Create the Magic Formula tire model
    mf_tire = MagicFormulaTire("Racing Tire")

# Create the tire object
    tire = Tire(mf_tire, position="front_left", radius=0.33, inertia=1.5)

# Simulate a braking event
    F_input = -2000  # Braking force (N)
    tire_angle = 0.1  # Tire angle (rad)
    Fz = 4000        # Vertical load (N)
    Vx = 30          # Longitudinal velocity (m/s)
    dt = 0.01        # Time step (s)

# Update the tire state
    tire.update(F_input, tire_angle, Fz, Vx, dt)

# Get the resulting forces and moments
    forces = tire.get_forces()
    print("Forces and Moments:", forces)

# Get the slip ratio and slip angle
    slip = tire.get_slip()
    print("Slip Ratio and Angle:", slip)




