
import numpy as np
import matplotlib.pyplot as plt

# --- Helper Functions (get_mu_y, get_Ky - unchanged) ---
def get_mu_y(Fz, **params):
    Fz0 = params.get('Fz0', 0); PDY1 = params.get('PDY1', 0); PDY2 = params.get('PDY2', 0)
    dfz = (Fz - Fz0) / Fz0 if Fz0 > 0 else 0
    return PDY1 + PDY2 * dfz

def get_Ky(Fz, **params):
    Fz0 = params.get('Fz0', 0); PKY1 = params.get('PKY1', 0); PKY2 = params.get('PKY2', 0)
    if Fz0 == 0 or PKY2 == 0: return 0
    Fz_abs = abs(Fz)
    return PKY1 * Fz0 * np.sin(2 * np.arctan(Fz_abs / (PKY2 * Fz0)))

# --- PAC2002 Fx Calculation Function (calculate_fx_pac2002 - unchanged) ---
def calculate_fx_pac2002(kappa_range, Fz, Fz0, params):
    dfz = (Fz - Fz0) / Fz0 if Fz0 > 0 else 0
    PCX1 = params.get('PCX1', 1.0); PDX1 = params.get('PDX1', 0.0); PDX2 = params.get('PDX2', 0.0)
    PEX1 = params.get('PEX1', 0.0); PEX2 = params.get('PEX2', 0.0); PEX3 = params.get('PEX3', 0.0); PEX4 = params.get('PEX4', 0.0)
    PKX1 = params.get('PKX1', 0.0); PKX2 = params.get('PKX2', 0.0); PKX3 = params.get('PKX3', 0.0)
    PHX1 = params.get('PHX1', 0.0); PHX2 = params.get('PHX2', 0.0)
    PVX1 = params.get('PVX1', 0.0); PVX2 = params.get('PVX2', 0.0)
    Cx = PCX1; mu_x = PDX1 + PDX2 * dfz; Dx = mu_x * Fz
    Kx = Fz * (PKX1 + PKX2 * dfz) * np.exp(PKX3 * dfz)
    if Cx * Dx == 0: Bx = 0
    else: Bx = abs(Kx / (Cx * Dx))
    Shx = PHX1 + PHX2 * dfz; Svx = Fz * (PVX1 + PVX2 * dfz)
    Fx = np.zeros_like(kappa_range)
    for i, kappa in enumerate(kappa_range):
        kappa_prime = kappa + Shx
        Ex = (PEX1 + PEX2 * dfz + PEX3 * dfz**2) * (1 - PEX4 * np.sign(kappa_prime))
        Ex = min(Ex, 1.0)
        if Bx == 0: term_in_arctan = 0
        else: term_in_arctan = Bx * kappa_prime
        angle_component = term_in_arctan - Ex * (term_in_arctan - np.arctan(term_in_arctan))
        Fx[i] = Dx * np.sin(Cx * np.arctan(angle_component)) + Svx
    return Fx

# --- PAC2002 Fy Calculation Function (calculate_fy_pac2002 - unchanged) ---
def calculate_fy_pac2002(alpha_range, Fz, Fz0, params):
    dfz = (Fz - Fz0) / Fz0 if Fz0 > 0 else 0
    PCY1 = params.get('PCY1', 1.0); PDY1 = params.get('PDY1', 0.0); PDY2 = params.get('PDY2', 0.0)
    PEY1 = params.get('PEY1', 0.0); PEY2 = params.get('PEY2', 0.0); PEY3 = params.get('PEY3', 0.0); PEY4 = params.get('PEY4', 0.0)
    PKY1 = params.get('PKY1', 0.0); PKY2 = params.get('PKY2', 0.0)
    PHY1 = params.get('PHY1', 0.0); PHY2 = params.get('PHY2', 0.0)
    PVY1 = params.get('PVY1', 0.0); PVY2 = params.get('PVY2', 0.0)
    Cy = PCY1; mu_y = PDY1 + PDY2 * dfz; Dy = mu_y * Fz
    Ky = PKY1 * Fz0 * np.sin(2 * np.arctan(Fz / (PKY2 * Fz0))) if Fz0 > 0 and PKY2 != 0 else 0
    if Cy * Dy == 0: By = 0
    else: By = abs(Ky / (Cy * Dy))
    Shy = PHY1 + PHY2 * dfz; Svy = Fz * (PVY1 + PVY2 * dfz)
    Fy = np.zeros_like(alpha_range)
    for i, alpha in enumerate(alpha_range):
        alpha_prime = alpha + Shy
        Ey = PEY1 + PEY2 * dfz; Ey = min(Ey, 1.0)
        if By == 0: term_in_arctan = 0
        else: term_in_arctan = By * alpha_prime
        angle_component = term_in_arctan - Ey * (term_in_arctan - np.arctan(term_in_arctan))
        Fy[i] = Dy * np.sin(Cy * np.arctan(angle_component)) + Svy
    return Fy

