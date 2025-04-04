
import math
import os
import numpy as np
import pandas as pd # For displaying results nicely

# --- Assumed Imports ---
# Make sure these files exist and are in Python's path
try:
    # Assuming your Pacejka class is in pacejka_model.py
    from tires.v3_magic_formula import PacejkaTireSimplified
    # Assuming your TimeSeriesStorage class is in time_series.py
    from helper_functions import TimeSeriesStorage
except ImportError as e:
    print(f"Error importing necessary classes: {e}")
    print("Please ensure pacejka_model.py and time_series.py are accessible.")
    exit()

# --- Basic Logger Setup ---
from logger import setup_logger
logger = setup_logger()

def run_tire_test(tire_model, test_conditions):
    """
    Runs a series of tests on the tire model using find_slips_prioritizing_fy.

    Args:
        tire_model (PacejkaTireSimplified): An initialized tire model instance.
        test_conditions (list): A list of dictionaries, each defining a test case:
            {
                'label': str,
                'Fz': float,      # Vertical load (N)
                'gamma_deg': float, # Camber angle (degrees)
                'target_fy': float, # Target lateral force (N)
                'long_mode': str,   # 'accelerate', 'brake', or 'coast'
                'long_intensity': float # 0.0 to 1.0
            }

    Returns:
        pandas.DataFrame: A DataFrame summarizing the test results.
    """
    results = []
    logger.info(f"--- Starting Tire Test Suite ({len(test_conditions)} cases) ---")

    for i, condition in enumerate(test_conditions):
        label = condition['label']
        fz = condition['Fz']
        gamma = math.radians(condition['gamma_deg'])
        target_fy = condition['target_fy']
        long_mode = condition['long_mode']
        long_intensity = condition['long_intensity']
        time_ms = i * 100 # Assign arbitrary time for potential history logging

        logger.info(f"Running Test Case {i+1}: '{label}'")
        logger.info(f"  Inputs: Fz={fz:.1f}N, gamma={condition['gamma_deg']:.1f}deg, Target Fy={target_fy:.1f}N, Mode={long_mode}, Intensity={long_intensity:.2f}")

        # 1. Find the target slips using the prioritizing method
        calculated_slips = tire_model.find_slips_prioritizing_fy(
            target_fy, fz, gamma, long_mode, long_intensity
        )

        alpha_req_rad = calculated_slips['alpha']
        kappa_req = calculated_slips['kappa']

        result_row = {
            'Test Case': label,
            'Fz (N)': fz,
            'Gamma (deg)': condition['gamma_deg'],
            'Target Fy (N)': target_fy,
            'Long Mode': long_mode,
            'Long Intensity': long_intensity,
            'Target Alpha (deg)': None,
            'Target Kappa': None,
            'Result Fy (N)': None,
            'Result Fx (N)': None,
            'Fy Error (N)': None,
            'Fy Error (%)': None,
            'Status': 'Failed: Target Fy Unachievable' # Default status
        }

        if not np.isnan(alpha_req_rad) and not np.isnan(kappa_req):
            # Slips were found, proceed to verification
            result_row['Target Alpha (deg)'] = math.degrees(alpha_req_rad)
            result_row['Target Kappa'] = kappa_req

            # 2. Verify by calculating forces with the found slips
            # Use store_history=False as we only care about the result here
            resulting_forces = tire_model.calculate_forces(
                fz, alpha_req_rad, kappa_req, gamma, time_ms, store_history=False
            )

            result_fy = resulting_forces['Fy']
            result_fx = resulting_forces['Fx']

            # 3. Calculate Errors and Update Status
            fy_error = result_fy - target_fy
            fy_error_percent = (fy_error / target_fy * 100) if abs(target_fy) > 1e-3 else (0 if abs(fy_error) < 1e-3 else np.inf)

            result_row.update({
                'Result Fy (N)': result_fy,
                'Result Fx (N)': result_fx,
                'Fy Error (N)': fy_error,
                'Fy Error (%)': fy_error_percent,
                'Status': 'Success'
            })
            logger.info(f"  Success: Target Slips: alpha={math.degrees(alpha_req_rad):.3f}deg, kappa={kappa_req:.4f}")
            logger.info(f"  Resulting Forces: Fx={result_fx:.1f}N, Fy={result_fy:.1f}N (Error Fy={fy_error:.1f}N / {fy_error_percent:.2f}%)")

        else:
            # Slips were NaN
            logger.warning(f"  Failed: Could not find valid slips for target Fy={target_fy:.1f}N.")
            # Keep default status

        results.append(result_row)

    logger.info("--- Tire Test Suite Finished ---")
    return pd.DataFrame(results)


