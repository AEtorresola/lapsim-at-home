
import math
import logging
import os
import numpy as np
import pandas as pd # For displaying results nicely

# --- Assumed Imports ---
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

# --- Test Suite for find_slips_prioritizing_fy ---
def run_fy_priority_test_suite(tire_model, test_conditions):
    """ Tests the find_slips_prioritizing_fy method. """
    results = []
    logger.info(f"--- Starting Fy Priority Test Suite ({len(test_conditions)} cases) ---")
    for i, condition in enumerate(test_conditions):
        label = condition['label']; fz = condition['Fz']; gamma = math.radians(condition['gamma_deg'])
        target_fy = condition['target_fy']; long_mode = condition['long_mode']; long_intensity = condition['long_intensity']
        time_ms = i * 100 # Arbitrary time
        logger.info(f"Running Fy Priority Test {i+1}: '{label}'")
        logger.debug(f"  Inputs: Fz={fz:.1f}N, gamma={condition['gamma_deg']:.1f}deg, Target Fy={target_fy:.1f}N, Mode={long_mode}, Intensity={long_intensity:.2f}")

        calculated_slips = tire_model.find_slips_prioritizing_fy(target_fy, fz, gamma, long_mode, long_intensity)
        alpha_req_rad = calculated_slips['alpha']; kappa_req = calculated_slips['kappa']

        result_row = {'Test Case': label, 'Fz (N)': fz, 'Gamma (deg)': condition['gamma_deg'], 'Target Fy (N)': target_fy, 'Long Mode': long_mode, 'Long Intensity': long_intensity,
                      'Target Alpha (deg)': None, 'Target Kappa': None, 'Result Fy (N)': None, 'Result Fx (N)': None, 'Fy Error (N)': None, 'Fy Error (%)': None, 'Status': 'Failed: Target/Solver'}

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


# --- NEW Test Suite for find_kappa_for_fx ---
def run_pure_fx_inverse_test_suite(tire_model, test_conditions):
    """ Tests the find_kappa_for_fx method (pure longitudinal slip). """
    results = []
    logger.info(f"--- Starting Pure Fx Inverse Test Suite ({len(test_conditions)} cases) ---")
    for i, condition in enumerate(test_conditions):
        label = condition['label']; fz = condition['Fz']; gamma = math.radians(condition['gamma_deg'])
        target_fx = condition['target_fx']
        time_ms = i * 100 # Arbitrary time
        logger.info(f"Running Pure Fx Inverse Test {i+1}: '{label}'")
        logger.debug(f"  Inputs: Fz={fz:.1f}N, gamma={condition['gamma_deg']:.1f}deg, Target Fx={target_fx:.1f}N")

        kappa_req = tire_model.find_kappa_for_fx(target_fx, fz, gamma)

        result_row = {'Test Case': label, 'Fz (N)': fz, 'Gamma (deg)': condition['gamma_deg'], 'Target Fx (N)': target_fx,
                      'Target Kappa': None, 'Result Fx (N)': None, 'Result Fy (N)': None, 'Fx Error (N)': None, 'Fx Error (%)': None, 'Status': 'Failed: Target/Solver'}

        if not np.isnan(kappa_req):
            result_row['Target Kappa'] = kappa_req
            # Verify by calculating forces with alpha=0 and found kappa
            resulting_forces = tire_model.calculate_forces(fz, 0.0, kappa_req, gamma, time_ms, store_history=False)
            result_fx = resulting_forces['Fx']; result_fy = resulting_forces['Fy']
            fx_error = result_fx - target_fx
            fx_error_percent = (fx_error / target_fx * 100) if abs(target_fx) > 1e-3 else (0 if abs(fx_error) < 1e-3 else np.inf)
            result_row.update({'Result Fx (N)': result_fx, 'Result Fy (N)': result_fy, 'Fx Error (N)': fx_error, 'Fx Error (%)': fx_error_percent, 'Status': 'Success'})
            logger.debug(f"  Success: Target Kappa: {kappa_req:.4f}")
            logger.debug(f"  Resulting Forces: Fx={result_fx:.1f}N, Fy={result_fy:.1f}N (Error Fx={fx_error:.1f}N / {fx_error_percent:.2f}%)")
        else: logger.warning(f"  Failed: Could not find valid kappa for target Fx={target_fx:.1f}N.")
        results.append(result_row)
    logger.info("--- Pure Fx Inverse Test Suite Finished ---")
    return pd.DataFrame(results)


