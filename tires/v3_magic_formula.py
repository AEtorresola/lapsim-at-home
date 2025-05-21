
import math
import warnings
import os
import pandas as pd
from logger import setup_logger
from scipy.optimize import root_scalar
import numpy as np
from helper_functions import TimeSeriesStorage, combine_dataframes, append_new_rows

# --- Basic Logger Setup ---
logger = setup_logger()


# --- Simplified PacejkaTireRefactored Class ---
class PacejkaTireSimplified:
    """
    Implements the Pacejka 2002 (Magic Formula 6.1) tire model with
    consolidated calculation methods for improved readability.

    Loads parameters from an external file. Uses TimeSeriesStorage for history.

    Calculates combined longitudinal (Fx) and lateral (Fy) forces based on
    vertical load (Fz), slip angle (alpha), slip ratio (kappa),
    camber angle (gamma), and simulation time (time_ms).
    """

    def __init__(self, parameter_filepath, return_errors=False, history_name="TireHistory"):
        """ Initializes the tire model, loads parameters, sets up history."""
        self.return_errors = return_errors
        self.parameters = {}
        self._history_name = history_name
        logger.info(f"Initializing Pacejka Tire Model from {parameter_filepath}")
        if not os.path.exists(parameter_filepath):
            logger.error(f"Parameter file not found: {parameter_filepath}")
            raise FileNotFoundError(f"Parameter file not found: {parameter_filepath}")
        self._load_parameters_from_file(parameter_filepath)
        self._validate_required_parameters()
        # Set constants and ranges as attributes
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
        self._setup_history_storage()
        logger.info(f"Pacejka Tire Model initialized successfully.")

    def _load_parameters_from_file(self, filepath):
        """Loads parameters from a 'key = value' formatted file."""
        logger.info(f"Loading parameters from: {filepath}")
        try:
            with open(filepath, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#') or line.startswith('!'): continue
                    if line.startswith('[') and line.endswith(']'): continue # Ignore sections for now
                    if '=' not in line: logger.warning(f"Skipping malformed line {line_num} in {filepath}: '{line}'"); continue
                    key, value = line.split('=', 1); key = key.strip(); value = value.strip()
                    try: self.parameters[key] = float(value)
                    except ValueError: logger.warning(f"Non-float value on line {line_num}: '{value}' for key '{key}'. Storing as string."); self.parameters[key] = value
            logger.info(f"Finished loading parameters from {filepath}")
        except Exception as e: logger.error(f"Error reading parameter file {filepath}: {e}"); raise IOError(f"Error reading parameter file {filepath}: {e}")

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
        if missing_keys: logger.error(f"Missing required parameters: {', '.join(missing_keys)}"); raise ValueError(f"Missing required parameters: {', '.join(missing_keys)}")
        logger.info("All required parameters loaded successfully.")

    def _setup_history_storage(self):
        """Helper method to initialize or re-initialize history storage."""
        history_columns = [
            'time', 'Fz_orig', 'alpha_orig', 'kappa_orig', 'gamma_orig', 'Fz_proc', 'alpha_proc', 'kappa_proc', 'gamma_proc',
            'dfz', 'mu_y', 'K_y_alpha', 'S_Hy', 'S_Vy', 'alpha_eff', 'D_y', 'C_y', 'B_y', 'E_y',
            'mu_x', 'K_x_kappa', 'S_Hx', 'S_Vx', 'kappa_eff', 'D_x', 'C_x', 'B_x', 'E_x',
            'B_yk', 'C_yk', 'B_xa', 'C_xa', 'Fx_pure', 'Fy_pure', 'Gxa', 'Gyk', 'Fx', 'Fy'
        ]
        initial_history_data = {col: [] for col in history_columns}
        col_types = {col: float for col in history_columns if col != 'time'}
        self.history_storage = TimeSeriesStorage(initial_history_data, self._history_name, col_types)

    def _clamp_inputs(self, Fz, alpha, kappa, gamma):
        """Clamps or raises errors for inputs outside valid ranges."""
        clamped = False; clamped_vars = []
        original_inputs = {'Fz': Fz, 'alpha': alpha, 'kappa': kappa, 'gamma': gamma}
        if self.min_load_z is None: raise ValueError("Range limits not loaded.") # Basic check
        if not (self.min_load_z <= Fz <= self.max_load_z):
            if self.return_errors: logger.error(f"Input Fz {Fz} out of range"); raise ValueError(f"Fz {Fz} out of range")
            Fz = max(self.min_load_z, min(self.max_load_z, Fz)); clamped = True; clamped_vars.append('Fz')
        if not (self.min_slip_angle <= alpha <= self.max_slip_angle):
            if self.return_errors: logger.error(f"Input alpha {alpha} out of range"); raise ValueError(f"alpha {alpha} out of range")
            alpha = max(self.min_slip_angle, min(self.max_slip_angle, alpha)); clamped = True; clamped_vars.append('alpha')
        if not (self.min_slip_ratio <= kappa <= self.max_slip_ratio):
            if self.return_errors: logger.error(f"Input kappa {kappa} out of range"); raise ValueError(f"kappa {kappa} out of range")
            kappa = max(self.min_slip_ratio, min(self.max_slip_ratio, kappa)); clamped = True; clamped_vars.append('kappa')
        if not (self.min_camber <= gamma <= self.max_camber):
             if self.return_errors: logger.error(f"Input gamma {gamma} out of range"); raise ValueError(f"gamma {gamma} out of range")
             gamma = max(self.min_camber, min(self.max_camber, gamma)); clamped = True; clamped_vars.append('gamma')
        if clamped and not self.return_errors: logger.warning(f"Input(s) clamped: {', '.join(clamped_vars)}. Original={original_inputs}, Clamped={{'Fz': {Fz}, 'alpha': {alpha}, 'kappa': {kappa}, 'gamma': {gamma}}}")
        return Fz, alpha, kappa, gamma

    def _calculate_pure_forces_and_components(self, Fz, alpha, kappa, gamma):
        """
        Calculates intermediate components and pure Fx, Fy forces.
        Consolidates multiple calculation steps.
        """
        p = self.parameters
        nom_load = self.nominal_load_z
        results = {}

        # --- Level 5: Base Components ---
        # Eq 29: Normalized load change
        dfz = (Fz - nom_load) / nom_load if nom_load != 0 else 0
        results['dfz'] = dfz
        fz_ratio = max(Fz / nom_load, 1e-6) if nom_load != 0 else 1e-6

        # Eq 27: Lateral friction potential
        mu_y = (p['lat_peak_friction_d_pdy1'] + p['lat_friction_load_var_pdy2'] * dfz) * \
               (1.0 + p['lat_friction_camber_var_pdy3'] * gamma**2)
        results['mu_y'] = mu_y

        # Eq 28: Cornering stiffness
        K_y_alpha = p['lat_stiffness_k_max_pky1'] * nom_load * \
                    math.sin(p['lat_stiffness_load_max_pky2'] * math.atan(fz_ratio)) * \
                    (1.0 - p['lat_stiffness_camber_var_pky3'] * abs(gamma))
        results['K_y_alpha'] = K_y_alpha

        # Eq 25: Longitudinal friction potential (Approx)
        mu_x = (p['lon_peak_friction_d_pdx1'] + p['lon_friction_load_var_pdx2'] * dfz) * \
               (1.0 + p['lon_friction_camber_var_pdx3'] * gamma**2)
        results['mu_x'] = mu_x

        # Eq 26: Longitudinal stiffness (Approx)
        K_x_kappa = p['lon_stiffness_k_pkx1'] * nom_load * \
                    math.sin(p['lon_stiffness_load_var_pkx2'] * math.atan(fz_ratio)) * \
                    (1.0 - p['lon_stiffness_load_exp_pkx3'] * abs(gamma))
        results['K_x_kappa'] = K_x_kappa

        # --- Level 4: Shifts ---
        # Eq 24: Horizontal shift Fy
        S_Hy = (p['lat_shift_h_phy1'] + p['lat_shift_load_var_phy2'] * dfz) + \
               p['lat_shift_camber_var_phy3'] * gamma
        results['S_Hy'] = S_Hy

        # Eq 23: Vertical shift Fy
        S_Vy = Fz * ((p['lat_shift_v_pvy1'] + p['lat_shift_v_load_var_pvy2'] * dfz) + \
                     (p['lat_shift_v_camber_var_pvy3'] + p['lat_shift_v_camber_load_var_pvy4'] * dfz) * gamma)
        results['S_Vy'] = S_Vy

        # Eq 18: Horizontal shift Fx (Approx)
        S_Hx = p['lon_shift_h_phx1'] + p['lon_shift_load_var_phx2'] * dfz
        results['S_Hx'] = S_Hx

        # Eq 17: Vertical shift Fx (Approx)
        S_Vx = Fz * (p['lon_shift_v_pvx1'] + p['lon_shift_v_load_var_pvx2'] * dfz)
        results['S_Vx'] = S_Vx

        # --- Level 3: Effective Slips ---
        # Eq 12: Effective alpha
        alpha_eff = alpha + S_Hy
        results['alpha_eff'] = alpha_eff

        # Eq 11: Effective kappa
        kappa_eff = kappa + S_Hx
        results['kappa_eff'] = kappa_eff

        # --- Level 4: Magic Formula Parameters (D, C, B, E) ---
        # Lateral (Fy)
        # Eq 19: Peak factor Fy
        D_y = mu_y * Fz
        results['D_y'] = D_y
        # Eq 20: Shape factor Fy
        C_y = p['lat_shape_factor_c_pcy1']
        results['C_y'] = C_y
        # Eq 21: Stiffness factor Fy
        denominator_by = C_y * D_y
        B_y = K_y_alpha / denominator_by if abs(denominator_by) > 1e-6 else 0.0
        results['B_y'] = B_y
        # Eq 22: Curvature factor Fy
        E_y_base = p['lat_curve_e_pey1'] + p['lat_curve_load_var_pey2'] * dfz
        E_y_gamma_term = p['lat_curve_camber_dep_0_pey3'] + p['lat_curve_camber_var_pey4'] * gamma
        alpha_eff_sign = math.copysign(1, alpha_eff) if alpha_eff != 0 else 0
        E_y = E_y_base * (1.0 - E_y_gamma_term * alpha_eff_sign)
        results['E_y'] = E_y

        # Longitudinal (Fx - Approx)
        # Eq 13: Peak factor Fx
        D_x = mu_x * Fz
        results['D_x'] = D_x
        # Eq 14: Shape factor Fx
        C_x = p['lon_shape_factor_c_pcx1']
        results['C_x'] = C_x
        # Eq 15: Stiffness factor Fx
        denominator_bx = C_x * D_x
        B_x = K_x_kappa / denominator_bx if abs(denominator_bx) > 1e-6 else 0.0
        results['B_x'] = B_x
        # Eq 16: Curvature factor Fx (Simplified as PEX3=PEX4=0)
        E_x = p['lon_curve_e_pex1'] + p['lon_curve_load_var_pex2'] * dfz
        results['E_x'] = E_x

        # --- Level 2: Pure Forces ---
        # Eq 6: Pure lateral force
        if abs(B_y) < 1e-9: Fy_pure = S_Vy
        else:
            X_y = B_y * alpha_eff
            try:
                arctan_Xy = math.atan(X_y)
                inner_arg_y = C_y * math.atan(X_y - E_y * (X_y - arctan_Xy))
                Fy_pure = D_y * math.sin(inner_arg_y) + S_Vy
            except ValueError as e: logger.warning(f"Math domain error in Fy_pure: {e}"); Fy_pure = S_Vy
        results['Fy_pure'] = Fy_pure

        # Eq 5: Pure longitudinal force
        if abs(B_x) < 1e-9: Fx_pure = S_Vx
        else:
            X_x = B_x * kappa_eff
            try:
                arctan_Xx = math.atan(X_x)
                inner_arg_x = C_x * math.atan(X_x - E_x * (X_x - arctan_Xx))
                Fx_pure = D_x * math.sin(inner_arg_x) + S_Vx
            except ValueError as e: logger.warning(f"Math domain error in Fx_pure: {e}"); Fx_pure = S_Vx
        results['Fx_pure'] = Fx_pure

        return results

    def _calculate_combined_slip_factors(self, alpha, kappa):
        """ Calculates combined slip weighting factors Gxa and Gyk. """
        p = self.parameters
        results = {}

        # --- Level 3: Weighting Factor Components (Approx) ---
        # Eq 7: Slope factor B_xa
        B_xa = p['comb_lon_slope_b_rbx1'] * math.cos(math.atan(p['comb_lon_slope_kappa_var_rbx2'] * kappa))
        results['B_xa'] = B_xa
        # Eq 8: Shape factor C_xa
        C_xa = p['comb_lon_shape_c_rcx1']
        results['C_xa'] = C_xa
        # Eq 9: Slope factor B_yk
        B_yk = p['comb_lat_slope_b_rby1'] * math.cos(math.atan(p['comb_lat_slope_alpha_var_rby2'] * (alpha - p['comb_lat_slope_alpha_shift_rby3'])))
        results['B_yk'] = B_yk
        # Eq 10: Shape factor C_yk
        C_yk = p['comb_lat_shape_c_rcy1']
        results['C_yk'] = C_yk

        # --- Level 2: Weighting Factors (Approx) ---
        # Eq 3: Weighting factor G_xa
        arg_xa = max(-100.0, min(100.0, B_xa * alpha))
        G_xa = math.cos(C_xa * math.atan(arg_xa))
        results['Gxa'] = G_xa
        # Eq 4: Weighting factor G_yk
        arg_yk = max(-100.0, min(100.0, B_yk * kappa))
        G_yk = math.cos(C_yk * math.atan(arg_yk))
        results['Gyk'] = G_yk

        return results

    def calculate_forces(self, Fz, alpha, kappa, gamma, time_ms, store_history=False):
        """ Calculates combined Fx and Fy using consolidated helper methods. """
        logger.debug(f"Calculating forces for time {time_ms} ms. Inputs: Fz={Fz}, alpha={alpha}, kappa={kappa}, gamma={gamma}")
        original_inputs = {'Fz': Fz, 'alpha': alpha, 'kappa': kappa, 'gamma': gamma, 'time_ms': time_ms}

        try:
            # Clamp Inputs
            Fz_proc, alpha_proc, kappa_proc, gamma_proc = self._clamp_inputs(Fz, alpha, kappa, gamma)

            # Calculate Pure Forces and necessary components
            pure_force_calcs = self._calculate_pure_forces_and_components(Fz_proc, alpha_proc, kappa_proc, gamma_proc)
            Fx_pure = pure_force_calcs['Fx_pure']
            Fy_pure = pure_force_calcs['Fy_pure']

            # Calculate Combined Slip Factors
            combined_slip_factors = self._calculate_combined_slip_factors(alpha_proc, kappa_proc)
            G_xa = combined_slip_factors['Gxa']
            G_yk = combined_slip_factors['Gyk']

            # --- Level 1: Final Combined Forces ---
            # Eq 1: Combined Fx
            Fx_combined = Fx_pure * G_xa
            # Eq 2: Combined Fy
            Fy_combined = Fy_pure * G_yk

            if store_history:
                logger.debug(f"Storing history for time {time_ms} ms.")
                # Prepare data row for TimeSeriesStorage update
                history_data_row = {
                    'Fz_orig': Fz, 'alpha_orig': alpha, 'kappa_orig': kappa, 'gamma_orig': gamma,
                    'Fz_proc': Fz_proc, 'alpha_proc': alpha_proc, 'kappa_proc': kappa_proc, 'gamma_proc': gamma_proc,
                    **pure_force_calcs, # Unpack results from pure force calculation
                    **combined_slip_factors, # Unpack results from combined slip calculation
                    'Fx': Fx_combined, 'Fy': Fy_combined
                }
                # Remove redundant keys if necessary (e.g., if pure_force_calcs contained Fx/Fy)
                # Ensure all expected columns exist in history_data_row before updating
                expected_cols = self.history_storage._initial_columns
                row_to_store = {k: history_data_row.get(k, np.nan) for k in expected_cols if k != 'time'}

                try:
                    self.history_storage.update(row_to_store, time_ms)
                except Exception as e: logger.error(f"Failed to store history at time {time_ms}: {e}")

            logger.debug(f"Force calculation complete for time {time_ms}. Fx={Fx_combined:.2f}, Fy={Fy_combined:.2f}")
            return {'Fx': Fx_combined, 'Fy': Fy_combined}

        except Exception as e:
            logger.exception(f"Error during force calculation at time {time_ms}:") # Log traceback
            return {'Fx': 0.0, 'Fy': 0.0} # Return safe values

    # --- Peak Potential Methods (Consolidated) ---
    def get_peak_fx_potential(self, Fz, gamma):
        """ Calculates the maximum positive pure longitudinal force potential (Dx + SVx). """
        logger.debug(f"Calculating peak Fx potential for Fz={Fz}, gamma={gamma}")
        try:
            Fz_proc, _, _, gamma_proc = self._clamp_inputs(Fz, 0.0, 0.0, gamma)
            p = self.parameters
            nom_load = self.nominal_load_z
            # Calculate necessary components inline
            dfz = (Fz_proc - nom_load) / nom_load if nom_load != 0 else 0
            mu_x = (p['lon_peak_friction_d_pdx1'] + p['lon_friction_load_var_pdx2'] * dfz) * \
                   (1.0 + p['lon_friction_camber_var_pdx3'] * gamma_proc**2)
            D_x = mu_x * Fz_proc
            S_Vx = Fz_proc * (p['lon_shift_v_pvx1'] + p['lon_shift_v_load_var_pvx2'] * dfz)
            peak_potential = D_x + S_Vx
            logger.debug(f"Peak Fx potential: Dx={D_x:.2f}, SVx={S_Vx:.2f}, Peak={peak_potential:.2f}")
            return peak_potential
        except Exception as e: logger.error(f"Error calculating peak Fx potential: {e}"); return 0.0

    def get_min_fx_potential(self, Fz, gamma):
        """ Calculates the maximum negative pure longitudinal force potential (-Dx + SVx). """
        logger.debug(f"Calculating min Fx potential for Fz={Fz}, gamma={gamma}")
        try:
            Fz_proc, _, _, gamma_proc = self._clamp_inputs(Fz, 0.0, 0.0, gamma)
            p = self.parameters
            nom_load = self.nominal_load_z
            # Calculate necessary components inline
            dfz = (Fz_proc - nom_load) / nom_load if nom_load != 0 else 0
            mu_x = (p['lon_peak_friction_d_pdx1'] + p['lon_friction_load_var_pdx2'] * dfz) * \
                   (1.0 + p['lon_friction_camber_var_pdx3'] * gamma_proc**2)
            D_x = mu_x * Fz_proc
            S_Vx = Fz_proc * (p['lon_shift_v_pvx1'] + p['lon_shift_v_load_var_pvx2'] * dfz)
            min_potential = -D_x + S_Vx
            logger.debug(f"Min Fx potential: Dx={D_x:.2f}, SVx={S_Vx:.2f}, Min={min_potential:.2f}")
            return min_potential
        except Exception as e: logger.error(f"Error calculating min Fx potential: {e}"); return 0.0

    # --- Inverse Methods (Corrected for Peak Targets v4 - Using Optimizer + Enhanced Logging) ---
    def find_kappa_for_fx(self, target_fx, Fz, gamma, tol=1e-4, max_iter=100):
        """ Finds kappa for target pure Fx, using optimization for peaks. (Corrected v4 + Logging) """
        # Use a local logger instance if preferred, or the class/module logger
        local_logger = setup_logger()
        local_logger.debug(f"Starting: target_fx={target_fx:.4f}, Fz={Fz:.1f}, gamma={math.degrees(gamma):.2f} deg")

        try:
            # Clamp Inputs
            Fz_proc, _, _, gamma_proc = self._clamp_inputs(Fz, 0.0, 0.0, gamma)
            local_logger.debug(f"Clamped inputs: Fz_proc={Fz_proc:.1f}, gamma_proc={gamma_proc:.4f} rad")

            # Calculate components needed
            p = self.parameters; nom_load = self.nominal_load_z
            dfz = (Fz_proc - nom_load) / nom_load if nom_load != 0 else 0
            fz_ratio = max(Fz_proc / nom_load, 1e-6) if nom_load != 0 else 1e-6
            mu_x = (p['lon_peak_friction_d_pdx1'] + p['lon_friction_load_var_pdx2'] * dfz) * (1.0 + p['lon_friction_camber_var_pdx3'] * gamma_proc**2)
            K_x_kappa = p['lon_stiffness_k_pkx1'] * nom_load * math.sin(p['lon_stiffness_load_var_pkx2'] * math.atan(fz_ratio)) * (1.0 - p['lon_stiffness_load_exp_pkx3'] * abs(gamma_proc))
            S_Hx = p['lon_shift_h_phx1'] + p['lon_shift_load_var_phx2'] * dfz
            S_Vx = Fz_proc * (p['lon_shift_v_pvx1'] + p['lon_shift_v_load_var_pvx2'] * dfz)
            D_x = mu_x * Fz_proc
            C_x = p['lon_shape_factor_c_pcx1']
            E_x_base = p['lon_curve_e_pex1'] + p['lon_curve_load_var_pex2'] * dfz
            local_logger.debug(f"Components: dfz={dfz:.4f}, mu_x={mu_x:.4f}, K_x_k={K_x_kappa:.2f}, S_Hx={S_Hx:.4f}, S_Vx={S_Vx:.2f}, D_x={D_x:.2f}, C_x={C_x:.4f}, E_x_base={E_x_base:.4f}")

            # import pdb; pdb.set_trace() 
            # 1. Check Achievable Range
            min_fx = -D_x + S_Vx
            max_fx = D_x + S_Vx
            local_logger.debug(f"Achievable Fx range: [{min_fx:.4f}, {max_fx:.4f}]")
            if not (min_fx - tol <= target_fx <= max_fx + tol):
                local_logger.warning(f"Target Fx={target_fx:.4f} is outside achievable range.")
                return np.nan

            # import pdb; pdb.set_trace() 
            # 2. Handle Target Fx near Vertical Shift (Zero Effective Slip)
            if abs(target_fx - S_Vx) < tol:
                 kappa_result = -S_Hx
                 kappa_result = max(self.min_slip_ratio, min(self.max_slip_ratio, kappa_result))
                 local_logger.info(f"Target Fx ({target_fx:.4f}) near vertical shift ({S_Vx:.4f}). Returning kappa = -S_Hx = {kappa_result:.4f}")
                 return kappa_result

            # import pdb; pdb.set_trace() 
            # --- Define function to calculate Fx_pure ---
            def calculate_fx_pure_at_kappa(kappa_input):
                kappa_eff = kappa_input + S_Hx
                denominator_bx = C_x * D_x
                B_x = K_x_kappa / denominator_bx if abs(denominator_bx) > 1e-6 else 0.0
                E_x = E_x_base
                if abs(B_x) < 1e-9: return S_Vx
                X_x = B_x * kappa_eff
                # import pdb; pdb.set_trace() 
                try:
                    arctan_Xx = math.atan(X_x)
                    inner_arg_x = C_x * math.atan(X_x - E_x * (X_x - arctan_Xx))
                    return D_x * math.sin(inner_arg_x) + S_Vx
                except ValueError: return S_Vx

            # import pdb; pdb.set_trace() 
            # 3. Check if target is near peak and use optimizer if so
            is_near_max = abs(target_fx - max_fx) < tol
            is_near_min = abs(target_fx - min_fx) < tol

            if is_near_max or is_near_min:
                import pdb; pdb.set_trace() 
                local_logger.info(f"Target Fx={target_fx:.4f} is near extremum ({'max' if is_near_max else 'min'}). Using optimizer.")
                func_to_minimize = lambda k: -calculate_fx_pure_at_kappa(k) if is_near_max else calculate_fx_pure_at_kappa(k)
                opt_bounds = (self.min_slip_ratio, self.max_slip_ratio)
                local_logger.debug(f"Optimizing with bounds: {opt_bounds}")
                import pdb; pdb.set_trace() 
                opt_result = minimize_scalar(func_to_minimize, bounds=opt_bounds, method='bounded', options={'xatol': tol, 'maxiter': max_iter})

                if opt_result.success:
                    peak_kappa = opt_result.x
                    found_fx = calculate_fx_pure_at_kappa(peak_kappa)
                    local_logger.info(f"Optimizer found extremum kappa={peak_kappa:.4f} giving Fx={found_fx:.2f} (Target was {target_fx:.2f})")
                    import pdb; pdb.set_trace() 
                    return max(self.min_slip_ratio, min(self.max_slip_ratio, peak_kappa))
                else:
                    import pdb; pdb.set_trace() 
                    local_logger.warning(f"Optimizer failed to find extremum for target Fx={target_fx:.2f}. Status: {opt_result.message}")
                    return np.nan # Optimizer failed

            else:
                # 4. Target is not near peak, use root-finding
                local_logger.debug("Target Fx not near extremum. Using root-finder.")
                def fx_error(kappa_input):
                    return calculate_fx_pure_at_kappa(kappa_input) - target_fx

                search_min = self.min_slip_ratio * 1.1; search_max = self.max_slip_ratio * 1.1
                if abs(search_min - search_max) < 1e-9: local_logger.warning("Slip ratio search range is too small."); return np.nan
                local_logger.debug(f"Root finding bracket: [{search_min:.4f}, {search_max:.4f}]")

                try:
                    err_min = fx_error(search_min); err_max = fx_error(search_max)
                    local_logger.debug(f"Errors at boundaries: f({search_min:.4f})={err_min:.4f}, f({search_max:.4f})={err_max:.4f}")
                    if abs(err_min) < tol: local_logger.info("Root found at lower boundary."); return search_min
                    if abs(err_max) < tol: local_logger.info("Root found at upper boundary."); return search_max

                    import pdb; pdb.set_trace() 
                    if np.sign(err_min) != np.sign(err_max):
                        local_logger.debug("Signs differ, trying brentq...")
                        sol = root_scalar(fx_error, bracket=[search_min, search_max], method='brentq', xtol=tol, maxiter=max_iter)
                        if sol.converged: local_logger.info(f"Found kappa={sol.root:.4f} for target Fx={target_fx:.2f} (brentq)."); return sol.root
                        else: local_logger.warning(f"Kappa solver (brentq) failed: {sol.flag}"); return np.nan
                    else:
                        local_logger.warning(f"Kappa bracketing failed. Trying ridder.")
                        import pdb; pdb.set_trace() 
                        try: # Fallback to ridder
                             sol = root_scalar(fx_error, bracket=[search_min, search_max], method='ridder', xtol=tol, maxiter=max_iter)
                             if sol.converged: local_logger.info(f"Found kappa={sol.root:.4f} for target Fx={target_fx:.2f} (ridder)."); return sol.root
                             else: local_logger.warning(f"Kappa solver (ridder) also failed: {sol.flag}"); return np.nan
                        except ValueError as e_ridder: local_logger.warning(f"Ridder method also failed for kappa: {e_ridder}"); return np.nan
                except ValueError as e_root: local_logger.warning(f"Root finding error for kappa: {e_root}"); return np.nan

        except Exception as e:
            import pdb; pbd.set_trace()
            local_logger.error(f"Unexpected error in find_kappa_for_fx: {e}", exc_info=True) # Log traceback for unexpected errors
            return np.nan    

    def find_alpha_for_fy(self, target_fy, Fz, gamma, tol=1e-4, max_iter=100):
        """ Finds alpha for target pure Fy, handling peaks by adjusting target. (Corrected v3) """
        logger.debug(f"Finding alpha for target Fy={target_fy:.2f} N at Fz={Fz:.1f}, gamma={math.degrees(gamma):.2f} deg")
        try:
            # ... (Setup Fz_proc, gamma_proc, p, nom_load, dfz, fz_ratio) ...
            Fz_proc, _, _, gamma_proc = self._clamp_inputs(Fz, 0.0, 0.0, gamma)
            p = self.parameters; nom_load = self.nominal_load_z
            dfz = (Fz_proc - nom_load) / nom_load if nom_load != 0 else 0
            fz_ratio = max(Fz_proc / nom_load, 1e-6) if nom_load != 0 else 1e-6

            # ... (Calculate components: mu_y, D_y, S_Vy, K_y_alpha, S_Hy, C_y, E_y_base, E_y_gamma_term) ...
            mu_y = (p['lat_peak_friction_d_pdy1'] + p['lat_friction_load_var_pdy2'] * dfz) * (1.0 + p['lat_friction_camber_var_pdy3'] * gamma_proc**2)
            D_y = mu_y * Fz_proc
            S_Vy = Fz_proc * ((p['lat_shift_v_pvy1'] + p['lat_shift_v_load_var_pvy2'] * dfz) + (p['lat_shift_v_camber_var_pvy3'] + p['lat_shift_v_camber_load_var_pvy4'] * dfz) * gamma_proc)
            K_y_alpha = p['lat_stiffness_k_max_pky1'] * nom_load * math.sin(p['lat_stiffness_load_max_pky2'] * math.atan(fz_ratio)) * (1.0 - p['lat_stiffness_camber_var_pky3'] * abs(gamma_proc))
            S_Hy = (p['lat_shift_h_phy1'] + p['lat_shift_load_var_phy2'] * dfz) + p['lat_shift_camber_var_phy3'] * gamma_proc
            C_y = p['lat_shape_factor_c_pcy1']
            E_y_base = p['lat_curve_e_pey1'] + p['lat_curve_load_var_pey2'] * dfz
            E_y_gamma_term = p['lat_curve_camber_dep_0_pey3'] + p['lat_curve_camber_var_pey4'] * gamma_proc

            # 1. Check Achievable Range (Approximate)
            max_fy_approx = D_y + S_Vy
            min_fy_approx = -D_y + S_Vy
            fy_lower_bound = min(min_fy_approx, max_fy_approx)
            fy_upper_bound = max(min_fy_approx, max_fy_approx)
            target_fy_solver = target_fy # Target used for the solver

            if not (fy_lower_bound - tol <= target_fy <= fy_upper_bound + tol):
                 logger.warning(f"Target Fy={target_fy:.2f} outside approx range [{fy_lower_bound:.2f}, {fy_upper_bound:.2f}]")
                 return np.nan

            # 2. Handle Target Fy near Vertical Shift
            if abs(target_fy - S_Vy) < tol:
                 alpha_result = -S_Hy
                 alpha_result = max(self.min_slip_angle, min(self.max_slip_angle, alpha_result))
                 logger.info(f"Target Fy ({target_fy:.2f}) near vertical shift ({S_Vy:.2f}). Returning alpha = -S_Hy = {math.degrees(alpha_result):.3f} deg")
                 return alpha_result

            # 3. Check if target is near peak and adjust slightly for solver stability
            peak_adjustment_factor = 1e-3
            if abs(target_fy - fy_upper_bound) < tol:
                target_fy_solver = fy_upper_bound - abs(fy_upper_bound * peak_adjustment_factor) # Move slightly down
                logger.debug(f"Adjusting target Fy near upper bound from {target_fy:.4f} to {target_fy_solver:.4f} to aid solver.")
            elif abs(target_fy - fy_lower_bound) < tol:
                target_fy_solver = fy_lower_bound + abs(fy_lower_bound * peak_adjustment_factor) # Move slightly up
                logger.debug(f"Adjusting target Fy near lower bound from {target_fy:.4f} to {target_fy_solver:.4f} to aid solver.")


            # 4. Define the error function (using potentially adjusted target)
            def fy_error(alpha_input):
                # ... (fy_error function definition remains the same) ...
                alpha_eff = alpha_input + S_Hy
                denominator_by = C_y * D_y
                B_y = K_y_alpha / denominator_by if abs(denominator_by) > 1e-6 else 0.0
                alpha_eff_sign = math.copysign(1, alpha_eff) if alpha_eff != 0 else 0
                E_y = E_y_base * (1.0 - E_y_gamma_term * alpha_eff_sign)
                if abs(B_y) < 1e-9: fy_pure_calc = S_Vy
                else:
                    X_y = B_y * alpha_eff
                    try:
                        arctan_Xy = math.atan(X_y)
                        inner_arg_y = C_y * math.atan(X_y - E_y * (X_y - arctan_Xy))
                        fy_pure_calc = D_y * math.sin(inner_arg_y) + S_Vy
                    except ValueError: fy_pure_calc = S_Vy
                # Use the potentially adjusted target_fy_solver here
                return fy_pure_calc - target_fy_solver

            # 5. Use root-finding algorithm
            # ... (solver logic with brentq/ridder as before) ...
            search_min = self.min_slip_angle * 1.1; search_max = self.max_slip_angle * 1.1
            if abs(search_min - search_max) < 1e-9: logger.warning("Slip angle search range too small."); return np.nan
            try:
                err_min = fy_error(search_min); err_max = fy_error(search_max)
                if abs(err_min) < tol: return search_min
                if abs(err_max) < tol: return search_max
                if np.sign(err_min) != np.sign(err_max):
                    sol = root_scalar(fy_error, bracket=[search_min, search_max], method='brentq', xtol=tol, maxiter=max_iter)
                    if sol.converged: logger.info(f"Found alpha={math.degrees(sol.root):.3f} deg for target Fy={target_fy:.2f} (brentq)."); return sol.root
                    else: logger.warning(f"Alpha solver (brentq) failed: {sol.flag}"); return np.nan
                else:
                    logger.warning(f"Alpha bracketing failed (errors: f({search_min:.3f})={err_min:.3f}, f({search_max:.3f})={err_max:.3f}). Trying ridder.")
                    try: # Fallback to ridder
                         sol = root_scalar(fy_error, bracket=[search_min, search_max], method='ridder', xtol=tol, maxiter=max_iter)
                         if sol.converged: logger.info(f"Found alpha={math.degrees(sol.root):.3f} deg for target Fy={target_fy:.2f} (ridder)."); return sol.root
                         else: logger.warning(f"Alpha solver (ridder) also failed: {sol.flag}"); return np.nan
                    except ValueError: logger.warning("Ridder method also failed for alpha."); return np.nan
            except ValueError as e: logger.warning(f"Root finding error for alpha: {e}"); return np.nan

        except Exception as e:
            logger.error(f"Unexpected error in find_alpha_for_fy: {e}")
            return np.nan

    def find_slips_prioritizing_fy(self, target_fy, Fz, gamma, longitudinal_mode, longitudinal_intensity=1.0, tol=1e-4):
        """ Finds alpha for target_fy, then kappa for scaled remaining Fx capacity. """
        logger.info(f"Finding slips for target Fy={target_fy:.2f} N, Fz={Fz:.1f}, gamma={math.degrees(gamma):.2f} deg, mode='{longitudinal_mode}', intensity={longitudinal_intensity:.2f}")
        alpha_req = np.nan; kappa_req = np.nan
        try:
            # Step 1: Find Alpha for Target Fy
            alpha_req = self.find_alpha_for_fy(target_fy, Fz, gamma, tol=tol)
            if np.isnan(alpha_req): logger.warning(f"Target Fy={target_fy:.2f} N unachievable."); return {'alpha': np.nan, 'kappa': np.nan}
            logger.debug(f"Step 1: Required alpha (approx) = {math.degrees(alpha_req):.3f} deg")

            # Step 2: Estimate Remaining Fx Capacity
            Fz_proc, _, _, gamma_proc = self._clamp_inputs(Fz, 0.0, 0.0, gamma)
            Fx_peak_pure = self.get_peak_fx_potential(Fz_proc, gamma_proc)
            Fx_min_pure = self.get_min_fx_potential(Fz_proc, gamma_proc)
            # import pdb; pdb.set_trace()
            # Estimate Gxa at kappa=0
            p = self.parameters
            B_xa_k0 = p['comb_lon_slope_b_rbx1'] * math.cos(math.atan(p['comb_lon_slope_kappa_var_rbx2'] * 0.0))
            C_xa = p['comb_lon_shape_c_rcx1']
            arg_xa = max(-100.0, min(100.0, B_xa_k0 * alpha_req)) # Use alpha_req
            G_xa_approx = math.cos(C_xa * math.atan(arg_xa))
            logger.debug(f"Step 2: Approx Gxa(alpha_req, k=0) = {G_xa_approx:.4f}")

            Fx_avail_max = Fx_peak_pure * G_xa_approx
            Fx_avail_min = Fx_min_pure * G_xa_approx

            import pdb; pdb.set_trace()
            # Step 3: Determine Target Fx based on mode and intensity
            target_fx = 0.0
            if longitudinal_mode.lower() == 'accelerate':
                target_fx = longitudinal_intensity * Fx_avail_max
                logger.debug(f"Step 3: Target Accel Fx = {target_fx:.2f} N (AvailMax={Fx_avail_max:.2f})")
            elif longitudinal_mode.lower() == 'brake':
                target_fx = longitudinal_intensity * Fx_avail_min # Intensity scales magnitude
                logger.debug(f"Step 3: Target Brake Fx = {target_fx:.2f} N (AvailMin={Fx_avail_min:.2f})")
            elif longitudinal_mode.lower() not in ['none', 'coast']:
                logger.warning(f"Invalid longitudinal_mode: '{longitudinal_mode}'. Assuming zero target Fx.")

            # Step 4: Find Kappa for Target Fx
            if abs(target_fx) < tol: logger.info("Target longitudinal force is near zero. Setting kappa_req = 0."); kappa_req = 0.0
            else:
                import pdb; pdb.set_trace()
                kappa_req = self.find_kappa_for_fx(target_fx, Fz_proc, gamma_proc, tol=tol)
                if np.isnan(kappa_req): logger.warning(f"Could not find kappa for target Fx={target_fx:.2f}. Setting kappa_req = 0."); kappa_req = 0.0
                else: logger.debug(f"Step 4: Required kappa (approx) = {kappa_req:.4f}")

            logger.info(f"Result: alpha={math.degrees(alpha_req):.3f} deg, kappa={kappa_req:.4f}")
            import pdb; pdb.set_trace()
            return {'alpha': alpha_req, 'kappa': kappa_req}
        except Exception as e: logger.error(f"Error in find_slips_prioritizing_fy: {e}"); return {'alpha': np.nan, 'kappa': np.nan}

    # --- History Management ---
    def get_history_dataframe(self): return self.history_storage.get_dataframe()
    def get_history_at_time(self, time_ms): return self.history_storage.get_time_series(time_ms)
    def clear_history(self): logger.info(f"Clearing history for {self.history_storage.name}"); self.history_storage.clear()


# --- Example Usage (Illustrating Simplified Structure) ---
if __name__ == "__main__":
    logger.setLevel(logging.DEBUG) # Set to DEBUG to see more detailed logs

    param_file = 'hoosier_r20.par'
    # ... (param_file check/creation as before) ...

    try:
        tire = PacejkaTireSimplified(param_file, return_errors=False)

        # --- Test calculate_forces ---
        fz1=600; alpha1=math.radians(5); kappa1=0.05; gamma1=math.radians(-2); time1=100
        forces1 = tire.calculate_forces(fz1, alpha1, kappa1, gamma1, time1, store_history=True)
        print(f"\n--- Calculate Forces Example ---")
        print(f"Time: {time1} ms, Inputs: Fz={fz1}, alpha={alpha1:.3f}, kappa={kappa1:.3f}, gamma={gamma1:.3f}")
        print(f"Outputs: Fx={forces1['Fx']:.2f}, Fy={forces1['Fy']:.2f}")

        # --- Test Inverse Method (Prioritizing Fy) ---
        target_fy = -1500.0
        fz2 = 700.0
        gamma2 = math.radians(-1.0)
        time2 = 200

        print(f"\n--- Find Slips Prioritizing Fy Example ---")
        print(f"Target Fy={target_fy} N, Fz={fz2} N, gamma={math.degrees(gamma2):.2f} deg, Mode=Accelerate, Intensity=0.8")
        slips_accel = tire.find_slips_prioritizing_fy(target_fy, fz2, gamma2, 'accelerate', longitudinal_intensity=0.8)
        if not np.isnan(slips_accel['alpha']):
            print(f"  Result: alpha={math.degrees(slips_accel['alpha']):.3f} deg, kappa={slips_accel['kappa']:.4f}")
            # Verification
            verify_forces = tire.calculate_forces(fz2, slips_accel['alpha'], slips_accel['kappa'], gamma2, time2)
            print(f"  Verification: Fx={verify_forces['Fx']:.1f} N, Fy={verify_forces['Fy']:.1f} N (Target Fy was {target_fy:.1f})")

        print(f"\nTarget Fy={target_fy} N, Fz={fz2} N, gamma={math.degrees(gamma2):.2f} deg, Mode=Brake, Intensity=1.0")
        slips_brake = tire.find_slips_prioritizing_fy(target_fy, fz2, gamma2, 'brake', longitudinal_intensity=1.0)
        if not np.isnan(slips_brake['alpha']):
            print(f"  Result: alpha={math.degrees(slips_brake['alpha']):.3f} deg, kappa={slips_brake['kappa']:.4f}")
            verify_forces = tire.calculate_forces(fz2, slips_brake['alpha'], slips_brake['kappa'], gamma2, time2+100)
            print(f"  Verification: Fx={verify_forces['Fx']:.1f} N, Fy={verify_forces['Fy']:.1f} N (Target Fy was {target_fy:.1f})")

    except:
        pass