# --- Define Parameters and Conditions ---
Fz_eval = 667.0 # Vertical Load (N)
kappa_range = np.linspace(-0.25, 0.25, 101)
alpha_range = np.deg2rad(np.linspace(-20, 20, 101)) # Slip angle range (rad)

# --- Parameter Sets ---
hoosier_params_lat = {
    'Fz0': 667.0, 'PCY1': 1.25788, 'PDY1': -2.50993, 'PDY2': 0.0780647, 'PDY3': 8.37358,
    'PEY1': -0.59049, 'PEY2': 0.162594, 'PEY3': 0.0, 'PEY4': 10.3142,
    'PKY1': -46.3491, 'PKY2': 1.4492, 'PKY3': 0.639078, 'PHY1': -0.00108397, 'PHY2': 0.00258753,
    'PHY3': 0.112578, 'PVY1': -0.0292988, 'PVY2': 0.0487652, 'PVY3': -0.586156, 'PVY4': -0.716249
}
sample_params_lon = {
    'Fz0': 659.49, 'PCX1': 1.26436, 'PDX1': -2.51713, 'PDX2': 0.35341, 'PDX3': 16.64587,
    'PEX1': 0.69745, 'PEX2': 0.09222, 'PEX3': -0.23494, 'PEX4': 0.36206, 'PKX1': 99.5975,
    'PKX2': 0.00007, 'PKX3': 0.00118, 'PHX1': 0.00178, 'PHX2': -0.00087, 'PVX1': -0.06461, 'PVX2': 0.04988
}
sample_params_lat = {
    'Fz0': 659.49, 'PCY1': 1.400, 'PDY1': -1.90034, 'PDY2': 0.224345, 'PDY3': -8.57317,
    'PEY1': -1.52888, 'PEY2': -0.08412, 'PEY3': 0.081699, 'PEY4': -3.07119, 'PKY1': -91.583,
    'PKY2': 3.25820, 'PKY3': -0.66338, 'PHY1': -0.00086, 'PHY2': 0.002418, 'PHY3': 0.027613,
    'PVY1': -0.00061, 'PVY2': -0.00981, 'PVY3': -2.18946, 'PVY4': -0.93557
}

# --- Calculate Parameters for Methods ---
# Method 1 Params
params_m1 = sample_params_lon
# Method 2 Params
params_m2 = {
    'Fz0': hoosier_params_lat['Fz0'], 'PCX1': hoosier_params_lat['PCY1'], 'PDX1': hoosier_params_lat['PDY1'],
    'PDX2': hoosier_params_lat['PDY2'], 'PDX3': hoosier_params_lat['PDY3'], 'PEX1': hoosier_params_lat['PEY1'],
    'PEX2': hoosier_params_lat['PEY2'], 'PEX3': hoosier_params_lat['PEY3'], 'PEX4': hoosier_params_lat['PEY4'],
    'PKX1': hoosier_params_lat['PKY1'], 'PKX2': hoosier_params_lat['PKY2'], 'PKX3': hoosier_params_lat['PKY3'],
    'PHX1': hoosier_params_lat['PHY1'], 'PHX2': hoosier_params_lat['PHY2'], 'PVX1': hoosier_params_lat['PVY1'],
    'PVX2': hoosier_params_lat['PVY2']
}
# Method 3 Params (Scaling)
mu_y_h = get_mu_y(Fz_eval, **hoosier_params_lat)
Ky_h = get_Ky(Fz_eval, **hoosier_params_lat)
mu_y_s = get_mu_y(Fz_eval, **sample_params_lat)
Ky_s = get_Ky(Fz_eval, **sample_params_lat)
R_D = mu_y_h / mu_y_s if mu_y_s != 0 else 1.0
R_K = Ky_h / Ky_s if Ky_s != 0 else 1.0
params_m3 = sample_params_lon.copy()
params_m3['PDX1'] = sample_params_lon['PDX1'] * R_D
params_m3['PKX1'] = sample_params_lon['PKX1'] * R_K

# --- Calculate Peak Forces ---

# Hoosier Peak Fy (Consistent for all methods)
fy_hoosier = calculate_fy_pac2002(alpha_range, Fz_eval, hoosier_params_lat['Fz0'], hoosier_params_lat)
Fy_peak_hoosier = np.abs(fy_hoosier).max()

# Peak Fx for each Hoosier approximation method
fx_m1 = calculate_fx_pac2002(kappa_range, Fz_eval, params_m1['Fz0'], params_m1)
Fx_peak_m1 = np.abs(fx_m1).max()
fx_m2 = calculate_fx_pac2002(kappa_range, Fz_eval, params_m2['Fz0'], params_m2)
Fx_peak_m2 = np.abs(fx_m2).max()
fx_m3 = calculate_fx_pac2002(kappa_range, Fz_eval, params_m3['Fz0'], params_m3)
Fx_peak_m3 = np.abs(fx_m3).max()

