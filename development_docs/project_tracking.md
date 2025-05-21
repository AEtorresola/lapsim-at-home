
# Make an interface for tracks; 

## Start visualizing the vehicle moving through a simple track 

### Important Segment types to check:

* Constant radius turn,
* Non-constant radius turn 
* Straightline acceleration
* Straightline braking 
* Consecutive turns (weight transfer?)

* Turn acceleration
* Turn Braking

### Forces needed; 

On car; 

1. Mass reaction ($\Delta V$ & Mass Distribution)
2. Drag Force Aerodynamics ($V,\ Area,\ C_d$)
3. Rolling Resistance ($m, C_{rr}$)
4. Tractive Force

### What we optimize for;

*We want to be utilizing the maximum tractive force at each and every point.*

#### Tractive force depends on:
* Current Velocity 
* Target Velocity for Segment
* Current Acceleration
* Current turning (and mass)
* Tire temperature 
* Tire coefficient 
* Normal Force on each tire
*


# Lapsim from FSAE Event 

## All forces at any given point:

1. $F_m=m*a$
  * Force needed to change velocity
2. Forces to overcome (losses);
  * Drag Force
  * Rolling Resistance
  * 
3. Forces applied to tires;
  * Steering force (front tires, solely involves changing the direction of the front tire forces)
  * Engine force (rear tires)
  * Braking force (both tires, with percent split)




Consider creating a vector type thing that is moved around at all points. One definite result to get is a vector track showing all forces at all points along the track
#### Braking; 

For braking, lets assume that the tire can fully be stopped at any point. At this point, all we want is to maximize the amount of tire force we use based on the target velocity.

#### Steering; 

Involves modifying direction of front tire vector. Whereas before the front tires apply no force, here they will 



