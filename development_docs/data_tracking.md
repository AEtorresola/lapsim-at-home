
# Data Capture 

In order to accurately simulate the laps, we need to calculate and store all parameters at the given time steps. 

## All parameters to track

* General Details 
  1. Time step
* Track Details
  1. Segment #
  2. Segment Type
  3. Segment Corner Radius
  4. Segment Length
  2. Segment Distance (current distance along the segment)

 
* Vehicle Details 
  1. Vehicle Velocity 
  2. Delta Acceleration (Sum of all forces, final)
  3. Vehicle Direction 

* Driver Details 
  1. Steering angle
  2. Throttle input 
  3. Brake input 

* Motor Details
  1. RPM (based on velocity)
  2. Maximum Torque (at RPM) 
  3. Continuous Torque (at RPM)
  4. Root Mean Squared Motor usage (for overheating)

* Vehicle Forces 
  * Body Loads 
    1. Loads on CoG
    2. Loads from downforce (can be point loads at location of car)
    3. 
  * Normal Force
    1. Front Left - Normal Force
    2. Front Right - Normal Force
    3. Rear Left - Normal Force
    2. Rear Right - Normal Force
  * Maximum Tire Force
    1. Front Left - Maximum Tire Force (grip)
    2. Front Right - Maximum Tire Force (grip)
    2. Rear Left - Maximum Tire Force (grip)
    2. Rear Right - Maximum Tire Force (grip)
  * Actual Tire Force
    1. Front Left - Actual Tire Force (grip)
    2. Front Right - Actual Tire Force (grip)
    2. Rear Left - Actual Tire Force (grip)
    2. Rear Right - Actual Tire Force (grip)
  * Tire Resistances ; 
    1. Front Left - Rolling Resistance
    2. Front Right - Rolling Resistance
    2. Rear Left - Rolling Resistance
    2. Rear Right - Rolling Resistance

* Tire Details 
  * Tire Angles (all four)
  * Slip Angle
    * To get slip angle, we will have to calculate it based on what direction the vehicle is moving. if it is turning in a regular curve, we can determine the rear tire angle based on what total angle the vehicle is taking, and what that means to the tire. basically, if the car had a yaw of 3 degrees, i think this would result in a 3 degree slip angle on the rear tires (whereas the front tires are the ones causing this yaw, so it works different there) - Diego
    *


## End Result;


By calculating all of the previous parameters based on either vehicle or track parameters (or previous timestep parameters), we can get an accurate picture of what is happening in the track
