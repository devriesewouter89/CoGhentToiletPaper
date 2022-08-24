import os

import fastai
from fastai.vision import *
from fastai.utils.mem import *
from fastai.vision import open_image, load_learner, image, torch
import numpy as np
import PIL.Image
from PIL import Image
from pathlib import Path
import subprocess


class FeatureLoss(nn.Module):
    def __init__(self, m_feat, layer_ids, layer_wgts):
        super().__init__()
        self.m_feat = m_feat
        self.loss_features = [self.m_feat[i] for i in layer_ids]
        self.hooks = hook_outputs(self.loss_features, detach=False)
        self.wgts = layer_wgts
        self.metric_names = ['pixel', ] + [f'feat_{i}' for i in range(len(layer_ids))
                                           ] + [f'gram_{i}' for i in range(len(layer_ids))]

    def make_features(self, x, clone=False):
        self.m_feat(x)
        return [(o.clone() if clone else o) for o in self.hooks.stored]

    def forward(self, input, target):
        out_feat = self.make_features(target, clone=True)
        in_feat = self.make_features(input)
        self.feat_losses = [base_loss(input, target)]
        self.feat_losses += [base_loss(f_in, f_out) * w
                             for f_in, f_out, w in zip(in_feat, out_feat, self.wgts)]
        self.feat_losses += [base_loss(gram_matrix(f_in), gram_matrix(f_out)) * w ** 2 * 5e3
                             for f_in, f_out, w in zip(in_feat, out_feat, self.wgts)]
        self.metrics = dict(zip(self.metric_names, self.feat_losses))
        return sum(self.feat_losses)

    def __del__(self): self.hooks.remove()


def add_margin(pil_img, top, right, bottom, left, color):
    width, height = pil_img.size
    new_width = width + right + left
    new_height = height + top + bottom
    result = Image.new(pil_img.mode, (new_width, new_height), color)
    result.paste(pil_img, (left, top))
    return result


def convert_dir_to_lineart(input_dir: Path, output_dir: Path):
    for img_name in os.listdir(input_dir):
        img = open_image(os.path.join(input_dir, img_name))
        p, img_hr, b = learn.predict(img)
        p.save(os.path.join(output_dir, img_name))


def convert_dir_to_vectors(input_dir: Path, output_dir: Path):
    for img_name in os.listdir(input_dir):
        fig_pth = os.path.join(input_dir, '{}.png'.format(img_name))
        svg_pth = os.path.join(output_dir, '{}.svg'.format(img_name))
        cnvt_fig_pth = os.path.join(output_dir, '{}.pnm'.format(img_name))
        subprocess.run("convert", fig_pth, cnvt_fig_pth)
        subprocess.run("potrace", cnvt_fig_pth, "--svg", "-o", svg_pth)
        with open(svg_pth, "r+") as f:
            # we open the file in read+append, after we change the content, we jump to start and overwrite the content
            a = f.read()
            a = a.replace('fill="#000000"', 'fill="none"')
            a = a.replace('stroke="none"', 'stroke="#000000"')
            f.seek(0)
            f.write(a)
            f.truncate()


def tensor_to_image(tensor):
    tensor = tensor * 255
    tensor = np.array(tensor, dtype=np.uint8)
    if np.ndim(tensor) > 3:
        assert tensor.shape[0] == 1
        tensor = tensor[0]
    return PIL.Image.fromarray(tensor)


if __name__ == '__main__':
    print("make sure to bind the input folder to /workspace/coghent_input and the output folder to "
          "/workspace/coghent_results")
    # MODEL_URL = Path(Path.cwd() / "models" / "Artline_920.pkl")
    # model_path = os.path.join(os.getcwd(), 'ArtLine_920.pkl')
    # urllib.request.urlretrieve(MODEL_URL, "ArtLine_920.pkl")
    print("hello world")
    path = Path(".")
    learn = load_learner(path, 'ArtLine_920.pkl')
    input_dir = Path(Path.cwd() / "coghent_input")
    output_dir = Path(Path.cwd() / "coghent_results")
    temp_dir = Path(Path.cwd() / "coghent" / "temp")
    os.makedirs(temp_dir, exist_ok=True)
    convert_dir_to_lineart(input_dir, output_dir)
    # convert_dir_to_vectors(temp_dir, output_dir)
