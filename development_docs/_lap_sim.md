

## Initial Lapsim Steps 

1. For the given track, determine the following
    * Velocity Profile, to see what speed the car should go through each part of the track
2. 



## Tire model based lapsim 

1. Velocity Profile of track is given.
2. With this velocity profile, at any given time, its simple to just ask "are we at the target velocity?" "if not, accelerate"
3. Lets define three basic parts of the vehicle movment.
  * Current Tire Capacity (based on current speed, mass transfer, etc)
  * Target Velocity
  * Driver inputs;
  * Previous Inputs

### Current Tire Capacity;

Two main parameters; Normal Force and Tire Force

They are each dependent on;

* Normal Force
  * Total Weight
  * Center of Gravity
  * Downforce
  * Weight Transfer (Longitudinally)
  * Weight Transfer (Laterally)
* Tire Force
  *

### Current Functioning Parts;; 

Given an x, y acceleration and time profile, we can determine the weight trasnfer. 

Using this, we can determine the normal force on each of the tires, therefore determine the max tire force for each timestep. 

One important thing to note is that since the max acceleration force is based on the tire force anyways, i can use one to get the other, 

ie; use the previous timestep to know the normal force, and thus tire force available.

# Bottom to Top; 

1. determine velocity profile for track. 
  * This is just a calculation of the max velocity the vehicle can be at for a given turn. 
  * Given this definition, might not include straights in the equation. 
2. 


## Velocity Profile Calculation; 

1. Use a turn radius to determine the maximum speed we can take it, knowing our weight transfer parameters and tire models. 
2. Mathematically


3. 

About velocity profile. it would be ideal to use all parts of the tire model for it. Whoa, what if the velocity profile just fully calculates a tire model?

#### Easy math; 

Centripetal Force at turn $F=ma=\frac{mv^2}{R}$

Now we know that the cornering force has to be equal to this, at least. 


## Tire Forces FBD;

Maybe what i need to make first is just the full dynamic model...

What does it need? 

The car 


# Dynamic Model 

So, i believe i should create as much of the dynamic model as i can firsthand.

This involves tracking all of the forces. So i need a good way to register which forces go where and how to track them. 

I think each point i want to track should have its own associated class?

okay so, lets have a force point class. at a given position, forces can be applied. So this class needs; a way to add/change force at a given timestep


