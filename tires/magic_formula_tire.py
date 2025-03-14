# magic_formula_tire.py
import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
import math
from scipy.interpolate import RegularGridInterpolator
from scipy.optimize import fsolve

class MagicFormulaTire:
    def __init__(self, tire_name, tire_file_path=None):
        # Simplified tire parameters for a racing tire (like Hoosier)
        self.tire_name = tire_name
        self.params = {
            # Tire dimensions
            'R_0': 0.330,  # unloaded tire radius [m]
            'R_e': 0.315,  # effective rolling radius [m]
            'F_z0': 4500,  # nominal load [N]
            'V_0': 30.0,   # reference velocity [m/s] (higher for race applications)
            
            # Tire stiffnesses
            'C_Fx': 500000,  # longitudinal tire stiffness [N]
            'C_Fy': 180000,  # lateral tire stiffness [N]
            
            # Longitudinal parameters (simplified)
            'p_Cx1': 1.65,  # shape factor
            'p_Dx1': 1.35,  # peak factor (higher for race tires = more grip)
            'p_Dx2': -0.1,  # load dependency of peak factor
            'p_Ex1': 0.5,   # curvature factor
            'p_Kx1': 25.0,  # longitudinal slip stiffness
            'p_Kx2': -0.2,  # load dependency of slip stiffness
            
            # Lateral parameters (simplified)
            'p_Cy1': 1.3,   # shape factor
            'p_Dy1': -1.1,  # peak factor
            'p_Dy2': -0.1,  # load dependency of peak factor
            'p_Ey1': -0.8,  # curvature factor
            'p_Ky1': 20.0,  # cornering stiffness factor
            'p_Ky2': 1.5,   # load at which cornering stiffness is maximum
            
            # Combined slip factors (simplified)
            'r_Bx1': 12.0,  # combined slip reduction factor for Fx
            'r_By1': 10.0,  # combined slip reduction factor for Fy
            
            # Temperature sensitivity - specific to racing tires
            'temp_opt': 85.0,     # optimal operating temperature [°C]
            'temp_range': 30.0,   # effective temperature range [°C]
            'grip_temp_factor': 0.2,  # grip reduction outside optimal temperature
            
            # Wear parameters - specific to racing tires
            'wear_constant': 0.0001,  # wear rate constant
            'wear_exponent': 2.0,     # wear rate sensitivity to slip
            
            # Scaling factors
            'lambda_mux': 1.2,  # higher grip for race tires
            'lambda_muy': 1.2   # higher grip for race tires
        }
        
        # Transient slip model parameters
        self.u = 0.0  # longitudinal carcass deflection
        self.v = 0.0  # lateral carcass deflection
        
        # Temperature and wear tracking
        self.temperature = 20.0  # initial temperature [°C]
        self.wear = 0.0          # initial wear [0-1]
        
        # Initialize tire parameters from file if provided
        if tire_file_path:
            self.load_tire_properties(tire_file_path)
        
        # Lookup table attributes
        self.lookup_table_generated = False
            
    def load_tire_properties(self, file_path):
        """Load tire properties from a .tire file or similar format."""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
                
            for line in lines:
                line = line.strip()
                if line.startswith('%') or not line:
                    continue  # Skip comments and empty lines
                    
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = float(value.strip())
                    if key in self.params:
                        self.params[key] = value
                        
            print(f"Loaded tire properties from {file_path}")
        except Exception as e:
            print(f"Error loading tire properties: {e}")
            
    def calculate_steady_state_forces(self, Fz, kappa, alpha, gamma=0, Vx=30, temp=None):
        """
        Calculate steady-state forces using a simplified Magic Formula.
        
        Args:
            Fz: Vertical load [N]
            kappa: Longitudinal slip ratio [-]
            alpha: Side slip angle [rad]
            gamma: Camber angle [rad]
            Vx: Longitudinal velocity [m/s]
            temp: Tire temperature [°C], if None uses internal temperature
            
        Returns:
            Dictionary containing forces and moments
        """
        # Use provided temperature or internal temperature
        if temp is None:
            temp = self.temperature
            
        # Calculate temperature effect on grip (bell curve)
        temp_effect = 1.0 - self.params['grip_temp_factor'] * (
            (temp - self.params['temp_opt'])**2 / (self.params['temp_range']**2))
        temp_effect = max(0.5, min(1.0, temp_effect))  # Limit reduction
        
        # Normalized vertical load
        Fz0 = self.params['F_z0']
        dfz = (Fz - Fz0) / Fz0
        
        # Pure longitudinal slip - calculate longitudinal force
        Fx0 = self._calculate_Fx0(kappa, Fz, dfz, temp_effect)
        
        # Pure lateral slip - calculate lateral force
        Fy0 = self._calculate_Fy0(alpha, Fz, dfz, gamma, temp_effect)
        
        # Combined slip effects
        Fx = self._calculate_Fx_combined(kappa, alpha, Fx0)
        Fy = self._calculate_Fy_combined(kappa, alpha, Fy0)
        
        # Calculate self-aligning moment (simplified)
        Mz = -0.05 * Fy * self.params['R_0']  # simplified pneumatic trail
        
        # Rolling resistance moment (simplified)
        My = -0.01 * Fz * self.params['R_e']
        
        # Overturning moment (simplified)
        Mx = Fz * gamma * 0.01
        
        return {
            'Fx': Fx,
            'Fy': Fy,
            'Fz': Fz,
            'Mx': Mx,
            'My': My,
            'Mz': Mz
        }
    
    def _calculate_Fx0(self, kappa, Fz, dfz, temp_effect):
        """Calculate pure longitudinal force Fx0 with simplified parameters."""
        p = self.params
        
        # Apply the Magic Formula with reduced parameter set
        B = p['p_Kx1'] * (1 + p['p_Kx2'] * dfz) * Fz / (p['p_Cx1'] * p['p_Dx1'] * Fz)
        C = p['p_Cx1']
        D = p['p_Dx1'] * Fz * (1 + p['p_Dx2'] * dfz) * p['lambda_mux'] * temp_effect
        E = p['p_Ex1']
        
        # Apply the Magic Formula equation
        Fx0 = D * math.sin(C * math.atan(B * kappa - E * (B * kappa - math.atan(B * kappa))))
        
        return Fx0
    
    def _calculate_Fy0(self, alpha, Fz, dfz, gamma, temp_effect):
        """Calculate pure lateral force Fy0 with simplified parameters."""
        p = self.params
        
        # Camber effect (simplified)
        gamma_effect = 0.1 * gamma  # Simple camber thrust component
        
        # Apply the Magic Formula with reduced parameter set
        B = p['p_Ky1'] * Fz / (p['p_Cy1'] * p['p_Dy1'] * Fz * p['p_Ky2'])
        C = p['p_Cy1']
        D = abs(p['p_Dy1']) * Fz * (1 + p['p_Dy2'] * dfz) * p['lambda_muy'] * temp_effect
        E = p['p_Ey1']
        
        # Apply the Magic Formula equation
        Fy0 = D * math.sin(C * math.atan(B * alpha - E * (B * alpha - math.atan(B * alpha)))) + gamma_effect * Fz
        
        return Fy0
    
    def _calculate_Fx_combined(self, kappa, alpha, Fx0):
        """Calculate combined longitudinal force with simplified approach."""
        # Simple cosine reduction of longitudinal force with slip angle
        reduction = math.cos(self.params['r_Bx1'] * abs(alpha))
        return Fx0 * reduction
    
    def _calculate_Fy_combined(self, kappa, alpha, Fy0):
        """Calculate combined lateral force with simplified approach."""
        # Simple cosine reduction of lateral force with slip ratio
        reduction = math.cos(self.params['r_By1'] * abs(kappa))
        return Fy0 * reduction
    
    def calculate_transient_slip(self, Vx, Vsx, Vsy, omega, gamma, dt):
        """
        Calculate transient slip using the Single Contact Point model.
        
        Args:
            Vx: Longitudinal velocity [m/s]
            Vsx: Longitudinal slip velocity [m/s]
            Vsy: Lateral slip velocity [m/s]
            omega: Wheel angular velocity [rad/s]
            gamma: Camber angle [rad]
            dt: Time step [s]
            
        Returns:
            Dictionary containing transient slip quantities
        """
        # Prevent division by zero in slip calculations
        Vx_abs = max(abs(Vx), 0.01)
        
        # Relaxation lengths based on vertical load
        sigma_kappa = self.params['C_Fx'] / (self.params['C_Fy'] * 2)  # longitudinal relaxation length
        sigma_alpha = self.params['C_Fy'] / (self.params['C_Fx'] * 2)  # lateral relaxation length
        
        # Calculate slip velocities
        kappa = -Vsx / Vx_abs  # Longitudinal slip ratio
        alpha = -math.atan2(Vsy, Vx_abs)  # Side slip angle
        
        # Update longitudinal deflection (u) using the differential equation
        u_dot = -Vx*self.u/sigma_kappa + Vx*kappa
        self.u += u_dot * dt
        
        # Update lateral deflection (v) using the differential equation
        v_dot = -Vx*self.v/sigma_alpha + Vx*math.tan(alpha)
        self.v += v_dot * dt
        
        # Calculate transient slip quantities
        kappa_prime = self.u / sigma_kappa
        alpha_prime = math.atan(self.v / sigma_alpha)
        gamma_prime = gamma  # Simplified assumption
        
        # Update temperature due to slip (simplified thermal model)
        slip_work = abs(Vsx * kappa) + abs(Vsy * alpha)
        temp_increase = slip_work * 0.001  # convert work to temperature increase
        self.temperature += temp_increase * dt - 0.1 * dt  # add cooling effect
        
        # Update wear based on slip (simplified wear model)
        wear_rate = self.params['wear_constant'] * (abs(kappa) + abs(alpha))**self.params['wear_exponent']
        self.wear += wear_rate * dt
        self.wear = min(1.0, self.wear)  # limit to 100%
        
        return {
            'kappa_prime': kappa_prime,
            'alpha_prime': alpha_prime,
            'gamma_prime': gamma_prime,
            'temperature': self.temperature,
            'wear': self.wear
        }
    
    def reset_state(self):
        """Reset the transient and state variables of the tire."""
        self.u = 0.0
        self.v = 0.0
        self.temperature = 20.0
        self.wear = 0.0

    def calculate_optimal_slip_ratio(self, Fz, alpha=0.0, gamma=0.0, temp=None):
        """
        Calculate the optimal slip ratio that provides maximum longitudinal force
        for the given conditions and store it in self.optimal_slip.
        
        Args:
            Fz: Vertical load [N]
            alpha: Side slip angle [rad], default 0
            gamma: Camber angle [rad], default 0
            temp: Tire temperature [°C], default None (uses internal temperature)
            
        Returns:
            Optimal slip ratio value
        """
        # Use provided temperature or internal temperature
        if temp is None:
            temp = self.temperature

        # Calculate normalized vertical load
        Fz0 = self.params['F_z0']
        dfz = (Fz - Fz0) / Fz0
        
        # Calculate temperature effect if needed
        temp_effect = 1.0
        if hasattr(self, 'params') and 'temp_opt' in self.params:
            temp_effect = 1.0 - self.params.get('grip_temp_factor', 0.2) * (
                (temp - self.params['temp_opt'])**2 / (self.params.get('temp_range', 30.0)**2))
            temp_effect = max(0.5, min(1.0, temp_effect))
        
        # Create a range of slip ratios to evaluate
        slip_ratios = np.linspace(0.01, 0.30, 50)  # 50 points between 1% and 30% slip
        
        # Calculate longitudinal force for each slip ratio
        forces = []
        for kappa in slip_ratios:
            # Calculate pure longitudinal force for this slip
            fx = self._calculate_Fx0(kappa, Fz, dfz, temp_effect)
            
            # Apply combined slip effects if there is nonzero slip angle
            if abs(alpha) > 1e-6:
                fx = self._calculate_Fx_combined(kappa, alpha, fx)
                
            forces.append(fx)
        
        # Find slip ratio with maximum force
        forces = np.array(forces)
        max_index = np.argmax(forces)
        optimal_slip = slip_ratios[max_index]
        
        # Store the optimal slip ratio
        self.optimal_slip = optimal_slip
        
        # Also store the maximum available force for reference
        self.max_available_fx = forces[max_index]
        
        return optimal_slip

    def calculate_max_longitudinal_force(self, Fz, alpha=0.0, gamma=0.0, temp=None):
        """
        Calculate the maximum longitudinal force available under the current conditions.
        
        Args:
            Fz: Vertical load [N]
            alpha: Current side slip angle [rad], default 0
            gamma: Current camber angle [rad], default 0
            temp: Current tire temperature [°C], default None (uses internal temperature)
            
        Returns:
            Dictionary containing maximum force information:
            - max_fx: Maximum longitudinal force [N]
            - optimal_slip: Slip ratio at which maximum force occurs
            - limited_by_lateral: Boolean indicating if max force is limited by lateral slip
        """
        # Use provided temperature or internal temperature
        if temp is None:
            temp = self.temperature

        # Calculate normalized vertical load
        Fz0 = self.params['F_z0']
        dfz = (Fz - Fz0) / Fz0
        
        # Calculate temperature effect
        temp_effect = 1.0
        if hasattr(self, 'params') and 'temp_opt' in self.params:
            temp_effect = 1.0 - self.params.get('grip_temp_factor', 0.2) * (
                (temp - self.params['temp_opt'])**2 / (self.params.get('temp_range', 30.0)**2))
            temp_effect = max(0.5, min(1.0, temp_effect))
        
        # Check if we have significant lateral slip that will affect longitudinal capacity
        lateral_limited = abs(alpha) > 0.01  # More than ~0.5 degrees slip angle
        
        # Find the optimal slip ratio for maximum force
        optimal_slip = self.calculate_optimal_slip_ratio(Fz, alpha, gamma, temp)
        
        # Calculate pure longitudinal force at optimal slip
        max_fx_pure = self._calculate_Fx0(optimal_slip, Fz, dfz, temp_effect)
        
        # Apply combined slip effects if there is lateral slip
        max_fx = max_fx_pure
        if lateral_limited:
            max_fx = self._calculate_Fx_combined(optimal_slip, alpha, max_fx_pure)
        
        # Calculate what percentage of maximum pure longitudinal force is available
        # This is useful to understand how much lateral slip is limiting longitudinal capacity
        percentage_available = 100.0 * max_fx / max_fx_pure if max_fx_pure > 0 else 0.0
        
        # Return comprehensive information about maximum longitudinal force
        return {
            'max_fx': max_fx,                  # Maximum available longitudinal force [N]
            'optimal_slip': optimal_slip,      # Slip ratio at which maximum force occurs
            'max_fx_pure': max_fx_pure,        # Maximum force with no lateral slip
            'limited_by_lateral': lateral_limited,  # Is force reduced by lateral slip?
            'available_percentage': percentage_available,  # % of pure longitudinal capacity
            'temperature_effect': temp_effect,  # Effect of temperature on grip (0.5-1.0)
            'vertical_load': Fz               # Vertical load used for calculation
        }
        
    def generate_force_to_slip_table(self, Fz_values, Fx_values, Fy_values, temp=None, gamma=0):
        """
        Generate a lookup table from desired forces to slip values.

        Args:
            Fz_values: Array of vertical load values [N]
            Fx_values: Array of longitudinal force values [N]
            Fy_values: Array of lateral force values [N]
            temp: Tire temperature [°C], if None uses internal temperature
            gamma: Camber angle [rad]

        Returns:
            None, but sets up lookup tables internally
        """
        # Use provided temperature or internal temperature
        if temp is None:
            temp = self.temperature
        
        # Create arrays to store slip values
        kappa_values = np.zeros((len(Fz_values), len(Fx_values), len(Fy_values)))
        alpha_values = np.zeros((len(Fz_values), len(Fx_values), len(Fy_values)))
        max_Fx_values = np.zeros((len(Fz_values), len(Fx_values), len(Fy_values)))
        
        # For each vertical load
        for i, Fz in enumerate(Fz_values):
            # For each combination of forces
            for j, Fx_desired in enumerate(Fx_values):
                for k, Fy_desired in enumerate(Fy_values):
                    # Find slip values that produce these forces
                    kappa, alpha = self._find_slip_from_forces(Fx_desired, Fy_desired, Fz)
                    kappa_values[i, j, k] = kappa
                    alpha_values[i, j, k] = alpha
                    
                    # Calculate max available Fx
                    max_Fx_info = self.calculate_max_longitudinal_force(Fz, alpha, gamma, temp)
                    max_Fx_values[i, j, k] = max_Fx_info['max_fx']
        
        # Store the lookup tables and grid values
        self.Fz_values = Fz_values
        self.Fx_values = Fx_values
        self.Fy_values = Fy_values
        
        # Create interpolation functions using RegularGridInterpolator
        # For now, we'll just use the first Fz value (index 0)
        self.kappa_interp = RegularGridInterpolator(
            (Fx_values, Fy_values), 
            kappa_values[0, :, :],
            bounds_error=False,
            fill_value=None  # Extrapolate
        )
        
        self.alpha_interp = RegularGridInterpolator(
            (Fx_values, Fy_values), 
            alpha_values[0, :, :],
            bounds_error=False,
            fill_value=None  # Extrapolate
        )
        
        self.max_Fx_interp = RegularGridInterpolator(
            (Fx_values, Fy_values), 
            max_Fx_values[0, :, :],
            bounds_error=False,
            fill_value=None  # Extrapolate
        )
        
        self.lookup_table_generated = True
        print("Generated force to slip lookup table.")       

    def _find_slip_from_forces(self, Fx_desired, Fy_desired, Fz, 
                              max_iterations=50):
        """
        Find the slip ratio and slip angle that produce the desired forces using
        an iterative method.

        Args:
            Fx_desired: Desired longitudinal force [N]
            Fy_desired: Desired lateral force [N]
            Fz: Vertical load [N]
            max_iterations: Maximum number of iterations

        Returns:
            Tuple containing slip ratio and slip angle
        """
        # Initial guesses for slip ratio and slip angle
        kappa = 0.0
        alpha = 0.0
        
        # Get normalized values for faster convergence
        Fx_normalized = Fx_desired / max(1.0, Fz)
        Fy_normalized = Fy_desired / max(1.0, Fz)
        
        # Define the optimization function
        def error_function(x):
            k, a = x
            forces = self.calculate_steady_state_forces(Fz, k, a)
            Fx_current = forces['Fx'] / max(1.0, Fz)
            Fy_current = forces['Fy'] / max(1.0, Fz)
            return [Fx_normalized - Fx_current, Fy_normalized - Fy_current]
        
        # Solve for slip ratio and slip angle
        try:
            solution = fsolve(error_function, [kappa, alpha])
            kappa, alpha = solution
        except:
            # Fallback to iterative approach if fsolve fails
            for _ in range(max_iterations):
                forces = self.calculate_steady_state_forces(Fz, kappa, alpha)
                Fx_error = Fx_desired - forces['Fx']
                Fy_error = Fy_desired - forces['Fy']
                
                # Check for convergence
                if abs(Fx_error) < 1.0 and abs(Fy_error) < 1.0:
                    break
                
                # Update slip values based on errors
                kappa += 0.0001 * Fx_error
                alpha += 0.0001 * Fy_error
                
                # Limit slip values to reasonable ranges
                kappa = max(-1.0, min(1.0, kappa))
                alpha = max(-0.5, min(0.5, alpha))
        
        return kappa, alpha
