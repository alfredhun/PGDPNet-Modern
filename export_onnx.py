"""
export_onnx.py - 将现代化重构的 PGDPNet 导出为移动端通用的 ONNX 格式
并使用 ONNX Runtime 验证精度
"""
import os
import sys
import numpy as np
import torch
import onnx
import onnxruntime as ort

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

from geo_parse.config import cfg
from geo_parse.modeling.detector import build_detection_model

def export_pgdp_to_onnx():
    print("=" * 65)
    print("🚀 开始执行 PGDPNet 移动端 ONNX 模型导出与精度验证")
    print("=" * 65)

    # 1. 初始化配置与模型
    cfg.merge_from_file('PGDP/configs/PGDP5K/geo_MNV2_FPN.yaml')
    cfg.MODEL.DEVICE = 'cpu'
    
    print("\n[1/4] 构建现代化 PGDPNet 模型...")
    model = build_detection_model(cfg)
    model.eval()

    # 主干提取网络 (MobileNetV2 + FPN: 输出 P2~P7 六个特征层)
    backbone = model.backbone
    backbone.eval()
    print("  ✓ 主干网络 (MobileNetV2-FPN) 准备就绪")

    # 2. 构造模拟输入 (Batch=1, C=3, H=384, W=384)
    # 支持动态宽高 (Dynamic Axes)，适配不同手机摄像头的裁剪尺寸
    dummy_input = torch.randn(1, 3, 384, 384, dtype=torch.float32)
    onnx_file_path = "pgdp_backbone.onnx"

    input_names = ["input_image"]
    output_names = [f"feat_p{i+2}" for i in range(6)]  # P2, P3, P4, P5, P6, P7

    dynamic_axes = {
        "input_image": {0: "batch_size", 2: "height", 3: "width"}
    }
    for name in output_names:
        dynamic_axes[name] = {0: "batch_size", 2: "feat_h", 3: "feat_w"}

    # 3. 执行导出
    print(f"\n[2/4] 正在导出 ONNX 模型至: {onnx_file_path} ...")
    torch.onnx.export(
        backbone,
        dummy_input,
        onnx_file_path,
        export_params=True,
        opset_version=18,
        do_constant_folding=True,
        input_names=input_names,
        output_names=output_names,
        dynamic_axes=dynamic_axes
    )
    
    # 转换为单一自包含 ONNX 文件 (内嵌所有参数权重，免除外部 .data 依赖)
    # 强制指定 ir_version = 9 兼容 Android 移动端 ONNX Runtime (支持 Android 10~15 / MIUI / HyperOS)
    onnx_model = onnx.load(onnx_file_path, load_external_data=True)
    onnx_model.ir_version = 9
    onnx.save_model(onnx_model, onnx_file_path, save_as_external_data=False)
    if os.path.exists(onnx_file_path + ".data"):
        try:
            os.remove(onnx_file_path + ".data")
        except Exception:
            pass

    file_size_mb = os.path.getsize(onnx_file_path) / (1024 * 1024)
    print(f"  ✓ 导出成功！自包含单文件 ONNX 大小: {file_size_mb:.2f} MB")

    # 4. 校验 ONNX 结构合法性
    print("\n[3/4] 正在校验 ONNX 结构完整性...")
    onnx_model = onnx.load(onnx_file_path)
    onnx.checker.check_model(onnx_model)
    print("  ✓ ONNX 模型结构符合标准规范！")

    # 5. 使用 ONNX Runtime 执行推理并与 PyTorch 对比
    print("\n[4/4] 启动 ONNX Runtime 模拟移动端推理，验证数值精度...")
    ort_session = ort.InferenceSession(onnx_file_path, providers=['CPUExecutionProvider'])

    # PyTorch 原生计算
    with torch.no_grad():
        torch_outputs = backbone(dummy_input)

    # ONNX Runtime 计算
    ort_inputs = {ort_session.get_inputs()[0].name: dummy_input.numpy()}
    ort_outputs = ort_session.run(None, ort_inputs)

    print(f"  ✓ 输出特征层级数: {len(ort_outputs)} (P2~P7)")
    max_diff_all = 0.0
    for idx, (t_out, o_out) in enumerate(zip(torch_outputs, ort_outputs)):
        diff = np.max(np.abs(t_out.numpy() - o_out))
        max_diff_all = max(max_diff_all, diff)
        print(f"     Level P{idx+2}: 尺寸 {o_out.shape}, PyTorch 与 ONNX 最大绝对误差 = {diff:.2e}")

    assert max_diff_all < 1e-4, f"误差过大: {max_diff_all}"
    print(f"\n🎉 验证完美通过！数值差异在 {max_diff_all:.2e} 以内，可直接放入 Android Studio 的 assets 目录中使用！")

if __name__ == "__main__":
    export_pgdp_to_onnx()
