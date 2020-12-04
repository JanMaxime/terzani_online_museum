import urllib.request
from PIL import Image
import torch
import os
import warnings
import pickle
from .deoldify.visualize import get_image_colorizer
from .deoldify import device
from .deoldify.device_id import DeviceId
device.set(device=DeviceId.GPU1)
torch.backends.cudnn.benchmark = True
warnings.filterwarnings("ignore", category=UserWarning,
                        message=".*?Your .*? set is empty.*?")


def colorise_image(source_url, render_factor=20):
    colorizer = get_image_colorizer()
    result_image = None
    if source_url is not None:
        result_image = colorizer.get_transformed_image(
            path=source_url, render_factor=render_factor)
    return result_image


def colorise_me(source_url, source_label, render_factor):

    if not os.path.exists('cached_color_images'):
        os.makedirs('cached_color_images')

    try:
        cached_color_images = pickle.load(
            open("./cached_color_images/cached_color_images.pickle", "rb"))
    except IOError:
        cached_color_images = {}


    colorised_image_link = "./static/colorised_images/"+source_label+".png"

    if source_label not in cached_color_images:
        if not os.path.exists('models'):
            os.makedirs('models')

        if not os.path.exists('./models/ColorizeStable_gen.pth'):
            model_url = 'https://www.dropbox.com/s/usf7uifrctqw9rl/ColorizeStable_gen.pth?dl=0'
            urllib.request.urlretrieve(
                model_url, './models/ColorizeStable_gen.pth')

        color_image = colorise_image(source_url, render_factor)
        cached_color_images[source_label] = color_image

        color_image.save(colorised_image_link)

        with open("./cached_color_images/cached_color_images.pickle", 'wb') as handle:
            pickle.dump(cached_color_images, handle, protocol=pickle.HIGHEST_PROTOCOL)


    return colorised_image_link
