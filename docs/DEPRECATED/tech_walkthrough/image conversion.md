Target: prepare an image to be 2D plotted

Problem: images are mostly camera pictures, high res. Thus we need to convert it to line art to be able to plot it.

Found a cool repo: artline, If combined with some tracing programs, this was a good way to go to generate my lineart. Yet due to need of cuda to be able to run it, or need pytorch compiled for CPU. I had a rpi4 lying around, yet immediately getting pytorch (old version!) functioning gave problems with torchvision. I then started looking for some nvidia jetsons, yet apparantly covid chip shortage isn't over yet... So either I had to wait for some jetsons, or recompile pytorch, or go for another approach...

I found a different repo which did 



https://monokai.medium.com/how-to-wirelessly-plot-with-the-axidraw-f9e0a872138e

try with e.g. `saxi plot -s A5  --pen-down-height 2 --pen-up-height 25 --path-join-radius 1 0.svg`

PLOT with pencil what the borders are of A5, then measure the distance for the toilet paper ==> adapt svgs for this.

I've noticed the repo isn't up-to-date anymore and has some issues with polylines, therefore I've adapted my scripts to use only paths in svg.
Basically to avoid my lack of js and dependencies.

## Issues on the toilet paper front

1. paper moving
	1. test with multiple holed plates
	2. perhaps stronger suction? 
2. paper ripping with too many lines/ink
	1. lower the amount of lines close to each other?
3. placement of plotter vs paper 
	1. need to have a fixed position!
	2. have size fixed in 'saxi' library
4. pen vs pencil?
	1. test setup
5. which kind of toilet paper?


## platform

### 3D printed parts

#### fixation for toilet paper
- remove collar
- 2nd part: have fixed size and smaller stem coming out to center
- hole for stepper to big & not aligning nicely
- have at the beginning also some support for rolling?
#### fixation for roll rollers
2x https://www.thingiverse.com/thing:18019
or 2x https://www.thingiverse.com/thing:990946


#### fixation for axi draw
https://www.thingiverse.com/thing:669325 ==> adapt
1x with extraneous holes for screwing
1x half this design, with extraneous holes


#### connection for suction? 
kruimeldief

### platform
#### fixations for rollers & axi draw
- next to each other
- have not holes, but lines, to be able to align the axi draw & rollers slightly
#### colored line
have a not so comon colour to detect?
Or better black, but have image clear of other black things
#### suction panels
3 layer:
1. top layer: multiple hole configurations
2. middle layer: open surface to spread oxygen
3. bottom layer: access for suction pipe
glue middle and bottom
engrave or route the top and middle one to remove some material. in there we place some rubber or let dry some tec7 (separately) to remove air gaps
#### fixation for camera

#### placement of components:
- axidraw **above** the platform
- rollers **beneath** the platform
- camera **above** the platform
raise the platform approx 15cm, keep it tight not to have wiggle when printing

ME311549