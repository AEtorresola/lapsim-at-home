
Okay so;

The tire is iterated on each timestep. 

On each timestep, a new set of values is provided; 

## Tire Timestep Parameters;
```python
self.force_input = 0                # Braking force (N) 
self.tire_angle = 0                 # Tire angle (rad)
self.tire_vertical_load = self.f_t("vertical_load", self.Car.current_time)        # Vertical load (N)
self.tire_longitudinal_vel = 0      # Longitudinal velocity (m/s)
self.dt = Car.timestep                  # Time step (s)
```
## Explanation; 

In each new timestep, these are the things that change. The force input is one of two types of inputs we want. The other is tire_angle. 

Then we have something like tire_vertical_load. This is fully dependent on the state of the system, but is relatively simple since it has already been implemented.

Next, is the harder part; the tire longitudinal velocity. 

### Tire Longitudinal Velocity;

The longitudinal velocity is used to calculate slip ratio? 

#### Implementation options; 

Since the final product is just determining how the tire behaves, we should define how we want to input information. Should I define on my end a given slip-ratio / slip angle? or do I give it just the basics of tire speed vs real speed. 

Would it make sense to create a tire model for a simulation program that uses all of the necessary math from the magic formula, but ends up simplifying to inputting the amount of force I want to apply to acceleration and braking and cornering. then it gets the right slip ratios and slip angles that correspond to these braking and accelerating inputs (or also lateral force inputs for front lateral forces), and uses them in the tire model to get the output of the requisite slip angles or slip ratios to get there. 


## Weight transfer; 

Keep in mind that current implementation only does weight transfer based on the total mass of the vehicle. 

In 5.3 of Race Car Design, it discusses utilizing a combination of sprung and unsprung mass in order to get a more accurate model of how weight transfer loads the tires. 