# --- Main Execution ---
if __name__ == "__main__":
    param_file = 'hoosier_r20.par' # Make sure this exists

    # Check if the parameter file exists
    if not os.path.exists(param_file):
        logger.critical(f"Parameter file '{param_file}' not found. Cannot run tests.")
        exit()

    try:
        # Initialize the tire model
        # Use return_errors=False so clamping doesn't stop the test suite
        tire = PacejkaTireSimplified(param_file, return_errors=False, history_name="TestTire")

        # Define Test Conditions
        test_conditions = [
            # --- Basic Cases ---
            {'label': 'Coast Straight', 'Fz': 600, 'gamma_deg': 0, 'target_fy': 0, 'long_mode': 'coast', 'long_intensity': 0.0},
            {'label': 'Max Accel Straight', 'Fz': 700, 'gamma_deg': 0, 'target_fy': 0, 'long_mode': 'accelerate', 'long_intensity': 1.0},
            {'label': 'Max Brake Straight', 'Fz': 500, 'gamma_deg': 0, 'target_fy': 0, 'long_mode': 'brake', 'long_intensity': 1.0},
            {'label': 'Partial Accel Straight', 'Fz': 700, 'gamma_deg': 0, 'target_fy': 0, 'long_mode': 'accelerate', 'long_intensity': 0.5},
            {'label': 'Partial Brake Straight', 'Fz': 500, 'gamma_deg': 0, 'target_fy': 0, 'long_mode': 'brake', 'long_intensity': 0.7},
            # --- Cornering Cases ---
            {'label': 'Cornering Coast', 'Fz': 600, 'gamma_deg': -2, 'target_fy': -1500, 'long_mode': 'coast', 'long_intensity': 0.0},
            {'label': 'Cornering Max Accel', 'Fz': 700, 'gamma_deg': -2, 'target_fy': -1500, 'long_mode': 'accelerate', 'long_intensity': 1.0},
            {'label': 'Cornering Max Brake', 'Fz': 500, 'gamma_deg': -2, 'target_fy': -1500, 'long_mode': 'brake', 'long_intensity': 1.0},
            {'label': 'Cornering Partial Accel', 'Fz': 700, 'gamma_deg': -2, 'target_fy': -1500, 'long_mode': 'accelerate', 'long_intensity': 0.4},
            {'label': 'Cornering Partial Brake', 'Fz': 500, 'gamma_deg': -2, 'target_fy': -1500, 'long_mode': 'brake', 'long_intensity': 0.6},
            # --- Edge Cases / High Demand ---
            {'label': 'High Cornering Coast', 'Fz': 800, 'gamma_deg': -3, 'target_fy': -3500, 'long_mode': 'coast', 'long_intensity': 0.0},
            {'label': 'High Cornering Max Accel', 'Fz': 800, 'gamma_deg': -3, 'target_fy': -3500, 'long_mode': 'accelerate', 'long_intensity': 1.0},
            {'label': 'Impossible Fy Target', 'Fz': 400, 'gamma_deg': 0, 'target_fy': -5000, 'long_mode': 'coast', 'long_intensity': 0.0},
        ]

        # Run the tests
        results_df = run_tire_test(tire, test_conditions)

        # Display results
        print("\n--- Test Results Summary ---")
        # Configure pandas display options for better readability
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        pd.set_option('display.float_format', '{:.3f}'.format) # Format floats
        print(results_df.to_string(index=False)) # Print without index
        print("--------------------------")

        # Optional: Save results to CSV
        # results_df.to_csv("tire_test_results.csv", index=False)
        # logger.info("Test results saved to tire_test_results.csv")

    except FileNotFoundError as e:
        logger.critical(f"Execution failed: {e}")
    except ValueError as e:
        logger.critical(f"Execution failed: {e}")
    except Exception as e:
        logger.exception("An unexpected error occurred during testing:")