# Sample Tire Peak Forces
fx_sample = calculate_fx_pac2002(kappa_range, Fz_eval, sample_params_lon['Fz0'], sample_params_lon)
Fx_peak_sample = np.abs(fx_sample).max() # Same as Fx_peak_m1
fy_sample = calculate_fy_pac2002(alpha_range, Fz_eval, sample_params_lat['Fz0'], sample_params_lat)
Fy_peak_sample = np.abs(fy_sample).max()


print("Calculated Pure Slip Peak Forces for Ellipses:")
print(f"  Hoosier Fy Peak (All Methods): {Fy_peak_hoosier:.0f} N")
print(f"  Method 1 Approx Fx Peak:       {Fx_peak_m1:.0f} N")
print(f"  Method 2 Approx Fx Peak:       {Fx_peak_m2:.0f} N")
print(f"  Method 3 Approx Fx Peak:       {Fx_peak_m3:.0f} N")
print(f"  Sample Tire Fx Peak:           {Fx_peak_sample:.0f} N")
print(f"  Sample Tire Fy Peak:           {Fy_peak_sample:.0f} N\n")


# --- Generate Ellipse Points ---
theta = np.linspace(0, 2 * np.pi, 100)

# Hoosier Method 1 Ellipse
fx_ellipse_m1 = Fx_peak_m1 * np.cos(theta)
fy_ellipse_m1 = Fy_peak_hoosier * np.sin(theta)
# Hoosier Method 2 Ellipse
fx_ellipse_m2 = Fx_peak_m2 * np.cos(theta)
fy_ellipse_m2 = Fy_peak_hoosier * np.sin(theta)
# Hoosier Method 3 Ellipse
fx_ellipse_m3 = Fx_peak_m3 * np.cos(theta)
fy_ellipse_m3 = Fy_peak_hoosier * np.sin(theta)
# Sample Tire Ellipse
fx_ellipse_s = Fx_peak_sample * np.cos(theta)
fy_ellipse_s = Fy_peak_sample * np.sin(theta)


# --- Plot Results ---
plt.style.use('seaborn-v0_8-darkgrid')
plt.figure(figsize=(9, 9)) # Make figure square

# Plot Hoosier Approximations
plt.plot(fx_ellipse_m1, fy_ellipse_m1, label=f"Hoosier (Method 1 Fx)", linestyle='-', linewidth=2, color='C0')
plt.plot(fx_ellipse_m2, fy_ellipse_m2, label=f"Hoosier (Method 2 Fx)", linestyle='--', linewidth=2, color='C1')
plt.plot(fx_ellipse_m3, fy_ellipse_m3, label=f"Hoosier (Method 3 Fx)", linestyle=':', linewidth=2, color='C2')
# Plot Sample Tire
plt.plot(fx_ellipse_s, fy_ellipse_s, label=f"Sample Tire (Pure Slip)", linestyle='-', linewidth=2, color='C3')


plt.xlabel(r"Longitudinal Force $F_x$ (N)", fontsize=12)
plt.ylabel(r"Lateral Force $F_y$ (N)", fontsize=12)
plt.title(f"Comparison of Friction Ellipses ($F_z$ = {Fz_eval:.0f} N)", fontsize=14)
plt.grid(True, which='both', linestyle='-', linewidth=0.5)
plt.legend(fontsize=10)
plt.axhline(0, color='black', linewidth=0.7)
plt.axvline(0, color='black', linewidth=0.7)
plt.axis('equal') # Ensure aspect ratio is 1:1

# Add text for peak values (adjust positions slightly for clarity)
plt.text(0, Fy_peak_hoosier * 1.02, f'Hoosier Fy:{Fy_peak_hoosier:.0f} N', ha='center', va='bottom', fontsize=9)
plt.text(0, Fy_peak_sample * 1.02, f'Sample Fy:{Fy_peak_sample:.0f} N', ha='center', va='bottom', fontsize=9, color='C3')

plt.text(Fx_peak_m1 * 1.02, 0, f'M1:{Fx_peak_m1:.0f} N', ha='left', va='center', fontsize=9, rotation=90, color='C0')
plt.text(Fx_peak_m2 * 1.02, 0, f'M2:{Fx_peak_m2:.0f} N', ha='left', va='center', fontsize=9, rotation=90, color='C1')
plt.text(Fx_peak_m3 * 1.02, 0, f'M3:{Fx_peak_m3:.0f} N', ha='left', va='center', fontsize=9, rotation=90, color='C2')
# Sample Fx peak is same as M1 peak
# plt.text(Fx_peak_sample * 1.02, 0, f'Sample Fx:{Fx_peak_sample:.0f} N', ha='left', va='center', fontsize=9, rotation=90, color='C3')


plt.tight_layout()

