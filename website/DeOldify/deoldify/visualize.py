from fastai.core import *
from fastai.vision import *
from .filters import IFilter, MasterFilter, ColorizerFilter
from .generators import gen_inference_deep, gen_inference_wide
from PIL import Image
import requests
from io import BytesIO
import cv2


# adapted from https://www.pyimagesearch.com/2016/04/25/watermarking-images-with-opencv-and-python/
def get_watermarked(pil_image: Image) -> Image:
    try:
        image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        (h, w) = image.shape[:2]
        image = np.dstack([image, np.ones((h, w), dtype="uint8") * 255])
        pct = 0.05
        full_watermark = cv2.imread(
            './resource_images/watermark.png', cv2.IMREAD_UNCHANGED
        )
        (fwH, fwW) = full_watermark.shape[:2]
        wH = int(pct * h)
        wW = int((pct * h / fwH) * fwW)
        watermark = cv2.resize(full_watermark, (wH, wW),
                               interpolation=cv2.INTER_AREA)
        overlay = np.zeros((h, w, 4), dtype="uint8")
        (wH, wW) = watermark.shape[:2]
        overlay[h - wH - 10: h - 10, 10: 10 + wW] = watermark
        # blend the two images together using transparent overlays
        output = image.copy()
        cv2.addWeighted(overlay, 0.5, output, 1.0, 0, output)
        rgb_image = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)
        final_image = Image.fromarray(rgb_image)
        return final_image
    except:
        # Don't want this to crash everything, so let's just not watermark the image for now.
        return pil_image


class ModelImageVisualizer:
    def __init__(self, filter: IFilter):
        self.filter = filter

    def _clean_mem(self):
        torch.cuda.empty_cache()
        # gc.collect()

    def _get_image_from_url(self, url: str) -> Image:
        response = requests.get(url, timeout=30, headers={
                                'Accept': '*/*;q=0.8'})
        img = PIL.Image.open(BytesIO(response.content)).convert('RGB')
        return img

    def get_transformed_image(
        self, path: Path, render_factor: int = None, post_process: bool = True,
        watermarked: bool = True,
    ) -> Image:
        self._clean_mem()
        orig_image = self._get_image_from_url(path)
        filtered_image = self.filter.filter(
            orig_image, orig_image, render_factor=render_factor, post_process=post_process
        )

        if watermarked:
            return get_watermarked(filtered_image)

        return filtered_image


def get_image_colorizer(folder, render_factor: int = 35) -> ModelImageVisualizer:
    return get_stable_image_colorizer(root_folder=folder, render_factor=render_factor)


def get_stable_image_colorizer(
    root_folder: Path = Path('./'),
    weights_name: str = 'ColorizeStable_gen',
    results_dir='result_images',
    render_factor: int = 35
) -> ModelImageVisualizer:
    learn = gen_inference_wide(
        root_folder=Path(root_folder), weights_name=weights_name)
    filtr = MasterFilter([ColorizerFilter(learn=learn)],
                         render_factor=render_factor)
    vis = ModelImageVisualizer(filtr)
    return vis