# --- Function to test find_slips_prioritizing_fy (from previous step) ---
def run_fy_priority_test_suite(tire_model, test_conditions):
    """
    Runs a series of tests on the tire model using find_slips_prioritizing_fy.
    (Code from previous step - kept for completeness, can be collapsed if desired)
    """
    results = []
    logger.info(f"--- Starting Fy Priority Test Suite ({len(test_conditions)} cases) ---")
    for i, condition in enumerate(test_conditions):
        # ... (rest of the function as defined previously) ...
        label = condition['label']; fz = condition['Fz']; gamma = math.radians(condition['gamma_deg'])
        target_fy = condition['target_fy']; long_mode = condition['long_mode']; long_intensity = condition['long_intensity']
        time_ms = i * 100
        logger.info(f"Running Fy Priority Test {i+1}: '{label}'")
        logger.debug(f"  Inputs: Fz={fz:.1f}N, gamma={condition['gamma_deg']:.1f}deg, Target Fy={target_fy:.1f}N, Mode={long_mode}, Intensity={long_intensity:.2f}")
        calculated_slips = tire_model.find_slips_prioritizing_fy(target_fy, fz, gamma, long_mode, long_intensity)
        alpha_req_rad = calculated_slips['alpha']; kappa_req = calculated_slips['kappa']
        result_row = {'Test Case': label, 'Fz (N)': fz, 'Gamma (deg)': condition['gamma_deg'], 'Target Fy (N)': target_fy, 'Long Mode': long_mode, 'Long Intensity': long_intensity,
                      'Target Alpha (deg)': None, 'Target Kappa': None, 'Result Fy (N)': None, 'Result Fx (N)': None, 'Fy Error (N)': None, 'Fy Error (%)': None, 'Status': 'Failed: Target Fy Unachievable'}
        if not np.isnan(alpha_req_rad) and not np.isnan(kappa_req):
            result_row['Target Alpha (deg)'] = math.degrees(alpha_req_rad); result_row['Target Kappa'] = kappa_req
            resulting_forces = tire_model.calculate_forces(fz, alpha_req_rad, kappa_req, gamma, time_ms, store_history=False)
            result_fy = resulting_forces['Fy']; result_fx = resulting_forces['Fx']
            fy_error = result_fy - target_fy
            fy_error_percent = (fy_error / target_fy * 100) if abs(target_fy) > 1e-3 else (0 if abs(fy_error) < 1e-3 else np.inf)
            result_row.update({'Result Fy (N)': result_fy, 'Result Fx (N)': result_fx, 'Fy Error (N)': fy_error, 'Fy Error (%)': fy_error_percent, 'Status': 'Success'})
            logger.debug(f"  Success: Target Slips: alpha={math.degrees(alpha_req_rad):.3f}deg, kappa={kappa_req:.4f}")
            logger.debug(f"  Resulting Forces: Fx={result_fx:.1f}N, Fy={result_fy:.1f}N (Error Fy={fy_error:.1f}N / {fy_error_percent:.2f}%)")
        else: logger.warning(f"  Failed: Could not find valid slips for target Fy={target_fy:.1f}N.")
        results.append(result_row)
    logger.info("--- Fy Priority Test Suite Finished ---")
    return pd.DataFrame(results)


