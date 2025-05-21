
import math
import warnings
import os
import pandas as pd # Required for TimeSeriesStorage
import numpy as np 
from scipy.optimize import root_scalar
# --- Basic Logger Setup (for demonstration) ---
from helper_functions import TimeSeriesStorage
from logger import setup_logger
logger = setup_logger()

# --- Modified PacejkaTireRefactored Class ---
class PacejkaTireRefactored:
    """
    Implements the Pacejka 2002 (Magic Formula 6.1) tire model with
    a sequential calculation structure for clarity and traceability.

    Loads parameters from an external file. Uses TimeSeriesStorage for history.

    Calculates combined longitudinal (Fx) and lateral (Fy) forces based on
    vertical load (Fz), slip angle (alpha), slip ratio (kappa),
    camber angle (gamma), and simulation time (time_ms).

    Attributes:
        history_storage (TimeSeriesStorage): Stores records of calculations.
        return_errors (bool): Flag to determine error handling behavior.
        parameters (dict): Stores the loaded parameters.
    """

    def __init__(self, parameter_filepath, return_errors=False, history_name="TireHistory"):
        """
        Initializes the PacejkaTire object by loading parameters from a file
        and setting up TimeSeriesStorage for history.

        Args:
            parameter_filepath (str): Path to the tire parameter file.
            return_errors (bool): If True, raise ValueError on out-of-range
                                   inputs. If False, clamp inputs to valid
                                   ranges and issue a warning.
            history_name (str): Name for the TimeSeriesStorage instance.
        """
        self.return_errors = return_errors
        self.parameters = {} # Dictionary to hold loaded parameters
        self._history_name = history_name # Store name for potential re-init

        logger.info(f"Initializing Pacejka Tire Model from {parameter_filepath}")

        if not os.path.exists(parameter_filepath):
            logger.error(f"Parameter file not found: {parameter_filepath}")
            raise FileNotFoundError(f"Parameter file not found: {parameter_filepath}")

        self._load_parameters_from_file(parameter_filepath)
        self._validate_required_parameters() # Ensure all needed params were loaded

        # Set frequently used constants and ranges as direct attributes
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

        # --- Initialize TimeSeriesStorage ---
        self._setup_history_storage()
        logger.info(f"Pacejka Tire Model initialized successfully.")


    def _setup_history_storage(self):
        """Helper method to initialize or re-initialize history storage."""
        history_columns = [
            'time', 'Fz_orig', 'alpha_orig', 'kappa_orig', 'gamma_orig',
            'Fz_proc', 'alpha_proc', 'kappa_proc', 'gamma_proc',
            'dfz', 'mu_y', 'K_y_alpha', 'S_Hy', 'S_Vy', 'alpha_eff', 'D_y', 'C_y', 'B_y', 'E_y',
            'mu_x', 'K_x_kappa', 'S_Hx', 'S_Vx', 'kappa_eff', 'D_x', 'C_x', 'B_x', 'E_x',
            'B_yk', 'C_yk', 'B_xa', 'C_xa', 'Fx_pure', 'Fy_pure', 'Gxa', 'Gyk', 'Fx', 'Fy'
        ]
        initial_history_data = {col: [] for col in history_columns}
        col_types = {col: float for col in history_columns if col != 'time'}
        self.history_storage = TimeSeriesStorage(
            initial_data=initial_history_data,
            name=self._history_name,
            col_types=col_types
        )

    def _load_parameters_from_file(self, filepath):
        """Loads parameters from a 'key = value' formatted file."""
        logger.info(f"Loading parameters from: {filepath}")
        current_section = "DEFAULT"
        try:
            with open(filepath, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#') or line.startswith('!'): continue
                    if line.startswith('[') and line.endswith(']'):
                         current_section = line[1:-1].strip().upper(); continue
                    if '=' not in line:
                        logger.warning(f"Skipping malformed line {line_num} in {filepath}: '{line}' (missing '=')")
                        continue
                    key, value = line.split('=', 1); key = key.strip(); value = value.strip()
                    try: self.parameters[key] = float(value)
                    except ValueError:
                        logger.warning(f"Could not convert value to float on line {line_num} in {filepath}: '{value}' for key '{key}'. Storing as string.")
                        self.parameters[key] = value
            logger.info(f"Finished loading parameters from {filepath}")
        except Exception as e:
            logger.error(f"Error reading parameter file {filepath}: {e}")
            raise IOError(f"Error reading parameter file {filepath}: {e}")

    def _validate_required_parameters(self):
        """Checks if all essential parameters were loaded."""
        logger.debug("Validating required parameters...")
        required_keys = [
            'nominal_load_z', 'unloaded_radius', 'min_slip_ratio', 'max_slip_ratio',
            'min_slip_angle', 'max_slip_angle', 'min_camber', 'max_camber',
            'min_load_z', 'max_load_z',
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
        missing_keys = [key for key in required_keys if key not in self.parameters]
        if missing_keys:
            logger.error(f"Missing required parameters in file: {', '.join(missing_keys)}")
            raise ValueError(f"Missing required parameters in file: {', '.join(missing_keys)}")
        logger.info("All required parameters loaded successfully.")


    # --- Helper Functions for Each Calculation Step ---
    # (No changes needed here, they don't log directly)
    # Level 5 Calculations
    def _compute_dfz(self, Fz):
        nom_load = self.parameters['nominal_load_z']
        return (Fz - nom_load) / nom_load if nom_load != 0 else 0
    def _compute_mu_y(self, dfz, gamma):
        p = self.parameters
        return (p['lat_peak_friction_d_pdy1'] + p['lat_friction_load_var_pdy2'] * dfz) * \
               (1.0 + p['lat_friction_camber_var_pdy3'] * gamma**2)
    def _compute_K_y_alpha(self, Fz, gamma):
        p = self.parameters
        nom_load = p['nominal_load_z']
        fz_ratio = max(Fz / nom_load, 1e-6) if nom_load != 0 else 1e-6
        return p['lat_stiffness_k_max_pky1'] * nom_load * \
               math.sin(p['lat_stiffness_load_max_pky2'] * math.atan(fz_ratio)) * \
               (1.0 - p['lat_stiffness_camber_var_pky3'] * abs(gamma))
    def _compute_mu_x(self, dfz, gamma):
        p = self.parameters
        return (p['lon_peak_friction_d_pdx1'] + p['lon_friction_load_var_pdx2'] * dfz) * \
               (1.0 + p['lon_friction_camber_var_pdx3'] * gamma**2)
    def _compute_K_x_kappa(self, Fz, gamma):
        p = self.parameters
        nom_load = p['nominal_load_z']
        fz_ratio = max(Fz / nom_load, 1e-6) if nom_load != 0 else 1e-6
        return p['lon_stiffness_k_pkx1'] * nom_load * \
               math.sin(p['lon_stiffness_load_var_pkx2'] * math.atan(fz_ratio)) * \
               (1.0 - p['lon_stiffness_load_exp_pkx3'] * abs(gamma))
    # Level 4 Calculations (Shifts)
    def _compute_S_Hy(self, dfz, gamma):
        p = self.parameters
        return (p['lat_shift_h_phy1'] + p['lat_shift_load_var_phy2'] * dfz) + \
               p['lat_shift_camber_var_phy3'] * gamma
    def _compute_S_Vy(self, Fz, dfz, gamma):
        p = self.parameters
        return Fz * ((p['lat_shift_v_pvy1'] + p['lat_shift_v_load_var_pvy2'] * dfz) + \
                     (p['lat_shift_v_camber_var_pvy3'] + p['lat_shift_v_camber_load_var_pvy4'] * dfz) * gamma)
    def _compute_S_Hx(self, dfz):
        p = self.parameters
        return p['lon_shift_h_phx1'] + p['lon_shift_load_var_phx2'] * dfz
    def _compute_S_Vx(self, Fz, dfz):
        p = self.parameters
        return Fz * (p['lon_shift_v_pvx1'] + p['lon_shift_v_load_var_pvx2'] * dfz)
    # Level 3 Calculations (Effective Slips)
    def _compute_alpha_eff(self, alpha, S_Hy): return alpha + S_Hy
    def _compute_kappa_eff(self, kappa, S_Hx): return kappa + S_Hx
    # Level 4 Calculations (D, C, B, E)
    def _compute_D_y(self, mu_y, Fz): return mu_y * Fz
    def _compute_C_y(self): return self.parameters['lat_shape_factor_c_pcy1']
    def _compute_B_y(self, K_y_alpha, C_y, D_y):
        denominator = C_y * D_y
        return K_y_alpha / denominator if abs(denominator) > 1e-6 else 0.0
    def _compute_E_y(self, dfz, gamma, alpha_eff):
        p = self.parameters
        E_y_base = p['lat_curve_e_pey1'] + p['lat_curve_load_var_pey2'] * dfz
        E_y_gamma_term = p['lat_curve_camber_dep_0_pey3'] + p['lat_curve_camber_var_pey4'] * gamma
        alpha_eff_sign = math.copysign(1, alpha_eff) if alpha_eff != 0 else 0
        return E_y_base * (1.0 - E_y_gamma_term * alpha_eff_sign)
    def _compute_D_x(self, mu_x, Fz): return mu_x * Fz
    def _compute_C_x(self): return self.parameters['lon_shape_factor_c_pcx1']
    def _compute_B_x(self, K_x_kappa, C_x, D_x):
        denominator = C_x * D_x
        return K_x_kappa / denominator if abs(denominator) > 1e-6 else 0.0
    def _compute_E_x(self, dfz, kappa_eff):
        p = self.parameters
        E_x_base = p['lon_curve_e_pex1'] + p['lon_curve_load_var_pex2'] * dfz
        return E_x_base
    # Level 2 Calculations (Pure Forces)
    def _compute_pure_fy(self, D_y, C_y, B_y, E_y, alpha_eff, S_Vy):
        if abs(B_y) < 1e-9: return S_Vy
        X = B_y * alpha_eff
        try:
            arctan_X = math.atan(X)
            inner_arg = C_y * math.atan(X - E_y * (X - arctan_X))
            Fy_pure = D_y * math.sin(inner_arg) + S_Vy
        except ValueError as e:
             # Log math domain errors
             logger.warning(f"Math domain error in pure Fy calculation: {e}. Inputs: D={D_y}, C={C_y}, B={B_y}, E={E_y}, alpha_eff={alpha_eff}, S_V={S_Vy}")
             Fy_pure = S_Vy
        return Fy_pure
    def _compute_pure_fx(self, D_x, C_x, B_x, E_x, kappa_eff, S_Vx):
        if abs(B_x) < 1e-9: return S_Vx
        X = B_x * kappa_eff
        try:
            arctan_X = math.atan(X)
            inner_arg = C_x * math.atan(X - E_x * (X - arctan_X))
            Fx_pure = D_x * math.sin(inner_arg) + S_Vx
        except ValueError as e:
            logger.warning(f"Math domain error in pure Fx calculation: {e}. Inputs: D={D_x}, C={C_x}, B={B_x}, E={E_x}, kappa_eff={kappa_eff}, S_V={S_Vx}")
            Fx_pure = S_Vx
        return Fx_pure
    # Level 3 Calculations (Weighting Factor Components)
    def _compute_B_xa(self, kappa):
        p = self.parameters
        return p['comb_lon_slope_b_rbx1'] * math.cos(math.atan(p['comb_lon_slope_kappa_var_rbx2'] * kappa))
    def _compute_C_xa(self): return self.parameters['comb_lon_shape_c_rcx1']
    def _compute_B_yk(self, alpha):
        p = self.parameters
        return p['comb_lat_slope_b_rby1'] * math.cos(math.atan(p['comb_lat_slope_alpha_var_rby2'] * (alpha - p['comb_lat_slope_alpha_shift_rby3'])))
    def _compute_C_yk(self): return self.parameters['comb_lat_shape_c_rcy1']
    # Level 2 Calculations (Weighting Factors)
    def _compute_G_xa(self, C_xa, B_xa, alpha):
        arg = max(-100.0, min(100.0, B_xa * alpha))
        return math.cos(C_xa * math.atan(arg))
    def _compute_G_yk(self, C_yk, B_yk, kappa):
        arg = max(-100.0, min(100.0, B_yk * kappa))
        return math.cos(C_yk * math.atan(arg))
    # Level 1 Calculations (Final Combined Forces)
    def _compute_Fx_combined(self, Fx_pure, G_xa): return Fx_pure * G_xa
    def _compute_Fy_combined(self, Fy_pure, G_yk): return Fy_pure * G_yk

    # --- Input Clamping ---
    def _clamp_inputs(self, Fz, alpha, kappa, gamma):
        """Clamps or raises errors for inputs outside valid ranges."""
        clamped = False
        clamped_vars = []
        original_inputs = {'Fz': Fz, 'alpha': alpha, 'kappa': kappa, 'gamma': gamma}

        # Check if limits were loaded correctly
        if self.min_load_z is None or self.max_load_z is None or \
           self.min_slip_angle is None or self.max_slip_angle is None or \
           self.min_slip_ratio is None or self.max_slip_ratio is None or \
           self.min_camber is None or self.max_camber is None:
            logger.critical("Input range limits were not loaded correctly from parameter file.")
            raise ValueError("Input range limits were not loaded correctly from parameter file.")


        if not (self.min_load_z <= Fz <= self.max_load_z):
            if self.return_errors:
                logger.error(f"Input Fz {Fz} out of range [{self.min_load_z}, {self.max_load_z}]")
                raise ValueError(f"Fz {Fz} out of range [{self.min_load_z}, {self.max_load_z}]")
            Fz = max(self.min_load_z, min(self.max_load_z, Fz))
            clamped = True; clamped_vars.append('Fz')

        if not (self.min_slip_angle <= alpha <= self.max_slip_angle):
            if self.return_errors:
                logger.error(f"Input alpha {alpha} out of range [{self.min_slip_angle}, {self.max_slip_angle}]")
                raise ValueError(f"alpha {alpha} out of range [{self.min_slip_angle}, {self.max_slip_angle}]")
            alpha = max(self.min_slip_angle, min(self.max_slip_angle, alpha))
            clamped = True; clamped_vars.append('alpha')

        if not (self.min_slip_ratio <= kappa <= self.max_slip_ratio):
            if self.return_errors:
                logger.error(f"Input kappa {kappa} out of range [{self.min_slip_ratio}, {self.max_slip_ratio}]")
                raise ValueError(f"kappa {kappa} out of range [{self.min_slip_ratio}, {self.max_slip_ratio}]")
            kappa = max(self.min_slip_ratio, min(self.max_slip_ratio, kappa))
            clamped = True; clamped_vars.append('kappa')

        if not (self.min_camber <= gamma <= self.max_camber):
             if self.return_errors:
                 logger.error(f"Input gamma {gamma} out of range [{self.min_camber}, {self.max_camber}]")
                 raise ValueError(f"gamma {gamma} out of range [{self.min_camber}, {self.max_camber}]")
             gamma = max(self.min_camber, min(self.max_camber, gamma))
             clamped = True; clamped_vars.append('gamma')

        if clamped and not self.return_errors:
             # Log clamping event
             logger.warning(f"Input(s) clamped: {', '.join(clamped_vars)}. Original={original_inputs}, Clamped={{'Fz': {Fz}, 'alpha': {alpha}, 'kappa': {kappa}, 'gamma': {gamma}}}")
             # warnings.warn is still useful for direct user feedback if needed
             # warnings.warn(f"Input(s) clamped: {', '.join(clamped_vars)}. Original={original_inputs}, Clamped={{'Fz': {Fz}, 'alpha': {alpha}, 'kappa': {kappa}, 'gamma': {gamma}}}", RuntimeWarning)


        return Fz, alpha, kappa, gamma

    # --- Main Calculation Orchestrator ---
    def calculate_forces(self, Fz, alpha, kappa, gamma, time_ms, store_history=False):
        """
        Calculates combined Fx and Fy using a sequential, traceable approach.
        Parameters are loaded from the file specified during initialization.

        Args:
            Fz (float): Vertical load (N).
            alpha (float): Slip angle (radians).
            kappa (float): Slip ratio (dimensionless).
            gamma (float): Camber angle (radians).
            time_ms (int): Simulation time in milliseconds.
            store_history (bool): If True, store inputs and outputs in history.

        Returns:
            dict: {'Fx': Fx_combined (N), 'Fy': Fy_combined (N)}
        """
        logger.debug(f"Calculating forces for time {time_ms} ms. Inputs: Fz={Fz}, alpha={alpha}, kappa={kappa}, gamma={gamma}")
        original_inputs = {'Fz': Fz, 'alpha': alpha, 'kappa': kappa, 'gamma': gamma, 'time_ms': time_ms}

        try:
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
                logger.debug(f"Storing history for time {time_ms} ms.")
                # Prepare data row for TimeSeriesStorage update
                history_data_row = {
                    # Original Inputs (match column names)
                    'Fz_orig': Fz, 'alpha_orig': alpha, 'kappa_orig': kappa, 'gamma_orig': gamma,
                    # Processed Inputs
                    'Fz_proc': Fz_proc, 'alpha_proc': alpha_proc, 'kappa_proc': kappa_proc, 'gamma_proc': gamma_proc,
                    # Intermediate
                    'dfz': dfz, 'mu_y': mu_y, 'K_y_alpha': K_y_alpha, 'S_Hy': S_Hy, 'S_Vy': S_Vy,
                    'alpha_eff': alpha_eff, 'D_y': D_y, 'C_y': C_y, 'B_y': B_y, 'E_y': E_y,
                    'mu_x': mu_x, 'K_x_kappa': K_x_kappa, 'S_Hx': S_Hx, 'S_Vx': S_Vx,
                    'kappa_eff': kappa_eff, 'D_x': D_x, 'C_x': C_x, 'B_x': B_x, 'E_x': E_x,
                    'B_yk': B_yk, 'C_yk': C_yk, 'B_xa': B_xa, 'C_xa': C_xa,
                    # Pure Forces
                    'Fx_pure': Fx_pure, 'Fy_pure': Fy_pure,
                    # Weighting
                    'Gxa': G_xa, 'Gyk': G_yk,
                    # Outputs
                    'Fx': Fx_combined, 'Fy': Fy_combined
                }
                try:
                    self.history_storage.update(history_data_row, time_ms)
                except Exception as e:
                    logger.error(f"Failed to store history at time {time_ms}: {e}")
                    # Decide if this should halt execution or just warn

            logger.debug(f"Force calculation complete for time {time_ms}. Fx={Fx_combined}, Fy={Fy_combined}")
            return {'Fx': Fx_combined, 'Fy': Fy_combined}

        except Exception as e:
            logger.error(f"Error during force calculation at time {time_ms}: {e}")
            # Depending on simulation needs, either re-raise or return default (e.g., zero forces)
            # raise # Option 1: Stop simulation
            return {'Fx': 0.0, 'Fy': 0.0} # Option 2: Return safe values


    # --- History Management ---
    def get_history_dataframe(self):
        """Returns the entire calculation history DataFrame."""
        return self.history_storage.get_dataframe()

    def get_history_at_time(self, time_ms):
        """
        Returns a Pandas Series representing the history record at a specific time.

        Args:
            time_ms (int): The simulation time in milliseconds to retrieve.

        Returns:
            pandas.Series: The history record for the given time, or None if not found.
        """
        return self.history_storage.get_time_series(time_ms)

    def clear_history(self):
        """Clears the calculation history stored in TimeSeriesStorage."""
        logger.info(f"Clearing history for {self.history_storage.name}")
        self.history_storage.clear()

    # --- Helper methods for peak force potential ---
    def get_peak_fx_potential(self, Fz, gamma):
        """
        Calculates the maximum positive pure longitudinal force potential (Dx + SVx).
        Assumes alpha = 0.

        Args:
            Fz (float): Vertical load (N).
            gamma (float): Camber angle (radians).

        Returns:
            float: The maximum potential pure acceleration force (N).
        """
        logger.debug(f"Calculating peak Fx potential for Fz={Fz}, gamma={gamma}")
        try:
            Fz_proc, _, _, gamma_proc = self._clamp_inputs(Fz, 0.0, 0.0, gamma)
            dfz = self._compute_dfz(Fz_proc)
            mu_x = self._compute_mu_x(dfz, gamma_proc)
            D_x = self._compute_D_x(mu_x, Fz_proc)
            S_Vx = self._compute_S_Vx(Fz_proc, dfz)
            peak_potential = D_x + S_Vx
            logger.debug(f"Peak Fx potential: Dx={D_x:.2f}, SVx={S_Vx:.2f}, Peak={peak_potential:.2f}")
            return peak_potential
        except Exception as e:
            logger.error(f"Error calculating peak Fx potential: {e}")
            return 0.0

    def get_min_fx_potential(self, Fz, gamma):
        """
        Calculates the maximum negative pure longitudinal force potential (-Dx + SVx).
        Assumes alpha = 0.

        Args:
            Fz (float): Vertical load (N).
            gamma (float): Camber angle (radians).

        Returns:
            float: The maximum potential pure braking force (N, will be negative).
        """
        logger.debug(f"Calculating min Fx potential for Fz={Fz}, gamma={gamma}")
        try:
            Fz_proc, _, _, gamma_proc = self._clamp_inputs(Fz, 0.0, 0.0, gamma)
            dfz = self._compute_dfz(Fz_proc)
            mu_x = self._compute_mu_x(dfz, gamma_proc)
            D_x = self._compute_D_x(mu_x, Fz_proc)
            S_Vx = self._compute_S_Vx(Fz_proc, dfz)
            min_potential = -D_x + S_Vx
            logger.debug(f"Min Fx potential: Dx={D_x:.2f}, SVx={S_Vx:.2f}, Min={min_potential:.2f}")
            return min_potential
        except Exception as e:
            logger.error(f"Error calculating min Fx potential: {e}")
            return 0.0

    # --- Inverse methods for pure slip ---
    def find_kappa_for_fx(self, target_fx, Fz, gamma, tol=1e-4, max_iter=100):
        """
        Finds the slip ratio (kappa) required to generate a target pure
        longitudinal force (Fx), assuming alpha = 0. Aims for smallest magnitude kappa.
        """
        logger.debug(f"Finding kappa for target Fx={target_fx:.2f} N at Fz={Fz:.1f}, gamma={math.degrees(gamma):.2f} deg")
        try:
            Fz_proc, _, _, gamma_proc = self._clamp_inputs(Fz, 0.0, 0.0, gamma)
            min_fx = self.get_min_fx_potential(Fz_proc, gamma_proc)
            max_fx = self.get_peak_fx_potential(Fz_proc, gamma_proc)

            if not (min_fx - tol <= target_fx <= max_fx + tol):
                logger.warning(f"Target Fx={target_fx:.2f} is outside achievable range [{min_fx:.2f}, {max_fx:.2f}] N.")
                return np.nan

            dfz = self._compute_dfz(Fz_proc)
            mu_x = self._compute_mu_x(dfz, gamma_proc)
            K_x_kappa = self._compute_K_x_kappa(Fz_proc, gamma_proc)
            S_Hx = self._compute_S_Hx(dfz)
            S_Vx = self._compute_S_Vx(Fz_proc, dfz)
            D_x = self._compute_D_x(mu_x, Fz_proc)
            C_x = self._compute_C_x()

            def fx_error(kappa_input):
                kappa_eff = self._compute_kappa_eff(kappa_input, S_Hx)
                B_x = self._compute_B_x(K_x_kappa, C_x, D_x)
                E_x = self._compute_E_x(dfz, kappa_eff)
                fx_pure_calc = self._compute_pure_fx(D_x, C_x, B_x, E_x, kappa_eff, S_Vx)
                return fx_pure_calc - target_fx

            search_min = self.min_slip_ratio * 1.1
            search_max = self.max_slip_ratio * 1.1
            try:
                # Prioritize bracket search for robustness
                sol = root_scalar(fx_error, bracket=[search_min, search_max], method='brentq', xtol=tol, maxiter=max_iter)
            except ValueError:
                # If bracketing fails, try a derivative-based method from guess 0
                logger.debug("Bracketing failed for kappa, trying 'newton' from 0.")
                try:
                    # Newton needs fprime, which we don't have easily. Use secant (approximates derivative)
                    # Or use a method that doesn't need derivative like ridder/bisect if bracket possible later
                    # For now, stick to brentq failure means NaN
                     logger.warning("Bracketing failed for kappa search. Returning NaN.")
                     return np.nan
                    # sol = root_scalar(fx_error, x0=0.0, method='secant', xtol=tol, maxiter=max_iter) # Example fallback
                except Exception as fallback_e:
                     logger.warning(f"Fallback solver also failed for kappa: {fallback_e}")
                     return np.nan

            if sol.converged:
                logger.info(f"Found kappa={sol.root:.4f} for target Fx={target_fx:.2f} N.")
                return sol.root
            else:
                logger.warning(f"Root finder for kappa did not converge: {sol.flag}")
                return np.nan

        except Exception as e:
            logger.error(f"Error in find_kappa_for_fx: {e}")
            return np.nan

    def find_alpha_for_fy(self, target_fy, Fz, gamma, tol=1e-4, max_iter=100):
        """
        Finds the slip angle (alpha) required to generate a target pure
        lateral force (Fy), assuming kappa = 0. Aims for smallest magnitude alpha.
        """
        logger.debug(f"Finding alpha for target Fy={target_fy:.2f} N at Fz={Fz:.1f}, gamma={math.degrees(gamma):.2f} deg")
        try:
            Fz_proc, _, _, gamma_proc = self._clamp_inputs(Fz, 0.0, 0.0, gamma)
            dfz = self._compute_dfz(Fz_proc)
            mu_y = self._compute_mu_y(dfz, gamma_proc)
            D_y = self._compute_D_y(mu_y, Fz_proc)
            S_Vy = self._compute_S_Vy(Fz_proc, dfz, gamma_proc)
            max_fy_approx = D_y + S_Vy
            min_fy_approx = -D_y + S_Vy

            if not (min(min_fy_approx, max_fy_approx) - tol <= target_fy <= max(min_fy_approx, max_fy_approx) + tol):
                 logger.warning(f"Target Fy={target_fy:.2f} is outside approximate achievable range [{min_fy_approx:.2f}, {max_fy_approx:.2f}] N.")
                 return np.nan

            K_y_alpha = self._compute_K_y_alpha(Fz_proc, gamma_proc)
            S_Hy = self._compute_S_Hy(dfz, gamma_proc)
            C_y = self._compute_C_y()

            def fy_error(alpha_input):
                alpha_eff = self._compute_alpha_eff(alpha_input, S_Hy)
                B_y = self._compute_B_y(K_y_alpha, C_y, D_y)
                E_y = self._compute_E_y(dfz, gamma_proc, alpha_eff)
                fy_pure_calc = self._compute_pure_fy(D_y, C_y, B_y, E_y, alpha_eff, S_Vy)
                return fy_pure_calc - target_fy

            search_min = self.min_slip_angle * 1.1
            search_max = self.max_slip_angle * 1.1
            try:
                sol = root_scalar(fy_error, bracket=[search_min, search_max], method='brentq', xtol=tol, maxiter=max_iter)
            except ValueError as e:
                logger.warning(f"Bracketing failed for alpha search ({e}). Returning NaN.")
                return np.nan

            if sol.converged:
                logger.info(f"Found alpha={math.degrees(sol.root):.3f} deg for target Fy={target_fy:.2f} N.")
                return sol.root
            else:
                logger.warning(f"Root finder for alpha did not converge: {sol.flag}")
                return np.nan

        except Exception as e:
            logger.error(f"Error in find_alpha_for_fy: {e}")
            return np.nan

    # --- Method prioritizing Fy with intensity control ---
    def find_slips_for_combined_target(self, target_fy, Fz, gamma, longitudinal_mode, longitudinal_intensity=1.0, tol=1e-4):
        """
        Finds slips (alpha, kappa) to achieve target_fy while using a
        specified intensity of the remaining longitudinal capacity.
        """
        logger.info(f"Finding slips for TargetFy={target_fy:.2f} N, Fz={Fz:.1f}, gamma={math.degrees(gamma):.2f} deg, Mode='{longitudinal_mode}', Intensity={longitudinal_intensity:.2f}")
        alpha_req = np.nan
        kappa_req = np.nan
        longitudinal_intensity = max(0.0, min(1.0, longitudinal_intensity))

        try:
            # Step 1: Determine Target Alpha
            alpha_req = self.find_alpha_for_fy(target_fy, Fz, gamma, tol=tol)
            if np.isnan(alpha_req) and target_fy!=0:
                logger.warning(f"Target Fy={target_fy:.2f} N is unachievable. Cannot proceed.")
                return {'alpha': np.nan, 'kappa': np.nan}
            elif target_fy ==0:
                alpha_req = 0
            logger.debug(f"Step 1: Required alpha (approx) = {math.degrees(alpha_req):.3f} deg")

            # Step 2: Estimate Remaining Longitudinal Capacity
            Fz_proc, _, _, gamma_proc = self._clamp_inputs(Fz, 0.0, 0.0, gamma)
            dfz = self._compute_dfz(Fz_proc)
            Fx_peak_pure = self.get_peak_fx_potential(Fz_proc, gamma_proc)
            Fx_min_pure = self.get_min_fx_potential(Fz_proc, gamma_proc)
            B_xa_k0 = self._compute_B_xa(kappa=0.0)
            C_xa = self._compute_C_xa()
            G_xa_approx = self._compute_G_xa(C_xa, B_xa_k0, alpha_req)
            logger.debug(f"Step 2: Approx Gxa(alpha_req, k=0) = {G_xa_approx:.4f}")
            Fx_avail_max = Fx_peak_pure * G_xa_approx
            Fx_avail_min = Fx_min_pure * G_xa_approx
            logger.debug(f"Step 2: Estimated Available Fx Range = [{Fx_avail_min:.2f}, {Fx_avail_max:.2f}] N")

            # Step 3: Determine Target Fx
            target_fx = 0.0
            if longitudinal_mode.lower() == 'accelerate':
                target_fx = longitudinal_intensity * Fx_avail_max
            elif longitudinal_mode.lower() == 'brake':
                target_fx = longitudinal_intensity * Fx_avail_min # Intensity 1.0 = max brake
            elif longitudinal_mode.lower() in ['none', 'coast']:
                target_fx = 0.0
            else:
                logger.warning(f"Invalid longitudinal_mode: '{longitudinal_mode}'. Assuming zero target Fx.")
                target_fx = 0.0
            logger.debug(f"Step 3: Target Fx = {target_fx:.2f} N")

            # Step 4: Determine Target Kappa
            if abs(target_fx) < tol:
                 logger.info("Target longitudinal force is near zero. Setting kappa_req = 0.")
                 kappa_req = 0.0
            else:
                kappa_req = self.find_kappa_for_fx(target_fx, Fz_proc, gamma_proc, tol=tol)
                if np.isnan(kappa_req):
                    logger.warning(f"Could not find kappa for target Fx={target_fx:.2f}. Setting kappa_req = 0.")
                    kappa_req = 0.0
                else:
                     logger.debug(f"Step 4: Required kappa (approx) = {kappa_req:.4f}")

            logger.info(f"Result for combined target: alpha={math.degrees(alpha_req):.3f} deg, kappa={kappa_req:.4f}")
            return {'alpha': alpha_req, 'kappa': kappa_req}

        except Exception as e:
            logger.exception(f"Error in find_slips_for_combined_target: {e}")
            return {'alpha': np.nan, 'kappa': np.nan}



# --- Example Usage ---
if __name__ == "__main__":
    # Configure logger level (e.g., DEBUG to see more messages)

    param_file = 'hoosier_r20.par'
    if not os.path.exists(param_file):
        logger.warning(f"Parameter file '{param_file}' not found. Creating a dummy file for testing.")
        with open(param_file, 'w') as f:
             f.write("# Dummy parameter file\n")
             f.write("[CONSTANTS]\nnominal_load_z = 600.0\nunloaded_radius = 0.2\n")
             f.write("[RANGES]\nmin_load_z=100\nmax_load_z=1000\nmin_slip_angle=-0.3\nmax_slip_angle=0.3\n")
             f.write("min_slip_ratio=-0.3\nmax_slip_ratio=0.3\nmin_camber=-0.1\nmax_camber=0.1\n")
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
                 if 'lat' in key or 'lon' in key or 'comb' in key:
                     f.write(f"{key} = 1.0\n")

    try:
        # Initialize the tire model
        tire = PacejkaTireRefactored(param_file, return_errors=False, history_name="FrontLeftTire")

        # Example conditions
        fz1 = 600.0; alpha1 = math.radians(5.0); kappa1 = 0.05; gamma1 = math.radians(-2.0); time1 = 100
        fz2 = 700.0; alpha2 = math.radians(-8.0); kappa2 = -0.10; gamma2 = math.radians(-2.5); time2 = 535

        # Calculate forces, store history
        forces1 = tire.calculate_forces(fz1, alpha1, kappa1, gamma1, time1, store_history=True)
        forces2 = tire.calculate_forces(fz2, alpha2, kappa2, gamma2, time2, store_history=True)

        # Calculate forces again, don't store
        forces_check = tire.calculate_forces(fz1, alpha1, kappa1, gamma1, time2, store_history=False)

        # Retrieve history DataFrame
        history_df = tire.get_history_dataframe()
        print("\n--- History DataFrame ---")
        print(history_df)
        print("------------------------")

        # Retrieve history for a specific time
        print(f"\nRetrieving history for time = {time2} ms:")
        history_at_time2 = tire.get_history_at_time(time2)
        if history_at_time2 is not None:
            print(f"Found record at {time2} ms:")
            print(history_at_time2) # Print the Pandas Series
        else:
            print(f"No history found for time = {time2} ms.")

        # Clear history
        # tire.clear_history()
        # print("\nHistory cleared.")
        # print(tire.get_history_dataframe())


    except FileNotFoundError as e:
        logger.critical(f"Execution failed: {e}") # Use critical for fatal errors
        print(f"Error: {e}")
    except ValueError as e:
        logger.critical(f"Execution failed: {e}")
        print(f"Error during parameter validation or calculation: {e}")
    except Exception as e:
        logger.exception("An unexpected error occurred during execution:") # Logs traceback
        print(f"An unexpected error occurred: {e}")

