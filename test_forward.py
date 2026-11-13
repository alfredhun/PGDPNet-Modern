import numpy as np
import torch
from geo_parse.config import cfg
from geo_parse.modeling.detector import build_detection_model
from geo_parse.structures.image_list import to_image_list

def test_modernized_pipeline():
    cfg.merge_from_file('PGDP/configs/PGDP5K/geo_MNV2_FPN.yaml')
    cfg.MODEL.DEVICE = 'cpu'
    
    print("正在构建现代化 PGDPNet 模型...")
    model = build_detection_model(cfg)
    model.eval()
    
    # 模拟一张测试图像
    dummy_img = torch.randn(1, 3, 224, 224)
    img_list = to_image_list(dummy_img)
    
    print("正在执行现代 PyTorch 2.x 前向图元检测与分割计算...")
    with torch.no_grad():
        outputs = model(img_list)
    
    print(">>> [TEST COMPLETED SUCCESSFULLY!]")
    print("模型输出组件数:", len(outputs))
    return True

if __name__ == "__main__":
    test_modernized_pipeline()
