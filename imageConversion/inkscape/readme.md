# inkscape scripting

I want to be able to control what needs to happen to my images without the need for a GUI.

Example, I want to be able to open an svg file, remove the fills or alter the fills to hatches and generate GCODE based on the svg.

The GCODE file can then be used to send directly to the axidraw to plot on the paper.

## how to

you need to make an xml file and save it as .inx

Open it via python and adapt it for the purpose we want.

Copy the python as well as inx file to either 

- `.config/inkscape/extensions`
- `.var/app/org.inkscape.Inkscape/config/inkscape/extensions`

