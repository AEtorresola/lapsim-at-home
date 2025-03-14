# Racing Tire Parameter Identification Guide

This guide explains how to obtain parameter values for the simplified Magic Formula tire model for racing applications. It details the tire file format and methods to measure or estimate each parameter for racing tires like Hoosier.

## Tire File Format

The tire file uses a simple text format with parameters defined as `name = value` pairs. Comments start with a percent sign (`%`).

Example:
```
% Hoosier A7 Racing Slick 24.5x13.5-16
R_0 = 0.330       % unloaded tire radius [m]
R_e = 0.315       % effective rolling radius [m]
F_z0 = 4500       % nominal load [N]
% Additional parameters follow...
```

## Essential Parameter Categories

### 1. Geometric Parameters

| Parameter | Description | How to Obtain |
|-----------|-------------|---------------|
| `R_0` | Unloaded tire radius [m] | Measure the tire diameter from the ground to the center of the wheel when unloaded and divide by 2. |
| `R_e` | Effective rolling radius [m] | Mark the tire, roll it one revolution measuring the distance traveled, and divide by 2π. Typically 2-5% smaller than `R_0`. |
| `F_z0` | Nominal load [N] | Use the expected vertical load on the tire at normal operating conditions. For a race car, calculate from weight distribution and downforce. |

### 2. Stiffness Parameters

| Parameter | Description | How to Obtain |
|-----------|-------------|---------------|
| `C_Fx` | Longitudinal stiffness [N] | From the initial slope of a longitudinal force vs. slip ratio plot. If unavailable, use 500,000-600,000 N for racing slicks. |
| `C_Fy` | Lateral stiffness [N] | From the initial slope of a lateral force vs. slip angle plot. If unavailable, use 180,000-220,000 N for racing slicks. |

### 3. Longitudinal Force Parameters

| Parameter | Description | How to Obtain |
|-----------|-------------|---------------|
| `p_Cx1` | Shape factor | Typically 1.5-1.8 for racing tires. Defines the overall shape of the curve. |
| `p_Dx1` | Peak factor | From maximum longitudinal friction coefficient. Measure peak traction in a straight-line acceleration/braking test. Racing slicks typically range from 1.3-1.8. |
| `p_Dx2` | Load dependency | Measure how peak traction changes with load. Typically -0.1 to -0.2 for racing tires (decreasing with load). |
| `p_Ex1` | Curvature factor | Controls the sharpness of the peak. Typically 0.3-0.7 for racing slicks. Higher values create a sharper peak. |
| `p_Kx1` | Stiffness factor | Defines the initial slope. Calculate from the ratio of `C_Fx` to nominal load. Racing tires typically have values from 20-30. |
| `p_Kx2` | Load effect on stiffness | Measure how initial stiffness changes with load. Typically -0.1 to -0.3. |

### 4. Lateral Force Parameters

| Parameter | Description | How to Obtain |
|-----------|-------------|---------------|
| `p_Cy1` | Shape factor | Typically 1.2-1.4 for racing tires. |
| `p_Dy1` | Peak factor | From maximum lateral friction coefficient. Measure in a skidpad test. Racing slicks typically have values from -1.0 to -1.3. |
| `p_Dy2` | Load dependency | Measure how lateral peak traction changes with load. Typically -0.1 to -0.2. |
| `p_Ey1` | Curvature factor | Controls the sharpness of the lateral peak. Typically -0.5 to -1.0 for racing slicks. |
| `p_Ky1` | Cornering stiffness factor | Calculate from the ratio of `C_Fy` to nominal load. Racing tires typically have values from 15-25. |
| `p_Ky2` | Load at which cornering stiffness is maximum | Typically 1.2-1.8. Can be obtained by testing lateral force at different loads. |

### 5. Combined Slip Parameters

| Parameter | Description | How to Obtain |
|-----------|-------------|---------------|
| `r_Bx1` | Combined slip reduction for Fx | Typically 10-15. Controls how quickly longitudinal force drops with slip angle. |
| `r_By1` | Combined slip reduction for Fy | Typically 8-12. Controls how quickly lateral force drops with slip ratio. |

### 6. Temperature Sensitivity Parameters

| Parameter | Description | How to Obtain |
|-----------|-------------|---------------|
| `temp_opt` | Optimal operating temperature [°C] | From manufacturer data or testing peak grip at different temperatures. Hoosier slicks typically 80-90°C. |
| `temp_range` | Effective temperature range [°C] | Range where grip is within 10% of maximum. Typically 25-40°C for racing slicks. |
| `grip_temp_factor` | Grip reduction outside optimal temperature | Typically 0.1-0.3. Higher values mean more temperature sensitivity. |

### 7. Wear Parameters

| Parameter | Description | How to Obtain |
|-----------|-------------|---------------|
| `wear_constant` | Wear rate constant | Empirical value, typically 0.0001-0.001. Higher for softer compounds. |
| `wear_exponent` | Wear rate sensitivity to slip | Typically 1.5-2.5. Higher values indicate wear increases more rapidly with slip. |

## Testing Methodologies

### Force-Slip Curve Testing

**Equipment needed:**
- Tire test rig or instrumented vehicle
- Load cells to measure forces
- Wheel position/velocity sensors

**Testing procedure:**
1. Mount the tire with appropriate camber
2. Apply constant load (start with nominal load)
3. Gradually increase slip while measuring forces
4. Repeat for different loads and temperatures

**Parameter extraction:**
1. Plot force vs. slip curves
2. Identify initial slope for stiffness (C_Fx, C_Fy)
3. Identify peak force for D parameters
4. Fit the Magic Formula curve to extract B, C, E parameters

### Temperature Sensitivity Testing

1. Conduct skidpad tests at different tire temperatures
2. Plot grip vs. temperature
3. Identify the temperature at peak grip (temp_opt)
4. Calculate temperature range and sensitivity factor

### Combined Slip Testing

1. Hold a constant slip angle while varying slip ratio (or vice versa)
2. Measure both Fx and Fy
3. Plot the friction ellipse (Fx vs Fy)
4. Fit combined slip parameters to match the observed friction ellipse

## Simple Testing with Limited Equipment

If specialized testing equipment isn't available, here are alternative approaches:

1. **Skidpad Testing:** Use smartphone accelerometers or data loggers to measure lateral acceleration at different slip angles.

2. **Acceleration/Braking Tests:** Measure straight line acceleration/deceleration to estimate longitudinal parameters.

3. **Rollout Tests:** Roll the tire to measure effective radius.

4. **Tire Temperature Monitoring:** Use infrared thermometers or temperature stickers to correlate temperature with subjective grip.

5. **Manufacturer Data:** Contact Hoosier for general performance data for your specific tire model.

6. **Scaling from Known Tires:** Use publicly available data for similar tires and scale parameters proportionally.

## Parameter Refinement

After obtaining initial estimates:

1. Implement the model with estimated parameters
2. Compare model predictions with measured data
3. Use optimization algorithms to fine-tune parameters
4. Validate on different maneuvers

For racing applications, focus on accurately capturing:
- Peak forces
- Temperature sensitivity
- Initial response (stiffness)
- Combined slip behavior

This will give you the most important characteristics for race simulation and vehicle setup optimization.
