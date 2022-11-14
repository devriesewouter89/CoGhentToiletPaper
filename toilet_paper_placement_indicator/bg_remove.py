import os
from pathlib import Path
from rembg import remove
from PIL import Image, ImageEnhance

data_dir = Path(Path.cwd() / "training_init_toilet_roll" / "not_far_enough")

for i in os.listdir(data_dir):
    input = Image.open(Path(data_dir / i))
    # output = remove(input)#, alpha_matting=True, alpha_matting_background_threshold=15)
    # output.show()

    # image brightness enhancer
    enhancer = ImageEnhance.Contrast(input)

    factor = 1  # gives original image
    im_output = enhancer.enhance(factor)
    im_output.show("normal")
    factor = 0.5  # decrease constrast
    im_output = enhancer.enhance(factor)
    im_output.show("cont_05")

    factor = 1.5  # increase contrast
    im_output = enhancer.enhance(factor)
    im_output.show("cont_15")

    enhancer = ImageEnhance.Sharpness(input)

    factor = 0.05
    im_s_1 = enhancer.enhance(factor)
    im_s_1.show("sharp005")

    factor = 2
    im_s_1 = enhancer.enhance(factor)
    im_s_1.show("sharp2")
    break
