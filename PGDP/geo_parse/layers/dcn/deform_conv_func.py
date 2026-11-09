# Modernized DCN: Using torchvision.ops.deform_conv2d
import torch
import torchvision.ops as ops

def deform_conv(input, offset, weight, stride=1, padding=0, dilation=1, groups=1, deformable_groups=1, im2col_step=64):
    stride_pair = (stride, stride) if isinstance(stride, int) else stride
    padding_pair = (padding, padding) if isinstance(padding, int) else padding
    dilation_pair = (dilation, dilation) if isinstance(dilation, int) else dilation
    return ops.deform_conv2d(
        input=input,
        offset=offset,
        weight=weight,
        stride=stride_pair,
        padding=padding_pair,
        dilation=dilation_pair
    )

def modulated_deform_conv(input, offset, mask, weight, bias=None, stride=1, padding=0, dilation=1, groups=1, deformable_groups=1):
    stride_pair = (stride, stride) if isinstance(stride, int) else stride
    padding_pair = (padding, padding) if isinstance(padding, int) else padding
    dilation_pair = (dilation, dilation) if isinstance(dilation, int) else dilation
    return ops.deform_conv2d(
        input=input,
        offset=offset,
        weight=weight,
        bias=bias,
        stride=stride_pair,
        padding=padding_pair,
        dilation=dilation_pair,
        mask=mask
    )