# --- NEW Function to test internal components ---
def test_tire_components(tire_model, label, Fz, alpha_deg, kappa, gamma_deg):
    """
    Tests the internal calculation components of the Pacejka tire model.

    Calls the internal methods that calculate intermediate values and returns
    a dictionary containing these values for inspection.

    Args:
        tire_model (PacejkaTireSimplified): An initialized tire model instance.
        label (str): A descriptive label for this test case.
        Fz (float): Vertical load (N).
        alpha_deg (float): Slip angle (degrees).
        kappa (float): Slip ratio (dimensionless).
        gamma_deg (float): Camber angle (degrees).

    Returns:
        dict: A dictionary containing inputs and all calculated intermediate
              and final values. Includes a 'Status' key.
    """
    logger.info(f"--- Testing Components: '{label}' ---")
    alpha_rad = math.radians(alpha_deg)
    gamma_rad = math.radians(gamma_deg)
    logger.info(f"Inputs: Fz={Fz:.1f}, alpha={alpha_deg:.2f}deg, kappa={kappa:.3f}, gamma={gamma_deg:.2f}deg")

    # Store inputs for easy reference in the output
    results = {
        'Label': label,
        'Fz_in': Fz, 'alpha_in_deg': alpha_deg, 'kappa_in': kappa, 'gamma_in_deg': gamma_deg,
        'Status': 'Success' # Default status
    }

    try:
        # 1. Clamp Inputs
        Fz_proc, alpha_proc, kappa_proc, gamma_proc = tire_model._clamp_inputs(Fz, alpha_rad, kappa, gamma_rad)
        results.update({
            'Fz_proc': Fz_proc, 'alpha_proc_rad': alpha_proc,
            'kappa_proc': kappa_proc, 'gamma_proc_rad': gamma_proc
        })
        logger.debug("Clamped Inputs: Fz=%.1f, alpha=%.4f, kappa=%.4f, gamma=%.4f", Fz_proc, alpha_proc, kappa_proc, gamma_proc)

        # 2. Calculate Pure Forces and Components
        # This dictionary contains dfz, mu_y, K_y_alpha, ..., Fx_pure, Fy_pure
        pure_calcs = tire_model._calculate_pure_forces_and_components(
            Fz_proc, alpha_proc, kappa_proc, gamma_proc
        )
        results.update(pure_calcs) # Add all intermediate results
        logger.debug("Calculated Pure Components & Forces. Fy_pure=%.2f, Fx_pure=%.2f", pure_calcs.get('Fy_pure', np.nan), pure_calcs.get('Fx_pure', np.nan))


        # 3. Calculate Combined Slip Factors
        # This dictionary contains B_xa, C_xa, B_yk, C_yk, Gxa, Gyk
        comb_calcs = tire_model._calculate_combined_slip_factors(
            alpha_proc, kappa_proc
        )
        results.update(comb_calcs)
        logger.debug("Calculated Combined Slip Factors. Gxa=%.4f, Gyk=%.4f", comb_calcs.get('Gxa', np.nan), comb_calcs.get('Gyk', np.nan))


        # 4. Calculate Final Forces (using intermediate results)
        Fx_comb = pure_calcs.get('Fx_pure', 0) * comb_calcs.get('Gxa', 1)
        Fy_comb = pure_calcs.get('Fy_pure', 0) * comb_calcs.get('Gyk', 1)
        results['Fx_combined_calc'] = Fx_comb
        results['Fy_combined_calc'] = Fy_comb

        logger.info(f"Component Calculation Successful. Final Fx={Fx_comb:.2f}, Fy={Fy_comb:.2f}")

    except Exception as e:
        logger.error(f"Error during component test '{label}': {e}", exc_info=True) # Log traceback
        results['Status'] = f"Error: {e}" # Add error status

    return results