# --- NEW Test Suite for find_alpha_for_fy ---
def run_pure_fy_inverse_test_suite(tire_model, test_conditions):
    """ Tests the find_alpha_for_fy method (pure lateral slip). """
    results = []
    logger.info(f"--- Starting Pure Fy Inverse Test Suite ({len(test_conditions)} cases) ---")
    for i, condition in enumerate(test_conditions):
        label = condition['label']; fz = condition['Fz']; gamma = math.radians(condition['gamma_deg'])
        target_fy = condition['target_fy']
        time_ms = i * 100 # Arbitrary time
        logger.info(f"Running Pure Fy Inverse Test {i+1}: '{label}'")
        logger.debug(f"  Inputs: Fz={fz:.1f}N, gamma={condition['gamma_deg']:.1f}deg, Target Fy={target_fy:.1f}N")

        alpha_req_rad = tire_model.find_alpha_for_fy(target_fy, fz, gamma)

        result_row = {'Test Case': label, 'Fz (N)': fz, 'Gamma (deg)': condition['gamma_deg'], 'Target Fy (N)': target_fy,
                      'Target Alpha (deg)': None, 'Result Fy (N)': None, 'Result Fx (N)': None, 'Fy Error (N)': None, 'Fy Error (%)': None, 'Status': 'Failed: Target/Solver'}

        if not np.isnan(alpha_req_rad):
            result_row['Target Alpha (deg)'] = math.degrees(alpha_req_rad)
            # Verify by calculating forces with kappa=0 and found alpha
            resulting_forces = tire_model.calculate_forces(fz, alpha_req_rad, 0.0, gamma, time_ms, store_history=False)
            result_fy = resulting_forces['Fy']; result_fx = resulting_forces['Fx']
            fy_error = result_fy - target_fy
            fy_error_percent = (fy_error / target_fy * 100) if abs(target_fy) > 1e-3 else (0 if abs(fy_error) < 1e-3 else np.inf)
            result_row.update({'Result Fy (N)': result_fy, 'Result Fx (N)': result_fx, 'Fy Error (N)': fy_error, 'Fy Error (%)': fy_error_percent, 'Status': 'Success'})
            logger.debug(f"  Success: Target Alpha: {math.degrees(alpha_req_rad):.3f}deg")
            logger.debug(f"  Resulting Forces: Fx={result_fx:.1f}N, Fy={result_fy:.1f}N (Error Fy={fy_error:.1f}N / {fy_error_percent:.2f}%)")
        else: logger.warning(f"  Failed: Could not find valid alpha for target Fy={target_fy:.1f}N.")
        results.append(result_row)
    logger.info("--- Pure Fy Inverse Test Suite Finished ---")
    return pd.DataFrame(results)


