
== Lap Simulation Parts; 


- car.py 
 - Handles most of the highest level logic 
 - Most of the parts of the simulation in terms of things that the car does are handled by this part of the script. 
 - References most of the other scripts 
 - Generates for example the relevant tire model itself 
 
 

- tires.py 
  - One of the most important single parts of the car 
  - Inherently handles all of the tire-specific calculations 
  - Divided into physical tire and magic formula tire: 

- motor.py 
  - Handles the actual input/output of determining if a given torque can be provided 
  - Uses the motor power curves to determine whether a specific torque (given RPM) is valid, and then determines what the operating characteristics will thus be.
  -  Will have functions to limit torque based on the transient heat parameters 

- track.py 
  - Class to create and use tracks 
  - Has visualization methods 

- simulation.py
  - Combines all of the previous scripts to get the movement of the car around the track. 
  - Maybe consider dividing into different simulation types?

    
#pagebreak()

= Simulation 

\
\
\



=== Simulation Parts 


- Lateral Handling ;
  - This will be handled by an "optimizing" function. 
- Longitudinal Handling ;
  - Based on where on the track the vehicle is and the _precalculated_ velocity profile, we can determine whether we want to accelerate or decelerate. 

==== Optimizing Cornering 

+ Find the longest straight of the track 
+ In reverse, iterate the track segments 
+ For each track segment, determine input params for the following cases: 
  - Maximum entry speed (what is the fastest speed that a car can enter the turn at)
  - Minimum segment time 
+ Use the previous segments maximum entry speed as the maximum exit speed for the current segment
+ Always optimize for fastest 


=== Idea; 

determine the points myself. with some amount of calculation based on logic. 

I set an entrance speed, maybe desired acceleration? 

=== Current tasks 

#import "@preview/cheq:0.2.2": checklist
#show: checklist

- [ ] Finish building out vehicle simulation 
  - [ ] Implement Steering 
  - [ ] Implement Throttle 
  - [ ] Implement overall physics
  
- [ ] 

#pagebreak()

= Physical Model


=== Car 

+ 5 vector model 
  - Four Tires
  - Center of Gravity 
+ As throttle is applied, slip ratio is increased (thus accelerating car)
+ As steering angle is applied, slip angle is introduced which causes lateral acceleration. 

--- *Summary*:

Physical model works by applying throttle and steering to a given situation and it thus simulates the resultant movement of the vehicle.

== Process Overview

+ Make steering function 
+ Make motor function 
+ Make timestep function that combines the two. 
+ Test timestep function by tracking the vehicles movement from a set of inputs (inputs will be just straightline acceleration and then cornering of some kind)


= #underline()[Necessary Functions ]

==== Time step function 
- Timestep
  - inputs: 
    - Steering angle (must be within +- of previous) (basically ensure plausible steering velocity)
    - Throttle input (0-100%) (only varies the provided torque) (torque can be 0-100% of available torque at that given rpm)
  - outputs:
    - Calculates the torque based on previous
    - Calculates the slip angle of all the tires 
    - Calculates the slip ratio of all the tires
    - From the slip angle and slip ratio, calculates the resultant forces of the tires 
    - If the resultant forces exceed the capacity of the tires, we modify either of the inputs until it does work.

==== Motor Function
- Parts
  - inputs 
    - throttle % 
    - rpm 
  - outputs
    - $"output torque" = "throttle %" times "max available torque @ RPM"$
    - above continuous torque (flag)
    - overheat_value (rms of power usage)
  - parameters
    - continuous torque curve 
    - max torque curve 

==== Steering Function

- Parts
  - inputs 
    - steering angle % 
  - outputs 
    - sets the steering angle of the steered wheels 
    - does not apply the steering automatically, just provides the correct values 
    - verifies that the steering angle "speed" is not excessive (checks that the delta angle over time does not exceed an amount)
  - parameters
    - ratio between steering angle and actual steering performed per wheel





#pagebreak()


#columns(2)[
=== Physical Tire 
\
_*tire_class*_
\

Holds all non-magic formula tire parameters and methods divided into the following categories:

=== Static parameters 
- width 
- diameter 
- rotational inertia

===== Transient parameters 
- steering angle
- angular velocity 
- angular acceleration
- slip angle? 

=== Methods 



#colbreak()
=== Magic Formula Tire

\
_*new_magic_formula_tire*_
\

Holds all the parameters and methods to do with calculating tire forces themselves.
\
\

=== Static parameters 
- Magic tire formula parameters 
\

=== Transient parameters 
- longitudinal tire forces
- lateral tire forces

\
\

=== Methods 



]