# --- Main Execution ---
if __name__ != "__main__":
    param_file = 'hoosier_r20.par' # Make sure this exists

    if not os.path.exists(param_file):
        logger.critical(f"Parameter file '{param_file}' not found. Cannot run tests.")
        exit()

    try:
        # Initialize the tire model
        tire = PacejkaTireSimplified(param_file, return_errors=False, history_name="TestTire")

        # --- Run Fy Priority Test Suite (Optional) ---
        # fy_priority_test_conditions = [ ... define conditions ... ]
        # fy_priority_results_df = run_fy_priority_test_suite(tire, fy_priority_test_conditions)
        # print("\n--- Fy Priority Test Results Summary ---")
        # pd.set_option('display.max_rows', None); pd.set_option('display.max_columns', None)
        # pd.set_option('display.width', 1000); pd.set_option('display.float_format', '{:.3f}'.format)
        # print(fy_priority_results_df.to_string(index=False))
        # print("------------------------------------")


        # --- Run Component Test Suite ---
        component_test_conditions = [
            {'label': 'Zero Slips', 'Fz': 600, 'alpha_deg': 0, 'kappa': 0, 'gamma_deg': 0},
            {'label': 'Pure Accel', 'Fz': 700, 'alpha_deg': 0, 'kappa': 0.1, 'gamma_deg': 0},
            {'label': 'Pure Brake', 'Fz': 500, 'alpha_deg': 0, 'kappa': -0.08, 'gamma_deg': 0},
            {'label': 'Pure Cornering', 'Fz': 600, 'alpha_deg': 5, 'kappa': 0, 'gamma_deg': -2},
            {'label': 'Cornering + Accel', 'Fz': 700, 'alpha_deg': 4, 'kappa': 0.05, 'gamma_deg': -2},
            {'label': 'Cornering + Brake', 'Fz': 500, 'alpha_deg': -3, 'kappa': -0.06, 'gamma_deg': -1},
            {'label': 'High Load Cornering', 'Fz': 1000, 'alpha_deg': 6, 'kappa': 0.01, 'gamma_deg': -3},
            {'label': 'Low Load Braking', 'Fz': 200, 'alpha_deg': 1, 'kappa': -0.15, 'gamma_deg': 0},
            {'label': 'Clamping Fz High', 'Fz': 1500, 'alpha_deg': 2, 'kappa': 0.02, 'gamma_deg': -1},
            {'label': 'Clamping Alpha High', 'Fz': 600, 'alpha_deg': 20, 'kappa': 0.02, 'gamma_deg': -1},
            {'label': 'Clamping Kappa Low', 'Fz': 600, 'alpha_deg': 2, 'kappa': -0.3, 'gamma_deg': -1},
        ]

        all_component_results = []
        for cond in component_test_conditions:
            # Use dictionary unpacking for cleaner argument passing
            res = test_tire_components(tire_model=tire, **cond)
            all_component_results.append(res)

        # Convert results to DataFrame
        component_df = pd.DataFrame(all_component_results)

        # Display results
        print("\n--- Component Test Results ---")
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 200) # Adjust width as needed
        pd.set_option('display.float_format', '{:.4f}'.format) # Show more precision
        # Select and reorder columns for better readability if desired
        # Example: cols_to_show = ['Label', 'Fz_in', 'alpha_in_deg', ..., 'Fx_combined_calc', 'Fy_combined_calc', 'Status']
        # print(component_df[cols_to_show].to_string(index=False))
        print(component_df.to_string(index=False)) # Print all columns
        print("--------------------------")

        # Optional: Save component results to CSV
        # component_df.to_csv("tire_component_test_results.csv", index=False)
        # logger.info("Component test results saved to tire_component_test_results.csv")


    except FileNotFoundError as e:
        logger.critical(f"Execution failed: {e}")
    except ValueError as e:
        logger.critical(f"Execution failed: {e}")
    except Exception as e:
        logger.exception("An unexpected error occurred during testing:")

