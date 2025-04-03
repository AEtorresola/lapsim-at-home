import math
import warnings
import os # Needed for file path operations

class PacejkaTireRefactored:
    """
    Implements the Pacejka 2002 (Magic Formula 6.1) tire model with
    a sequential calculation structure for clarity and traceability.

    Loads parameters from an external file.

    Calculates combined longitudinal (Fx) and lateral (Fy) forces based on
    vertical load (Fz), slip angle (alpha), slip ratio (kappa), and
    camber angle (gamma).

    Attributes:
        history (list): Stores records of calculations if requested.
        return_errors (bool): Flag to determine error handling behavior.
        parameters (dict): Stores the loaded parameters.
        # Other attributes like nominal_load_z, min/max ranges etc. are set
        # dynamically during parameter loading.
    """

    def __init__(self, parameter_filepath, return_errors=False):
        """
        Initializes the PacejkaTire object by loading parameters from a file.

        Args:
            parameter_filepath (str): Path to the tire parameter file.
            return_errors (bool): If True, raise ValueError on out-of-range
                                   inputs. If False, clamp inputs to valid
                                   ranges and issue a warning.
        """
        self.return_errors = return_errors
        self.history = []
        self.parameters = {} # Dictionary to hold loaded parameters

        if not os.path.exists(parameter_filepath):
            raise FileNotFoundError(f"Parameter file not found: {parameter_filepath}")

        self._load_parameters_from_file(parameter_filepath)
        self._validate_required_parameters() # Ensure all needed params were loaded

        # Set frequently used constants and ranges as direct attributes for convenience
        # (assuming they exist after loading)
        self.nominal_load_z = self.parameters.get('nominal_load_z')
        self.unloaded_radius = self.parameters.get('unloaded_radius')
        self.min_slip_ratio = self.parameters.get('min_slip_ratio')
        self.max_slip_ratio = self.parameters.get('max_slip_ratio')
        self.min_slip_angle = self.parameters.get('min_slip_angle')
        self.max_slip_angle = self.parameters.get('max_slip_angle')
        self.min_camber = self.parameters.get('min_camber')
        self.max_camber = self.parameters.get('max_camber')
        self.min_load_z = self.parameters.get('min_load_z')
        self.max_load_z = self.parameters.get('max_load_z')


    def _load_parameters_from_file(self, filepath):
        """Loads parameters from a 'key = value' formatted file."""
        print(f"Loading parameters from: {filepath}")
        current_section = "DEFAULT" # For potential future use with sections
        try:
            with open(filepath, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#') or line.startswith('!'):
                        continue # Skip empty lines and comments

                    if line.startswith('[') and line.endswith(']'):
                         # Optional: Handle sections if needed later
                         current_section = line[1:-1].strip().upper()
                         continue

                    if '=' not in line:
                        warnings.warn(f"Skipping malformed line {line_num} in {filepath}: '{line}' (missing '=')", SyntaxWarning)
                        continue

                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    # Attempt to convert value to float
                    try:
                        float_value = float(value)
                        self.parameters[key] = float_value
                        # Dynamically set attribute if needed, though accessing via
                        # self.parameters[key] is generally safer to avoid conflicts
                        # setattr(self, key, float_value)
                        # print(f"  Loaded: {key} = {float_value}") # Debug print
                    except ValueError:
                        warnings.warn(f"Could not convert value to float on line {line_num} in {filepath}: '{value}' for key '{key}'. Storing as string.", SyntaxWarning)
                        self.parameters[key] = value # Store as string if not float

        except Exception as e:
            raise IOError(f"Error reading parameter file {filepath}: {e}")

    def _validate_required_parameters(self):
        """Checks if all essential parameters were loaded."""
        # List all parameter keys expected by the calculation methods
        required_keys = [
            'nominal_load_z', 'unloaded_radius', 'min_slip_ratio', 'max_slip_ratio',
            'min_slip_angle', 'max_slip_angle', 'min_camber', 'max_camber',
            'min_load_z', 'max_load_z',
            # Lateral
            'lat_shape_factor_c_pcy1', 'lat_peak_friction_d_pdy1', 'lat_friction_load_var_pdy2',
            'lat_friction_camber_var_pdy3', 'lat_curve_e_pey1', 'lat_curve_load_var_pey2',
            'lat_curve_camber_dep_0_pey3', 'lat_curve_camber_var_pey4', 'lat_stiffness_k_max_pky1',
            'lat_stiffness_load_max_pky2', 'lat_stiffness_camber_var_pky3', 'lat_shift_h_phy1',
            'lat_shift_load_var_phy2', 'lat_shift_camber_var_phy3', 'lat_shift_v_pvy1',
            'lat_shift_v_load_var_pvy2', 'lat_shift_v_camber_var_pvy3', 'lat_shift_v_camber_load_var_pvy4',
            # Longitudinal (Approx)
            'lon_shape_factor_c_pcx1', 'lon_peak_friction_d_pdx1', 'lon_friction_load_var_pdx2',
            'lon_friction_camber_var_pdx3', 'lon_curve_e_pex1', 'lon_curve_load_var_pex2',
            'lon_curve_load_sq_var_pex3', 'lon_curve_driving_factor_pex4', 'lon_stiffness_k_pkx1',
            'lon_stiffness_load_var_pkx2', 'lon_stiffness_load_exp_pkx3', 'lon_shift_h_phx1',
            'lon_shift_load_var_phx2', 'lon_shift_v_pvx1', 'lon_shift_v_load_var_pvx2',
            # Combined (Approx)
            'comb_lat_slope_b_rby1', 'comb_lat_slope_alpha_var_rby2', 'comb_lat_slope_alpha_shift_rby3',
            'comb_lat_shape_c_rcy1', 'comb_lon_slope_b_rbx1', 'comb_lon_slope_kappa_var_rbx2',
            'comb_lon_shape_c_rcx1'
        ]
        missing_keys = [key for key in required_keys if key not in self.parameters]
        if missing_keys:
            raise ValueError(f"Missing required parameters in file: {', '.join(missing_keys)}")
        print("All required parameters loaded successfully.")


    # --- Helper Functions for Each Calculation Step ---
    # These functions now need to access parameters via self.parameters['key_name']

    # Level 5 Calculations
    def _compute_dfz(self, Fz):
        """Eq 29: Calculates normalized load change."""
        nom_load = self.parameters['nominal_load_z']
        return (Fz - nom_load) / nom_load if nom_load != 0 else 0

    def _compute_mu_y(self, dfz, gamma):
        """Eq 27: Calculates lateral friction coefficient potential."""
        p = self.parameters
        return (p['lat_peak_friction_d_pdy1'] + p['lat_friction_load_var_pdy2'] * dfz) * \
               (1.0 + p['lat_friction_camber_var_pdy3'] * gamma**2)

    def _compute_K_y_alpha(self, Fz, gamma):
        """Eq 28: Calculates cornering stiffness."""
        p = self.parameters
        nom_load = p['nominal_load_z']
        fz_ratio = max(Fz / nom_load, 1e-6) if nom_load != 0 else 1e-6
        return p['lat_stiffness_k_max_pky1'] * nom_load * \
               math.sin(p['lat_stiffness_load_max_pky2'] * math.atan(fz_ratio)) * \
               (1.0 - p['lat_stiffness_camber_var_pky3'] * abs(gamma))

    def _compute_mu_x(self, dfz, gamma):
        """Eq 25: Calculates longitudinal friction coefficient potential (Approximated)."""
        p = self.parameters
        return (p['lon_peak_friction_d_pdx1'] + p['lon_friction_load_var_pdx2'] * dfz) * \
               (1.0 + p['lon_friction_camber_var_pdx3'] * gamma**2)

    def _compute_K_x_kappa(self, Fz, gamma):
        """Eq 26: Calculates longitudinal slip stiffness (Approximated)."""
        p = self.parameters
        nom_load = p['nominal_load_z']
        fz_ratio = max(Fz / nom_load, 1e-6) if nom_load != 0 else 1e-6
        return p['lon_stiffness_k_pkx1'] * nom_load * \
               math.sin(p['lon_stiffness_load_var_pkx2'] * math.atan(fz_ratio)) * \
               (1.0 - p['lon_stiffness_load_exp_pkx3'] * abs(gamma))

    # Level 4 Calculations (Shifts)
    def _compute_S_Hy(self, dfz, gamma):
        """Eq 24: Calculates horizontal shift for Fy."""
        p = self.parameters
        return (p['lat_shift_h_phy1'] + p['lat_shift_load_var_phy2'] * dfz) + \
               p['lat_shift_camber_var_phy3'] * gamma

    def _compute_S_Vy(self, Fz, dfz, gamma):
        """Eq 23: Calculates vertical shift for Fy."""
        p = self.parameters
        return Fz * ((p['lat_shift_v_pvy1'] + p['lat_shift_v_load_var_pvy2'] * dfz) + \
                     (p['lat_shift_v_camber_var_pvy3'] + p['lat_shift_v_camber_load_var_pvy4'] * dfz) * gamma)

    def _compute_S_Hx(self, dfz):
        """Eq 18: Calculates horizontal shift for Fx (Approximated)."""
        p = self.parameters
        return p['lon_shift_h_phx1'] + p['lon_shift_load_var_phx2'] * dfz

    def _compute_S_Vx(self, Fz, dfz):
        """Eq 17: Calculates vertical shift for Fx (Approximated)."""
        p = self.parameters
        return Fz * (p['lon_shift_v_pvx1'] + p['lon_shift_v_load_var_pvx2'] * dfz)

    # Level 3 Calculations (Effective Slips) - No change needed

    def _compute_alpha_eff(self, alpha, S_Hy):
        """Eq 12: Calculates effective lateral slip angle."""
        return alpha + S_Hy

    def _compute_kappa_eff(self, kappa, S_Hx):
        """Eq 11: Calculates effective longitudinal slip ratio."""
        return kappa + S_Hx

    # Level 4 Calculations (D, C, B, E)
    def _compute_D_y(self, mu_y, Fz):
        """Eq 19: Calculates peak factor for Fy."""
        return mu_y * Fz

    def _compute_C_y(self):
        """Eq 20: Calculates shape factor for Fy."""
        return self.parameters['lat_shape_factor_c_pcy1']

    def _compute_B_y(self, K_y_alpha, C_y, D_y):
        """Eq 21: Calculates stiffness factor for Fy."""
        denominator = C_y * D_y
        return K_y_alpha / denominator if abs(denominator) > 1e-6 else 0.0

    def _compute_E_y(self, dfz, gamma, alpha_eff):
        """Eq 22: Calculates curvature factor for Fy."""
        p = self.parameters
        E_y_base = p['lat_curve_e_pey1'] + p['lat_curve_load_var_pey2'] * dfz
        E_y_gamma_term = p['lat_curve_camber_dep_0_pey3'] + p['lat_curve_camber_var_pey4'] * gamma
        alpha_eff_sign = math.copysign(1, alpha_eff) if alpha_eff != 0 else 0
        return E_y_base * (1.0 - E_y_gamma_term * alpha_eff_sign)

    def _compute_D_x(self, mu_x, Fz):
        """Eq 13: Calculates peak factor for Fx (Approximated)."""
        return mu_x * Fz

    def _compute_C_x(self):
        """Eq 14: Calculates shape factor for Fx (Approximated)."""
        return self.parameters['lon_shape_factor_c_pcx1']

    def _compute_B_x(self, K_x_kappa, C_x, D_x):
        """Eq 15: Calculates stiffness factor for Fx (Approximated)."""
        denominator = C_x * D_x
        return K_x_kappa / denominator if abs(denominator) > 1e-6 else 0.0

    def _compute_E_x(self, dfz, kappa_eff):
        """Eq 16: Calculates curvature factor for Fx (Approximated)."""
        p = self.parameters
        E_x_base = p['lon_curve_e_pex1'] + p['lon_curve_load_var_pex2'] * dfz
        # Simplified version with PEX3=PEX4=0:
        return E_x_base

    # Level 2 Calculations (Pure Forces) - No change needed in logic, just access params

    def _compute_pure_fy(self, D_y, C_y, B_y, E_y, alpha_eff, S_Vy):
        """Eq 6: Calculates pure lateral force."""
        if abs(B_y) < 1e-9:
             return S_Vy
        X = B_y * alpha_eff
        try:
            arctan_X = math.atan(X)
            inner_arg = C_y * math.atan(X - E_y * (X - arctan_X))
            Fy_pure = D_y * math.sin(inner_arg) + S_Vy
        except ValueError:
             warnings.warn(f"Math domain error in pure Fy calculation. Inputs: D={D_y}, C={C_y}, B={B_y}, E={E_y}, alpha_eff={alpha_eff}, S_V={S_Vy}", RuntimeWarning)
             Fy_pure = S_Vy
        return Fy_pure

    def _compute_pure_fx(self, D_x, C_x, B_x, E_x, kappa_eff, S_Vx):
        """Eq 5: Calculates pure longitudinal force (Approximated)."""
        if abs(B_x) < 1e-9:
            return S_Vx
        X = B_x * kappa_eff
        try:
            arctan_X = math.atan(X)
            inner_arg = C_x * math.atan(X - E_x * (X - arctan_X))
            Fx_pure = D_x * math.sin(inner_arg) + S_Vx
        except ValueError:
            warnings.warn(f"Math domain error in pure Fx calculation. Inputs: D={D_x}, C={C_x}, B={B_x}, E={E_x}, kappa_eff={kappa_eff}, S_V={S_Vx}", RuntimeWarning)
            Fx_pure = S_Vx
        return Fx_pure

    # Level 3 Calculations (Weighting Factor Components)
    def _compute_B_xa(self, kappa):
        """Eq 7: Calculates slope factor for G_xa (Approximated)."""
        p = self.parameters
        return p['comb_lon_slope_b_rbx1'] * math.cos(math.atan(p['comb_lon_slope_kappa_var_rbx2'] * kappa))

    def _compute_C_xa(self):
        """Eq 8: Calculates shape factor for G_xa (Approximated)."""
        return self.parameters['comb_lon_shape_c_rcx1']

    def _compute_B_yk(self, alpha):
        """Eq 9: Calculates slope factor for G_yk (Approximated)."""
        p = self.parameters
        return p['comb_lat_slope_b_rby1'] * math.cos(math.atan(p['comb_lat_slope_alpha_var_rby2'] * (alpha - p['comb_lat_slope_alpha_shift_rby3'])))

    def _compute_C_yk(self):
        """Eq 10: Calculates shape factor for G_yk (Approximated)."""
        return self.parameters['comb_lat_shape_c_rcy1']

    # Level 2 Calculations (Weighting Factors) - No change needed in logic

    def _compute_G_xa(self, C_xa, B_xa, alpha):
        """Eq 3: Calculates longitudinal force weighting factor (Approximated)."""
        arg = max(-100.0, min(100.0, B_xa * alpha))
        return math.cos(C_xa * math.atan(arg))

    def _compute_G_yk(self, C_yk, B_yk, kappa):
        """Eq 4: Calculates lateral force weighting factor (Approximated)."""
        arg = max(-100.0, min(100.0, B_yk * kappa))
        return math.cos(C_yk * math.atan(arg))

    # Level 1 Calculations (Final Combined Forces) - No change needed in logic

    def _compute_Fx_combined(self, Fx_pure, G_xa):
        """Eq 1: Calculates final combined longitudinal force."""
        return Fx_pure * G_xa

    def _compute_Fy_combined(self, Fy_pure, G_yk):
        """Eq 2: Calculates final combined lateral force."""
        return Fy_pure * G_yk

    # --- Input Clamping ---
    # Uses self.min/max attributes set during __init__
    def _clamp_inputs(self, Fz, alpha, kappa, gamma):
        """Clamps or raises errors for inputs outside valid ranges."""
        clamped = False
        original_inputs = {'Fz': Fz, 'alpha': alpha, 'kappa': kappa, 'gamma': gamma}

        # Check if limits were loaded correctly
        if self.min_load_z is None or self.max_load_z is None or \
           self.min_slip_angle is None or self.max_slip_angle is None or \
           self.min_slip_ratio is None or self.max_slip_ratio is None or \
           self.min_camber is None or self.max_camber is None:
            raise ValueError("Input range limits were not loaded correctly from parameter file.")


        if not (self.min_load_z <= Fz <= self.max_load_z):
            if self.return_errors:
                raise ValueError(f"Fz {Fz} out of range [{self.min_load_z}, {self.max_load_z}]")
            Fz = max(self.min_load_z, min(self.max_load_z, Fz))
            clamped = True

        if not (self.min_slip_angle <= alpha <= self.max_slip_angle):
            if self.return_errors:
                raise ValueError(f"alpha {alpha} out of range [{self.min_slip_angle}, {self.max_slip_angle}]")
            alpha = max(self.min_slip_angle, min(self.max_slip_angle, alpha))
            clamped = True

        if not (self.min_slip_ratio <= kappa <= self.max_slip_ratio):
            if self.return_errors:
                raise ValueError(f"kappa {kappa} out of range [{self.min_slip_ratio}, {self.max_slip_ratio}]")
            kappa = max(self.min_slip_ratio, min(self.max_slip_ratio, kappa))
            clamped = True

        if not (self.min_camber <= gamma <= self.max_camber):
             if self.return_errors:
                 raise ValueError(f"gamma {gamma} out of range [{self.min_camber}, {self.max_camber}]")
             gamma = max(self.min_camber, min(self.max_camber, gamma))
             clamped = True

        if clamped and not self.return_errors:
             warnings.warn(f"Input clamped: Original={original_inputs}, Clamped={{'Fz': {Fz}, 'alpha': {alpha}, 'kappa': {kappa}, 'gamma': {gamma}}}", RuntimeWarning)

        return Fz, alpha, kappa, gamma

    # --- Main Calculation Orchestrator ---
    # No change needed in the sequence, just relies on helper functions using self.parameters
    def calculate_forces(self, Fz, alpha, kappa, gamma, store_history=False):
        """
        Calculates combined Fx and Fy using a sequential, traceable approach.
        Parameters are loaded from the file specified during initialization.

        Args:
            Fz (float): Vertical load (N).
            alpha (float): Slip angle (radians).
            kappa (float): Slip ratio (dimensionless).
            gamma (float): Camber angle (radians).
            store_history (bool): If True, store inputs and outputs in history.

        Returns:
            dict: {'Fx': Fx_combined (N), 'Fy': Fy_combined (N)}
        """
        original_inputs = {'Fz': Fz, 'alpha': alpha, 'kappa': kappa, 'gamma': gamma}

        # --- Calculation Sequence ---
        Fz_proc, alpha_proc, kappa_proc, gamma_proc = self._clamp_inputs(Fz, alpha, kappa, gamma)
        dfz = self._compute_dfz(Fz_proc)
        mu_y = self._compute_mu_y(dfz, gamma_proc)
        K_y_alpha = self._compute_K_y_alpha(Fz_proc, gamma_proc)
        mu_x = self._compute_mu_x(dfz, gamma_proc)
        K_x_kappa = self._compute_K_x_kappa(Fz_proc, gamma_proc)
        S_Hy = self._compute_S_Hy(dfz, gamma_proc)
        S_Vy = self._compute_S_Vy(Fz_proc, dfz, gamma_proc)
        S_Hx = self._compute_S_Hx(dfz)
        S_Vx = self._compute_S_Vx(Fz_proc, dfz)
        alpha_eff = self._compute_alpha_eff(alpha_proc, S_Hy)
        kappa_eff = self._compute_kappa_eff(kappa_proc, S_Hx)
        D_y = self._compute_D_y(mu_y, Fz_proc)
        C_y = self._compute_C_y()
        B_y = self._compute_B_y(K_y_alpha, C_y, D_y)
        E_y = self._compute_E_y(dfz, gamma_proc, alpha_eff)
        D_x = self._compute_D_x(mu_x, Fz_proc)
        C_x = self._compute_C_x()
        B_x = self._compute_B_x(K_x_kappa, C_x, D_x)
        E_x = self._compute_E_x(dfz, kappa_eff)
        Fy_pure = self._compute_pure_fy(D_y, C_y, B_y, E_y, alpha_eff, S_Vy)
        Fx_pure = self._compute_pure_fx(D_x, C_x, B_x, E_x, kappa_eff, S_Vx)
        B_yk = self._compute_B_yk(alpha_proc)
        C_yk = self._compute_C_yk()
        B_xa = self._compute_B_xa(kappa_proc)
        C_xa = self._compute_C_xa()
        G_yk = self._compute_G_yk(C_yk, B_yk, kappa_proc)
        G_xa = self._compute_G_xa(C_xa, B_xa, alpha_proc)
        Fx_combined = self._compute_Fx_combined(Fx_pure, G_xa)
        Fy_combined = self._compute_Fy_combined(Fy_pure, G_yk)
        # --- End Calculation Sequence ---

        if store_history:
            history_record = {
                'inputs': original_inputs,
                'processed_inputs': {'Fz': Fz_proc, 'alpha': alpha_proc, 'kappa': kappa_proc, 'gamma': gamma_proc},
                # Storing all loaded parameters might be too verbose, store key intermediates instead
                'intermediate': {
                    'dfz': dfz, 'mu_y': mu_y, 'K_y_alpha': K_y_alpha, 'S_Hy': S_Hy, 'S_Vy': S_Vy,
                    'alpha_eff': alpha_eff, 'D_y': D_y, 'C_y': C_y, 'B_y': B_y, 'E_y': E_y,
                    'mu_x': mu_x, 'K_x_kappa': K_x_kappa, 'S_Hx': S_Hx, 'S_Vx': S_Vx,
                    'kappa_eff': kappa_eff, 'D_x': D_x, 'C_x': C_x, 'B_x': B_x, 'E_x': E_x,
                    'B_yk': B_yk, 'C_yk': C_yk, 'B_xa': B_xa, 'C_xa': C_xa
                },
                'pure_forces': {'Fx': Fx_pure, 'Fy': Fy_pure},
                'weighting': {'Gxa': G_xa, 'Gyk': G_yk},
                'outputs': {'Fx': Fx_combined, 'Fy': Fy_combined}
            }
            self.history.append(history_record)

        return {'Fx': Fx_combined, 'Fy': Fy_combined}

    # --- History Management ---
    def get_history(self):
        """Returns the calculation history."""
        return self.history

    def clear_history(self):
        """Clears the calculation history."""
        self.history = []


# --- Example Usage ---
if __name__ == "__main__":
    # Define the path to your parameter file
    param_file = 'hoosier_r20.par' # Make sure this file exists in the same directory or provide the full path

    # Check if the example file exists, create a dummy one if not for testing
    if not os.path.exists(param_file):
        print(f"Warning: Parameter file '{param_file}' not found. Creating a dummy file for testing.")
        # You would normally create the full file as shown above
        with open(param_file, 'w') as f:
             f.write("# Dummy parameter file\n")
             f.write("[CONSTANTS]\nnominal_load_z = 600.0\nunloaded_radius = 0.2\n")
             f.write("[RANGES]\nmin_load_z=100\nmax_load_z=1000\nmin_slip_angle=-0.3\nmax_slip_angle=0.3\n")
             f.write("min_slip_ratio=-0.3\nmax_slip_ratio=0.3\nmin_camber=-0.1\nmax_camber=0.1\n")
             # Add dummy values for all required keys for the validation to pass
             required_keys_example = [
                'lat_shape_factor_c_pcy1', 'lat_peak_friction_d_pdy1', 'lat_friction_load_var_pdy2',
                'lat_friction_camber_var_pdy3', 'lat_curve_e_pey1', 'lat_curve_load_var_pey2',
                'lat_curve_camber_dep_0_pey3', 'lat_curve_camber_var_pey4', 'lat_stiffness_k_max_pky1',
                'lat_stiffness_load_max_pky2', 'lat_stiffness_camber_var_pky3', 'lat_shift_h_phy1',
                'lat_shift_load_var_phy2', 'lat_shift_camber_var_phy3', 'lat_shift_v_pvy1',
                'lat_shift_v_load_var_pvy2', 'lat_shift_v_camber_var_pvy3', 'lat_shift_v_camber_load_var_pvy4',
                'lon_shape_factor_c_pcx1', 'lon_peak_friction_d_pdx1', 'lon_friction_load_var_pdx2',
                'lon_friction_camber_var_pdx3', 'lon_curve_e_pex1', 'lon_curve_load_var_pex2',
                'lon_curve_load_sq_var_pex3', 'lon_curve_driving_factor_pex4', 'lon_stiffness_k_pkx1',
                'lon_stiffness_load_var_pkx2', 'lon_stiffness_load_exp_pkx3', 'lon_shift_h_phx1',
                'lon_shift_load_var_phx2', 'lon_shift_v_pvx1', 'lon_shift_v_load_var_pvx2',
                'comb_lat_slope_b_rby1', 'comb_lat_slope_alpha_var_rby2', 'comb_lat_slope_alpha_shift_rby3',
                'comb_lat_shape_c_rcy1', 'comb_lon_slope_b_rbx1', 'comb_lon_slope_kappa_var_rbx2',
                'comb_lon_shape_c_rcx1'
             ]
             f.write("[COEFFICIENTS]\n")
             for key in required_keys_example:
                 if 'lat' in key or 'lon' in key or 'comb' in key: # Avoid overwriting constants/ranges
                     f.write(f"{key} = 1.0\n") # Assign dummy value 1.0


    try:
        # Initialize the tire model by providing the file path
        tire = PacejkaTireRefactored(param_file, return_errors=False)

        # Example conditions (same as before)
        fz_example = 600.0 # N
        alpha_example = math.radians(5.0) # 5 degrees slip angle
        kappa_example = 0.05 # 5% slip ratio (acceleration)
        gamma_example = math.radians(-2.0) # -2 degrees camber

        # Calculate forces, store this one in history
        forces = tire.calculate_forces(fz_example, alpha_example, kappa_example, gamma_example, store_history=True)
        print(f"\nInputs: Fz={fz_example:.1f} N, alpha={math.degrees(alpha_example):.2f} deg, kappa={kappa_example:.3f}, gamma={math.degrees(gamma_example):.2f} deg")
        print(f"Calculated Forces: Fx={forces['Fx']:.2f} N, Fy={forces['Fy']:.2f} N")

        # Retrieve history
        calc_history = tire.get_history()
        print(f"\nCalculation History Length: {len(calc_history)}")
        if calc_history:
            print("Last history record (showing intermediate values):")
            last_record = calc_history[-1]
            print(f"  Original Inputs: {last_record['inputs']}")
            print(f"  Processed Inputs: {last_record['processed_inputs']}")
            print(f"  Intermediate (sample): dfz={last_record['intermediate']['dfz']:.3f}, mu_y={last_record['intermediate']['mu_y']:.3f}, K_y_alpha={last_record['intermediate']['K_y_alpha']:.1f}")
            print(f"  Pure Forces: {last_record['pure_forces']}")
            print(f"  Weighting: {last_record['weighting']}")
            print(f"  Outputs: {last_record['outputs']}")

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except ValueError as e:
        print(f"Error during parameter validation: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


