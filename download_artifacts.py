import os
import sys
import time
import subprocess
import zipfile
import requests

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

def get_gh_token():
    res = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True)
    return res.stdout.strip()

def download_file_with_resume(api_url, headers, dest_path, expected_size=None, max_retries=15):
    # 1. 解析出真实下载 CDN / Blob 存储 URL
    print(f"[*] 正在请求下载链接...")
    resp = requests.get(api_url, headers=headers, allow_redirects=False, timeout=30)
    if resp.status_code in (301, 302, 307):
        download_url = resp.headers['Location']
    else:
        resp.raise_for_status()
        download_url = api_url

    # 2. 支持断点续传的流式下载
    for attempt in range(max_retries):
        try:
            downloaded = os.path.getsize(dest_path) if os.path.exists(dest_path) else 0
            req_headers = {}
            if expected_size and downloaded >= expected_size:
                print(f"  ✓ 本地已有完整文件 ({downloaded / 1024 / 1024:.2f} MB)")
                return True

            if downloaded > 0:
                req_headers['Range'] = f"bytes={downloaded}-"
                print(f"\n[*] 断点续传中: 已有 {downloaded / 1024 / 1024:.2f} MB，继续下载 (第 {attempt+1} 次)...")
            else:
                print(f"[*] 开始下载 (第 {attempt+1} 次)...")

            # 对 Blob 存储请求时不带 GitHub Authorization header 以免签名失效
            with requests.get(download_url, headers=req_headers, stream=True, timeout=30) as r:
                if r.status_code == 416: # Range Not Satisfiable -> 说明已全部下载
                    print("\n  ✓ 远程指示已全部下载完成！")
                    return True
                r.raise_for_status()
                
                mode = 'ab' if (downloaded > 0 and r.status_code == 206) else 'wb'
                if mode == 'wb':
                    downloaded = 0
                
                content_len = int(r.headers.get('content-length', 0))
                total = downloaded + content_len if content_len else expected_size
                
                with open(dest_path, mode) as f:
                    for chunk in r.iter_content(chunk_size=256 * 1024):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total:
                                pct = downloaded / total * 100
                                print(f"\r    进度: {downloaded / 1024 / 1024:.2f} MB / {total / 1024 / 1024:.2f} MB ({pct:.1f}%)", end="", flush=True)

            if expected_size:
                cur_size = os.path.getsize(dest_path)
                if cur_size >= expected_size:
                    print(f"\n  ✓ 下载校验成功: {cur_size / 1024 / 1024:.2f} MB")
                    return True
            else:
                return True

        except Exception as e:
            print(f"\n  [网络抖动重试] {e}，2 秒后自动续传...")
            time.sleep(2)

    raise RuntimeError(f"重试 {max_retries} 次后仍未完成下载")

def download_and_extract_artifact(artifact_id, name, expected_size, out_dir):
    token = get_gh_token()
    api_url = f"https://api.github.com/repos/alfredhun/PGDPNet-Modern/actions/artifacts/{artifact_id}/zip"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    
    zip_path = os.path.join(out_dir, f"{name}.zip")
    print("=" * 60)
    print(f"📦 正在下载 Artifact: {name} (ID: {artifact_id}, 预期大小: {expected_size / 1024 / 1024:.2f} MB)")
    print("=" * 60)

    download_file_with_resume(api_url, headers, zip_path, expected_size)
    
    print("\n📂 正在解压产物包...")
    extract_dir = os.path.join(out_dir, name)
    os.makedirs(extract_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(extract_dir)
        for f in zf.namelist():
            print(f"  ✓ 提取: {f}")
            if f.endswith('.apk'):
                root_apk = os.path.join(".", os.path.basename(f))
                with open(os.path.join(extract_dir, f), 'rb') as src, open(root_apk, 'wb') as dst:
                    dst.write(src.read())
                print(f"  🎉【手机安装包已就绪】: {os.path.abspath(root_apk)}")
            elif f.endswith('.whl'):
                root_whl = os.path.join(".", os.path.basename(f))
                with open(os.path.join(extract_dir, f), 'rb') as src, open(root_whl, 'wb') as dst:
                    dst.write(src.read())
                print(f"  🎉【Python Wheel 安装包已就绪】: {os.path.abspath(root_whl)}")

def main():
    out_dir = "./downloaded_artifacts"
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. 下载包含真实相机拍照 + 相册读取 + 通用几何求解器的最新纯净版 APK
    # Run: 43540936917, ID: 14092291353, 71918920 bytes
    download_and_extract_artifact(14092291353, "GeometrySolver-Android-Debug-APK", 71918920, out_dir)
    
    # 2. 下载 Python Package (Run: 43540936917, ID: 14092356018, 323198 bytes)
    download_and_extract_artifact(14092356018, "PGDPNet-Modern-Python-Package", 323198, out_dir)

if __name__ == "__main__":
    main()
