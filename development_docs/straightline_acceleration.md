
##  Basic steps;

Okay, it is quite simple. On each timestep, the following should happen.

1. The vehicle calculates its current load conditions on all four tires. 
  - [X] Implemented 
2. The vehicle calculates the current parameters to do with the tires (slip angle, ratio, etc)
  - [ ] Pending 
3. The vehicle looks at what the track tells it to do 
  - [ ] Pending 
4. The vehicle applies the resulting forces to the tires
  - [ ] Pending 
5. The tires apply a resultant force to the vehicle.
  - [ ] Pending 
6. The vehicle calculates the next timestep (velocity)
  - [ ] Pending 


## Okay so what i need to do; 

implement inertial forces. All tires need to have both inertial x and y. Inertial is calculated based on the individual effect on each wheel when a force is applied at the center of gravity. 

no wait, "inertial" only applies to cornering. Yes because its the same as weight transfer. But yeah also yeah its true, in longitudinal it is still inertial lol. And so, the way to control this aspect is by going up a higher level and deciding by how much we want to accelerate. We should have a maximum and minimum.  

Okay anyways, for now: 

Inertial should be an added component. INertia is based on the mass thats trying to move. 

$F=ma$, so if we say that the tire accelerated sideways at a rate of $3m/s^2$ and I know that the "mass" associated counts to about 100kg, the total force required is $3000kg*m/s^2$

that means that the frictional force the tire applied in that direction was of ; $3000N$ 


lets assume all tires receive the exact vehicle parameters (velocity, acceleration)

The amount of lateral force determines not only lateral acceleration, but also angular acceleration. 

### Example Tire

$\sum F_x\rightarrow F_{x,grip}-F_{\text{rolling resistance}}=ma_x$

$\sum F_y\rightarrow F_{y,grip}=ma_y$


Lets figure out a way to calculate first : all the necessary parameters of the tire (velocity in x, velocity in y)
    Velocity in x is the same as the cars, cuz its in the direction of the car. 
    Velocity in y is proportional 
With velocity in y, we know what the angular acceleration of the car will cause 


## Parameters to calculate; 

All Forces; 
* front_right: 
  * intertial_x & y
  * x_friction : based on velocity profile
  * y_friction : based on necessary lateral force
  * rolling_resistance : based on tire 
* front_left: 
  * x_friction : based on velocity profile
  * y_friction : based on necessary lateral force
  * rolling_resistance : based on tire 
* rear_right: 
  * x_friction : based on velocity profile
  * y_friction : based on necessary lateral force
  * rolling_resistance : based on tire 
* rear_left: 
  * x_friction : based on velocity profile
  * y_friction : based on necessary lateral force
  * rolling_resistance : based on tire 
* cnt_grav: 
  * inertial_x : based on final acceleration (from force)
  * inertial_y : based on final acceleration (from force)


1. Vertical Load is calculated from the previous forces. (weight transfer)
2. The vehicle's current trajectory is already calculated (position, velocity, acceleration)
3. The tires have a speed and acceleration based on the angular velocity of the vehicle. So basically lets just imagine the tires as individual components that are contributing forces to the whole, and move with it. 
3. Y friction needs lateral force. Lateral force should be the amount 
3. The tires know the current yaw angle and angular speed of the car
2. Tire Velocity 

## To use

* Lateral Tire Force. If we are turning, we can figure out exactly how much force is needed

---
Okay wait so. 
What i need to do is calculate the forces. not just the forces from friction but of "sliding"

So, the force from spinning? Plus the force from inertia? and what they are looking

## 
The car is guide



## Thoughts; 

There is a torque applied to the vehicle through a timestep. This is what I use to determine yaw?

Based on rotational inertia, the applied torque converts to movement. 





# Back to basics; 

All I want is straightline acceleration. This means; 

* Acceleration starts, the tires rotate with torque, and are resisted by the road.
* Force by tire is in direction of travel, but is not in the same axis as the center of gravity. 
* Beacause of this, weight transfer happens. but we leave that for the next timestep. 
* By now however, I can calculate the rest. Because i know exactly what the limit of grip is in this moment (as the tire model will provide this information), I know thats the amount I want to apply. 
* As this force that is the exact limit of grip is applied, the force calculation goes ahead. 
* The Opposing forces are; rolling_resistance and drag. At this speed, there is no drag. you havent started.
* Rolling resistance, we will just use a constant to represent it. 
* Now, you are finally left with a real resultant.This resultant of both vectors is equal to the amount the vehicle will accelerate based on F=ma 
* That means that I set the acceleration throughout the following timestep to be exactly that, and in the correct direction. 
* The combined effect of the current velocity and acceleration is applied for a timestep, at which point the vehicle is in a new point location. 

# Programmatically; 

1. straightline acceleration is called within the simulation. 
    * Just a function running. 
2. A new timestep is created within the for loop. The for loop goes until the position of the vehicle is at or above the wanted one. 
    * lets say the intended distance is 75m 
3. For this part of the timestep, lets just get things ready. I want; 
    * Vertical Load on all four tires 
    * The current velocity and acceleration and yaw angle 
4. Now, I know i want maximum acceleration. what that means is that after figuring out vertical load, all i have to do is apply the maximum longitudinal force. 
5. after applying the maximum longitudinal force, i have to do a force balance. I will end up with a (hopefully) straight force vector that will remain. This is the amount it will accelerate. 
6. Based on acceleration force and direction, i determine where the vehicle point will end up after 75 meters.







#### Banished this bulletpoint because it is too early
4. Now, lets get more complicated; 
    * How much do we want to turn? or better yet, in order to get my point here to the point i want to be at, how much acceleration do i need. 
        * Programmatically compute what acceleration and in which direction is necessary in order to reach a point. This could be the curve acceleration. 