# --- Function to test internal components (from previous step) ---
def test_tire_components(tire_model, label, Fz, alpha_deg, kappa, gamma_deg):
    """ Tests the internal calculation components of the Pacejka tire model. """
    logger.info(f"--- Testing Components: '{label}' ---")
    alpha_rad = math.radians(alpha_deg); gamma_rad = math.radians(gamma_deg)
    logger.debug(f"Inputs: Fz={Fz:.1f}, alpha={alpha_deg:.2f}deg, kappa={kappa:.3f}, gamma={gamma_deg:.2f}deg")
    results = {'Label': label, 'Fz_in': Fz, 'alpha_in_deg': alpha_deg, 'kappa_in': kappa, 'gamma_in_deg': gamma_deg, 'Status': 'Success'}
    try:
        Fz_proc, alpha_proc, kappa_proc, gamma_proc = tire_model._clamp_inputs(Fz, alpha_rad, kappa, gamma_rad)
        results.update({'Fz_proc': Fz_proc, 'alpha_proc_rad': alpha_proc, 'kappa_proc': kappa_proc, 'gamma_proc_rad': gamma_proc})
        pure_calcs = tire_model._calculate_pure_forces_and_components(Fz_proc, alpha_proc, kappa_proc, gamma_proc)
        results.update(pure_calcs)
        comb_calcs = tire_model._calculate_combined_slip_factors(alpha_proc, kappa_proc)
        results.update(comb_calcs)
        Fx_comb = pure_calcs.get('Fx_pure', 0) * comb_calcs.get('Gxa', 1)
        Fy_comb = pure_calcs.get('Fy_pure', 0) * comb_calcs.get('Gyk', 1)
        results['Fx_combined_calc'] = Fx_comb; results['Fy_combined_calc'] = Fy_comb
        logger.debug(f"Component Calculation Successful. Final Fx={Fx_comb:.2f}, Fy={Fy_comb:.2f}")
    except Exception as e: logger.error(f"Error during component test '{label}': {e}", exc_info=True); results['Status'] = f"Error: {e}"
    return results


