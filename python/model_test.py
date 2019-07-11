#!/usr/bin/env python
# coding: utf-8

import torch
import itertools as it
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
import torchvision.transforms as transforms
import torch.nn as nn
import cv2
from torch.autograd import Variable

class SegBlockEncoder(nn.Module):
    def __init__(self,in_channel,out_channel, kernel=4,stride=2,pad=1):
        super().__init__()
        self.model = nn.Sequential(
            nn.Conv2d(
                in_channel,out_channel,kernel,stride=stride,
                padding=pad,bias=False),
            nn.BatchNorm2d(out_channel),
            nn.ReLU(True)
        )

    def forward(self, x):
        y=self.model(x)
        return y
class SegBlockDecoder(nn.Module):
    def __init__(self,in_channel,out_channel, kernel=4,stride=2,pad=1):
        super().__init__()
        self.model = nn.Sequential(
            nn.ConvTranspose2d(
                in_channel,out_channel,kernel,stride=stride,padding=pad,bias=False),
            nn.BatchNorm2d(out_channel),
            nn.ReLU(True)

        )

    def forward(self, x):
        y=self.model(x)
        return y

class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.cr = 64
        self.encoder = nn.Sequential(
            SegBlockEncoder(in_channel=3,out_channel=self.cr),
            SegBlockEncoder(in_channel=self.cr,out_channel=self.cr*2),
            SegBlockEncoder(in_channel=self.cr*2,out_channel=self.cr*4),
            SegBlockEncoder(in_channel=self.cr*4,out_channel=self.cr*8),
            SegBlockEncoder(in_channel=self.cr*8,out_channel=self.cr*16)
            )
        
        self.decoder = nn.Sequential(
            SegBlockDecoder(in_channel=self.cr*16, out_channel=self.cr*8),
            SegBlockDecoder(in_channel=self.cr*8, out_channel=self.cr*4),
            SegBlockDecoder(in_channel=self.cr*4, out_channel=self.cr*2),
            SegBlockDecoder(in_channel=self.cr*2, out_channel=self.cr),
            SegBlockDecoder(in_channel=self.cr, out_channel=2), 
            )

        self.output = nn.Softmax(dim =1)
        
    def forward(self,x):
        x1 = self.encoder(x)
        x2 = self.decoder(x1)
        y = self.output(x2)
        return y

net = Net()
net = nn.DataParallel(net)
net.load_state_dict(torch.load('model_inria.pt',map_location=lambda storage, loc: storage))

def accuracy(out, labels):
  outputs = np.argmax(out, axis=1)
  return np.sum(outputs==labels)/float(labels.size)

imsize = 4096
#loader = transforms.Compose([transforms.Resize(imsize), transforms.ToTensor()])
loader = transforms.Compose([ transforms.ToTensor()])

trans = transforms.ToPILImage()
def image_loader(image_name):
    """load image, returns cuda tensor"""
    image = Image.open(image_name)
    image = loader(image).float()
    RGB_image = trans(image)
    image = Variable(image, requires_grad=True)
    image = image.unsqueeze(0)  #this is for VGG, may not be needed for ResNet
    return image,RGB_image  #assumes that you're using GPU

image,RGB_image = image_loader('/exports/csce/eddie/geos/groups/geos_cnn_imgclass/data/AerialImageDataset/train/images/austin20.tif')

out = net(image)
variable = Variable(out)
num = variable.data[0]
num = num.permute(2,1,0)
b = num.numpy()
# building_images = b[:,:,0]
# no_building = b[:,:,1]
# fig=plt.figure(figsize=(5, 5), dpi= 300, facecolor='w', edgecolor='k')
# ax1 = plt.subplot(1,2,1)
# ax2 = plt.subplot(1,2,2)
# ax1.imshow(building_images)
# ax2.imshow(no_building)
final_prediction=b[:,:,0]
labels = (final_prediction > 0.5).astype(np.int)
fig=plt.figure(figsize=(5, 5), dpi= 300, facecolor='w', edgecolor='k')
ax1 = plt.subplot(1,2,1)
ax2 = plt.subplot(1,2,2)
ax2.imshow(labels)
ax1.imshow(RGB_image)