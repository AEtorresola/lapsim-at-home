
# Basics of Lap-simulation

The express purpose of a lap simulation is to model all of the feasible components of the vehicle in a fully physics defined way that allows for programmatically running the car around a track. 

### Desired Output; 

There are many reasons to want to create an accurate lap simulation. Among them, the most important for our use-cases are finding transient load characteristics of parts of the vehicle, determining transient motor usage, and understanding the real combined effects of component modification. 

Being able to tangibly compare the performance characteristics of different parameters allows us to not only push for optimized parameters, but to do so in the absolute most effective way possible; ie, give quantitative values to parameters that might usually be overlooked.
    
#### Example; 
* Rather than simply choosing to reduce weight because of the perceived positive effects on the vehicle performance, solid numbers can be given to support the change. 
* Instead of saying "Reduced Center of Gravity height by 30cm in order to improve handling characteristics", we can quantitatively state something like "Reduced Center of Gravity height by 30cm, contributing to a x.x second lap time saving and a x% decrease in lateral and longitudinal load transfer".
* This allows us to not just pick and choose which parameters based on subjective criteria, and contributes to a much more cohesive design methodology 
  
 ---- 

As mentioned, the transient load characteristics of the vehicle are going to be incredibly useful as well. When validating a design through analysis, we can apply not just steady state or maximum loads to a part, but instead see how the part is stressed throughout a typical run. Rather than fully replace the existing "maximum stress analysis" that is done, it is meant to complement it. To further validate that not only does the part work well under its maximum parameters, but that it behaves ideally under its real-world load characteristic.

### Output Parameters; 
The following is a non-comprehensive list of all the parameters that will be tracked throughout a given lap
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
  * Tire temperatures (can use a simple slip-angle heat generation model in the future to model tire temps)

# Lap Simulation Methodology

As mentioned, the lap simulation is a purely physical dynamic model. In contrast to previous offerings that have been utilized, this simulation will not use simple point mass model. Instead, we will use a 5 vector force model.


This method allows us to track the vehicle model by boiling it down to the 5 most important points where forces are transferred, the four tires and the center of gravity. 

By creating transient force vectors that respond to driver input, track parameters, vehicle responses, vehicle constants, and tire models, we can get a more accurate dynamic view of what is happening throughout a given track.

Additionally, the way it is being built up will allow for additional force vectors to be added. This means that in the future, we could create additional force vectors to represent aerodynamic components (and the transient nature of the simulation means that these components can even be modelled as active aero in a future). 

## Simulation Process 

This is a preliminary summary of the process through which the program will go about modelling a track.

1. Define all vehicle and track parameters.
2. The program utilizes the tire and weight transfer parameters to create a preliminary velocity profile of the track
    * This velocity profile is basically a solely traction limited model of how fast the car can move around the track. 
    * It will approach each individual segment with the knowledge of how fast it can theoretically go at each timestep.
    * if it reaches a corner, it not only uses steady state cornering, but also will implement combined braking and cornering for maximum use of the tire circle at all points. 
* The basics of it are this: Use the maximum amount of combined lateral and longitudinal tire force for any given track segment. 

With this, we now have a "target" for our velocities

3. Now, with the actual vehicle we can simulate a "real" run. 
    * A real run involves a motor power limited simulation. Rather than running at maximum traction all of the time, we now have to take into account that motor power reaches a cap
    * The step by step process is similar to before, except that now the determination for how the vehicle moves around the track now has a limited amount of acceleration. 
4. A real run is defined in 4 steps for each and every time-step:
    * What is our current velocity, and what is the target velocity?
    * What is our current cornering force, and what is the target cornering force?
    * What throttle and braking inputs make us reach the target velocity (or target acceleration)
    * What cornering input makes us reach the target cornering force
 5. Thus, for each consecutive time-step, we are calculating all forces in the 5 vectors and determining the vehicle inputs based on the target profiles. 
    * Basically, if we are currently at a constant speed, but the target velocity profile says that we need to be braking for the following time-step, we can determine the desired braking force, and then apply it to the physical model. 
    * This allows us to actually physically observe what the vehicle is doing at any point based on the forces it is receiving whether they be forces on the track (lateral loads in cornering), or forces applied by the vehicle (longitudinal load in acceleration)
    
## Tire model

"The Formula Ford that finished dead last at the East Nowhere SCCA Regional has one vital factor in common with the Indianapolis or Grand Prix winning machine--it is connected to the race track only by the contact patches of its four tires" - Carrol Smith, Tune to Win

None of the previous components mean anything if we are not accurately modeling the tire. After all, the "maximum grip model" only works if we have a decently accurate model of the maximum grip at any given time. This is where the five vectors come in handy. 

The two main transient components on a tire that we can input are:
1. Vertical load (Normal Force)
2. Slip Angle

These are the components that let us determine how much grip the tire can provide at a given timestep.


Slip angle is calculated purely from difference between vehicle yaw angle and the tire angle.

Vertical load is a bit more involved. Statically it can be calculated based on the position of the center of gravity. Once the situation is dynamic however, we must involve weight transfer. 

Lateral and Longitudinal load transfer can be calculated by the following equations respectively. 

* Lateral Load Transfer 

$\Delta W_y=\pm \frac{Fh_m}{T}$ where $T=trackwidth$

* Longitudinal Weight Transfer $\Delta W_x=\pm \frac{Fh_m}{L}$ where $L=wheelbase$

The force that must be use is the force corresponding to the x and y force in a previous timesteps grip. By delaying which force is used (lets say use the force at time = -0.20), we are basically saying that it takes about 0.20 seconds for a given force to be transmitted throughout the chassis, and thus we can determine the weight transfer as a lagged function of time (which is more accurate to the real use-case. it takes time for the force to go through the springs and dampeners in the system)


## feedback 

para optimizar; el motor funciona a un putno. para aceleracoin por ejemplo se empuja hasta abajo. 




