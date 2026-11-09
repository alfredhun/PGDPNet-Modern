# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved.
# Modernized: Using native torchvision.ops.roi_pool to eliminate C++ compilation
import torch
from torch import nn
from torch.nn.modules.utils import _pair
import torchvision.ops as ops

def roi_pool(input, rois, output_size, spatial_scale):
    output_size = _pair(output_size)
    return ops.roi_pool(
        input=input,
        boxes=rois,
        output_size=output_size,
        spatial_scale=spatial_scale
    )

class ROIPool(nn.Module):
    def __init__(self, output_size, spatial_scale):
        super(ROIPool, self).__init__()
        self.output_size = _pair(output_size)
        self.spatial_scale = spatial_scale

    def forward(self, input, rois):
        return roi_pool(input, rois, self.output_size, self.spatial_scale)

    def __repr__(self):
        tmpstr = self.__class__.__name__ + "("
        tmpstr += "output_size=" + str(self.output_size)
        tmpstr += ", spatial_scale=" + str(self.spatial_scale)
        tmpstr += ")"
        return tmpstr
