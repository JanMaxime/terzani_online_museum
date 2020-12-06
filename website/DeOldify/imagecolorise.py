import urllib.request
from PIL import Image
import torch
import os
import warnings
import pickle
from .deoldify.visualize import get_image_colorizer
from .deoldify import device
from .deoldify.device_id import DeviceId
device.set(device=DeviceId.GPU0)
torch.backends.cudnn.benchmark = True
warnings.filterwarnings("ignore", category=UserWarning,
                        message=".*?Your .*? set is empty.*?")


def colorise_image(source_url, current_directory, render_factor=20):
    colorizer = get_image_colorizer(current_directory, render_factor)
    result_image = None
    if source_url is not None:
        result_image = colorizer.get_transformed_image(
            path=source_url, render_factor=render_factor)
    return result_image


def colorise_me(source_url, source_label, render_factor):

    current_directory = os.path.dirname(os.path.realpath(__file__))

    cached_color_images_dir = os.path.join(
        current_directory, 'cached_color_images')

    if not os.path.exists(cached_color_images_dir):
        os.makedirs(cached_color_images_dir)

    color_images_pickle = os.path.join(
        cached_color_images_dir, 'cached_color_images.pickle')
    try:
        cached_color_images = pickle.load(
            open(color_images_pickle, "rb"))
    except IOError:
        cached_color_images = {}

    website_static_images = os.path.normpath(
        current_directory + os.sep + os.pardir+"/static")
    color_images_dir = os.path.join(
        website_static_images, 'colorised_images')
    if not os.path.exists(color_images_dir):
        os.makedirs(color_images_dir)
    colorised_image_link = os.path.join(color_images_dir, source_label+".png")

    if source_label not in cached_color_images:

        models_dir = os.path.join(current_directory, 'models')

        if not os.path.exists(models_dir):
            os.makedirs(models_dir)

        model_path = os.path.join(models_dir, 'ColorizeStable_gen.pth')

        if not os.path.exists(model_path):
            model_url = 'https://www.dropbox.com/s/usf7uifrctqw9rl/ColorizeStable_gen.pth?dl=0'
            urllib.request.urlretrieve(model_url, model_path)

        color_image = colorise_image(
            source_url, current_directory, render_factor)
        cached_color_images[source_label] = color_image

        color_image.save(colorised_image_link)

        with open(color_images_pickle, 'wb') as handle:
            pickle.dump(cached_color_images, handle,
                        protocol=pickle.HIGHEST_PROTOCOL)

        for fname in os.listdir(models_dir):
            if fname.startswith("tmp"):
                os.remove(os.path.join(models_dir, fname))

    return colorised_image_link
