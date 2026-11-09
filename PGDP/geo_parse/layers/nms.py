# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved.
# Modernized: Using native torchvision.ops to eliminate C++ compilation
import torch
import torchvision.ops as ops

def nms(boxes, scores, threshold):
    """
    原生 torchvision.ops.nms 实现
    """
    return ops.nms(boxes, scores, threshold)

def ml_nms(boxes, scores, labels, threshold):
    """
    原生 torchvision.ops.batched_nms 实现多类别 NMS
    """
    return ops.batched_nms(boxes, scores, labels, threshold)
