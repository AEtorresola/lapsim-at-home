
# Okay so, this will be the simulation process.

1. For a given state, the vehicle has a given target velocity.





# Definitions; 

## Target Velocity 

* Description
  * Calculated based on the maximum velocity at which the vehicle is still able to take a given section
* Inputs
  * Acceleration through turn 
  * Max output velocity 
  * Corner Radius

* Notes; 
  * Target velocity is capped by next segment as well. 
  

* Ideas:
  * Maybe go in reverse? 
  * Get the longest straight as the fr "no limit needed"
  * Actually physically simulate the car per segment?

* What do we want from this? 
  * Determine the maximum velocity at which the car can take a segment 
  * Determine the operating parameters to get to this max amount

* Calculation process (simulated)
  * Given 
    * Vehicle Details 
    * Track segments 
    * Segment radius
  * Process 

* Calculation process (calculated);
  * Given
    * Grip details (G's)
    * Track segments 
    * Segment Radius
    * Steady State max cornering
  * 
    
    
## Maybe its just one simulation? 

* For the track, go in reverse (starting from the longest straight segment).

### Process; 
1. Pick the longest straight segment
2. Start iterating for segments before it.
3. For each segment, 
  * iterate up the velocity 
  * for each velocity, iterate up to find the right steering input 
  * find maximum velocity with which the vehicle is able to take the turn. 
  *

### Necessary functions for it; 

optimize_segment(segment, max_end_velocity, car_details)

cornering_at_vel(cornering_vel , segment, car_details)
    return vehicle_control_params(), 



## Maybe i just make a turn and a align function.


# Defining Control Parameters; 

* Steering angle (affects Forces, Directions)
* Acceleration (affects forces, amount of grip)

## Useful functions; 

* Ability to maintain direction (accelerate or coast while maintaining a given direction)
  * requires using the steering angle to find steady state
  * "if trajectory is off by more than X degrees, adjust steering angle"

* Control system for turning;
  * Gotta figure out what type of profile is used for this sort of thing. 
  
  
# Next steps 

* I am working on a lap simulation piece of software in python. im currently trying to figure out how best to implement the turning control system. i have taken control systems, am finishing the class now. I learned about basic mass springs, and more complex things too in line for the first part of this class. 
question for doing control systems steering type thing

