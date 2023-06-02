#! /bin/bash
echo "going to calibrate mode for camera"
python physical_control/toilet_paper_placement_indicator/template_matching.py -p
echo "going to calibrate height of the pencil"
python print_timeline/plotter/plotter.py


