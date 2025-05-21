## How we want to create a simulation loop 

Maybe its using the current dynamic model 


## Velocity Profile (Tires)

### Track segment types; 

Each segment of a track can only be either straight, or curved. A straight track only has two parameters; its length and the fact that it is straight. A curved track is either Left or Right, and has an associated corner radius and segment length. Depending on the segment the vehicle is traveling on, the velocity profile will vary. 




#### 



# Points along track method

## Implementation 

### Points along track; 

Rather than defining the velocity based on all those dumb parameters and recommended things, why not just define the cornering forces?

cornering forces are purely saying "you need this much force to do this action" 

Does that mean that we do need to fully dynamic analyse?

Wait, not necessarily because i could just do it a point based system. 

## The two point theory

I have two points. One tells me where I am, the other where I want to be. Between the two a distance.

I know a few things. 

I know the velocity of the first point. Its the velocity of the vehicle at that point. 

The distance between the points represents the distance, thus the ?Force? that needs to be exerted. The line between the two also represents the **VECTOR**, the direction you need to apply that force. 


## Okay, so I have 5 vectors. From these 5 vectors, I apply forces to all five of the vectors and find the resultant. Each point has its own vectors corresponding to different forces. These are;

* Front Left Tire  (shares forces with all other tires)
  * Friction Lateral [y]
  * Friction Longitudinal [x]
  * Rolling Resistance [x] 
  * Vertical Load [z]
* Front Right Tire 
* Rear Left Tire 
* Rear Right Tire 
* Center of Gravity
  * Drag Force
  * Mass Acceleration (Force required to accelerate a mass)


Now, for any given time step, there are the following things to note. 

Based on the parameters of vertical load, car position (location and direction), etc i can calculate the frictional force each tire provides. Each tire has its own angle, and the car has its own movement. Based on these is how you get the actual frictional force at those timesteps. 

## I only want straightline Acceleration

In each timestep, use all the force possible on the tires. 

This maximum amount is based on the tire parameters. 

### Parameters
For each timestep, provide the following 

* Ratio of force to apply to cornering. 
* Current Velocity vs Target Velocity 
  * For now, only use this as a boolean "if current_velocity < target_velocity accelerate else brake"
* 
*

### Computing


```python
def compute_acceleration_timestep(
    cornering_force: float,     # 0 to 1, ratio of how much goes to cornering
    current_velocity: float,    # Velocity the vehicle is currently going at [m/s]
    tire_state: dict,           # Current parameters that describe the angle, vertical load, etc of the tire 
                                      #  (all needed to calculate frictional forces)
    target_velocity: float=None # Velocity we are seeking to reach
) -> pd.DataFrame:
```


```
```



### Current steps; 

Implement individual tires; 

Mayeb this could be done within the force point class itself? I coudl just apply the tire attribute to it? that way it can always determine what it needs? this seems kinda good, lets see. 






