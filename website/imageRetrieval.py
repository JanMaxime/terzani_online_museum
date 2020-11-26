import torch
import torchvision.models as models
import torchvision.transforms as transforms
from torch.autograd import Variable
from PIL import Image


def get_similarity(img_vec1, img_vec2):
    if not torch.is_tensor(img_vec1):
        img_vec1 = torch.Tensor(img_vec1)
    if not torch.is_tensor(img_vec2):
        img_vec2 = torch.Tensor(img_vec2)
    cossim = torch.nn.CosineSimilarity(dim=1, eps=1e-6)
    sim = cossim(img_vec1.unsqueeze(0), img_vec2.unsqueeze(0))
    return sim


def load_pretrained_resnet():
    """
    As we do not want the classification part of the network,
    we select the last layer where we would want to extract information.
    """

    # Loading pretrained Resnet model
    model = models.resnet18(pretrained=True)
    layer = model._modules.get('avgpool')
    # Set model to evaluation mode as we plan to use pre trained model
    model.eval()

    return model, layer


def transformers():
    """
    ResNet-18 expects images to be at least 224x224, as well as normalized with a specific mean and standard deviation. Thus we define some transformations 
    """

    scaler = transforms.Scale((224, 224))
    normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                     std=[0.229, 0.224, 0.225])
    to_tensor = transforms.ToTensor()

    return scaler, normalize, to_tensor


def get_embedding(image_name, model, layer, scaler, normalize, to_tensor):
    img = Image.open(image_name).convert('RGB')
    t_img = Variable(normalize(to_tensor(scaler(img))).unsqueeze(0))
    #    The 'avgpool' layer that we selected has an output size of 512
    my_embedding = torch.zeros(512)

    def copy_data(m, i, o):
        my_embedding.copy_(o.data.squeeze())
    h = layer.register_forward_hook(copy_data)
    model(t_img)
    h.remove()
    return my_embedding


def get_imagevector(image_name):
    model, layer = load_pretrained_resnet()
    scaler, normalize, to_tensor = transformers()
    img_embd = get_embedding(image_name, model, layer,
                             scaler, normalize, to_tensor)
    return img_embd
