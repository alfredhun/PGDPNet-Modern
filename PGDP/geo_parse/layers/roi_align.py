# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved.
# Modernized: Using native torchvision.ops.roi_align to eliminate C++ compilation
import torch
from torch import nn
from torch.nn.modules.utils import _pair
import torchvision.ops as ops

def roi_align(input, rois, output_size, spatial_scale, sampling_ratio):
    """
    直接调用官方原生 ops.roi_align
    """
    output_size = _pair(output_size)
    return ops.roi_align(
        input=input,
        boxes=rois,
        output_size=output_size,
        spatial_scale=spatial_scale,
        sampling_ratio=sampling_ratio,
        aligned=False
    )

class ROIAlign(nn.Module):
    def __init__(self, output_size, spatial_scale, sampling_ratio):
        super(ROIAlign, self).__init__()
        self.output_size = _pair(output_size)
        self.spatial_scale = spatial_scale
        self.sampling_ratio = sampling_ratio

    def forward(self, input, rois):
        return roi_align(
            input, rois, self.output_size, self.spatial_scale, self.sampling_ratio
        )

    def __repr__(self):
        tmpstr = self.__class__.__name__ + "("
        tmpstr += "output_size=" + str(self.output_size)
        tmpstr += ", spatial_scale=" + str(self.spatial_scale)
        tmpstr += ", sampling_ratio=" + str(self.sampling_ratio)
        tmpstr += ")"
        return tmpstr
