# from purl import URL
from PIL import Image
from io import BytesIO
import requests
import matplotlib.pyplot as plt
from torch.autograd import Variable
import torchvision.transforms as transforms
import torchvision.models as models
import torch
from typing import Union

URL = str


def get_similarity(img_vec1, img_vec2):
    if not torch.is_tensor(img_vec1):
        img_vec1 = torch.Tensor(img_vec1)
    if not torch.is_tensor(img_vec2):
        img_vec2 = torch.Tensor(img_vec2)
    cossim = torch.nn.CosineSimilarity(dim=1, eps=1e-6)
    sim = cossim(img_vec1.unsqueeze(0), img_vec2.unsqueeze(0))
    return sim


def load_resnet_model():
    """
    This function return a pretrained resnet model, the layer at which the feature vector needs to be extracted
    and the transformations to be performed on the image.

    :return model: The pretrained Resnet Model
    :return layer: The averaging pool layer of the Resnet 18 model
    :return scaler: Transformer to resize the image to fit into rest
    :return normalize: Transformer to normalise the image
    :return to_tensor: Transformer to convert the image into Tensor
    """

    # Loading pretrained Resnet model
    model = models.resnet18(pretrained=True)
    layer = model._modules.get('avgpool')
    # Set model to evaluation mode as we plan to use pre trained model
    model.eval()
    scaler = transforms.Resize((224, 224))
    normalize = transforms.Normalize(
        mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    to_tensor = transforms.ToTensor()

    return model, layer, scaler, normalize, to_tensor


def transform_image(image, scaler, normalize, to_tensor):
    """
    This function transforms the image to be suitable for processing by a pretrained resnet model.

    :param image: The image to be transformed
    :param scaler: Transformer to resize the image to fit into rest
    :param normalize: Transformer to normalise the image
    :param to_tensor: TTransformer to convert the image into Tensor
    :return : Transformed image
    """
    return Variable(normalize(to_tensor(scaler(image))).unsqueeze(0))


def get_vector(image: Union[URL], model, layer, scaler, normalize, to_tensor, is_url=True):
    """
    This function accepts the image URL, model, transformations and returns the feature vector of the image.

    :param image: The image or the url of the image
    :param model: The pretrained Resnet Model
    :param layer: The averaging pool layer of the Resnet 18 model
    :param scaler: Transformer to resize the image to fit into rest
    :param normalize: Transformer to normalise the image
    :param to_tensor: Transformer to convert the image into Tensor
    :param is_url: To indicate if the input image is a Image file or a URL
    :return my_embedding(tensor): The feature vector of the image obtained through resnet 18
    """

    if is_url:
        response = requests.get(image)
        img = Image.open(BytesIO(response.content))
    else:
        img = Image.open(image).convert('RGB')
    t_img = transform_image(img, scaler, normalize, to_tensor)
    #  The avgpool layer that we selected has an output size of 512
    my_embedding = torch.zeros(512)

    def copy_data(m, i, o):
        my_embedding.copy_(o.data.squeeze())

    h = layer.register_forward_hook(copy_data)
    model(t_img)
    h.remove()
    return my_embedding