# --- Main Execution ---
if __name__ == "__main__":
    param_file = 'hoosier_r20.par' # Make sure this exists

    if not os.path.exists(param_file):
        logger.critical(f"Parameter file '{param_file}' not found. Cannot run tests.")
        exit()

    try:
        # Initialize the tire model
        tire = PacejkaTireSimplified(param_file, return_errors=False, history_name="TestTire")

        # --- Define Test Conditions for Fy Priority ---
        fy_priority_test_conditions = [
            {'label': 'Coast Straight', 'Fz': 600, 'gamma_deg': 0, 'target_fy': 0, 'long_mode': 'coast', 'long_intensity': 0.0},
            {'label': 'Max Accel Straight', 'Fz': 700, 'gamma_deg': 0, 'target_fy': 0, 'long_mode': 'accelerate', 'long_intensity': 1.0},
            {'label': 'Max Brake Straight', 'Fz': 500, 'gamma_deg': 0, 'target_fy': 0, 'long_mode': 'brake', 'long_intensity': 1.0},
            {'label': 'Cornering Coast', 'Fz': 600, 'gamma_deg': -2, 'target_fy': -1500, 'long_mode': 'coast', 'long_intensity': 0.0}, # Should fail if -1500 is too high
            {'label': 'Cornering Med Fy Accel', 'Fz': 700, 'gamma_deg': -2, 'target_fy': -1000, 'long_mode': 'accelerate', 'long_intensity': 0.5},
            {'label': 'Cornering Med Fy Brake', 'Fz': 500, 'gamma_deg': -2, 'target_fy': -800, 'long_mode': 'brake', 'long_intensity': 0.8},
            {'label': 'Impossible Fy Target', 'Fz': 400, 'gamma_deg': 0, 'target_fy': -5000, 'long_mode': 'coast', 'long_intensity': 0.0},
        ]

        # --- Define Test Conditions for Pure Fx Inverse ---
        pure_fx_test_conditions = [
            {'label': 'Zero Fx Target', 'Fz': 600, 'gamma_deg': 0, 'target_fx': 0},
            {'label': 'Moderate Accel', 'Fz': 700, 'gamma_deg': 0, 'target_fx': 1000},
            {'label': 'High Accel', 'Fz': 700, 'gamma_deg': 0, 'target_fx': 1800},
            {'label': 'Moderate Brake', 'Fz': 500, 'gamma_deg': 0, 'target_fx': -800},
            {'label': 'High Brake', 'Fz': 500, 'gamma_deg': 0, 'target_fx': -1300},
            {'label': 'Accel w/ Camber', 'Fz': 700, 'gamma_deg': -2, 'target_fx': 1500},
            {'label': 'Impossible Accel', 'Fz': 400, 'gamma_deg': 0, 'target_fx': 3000},
            {'label': 'Impossible Brake', 'Fz': 400, 'gamma_deg': 0, 'target_fx': -3000},
        ]

        # --- Define Test Conditions for Pure Fy Inverse ---
        pure_fy_test_conditions = [
            {'label': 'Zero Fy Target', 'Fz': 600, 'gamma_deg': 0, 'target_fy': 0},
            {'label': 'Moderate Corner L', 'Fz': 600, 'gamma_deg': 0, 'target_fy': -1000},
            {'label': 'High Corner L', 'Fz': 600, 'gamma_deg': 0, 'target_fy': -1400},
            {'label': 'Moderate Corner R', 'Fz': 700, 'gamma_deg': 0, 'target_fy': 800},
            {'label': 'Corner w/ Camber L', 'Fz': 600, 'gamma_deg': -2, 'target_fy': -1200},
            {'label': 'Corner w/ Camber R', 'Fz': 600, 'gamma_deg': -2, 'target_fy': 1000},
            {'label': 'Impossible Corner L', 'Fz': 400, 'gamma_deg': 0, 'target_fy': -2000},
            {'label': 'Impossible Corner R', 'Fz': 400, 'gamma_deg': 0, 'target_fy': 2000},
        ]

        # --- Define Test Conditions for Components ---
        component_test_conditions = [
            {'label': 'Zero Slips', 'Fz': 600, 'alpha_deg': 0, 'kappa': 0, 'gamma_deg': 0},
            {'label': 'Pure Accel', 'Fz': 700, 'alpha_deg': 0, 'kappa': 0.1, 'gamma_deg': 0},
            {'label': 'Pure Brake', 'Fz': 500, 'alpha_deg': 0, 'kappa': -0.08, 'gamma_deg': 0},
            {'label': 'Pure Cornering', 'Fz': 600, 'alpha_deg': 5, 'kappa': 0, 'gamma_deg': -2},
            {'label': 'Cornering + Accel', 'Fz': 700, 'alpha_deg': 4, 'kappa': 0.05, 'gamma_deg': -2},
            {'label': 'Cornering + Brake', 'Fz': 500, 'alpha_deg': -3, 'kappa': -0.06, 'gamma_deg': -1},
        ]

        # --- Run Test Suites ---
        fy_priority_results_df = run_fy_priority_test_suite(tire, fy_priority_test_conditions)
        pure_fx_results_df = run_pure_fx_inverse_test_suite(tire, pure_fx_test_conditions)
        pure_fy_results_df = run_pure_fy_inverse_test_suite(tire, pure_fy_test_conditions)

        all_component_results = []
        for cond in component_test_conditions:
            res = test_tire_components(tire_model=tire, **cond)
            all_component_results.append(res)
        component_df = pd.DataFrame(all_component_results)


        # --- Display Results ---
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 200)
        pd.set_option('display.float_format', '{:.3f}'.format)

        print("\n\n--- Fy Priority Test Results Summary ---")
        print(fy_priority_results_df.to_string(index=False))
        print("------------------------------------")

        print("\n\n--- Pure Fx Inverse Test Results Summary ---")
        print(pure_fx_results_df.to_string(index=False))
        print("------------------------------------")

        print("\n\n--- Pure Fy Inverse Test Results Summary ---")
        print(pure_fy_results_df.to_string(index=False))
        print("------------------------------------")

        print("\n\n--- Component Test Results ---")
        # Adjust float format for component details if needed
        pd.set_option('display.float_format', '{:.4f}'.format)
        print(component_df.to_string(index=False))
        print("--------------------------")


    except FileNotFoundError as e:
        logger.critical(f"Execution failed: {e}")
    except ValueError as e:
        logger.critical(f"Execution failed: {e}")
    except Exception as e:
        logger.exception("An unexpected error occurred during testing:")


