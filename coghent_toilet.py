'''
Coghent toilet

we want a state machine calling the different blocks of code:
---PREPPING---
1. Waiting state:
    1. no toilet paper rol is present and is prepared
    2. or we've finished a toilet paper roll
    DEBUG: A **light** gives signal that we're in waiting state
    NEXT STATE: we wait for a switch to indicate that we're going to the next state
    ! 4 way switch: forward, backward, neutral, ready to start
2. we find the path in the database of the museum we are (via config file)
    NEXT STATE: once path is found,
    DEBUG ERROR: if not found ERROR LAMP Path
3. prepare toilet paper images:
    1. we download the images
    2. convert images to linedraw vectors in the correct size
    3. create in between pages
    4. place them altogether in folder
---PRINTING---
4. roll the toilet paper roll state:
    1. we start rolling the toilet paper (1 NEMA stepper motor with two GT2 pulleys and inbetween e.g. this belt: https://www.123-3d.nl/123-3D-GT2-timing-belt-6-mm-gesloten-848-mm-i2751-t3046.html)
        ! We keep track of the amount of rotations
    2. we rotate a little and then start checking the camera
    NEXT STATE: once position is correct
5. print the next prepared image
    NEXT STATE: if more images present => state 4 when image is finished
    NEXT STATE: if no more images present => state 6 when image is finished
6. roll back toilet paper state
    DEBUG: the waiting light is shown that we're ready
    We roll back the paper already a bit in approx of the amount of rotations already done
'''
from statemachine import StateMachine, State
from statemachine.exceptions import StateMachineError


class ToiletPaperStateMachine(StateMachine):
    waiting_state = State("waiting", initial=True)
    path_finding_state = State("path_finding")
    prep_images_state = State("prep_images")
    roll_paper_state = State("roll_paper")
    print_image_state = State("print_image")
    roll_back_paper_state = State("roll_back")

    start = waiting_state.to(path_finding_state)
    prep_images = path_finding_state.to(prep_images_state)
    roll_paper = prep_images_state.to(roll_paper_state) | print_image_state.to(roll_paper_state)
    print_image = roll_paper_state.to(print_image_state)
    roll_back_paper = print_image_state.to(roll_back_paper_state)
    wait = roll_back_paper_state.to(waiting_state)

    def on_roll_back_paper(self):
        print("printed the entire roll, rolling back now folks")


if __name__ == '__main__':
    print("starting the coghent toilet paper printer software")
    stm = ToiletPaperStateMachine()
    stm.start()
    stm.prep_images()
    for i in range(0,49):
        stm.roll_paper()
        stm.print_image()
    stm.roll_back_paper()
    stm.wait()
    try:
        stm.print_image() #should trigger an error
    except StateMachineError as e:
        print(e)