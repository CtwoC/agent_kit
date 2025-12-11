# coding:utf-8
"""
即梦视频生成测试脚本
支持图生视频功能（Image to Video）
"""
#%% 导入和函数定义
import json
import sys
import datetime
import hashlib
import hmac
import requests
import time
import os
import base64

# ========== 配置你的密钥 ==========
ACCESS_KEY = "YOUR_VOLCENGINE_ACCESS_KEY"  # 请替换为你的火山引擎 Access Key
SECRET_KEY = "YOUR_VOLCENGINE_SECRET_KEY"  # 请替换为你的火山引擎 Secret Key
# ==================================

SERVICE = "cv"
REGION = "cn-north-1"
HOST = "visual.volcengineapi.com"
ENDPOINT = f"https://{HOST}"
METHOD = "POST"
CONTENT_TYPE = "application/json"

# ------------------ 签名函数 ------------------
def sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

def get_signature_key(key, date_stamp, region_name, service_name):
    k_date = sign(key.encode("utf-8"), date_stamp)
    k_region = sign(k_date, region_name)
    k_service = sign(k_region, service_name)
    k_signing = sign(k_service, "request")
    return k_signing

def format_query(parameters):
    request_parameters_init = ""
    for key in sorted(parameters):
        request_parameters_init += key + "=" + parameters[key] + "&"
    return request_parameters_init[:-1]

def volc_sign_request(access_key, secret_key, service, query_str, body_str):
    t = datetime.datetime.utcnow()
    current_date = t.strftime("%Y%m%dT%H%M%SZ")
    datestamp = t.strftime("%Y%m%d")

    canonical_uri = "/"
    canonical_querystring = query_str
    payload_hash = hashlib.sha256(body_str.encode("utf-8")).hexdigest()

    canonical_headers = (
        f"content-type:{CONTENT_TYPE}\n"
        f"host:{HOST}\n"
        f"x-content-sha256:{payload_hash}\n"
        f"x-date:{current_date}\n"
    )
    signed_headers = "content-type;host;x-content-sha256;x-date"
    canonical_request = (
        f"{METHOD}\n{canonical_uri}\n{canonical_querystring}\n"
        f"{canonical_headers}\n{signed_headers}\n{payload_hash}"
    )

    algorithm = "HMAC-SHA256"
    credential_scope = f"{datestamp}/{REGION}/{service}/request"
    string_to_sign = (
        f"{algorithm}\n{current_date}\n{credential_scope}\n"
        + hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
    )

    signing_key = get_signature_key(secret_key, datestamp, REGION, service)
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    authorization_header = (
        f"{algorithm} Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    headers = {
        "X-Date": current_date,
        "Authorization": authorization_header,
        "X-Content-Sha256": payload_hash,
        "Content-Type": CONTENT_TYPE,
    }

    return headers

# ------------------ 发送请求 ------------------
def volc_post(action, body_dict):
    """
    发送请求到火山引擎API
    :param action: 接口名，如 CVSync2AsyncSubmitTask 或 CVSync2AsyncGetResult
    :param body_dict: 请求体字典
    :return: 响应JSON
    """
    query = {
        "Action": action,
        "Version": "2022-08-31"
    }
    query_str = format_query(query)
    body_str = json.dumps(body_dict, ensure_ascii=False)

    headers = volc_sign_request(ACCESS_KEY, SECRET_KEY, SERVICE, query_str, body_str)
    url = f"{ENDPOINT}?{query_str}"
    resp = requests.post(url, headers=headers, data=body_str.encode("utf-8"))
    resp.encoding = "utf-8"
    return resp.json()

# ------------------ 提交视频生成任务 ------------------
def submit_video_task(prompt: str, image_path: str, aspect_ratio: str = "9:16", frames: int = 121):
    """
    提交图生视频任务
    :param prompt: 提示词（必选），描述视频内容和动作
    :param image_path: 输入图片路径（必选）
    :param aspect_ratio: 视频宽高比，可选 "9:16", "16:9", "1:1" 等，默认 "9:16"
    :param frames: 视频帧数，121帧约5秒，默认121
    :return: task_id
    """
    def load_image_base64(image_path):
        """将图片转换为base64编码"""
        if not os.path.exists(image_path):
            print(f"❌ 图片文件不存在: {image_path}")
            return None
        
        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode('utf-8')
        return image_base64

    # 加载图片
    image_base64 = load_image_base64(image_path)
    if not image_base64:
        return None

    body = {
        "req_key": "jimeng_ti2v_v30_pro",
        "prompt": prompt,
        "frames": frames,
        "aspect_ratio": aspect_ratio,
        "binary_data_base64": [image_base64]
    }
    
    print(f"📤 正在提交视频生成任务...")
    print(f"   提示词: {prompt}")
    print(f"   输入图片: {image_path}")
    print(f"   宽高比: {aspect_ratio}")
    print(f"   帧数: {frames}")
    
    resp = volc_post("CVSync2AsyncSubmitTask", body)
    print("\n提交任务响应:", json.dumps(resp, indent=2, ensure_ascii=False))
    
    if resp.get("code") != 10000:
        print(f"❌ 任务提交失败: {resp.get('message', '未知错误')}")
        return None
    
    task_id = resp.get("data", {}).get("task_id")
    if task_id:
        print(f"✅ 任务提交成功，task_id: {task_id}")
    else:
        print("❌ 未获取到task_id")
    
    return task_id

