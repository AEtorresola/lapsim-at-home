
import math
import warnings

class PacejkaTireRefactored:
    """
    Implements the Pacejka 2002 (Magic Formula 6.1) tire model with
    a sequential calculation structure for clarity and traceability.

    Calculates combined longitudinal (Fx) and lateral (Fy) forces based on
    vertical load (Fz), slip angle (alpha), slip ratio (kappa), and
    camber angle (gamma).

    Uses parameters from a specific .tir file for lateral behavior and
    approximations for longitudinal and combined slip behavior where
    data is missing.

    Attributes:
        history (list): Stores records of calculations if requested.
        return_errors (bool): Flag to determine error handling behavior.
    """

    def __init__(self, return_errors=False):
        """
        Initializes the PacejkaTire object with parameters and settings.
        (Parameter definitions and mapping remain the same as before)
        """
        self.return_errors = return_errors
        self.history = []

        # --- Parameter Mapping (Descriptive Name: Pacejka Name) ---
        # [VERTICAL]
        self.nominal_load_z = 667.0  # FNOMIN (N)
        # [DIMENSION]
        self.unloaded_radius = 0.2032 # UNLOADED_RADIUS (m) R0
        # [RANGES]
        self.min_slip_ratio = -0.25 # KPUMIN
        self.max_slip_ratio = 0.25  # KPUMAX
        self.min_slip_angle = -0.261799 # ALPMIN (rad) approx -15 deg
        self.max_slip_angle = 0.261799  # ALPMAX (rad) approx 15 deg
        self.min_camber = -0.069813 # CAMMIN (rad) approx -4 deg
        self.max_camber = 0.069813  # CAMMAX (rad) approx 4 deg
        self.min_load_z = 100.0     # FZMIN (N)
        self.max_load_z = 1110.0    # FZMAX (N)

        # --- Lateral Coefficients (From .tir file) ---
        self.lat_shape_factor_c_pcy1 = 1.25788
        self.lat_peak_friction_d_pdy1 = -2.50993
        self.lat_friction_load_var_pdy2 = 0.0780647
        self.lat_friction_camber_var_pdy3 = 8.37358
        self.lat_curve_e_pey1 = -0.59049
        self.lat_curve_load_var_pey2 = 0.162594
        self.lat_curve_camber_dep_0_pey3 = 0.0
        self.lat_curve_camber_var_pey4 = 10.3142
        self.lat_stiffness_k_max_pky1 = -46.3491
        self.lat_stiffness_load_max_pky2 = 1.4492
        self.lat_stiffness_camber_var_pky3 = 0.639078
        self.lat_shift_h_phy1 = -0.00108397
        self.lat_shift_load_var_phy2 = 0.00258753
        self.lat_shift_camber_var_phy3 = 0.112578
        self.lat_shift_v_pvy1 = -0.0292988
        self.lat_shift_v_load_var_pvy2 = 0.0487652
        self.lat_shift_v_camber_var_pvy3 = -0.586156
        self.lat_shift_v_camber_load_var_pvy4 = -0.716249

        # --- Longitudinal Coefficients (Approximated) ---
        self.lon_shape_factor_c_pcx1 = self.lat_shape_factor_c_pcy1
        self.lon_peak_friction_d_pdx1 = -self.lat_peak_friction_d_pdy1 * 1.1
        self.lon_friction_load_var_pdx2 = self.lat_friction_load_var_pdy2 * 0.8
        self.lon_friction_camber_var_pdx3 = self.lat_friction_camber_var_pdy3 * 0.3
        self.lon_curve_e_pex1 = -self.lat_curve_e_pey1 * 0.9
        self.lon_curve_load_var_pex2 = self.lat_curve_load_var_pey2 * 0.9
        self.lon_curve_load_sq_var_pex3 = 0.0
        self.lon_curve_driving_factor_pex4 = 0.0
        self.lon_stiffness_k_pkx1 = -self.lat_stiffness_k_max_pky1 * 2.0
        self.lon_stiffness_load_var_pkx2 = self.lat_stiffness_load_max_pky2
        self.lon_stiffness_load_exp_pkx3 = self.lat_stiffness_camber_var_pky3 * 0.5
        self.lon_shift_h_phx1 = self.lat_shift_h_phy1
        self.lon_shift_load_var_phx2 = self.lat_shift_load_var_phy2
        self.lon_shift_v_pvx1 = self.lat_shift_v_pvy1
        self.lon_shift_v_load_var_pvx2 = self.lat_shift_v_load_var_pvy2

        # --- Combined Slip Coefficients (Approximated) ---
        self.comb_lat_slope_b_rby1 = 10.0
        self.comb_lat_slope_alpha_var_rby2 = 6.0
        self.comb_lat_slope_alpha_shift_rby3 = 0.0
        self.comb_lat_shape_c_rcy1 = 1.0
        self.comb_lon_slope_b_rbx1 = 12.0
        self.comb_lon_slope_kappa_var_rbx2 = 6.0
        self.comb_lon_shape_c_rcx1 = 1.0
    # --- Helper Functions for Each Calculation Step ---

    # Level 5 Calculations
    def _compute_dfz(self, Fz):
        """Eq 29: Calculates normalized load change."""
        # Avoid division by zero if nominal load is zero (shouldn't be)
        return (Fz - self.nominal_load_z) / self.nominal_load_z if self.nominal_load_z != 0 else 0

    def _compute_mu_y(self, dfz, gamma):
        """Eq 27: Calculates lateral friction coefficient potential."""
        return (self.lat_peak_friction_d_pdy1 + self.lat_friction_load_var_pdy2 * dfz) * \
               (1.0 + self.lat_friction_camber_var_pdy3 * gamma**2)

    def _compute_K_y_alpha(self, Fz, gamma):
        """Eq 28: Calculates cornering stiffness."""
        fz_ratio = max(Fz / self.nominal_load_z, 1e-6) # Ensure positive ratio
        return self.lat_stiffness_k_max_pky1 * self.nominal_load_z * \
               math.sin(self.lat_stiffness_load_max_pky2 * math.atan(fz_ratio)) * \
               (1.0 - self.lat_stiffness_camber_var_pky3 * abs(gamma))

    def _compute_mu_x(self, dfz, gamma):
        """Eq 25: Calculates longitudinal friction coefficient potential (Approximated)."""
        return (self.lon_peak_friction_d_pdx1 + self.lon_friction_load_var_pdx2 * dfz) * \
               (1.0 + self.lon_friction_camber_var_pdx3 * gamma**2)

    def _compute_K_x_kappa(self, Fz, gamma):
        """Eq 26: Calculates longitudinal slip stiffness (Approximated)."""
        fz_ratio = max(Fz / self.nominal_load_z, 1e-6)
        # Note: PKX3 is exponent in docs, but used linearly here like PKY3 based on common practice
        return self.lon_stiffness_k_pkx1 * self.nominal_load_z * \
               math.sin(self.lon_stiffness_load_var_pkx2 * math.atan(fz_ratio)) * \
               (1.0 - self.lon_stiffness_load_exp_pkx3 * abs(gamma))

    # Level 4 Calculations (Shifts)
    def _compute_S_Hy(self, dfz, gamma):
        """Eq 24: Calculates horizontal shift for Fy."""
        return (self.lat_shift_h_phy1 + self.lat_shift_load_var_phy2 * dfz) + \
               self.lat_shift_camber_var_phy3 * gamma

    def _compute_S_Vy(self, Fz, dfz, gamma):
        """Eq 23: Calculates vertical shift for Fy."""
        return Fz * ((self.lat_shift_v_pvy1 + self.lat_shift_v_load_var_pvy2 * dfz) + \
                     (self.lat_shift_v_camber_var_pvy3 + self.lat_shift_v_camber_load_var_pvy4 * dfz) * gamma)

    def _compute_S_Hx(self, dfz):
        """Eq 18: Calculates horizontal shift for Fx (Approximated)."""
        return self.lon_shift_h_phx1 + self.lon_shift_load_var_phx2 * dfz

    def _compute_S_Vx(self, Fz, dfz):
        """Eq 17: Calculates vertical shift for Fx (Approximated)."""
        return Fz * (self.lon_shift_v_pvx1 + self.lon_shift_v_load_var_pvx2 * dfz)

    # Level 3 Calculations (Effective Slips)
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
        return self.lat_shape_factor_c_pcy1

    def _compute_B_y(self, K_y_alpha, C_y, D_y):
        """Eq 21: Calculates stiffness factor for Fy."""
        # Avoid division by zero
        denominator = C_y * D_y
        return K_y_alpha / denominator if abs(denominator) > 1e-6 else 0.0

    def _compute_E_y(self, dfz, gamma, alpha_eff):
        """Eq 22: Calculates curvature factor for Fy."""
        E_y_base = self.lat_curve_e_pey1 + self.lat_curve_load_var_pey2 * dfz
        E_y_gamma_term = self.lat_curve_camber_dep_0_pey3 + self.lat_curve_camber_var_pey4 * gamma
        alpha_eff_sign = math.copysign(1, alpha_eff) if alpha_eff != 0 else 0
        return E_y_base * (1.0 - E_y_gamma_term * alpha_eff_sign)

    def _compute_D_x(self, mu_x, Fz):
        """Eq 13: Calculates peak factor for Fx (Approximated)."""
        return mu_x * Fz

    def _compute_C_x(self):
        """Eq 14: Calculates shape factor for Fx (Approximated)."""
        return self.lon_shape_factor_c_pcx1

    def _compute_B_x(self, K_x_kappa, C_x, D_x):
        """Eq 15: Calculates stiffness factor for Fx (Approximated)."""
        # Avoid division by zero
        denominator = C_x * D_x
        return K_x_kappa / denominator if abs(denominator) > 1e-6 else 0.0

    def _compute_E_x(self, dfz, kappa_eff):
        """Eq 16: Calculates curvature factor for Fx (Approximated)."""
        # PEX3 and PEX4 are approximated as 0, simplifying the term
        E_x_base = self.lon_curve_e_pex1 + self.lon_curve_load_var_pex2 * dfz
        # kappa_eff_sign = math.copysign(1, kappa_eff) if kappa_eff != 0 else 0
        # E_x_kappa_term_base = self.lon_curve_load_sq_var_pex3
        # E_x_kappa_term_driving = self.lon_curve_driving_factor_pex4
        # return E_x_base * (1.0 - (E_x_kappa_term_base + E_x_kappa_term_driving * kappa_eff) * kappa_eff_sign)
        # Simplified version with PEX3=PEX4=0:
        return E_x_base

    # Level 2 Calculations (Pure Forces)
    def _compute_pure_fy(self, D_y, C_y, B_y, E_y, alpha_eff, S_Vy):
        """Eq 6: Calculates pure lateral force."""
        # Handle cases where B_y might be zero (due to zero stiffness/peak)
        if abs(B_y) < 1e-9:
             return S_Vy # No force generated beyond vertical shift if stiffness is zero

        X = B_y * alpha_eff
        try:
            arctan_X = math.atan(X)
            # Handle potential large intermediate values in the argument of sin
            inner_arg = C_y * math.atan(X - E_y * (X - arctan_X))
            # Limit inner_arg to avoid potential floating point issues if needed, though usually okay
            # inner_arg = max(-math.pi * 10, min(math.pi * 10, inner_arg))
            Fy_pure = D_y * math.sin(inner_arg) + S_Vy
        except ValueError: # Catch potential math domain errors
             warnings.warn(f"Math domain error in pure Fy calculation. Inputs: D={D_y}, C={C_y}, B={B_y}, E={E_y}, alpha_eff={alpha_eff}, S_V={S_Vy}", RuntimeWarning)
             Fy_pure = S_Vy # Default to vertical shift on error
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
        return self.comb_lon_slope_b_rbx1 * math.cos(math.atan(self.comb_lon_slope_kappa_var_rbx2 * kappa))

    def _compute_C_xa(self):
        """Eq 8: Calculates shape factor for G_xa (Approximated)."""
        return self.comb_lon_shape_c_rcx1

    def _compute_B_yk(self, alpha):
        """Eq 9: Calculates slope factor for G_yk (Approximated)."""
        # RBY3 is approximated as 0
        return self.comb_lat_slope_b_rby1 * math.cos(math.atan(self.comb_lat_slope_alpha_var_rby2 * (alpha - self.comb_lat_slope_alpha_shift_rby3)))

    def _compute_C_yk(self):
        """Eq 10: Calculates shape factor for G_yk (Approximated)."""
        return self.comb_lat_shape_c_rcy1

    # Level 2 Calculations (Weighting Factors)
    def _compute_G_xa(self, C_xa, B_xa, alpha):
        """Eq 3: Calculates longitudinal force weighting factor (Approximated)."""
        arg = max(-100.0, min(100.0, B_xa * alpha)) # Limit argument magnitude
        return math.cos(C_xa * math.atan(arg))

    def _compute_G_yk(self, C_yk, B_yk, kappa):
        """Eq 4: Calculates lateral force weighting factor (Approximated)."""
        arg = max(-100.0, min(100.0, B_yk * kappa)) # Limit argument magnitude
        return math.cos(C_yk * math.atan(arg))

    # Level 1 Calculations (Final Combined Forces)
    def _compute_Fx_combined(self, Fx_pure, G_xa):
        """Eq 1: Calculates final combined longitudinal force."""
        return Fx_pure * G_xa

    def _compute_Fy_combined(self, Fy_pure, G_yk):
        """Eq 2: Calculates final combined lateral force."""
        return Fy_pure * G_yk

    # --- Input Clamping ---
    def _clamp_inputs(self, Fz, alpha, kappa, gamma):
        """Clamps or raises errors for inputs outside valid ranges."""
        clamped = False
        original_inputs = {'Fz': Fz, 'alpha': alpha, 'kappa': kappa, 'gamma': gamma}

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
    def calculate_forces(self, Fz, alpha, kappa, gamma, store_history=False):
        """
        Calculates combined Fx and Fy using a sequential, traceable approach.

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
        # Level 6: Base Inputs & Clamping
        Fz_proc, alpha_proc, kappa_proc, gamma_proc = self._clamp_inputs(Fz, alpha, kappa, gamma)

        # Level 5: Lowest Level Components
        dfz = self._compute_dfz(Fz_proc)
        mu_y = self._compute_mu_y(dfz, gamma_proc)
        K_y_alpha = self._compute_K_y_alpha(Fz_proc, gamma_proc)
        mu_x = self._compute_mu_x(dfz, gamma_proc) # Approx
        K_x_kappa = self._compute_K_x_kappa(Fz_proc, gamma_proc) # Approx

        # Level 4: Magic Formula Parameters (Shifts first)
        S_Hy = self._compute_S_Hy(dfz, gamma_proc)
        S_Vy = self._compute_S_Vy(Fz_proc, dfz, gamma_proc)
        S_Hx = self._compute_S_Hx(dfz) # Approx
        S_Vx = self._compute_S_Vx(Fz_proc, dfz) # Approx

        # Level 3: Effective Slips
        alpha_eff = self._compute_alpha_eff(alpha_proc, S_Hy)
        kappa_eff = self._compute_kappa_eff(kappa_proc, S_Hx)

        # Level 4: Remaining Magic Formula Parameters (D, C, B, E)
        D_y = self._compute_D_y(mu_y, Fz_proc)
        C_y = self._compute_C_y()
        B_y = self._compute_B_y(K_y_alpha, C_y, D_y)
        E_y = self._compute_E_y(dfz, gamma_proc, alpha_eff)

        D_x = self._compute_D_x(mu_x, Fz_proc) # Approx
        C_x = self._compute_C_x() # Approx
        B_x = self._compute_B_x(K_x_kappa, C_x, D_x) # Approx
        E_x = self._compute_E_x(dfz, kappa_eff) # Approx

        # Level 2: Pure Forces
        Fy_pure = self._compute_pure_fy(D_y, C_y, B_y, E_y, alpha_eff, S_Vy)
        Fx_pure = self._compute_pure_fx(D_x, C_x, B_x, E_x, kappa_eff, S_Vx) # Approx

        # Level 3: Components of Weighting Factors
        B_yk = self._compute_B_yk(alpha_proc) # Approx
        C_yk = self._compute_C_yk() # Approx
        B_xa = self._compute_B_xa(kappa_proc) # Approx
        C_xa = self._compute_C_xa() # Approx

        # Level 2: Weighting Factors
        G_yk = self._compute_G_yk(C_yk, B_yk, kappa_proc) # Approx
        G_xa = self._compute_G_xa(C_xa, B_xa, alpha_proc) # Approx

        # Level 1: Final Combined Forces
        Fx_combined = self._compute_Fx_combined(Fx_pure, G_xa)
        Fy_combined = self._compute_Fy_combined(Fy_pure, G_yk)
        # --- End Calculation Sequence ---


        # Store History if requested
        if store_history:
            # Store key intermediate values along with inputs/outputs
            history_record = {
                'inputs': original_inputs,
                'processed_inputs': {'Fz': Fz_proc, 'alpha': alpha_proc, 'kappa': kappa_proc, 'gamma': gamma_proc},
                'intermediate': {
                    'dfz': dfz, 'mu_y': mu_y, 'K_y_alpha': K_y_alpha, 'S_Hy': S_Hy, 'S_Vy': S_Vy,
                    'alpha_eff': alpha_eff, 'D_y': D_y, 'C_y': C_y, 'B_y': B_y, 'E_y': E_y,
                    'mu_x': mu_x, 'K_x_kappa': K_x_kappa, 'S_Hx': S_Hx, 'S_Vx': S_Vx, # Approx
                    'kappa_eff': kappa_eff, 'D_x': D_x, 'C_x': C_x, 'B_x': B_x, 'E_x': E_x, # Approx
                    'B_yk': B_yk, 'C_yk': C_yk, 'B_xa': B_xa, 'C_xa': C_xa # Approx
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


# --- Example Usage (Remains the same) ---
if __name__ == "__main__":
    # Initialize the tire model (clamp inputs, don't raise errors)
    tire = PacejkaTireRefactored(return_errors=False)

    # Example conditions
    fz_example = 600.0 # N
    alpha_example = math.radians(5.0) # 5 degrees slip angle
    kappa_example = 0.05 # 5% slip ratio (acceleration)
    gamma_example = math.radians(-2.0) # -2 degrees camber

    # Calculate forces, store this one in history
    forces = tire.calculate_forces(fz_example, alpha_example, kappa_example, gamma_example, store_history=True)
    print(f"Inputs: Fz={fz_example:.1f} N, alpha={math.degrees(alpha_example):.2f} deg, kappa={kappa_example:.3f}, gamma={math.degrees(gamma_example):.2f} deg")
    print(f"Calculated Forces: Fx={forces['Fx']:.2f} N, Fy={forces['Fy']:.2f} N")

    # Calculate forces for another condition, don't store
    alpha_example_2 = math.radians(-8.0)
    kappa_example_2 = -0.10 # Braking
    forces_check = tire.calculate_forces(fz_example, alpha_example_2, kappa_example_2, gamma_example, store_history=False)
    print(f"\nChecking Forces (not stored): Fx={forces_check['Fx']:.2f} N, Fy={forces_check['Fy']:.2f} N")

    # Example of out-of-range input (will be clamped and warning issued)
    fz_out_of_range = 1500.0
    forces_clamped = tire.calculate_forces(fz_out_of_range, alpha_example, kappa_example, gamma_example, store_history=True)
    print(f"\nInputs (Out of Range Fz): Fz={fz_out_of_range:.1f} N")
    print(f"Calculated Forces (Clamped): Fx={forces_clamped['Fx']:.2f} N, Fy={forces_clamped['Fy']:.2f} N")


    # Retrieve history
    calc_history = tire.get_history()
    print(f"\nCalculation History Length: {len(calc_history)}")
    if calc_history:
        print("Last history record (showing intermediate values):")
        last_record = calc_history[-1]
        print(f"  Original Inputs: {last_record['inputs']}")
        print(f"  Processed Inputs: {last_record['processed_inputs']}")
        # Print a few key intermediate values for demonstration
        print(f"  Intermediate (sample): dfz={last_record['intermediate']['dfz']:.3f}, mu_y={last_record['intermediate']['mu_y']:.3f}, K_y_alpha={last_record['intermediate']['K_y_alpha']:.1f}")
        print(f"  Pure Forces: {last_record['pure_forces']}")
        print(f"  Weighting: {last_record['weighting']}")
        print(f"  Outputs: {last_record['outputs']}")


    # Example with error raising enabled
    try:
        tire_strict = PacejkaTireRefactored(return_errors=True)
        fz_out_of_range = 50.0 # Below minimum
        tire_strict.calculate_forces(fz_out_of_range, alpha_example, kappa_example, gamma_example)
    except ValueError as e:
        print(f"\nCaught expected error with return_errors=True: {e}")
