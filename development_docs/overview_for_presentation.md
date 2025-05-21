
I am creating a lap simulation program and am looking to make an informative slide talking about the basics of it. I would like you to help me figure out how to format it based on the sort of stuff i want to write. 

To start, I want to show that its a 5 vector force balance. In essence, at any given timestep I go through and solve for each one of the many forces until it is solved. Im not sure how much i want to delve into this exact process, but lets leave the potential to add a small diagram showing the "flow" of calculations per timestep. 

An important parameter to highlight is that I am using the pacejka 2002 model which has quite a few additional parameters. Help me list them out but ill choose which ones i want to include.

Okay, now for the main diagram that shows the overall "process flow" of the simulation. 

First, the program does a preliminary "pass" through the provided track, at each point getting the maximum velocity that is possible based on the tires, and weight transfer, etc. Using this velocity profile, we can go to the next step. 

At any given point in the track, there are basically 3 possibilities for the car. Either it continues at its speed (coasting), starts cornering, or exhibits some amount of longitudinal acceleration (or of course some combination of cornering and one of the others). Cornering is my main "limiter". When the car finds a corner, it determines that there is some amount of yaw and lateral acceleration needed. It will thus determine the amount of forces necessary to reach the desired next position (of yaw angle and position to stay on the track). Then, once this is figured out and mapped to a slip angle (of the front tires, although both sets do have some slip angle, the point is that the program will simplify it such that it calculates how much force is wanted from the front tires to get the yaw angle taking into account the opposite force of the rear tires. but we dont need to delve into this that much, im saying it so you know what the program does). Now, from these desired forces, we can go to the next. One last thing though is that the exact set of things done for lateral, is then done to use the "remaining" tire friction for longitudinal acceleration. This is where the previous steps velocity profile is important. For any given bit of track, I know what the maximum velocity i can reach is. So if i am below that by a margin, i can accelerate (and same thing for deceleration). 

So, i sorta covered this a bit in the previous but now we determine the slip angle. By knowing the desired slip angle for the given forces, (of course taking into account physical  limits), we can calculate what the steering angle needs to be to achieve this. In this same exact way, as i had mentioned the rest of the grip will be used for longitudinal. Since the combined loading of the tire depends on both slip angle and ratio, thats why i first calculate the desired lateral so that then i can just use the "rest" for longitudinal since its less of a limiting factor (unless i am going too fast which i can fix in other ways)

Now, "lastly", the given slip angle and ratio provide me the "desired" steering angle and torque on tires. This ends up being the "top level" output. This is fundamentally what controls the entire car. 

Now, given all these steps i end up with a lot of very useful outputs that i would like to divide into categories, for now Powertrain and Vehicle Dynamics. 

### Powertrain 

* Transient Torques and motor speeds throughout the track 
* From this, we can get the transient power draw 
* We can also end up limiting the torque output dynamically, since the motor is its own class. This means that if the car "asks" for more torque than is available, whether it be because its above the maximum, or the transient heat generation has gotten too high, the motor will be "smart" and limit itself within the program. 

### Vehicle Dynamics; 

* Transient forces on tires, X, Y, Z. This will be useful for transient simulations of all vehicle dynamics parts. 
* Transient traction that tires provide. This is less necessary, and doesnt necesarrily have to be shown as much if at all. Its just useful from a vehicle dynamics perspective to know how much of the tire grip we are using, how we are using it, etc. 
* Then, almost most importantly, we can see how lap times are affected by each and every one of the following parameters (to name a few, but if you think of more that might be applicable ask me and ill check)
  * Center of gravity / height of cog 
  * Tire parameters (pacejka)
  * Steering ratios (the angle difference between the left and right front tires, ackerman / antiackerman)
  * Weight / weight distribution

Okay, so this is the base information. what else do you think we should keep in mind before starting to structure? also, i want it to mostly be diagrams btw so lets keep that in mind. 