# ------------------ 查询视频生成结果 ------------------
def get_video_result(task_id: str, interval: int = 3, timeout: int = 600):
    """
    轮询查询视频生成任务状态，直到生成完成或超时
    :param task_id: 提交任务时返回的 task_id
    :param interval: 轮询间隔（秒），默认3秒
    :param timeout: 超时时间（秒），默认600秒（10分钟）
    :return: 视频URL或None
    """
    start_time = time.time()
    
    print(f"\n⏳ 开始查询任务结果，task_id: {task_id}")
    
    while True:
        body = {
            "req_key": "jimeng_ti2v_v30_pro",
            "task_id": task_id
        }
        
        resp = volc_post("CVSync2AsyncGetResult", body)
        
        # 打印原始响应（可调试）
        print("\n查询响应:", json.dumps(resp, indent=2, ensure_ascii=False))
        
        if not resp or "data" not in resp:
            print("⚠️ 查询失败，等待重试...")
            time.sleep(interval)
            continue
        
        data = resp.get("data", {})
        status = data.get("status", "").lower()
        
        # 根据返回状态判断
        if status in ["running", "pending", "init", "in_queue"]:
            elapsed = int(time.time() - start_time)
            print(f"⏳ 任务状态: {status}（已等待 {elapsed}s）")
            if elapsed > timeout:
                print("❌ 超时未完成，退出。")
                return None
            time.sleep(interval)
            continue
        
        elif status in ["failed", "error"]:
            error_msg = data.get("message") or data.get("status_message") or "任务执行失败"
            print(f"❌ 视频生成失败: {error_msg}")
            return None
        
        elif status in ["done", "succeeded", "success"]:
            # 视频生成成功，获取视频URL
            video_url = data.get("video_url")
            if video_url:
                print(f"✅ 视频生成成功！URL: {video_url}")
                return video_url
            else:
                print("⚠️ 任务已完成但未返回视频URL。")
                print(f"完整响应数据: {data}")
                return None
        
        else:
            print(f"⚠️ 未知状态: {status}")
            time.sleep(interval)

# ------------------ 下载视频 ------------------
def download_video(video_url: str, output_dir: str = ".", filename: str = None):
    """
    下载生成的视频为本地MP4文件
    :param video_url: 视频URL
    :param output_dir: 输出目录，默认当前目录
    :param filename: 输出文件名，默认自动生成（jimeng_video_{timestamp}.mp4）
    :return: 下载的文件路径
    """
    if not video_url:
        print("⚠️ 没有视频需要下载")
        return None
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成文件名
    if not filename:
        timestamp = int(time.time())
        filename = f"jimeng_video_{timestamp}.mp4"
    
    # 确保文件扩展名为.mp4
    if not filename.endswith(".mp4"):
        filename += ".mp4"
    
    filepath = os.path.join(output_dir, filename)
    
    # 如果文件已存在，添加序号
    counter = 1
    base_filename = filename[:-4]  # 去掉.mp4
    while os.path.exists(filepath):
        filename = f"{base_filename}_{counter}.mp4"
        filepath = os.path.join(output_dir, filename)
        counter += 1
    
    print(f"🎬 正在下载视频: {filename}")
    
    try:
        resp = requests.get(video_url, stream=True, timeout=60)
        resp.raise_for_status()
        
        total_size = 0
        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    total_size += len(chunk)
        
        # 转换文件大小为可读格式
        size_mb = total_size / (1024 * 1024)
        print(f"✅ 下载完成: {filepath} (大小: {size_mb:.2f} MB)")
        return filepath
    
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return None

#%% 示例1：提交视频生成任务
# 取消注释以下代码来提交任务
# prompt = "粉底液被缓慢地轻轻推开在肌肤上，延展顺滑，质地细腻。随着往一个方向抹开，液体变得更薄，变成哑光，微距慢动作镜头下肌肤纹理自然呼吸。"
# image_path = "model_2.png"
# aspect_ratio = "9:16"  # 可选: "9:16", "16:9", "1:1"
# frames = 121  # 121帧约5秒

# task_id = submit_video_task(
#     prompt=prompt,
#     image_path=image_path,
#     aspect_ratio=aspect_ratio,
#     frames=frames
# )

#%% 示例2：查询已有任务结果并下载
# 如果你已经有一个task_id，可以直接查询结果
# task_id = "你的task_id"  # 替换为实际的task_id

# video_url = get_video_result(task_id, interval=3, timeout=600)

# if video_url:
#     download_video(video_url, output_dir=".", filename="my_video.mp4")

#%% 示例3：完整流程（提交任务 -> 查询结果 -> 下载视频）
# 这是最常用的完整流程
if __name__ == "__main__":
    # 第1步：提交视频生成任务
    prompt = "粉底液被缓慢地轻轻推开在肌肤上，延展顺滑，质地细腻。随着往一个方向抹开，液体变得更薄，变成哑光，微距慢动作镜头下肌肤纹理自然呼吸。"
    image_path = "model_2.png"  # 替换为你的图片路径
    aspect_ratio = "9:16"
    frames = 121  # 5秒视频
    
    task_id = submit_video_task(
        prompt=prompt,
        image_path=image_path,
        aspect_ratio=aspect_ratio,
        frames=frames
    )
    
    if not task_id:
        print("❌ 任务提交失败，退出。")
        sys.exit(1)
    
    # 第2步：查询结果（轮询直到视频完成）
    video_url = get_video_result(task_id, interval=3, timeout=600)
    
    # 第3步：下载视频
    if video_url:
        download_video(video_url, output_dir=".", filename="jimeng_video.mp4")
    else:
        print("❌ 未获取到视频URL，无法下载。")

# %%

