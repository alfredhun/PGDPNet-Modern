import numpy as np
import torch
import cv2
from torchvision import transforms as T
from geo_parse.config import cfg
from geo_parse.modeling.detector import build_detection_model
from geo_parse.structures.image_list import to_image_list

def test_local_pgdp(img_path, title):
    print("=" * 60)
    print(f"[*] 本地 PGDPNet 神经特征抽取: {title}")
    cfg.merge_from_file('PGDP/configs/PGDP5K/geo_MNV2_FPN.yaml')
    cfg.MODEL.DEVICE = 'cpu'
    model = build_detection_model(cfg)
    model.eval()

    img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    h, w, _ = img.shape
    transform = T.Compose([
        T.ToTensor(),
        T.Normalize(mean=cfg.INPUT.PIXEL_MEAN, std=cfg.INPUT.PIXEL_STD)
    ])
    tensor_img = transform(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).unsqueeze(0)
    img_list = to_image_list(tensor_img, 0)
    
    with torch.no_grad():
        features = model.backbone(img_list.tensors)
        print(f"  -> 输入分辨率: {w}x{h}")
        print(f"  -> FPN 特征金字塔抽取完成，各层通道与特征图尺寸:")
        for idx, feat in enumerate(features):
            print(f"     Level P{idx+2}: shape = {list(feat.shape)}")
    print("=" * 60)

if __name__ == "__main__":
    img1 = r"C:/Users/40705/.gemini/antigravity/brain/34d3b2ee-4ca6-4b69-96ec-450d730d8fa1/.user_uploaded/media_1793957597905_692229e0.png"
    img2 = r"C:/Users/40705/.gemini/antigravity/brain/34d3b2ee-4ca6-4b69-96ec-450d730d8fa1/.user_uploaded/media_1793957771927_2f5029c4.png"
    test_local_pgdp(img1, "多子图坐标探究题")
    test_local_pgdp(img2, "函数行程折线图")
