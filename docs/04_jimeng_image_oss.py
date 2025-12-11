# coding:utf-8
"""
即梦图片生成测试脚本
支持文生图和图生图功能
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
try:
    import oss2
    OSS_AVAILABLE = True
except ImportError:
    OSS_AVAILABLE = False
    print("⚠️ 未安装oss2库，OSS功能不可用。请运行: pip install oss2")

# ========== 配置你的密钥 ==========
ACCESS_KEY = "YOUR_VOLCENGINE_ACCESS_KEY"  # 请替换为你的火山引擎 Access Key
SECRET_KEY = "YOUR_VOLCENGINE_SECRET_KEY"  # 请替换为你的火山引擎 Secret Key
# ==================================

# ========== 配置阿里云OSS ==========
OSS_ACCESS_KEY_ID = 'YOUR_ALIYUN_OSS_ACCESS_KEY_ID'  # 请替换为你的阿里云 AccessKey ID
OSS_ACCESS_KEY_SECRET = 'YOUR_ALIYUN_OSS_ACCESS_KEY_SECRET'  # 请替换为你的阿里云 AccessKey Secret
OSS_ENDPOINT = 'oss-cn-beijing.aliyuncs.com'
OSS_BUCKET_NAME = 'img-ref'
# ===================================

SERVICE = "cv"
REGION = "cn-north-1"
HOST = "visual.volcengineapi.com"
ENDPOINT = f"https://{HOST}"
METHOD = "POST"
CONTENT_TYPE = "application/json"

# 签名函数
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

# OSS相关函数
def init_oss_bucket():
    """初始化OSS存储桶"""
    if not OSS_AVAILABLE:
        return None
    auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
    bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)
    return bucket

def upload_file_to_oss(file_path: str, object_name: str = None) -> str:
    """
    上传文件到OSS并返回访问URL
    :param file_path: 本地文件路径
    :param object_name: OSS对象名称（可选，默认使用文件名+时间戳）
    :return: 文件的访问URL
    """
    if not OSS_AVAILABLE:
        print("❌ OSS功能不可用，请先安装oss2库")
        return None
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return None
    
    try:
        bucket = init_oss_bucket()
        
        # 如果没有指定object_name，使用文件名+时间戳
        if not object_name:
            filename = os.path.basename(file_path)
            name, ext = os.path.splitext(filename)
            timestamp = int(time.time())
            object_name = f"jimeng/{timestamp}_{name}{ext}"
        
        print(f"📤 正在上传文件到OSS: {file_path} -> {object_name}")
        
        # 上传文件
        with open(file_path, 'rb') as file:
            bucket.put_object(object_name, file)
        
        # 获取文件访问URL
        url = f"https://{OSS_BUCKET_NAME}.{OSS_ENDPOINT}/{object_name}"
        print(f"✅ 上传成功，访问URL: {url}")
        return url
    
    except Exception as e:
        print(f"❌ OSS上传失败: {e}")
        return None

def upload_images_to_oss(image_paths: list) -> list:
    """
    批量上传图片到OSS
    :param image_paths: 本地图片路径列表
    :return: 图片URL列表
    """
    image_urls = []
    for i, path in enumerate(image_paths, 1):
        print(f"📤 上传图片 {i}/{len(image_paths)}: {path}")
        url = upload_file_to_oss(path)
        if url:
            image_urls.append(url)
        else:
            print(f"⚠️ 跳过文件: {path}")
    return image_urls

def find_images_in_output_dir(output_dir: str = "output_images", max_count: int = 1) -> list:
    """
    在output_images目录中查找图片文件
    :param output_dir: 输出目录，默认 output_images
    :param max_count: 最多返回的图片数量，默认1
    :return: 图片路径列表
    """
    if not os.path.exists(output_dir):
        print(f"⚠️ 目录不存在: {output_dir}")
        return []
    
    import glob
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.webp']
    image_files = []
    
    for ext in image_extensions:
        pattern = os.path.join(output_dir, ext)
        image_files.extend(glob.glob(pattern))
        # 也查找大写扩展名
        pattern = os.path.join(output_dir, ext.upper())
        image_files.extend(glob.glob(pattern))
    
    # 按修改时间排序，最新的在前
    image_files.sort(key=os.path.getmtime, reverse=True)
    
    # 返回最新的几个
    return image_files[:max_count]

# 发送请求函数
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
    # 将字符串编码为bytes，避免UnicodeEncodeError
    body_bytes = body_str.encode("utf-8")

    headers = volc_sign_request(ACCESS_KEY, SECRET_KEY, SERVICE, query_str, body_str)
    url = f"{ENDPOINT}?{query_str}"
    resp = requests.post(url, headers=headers, data=body_bytes)
    resp.encoding = "utf-8"
    return resp.json()

# 提交图片生成任务
def submit_image_task(
    prompt: str,
    image_urls: list = None,
    image_paths: list = None,
    size: int = None,
    width: int = None,
    height: int = None,
    scale: float = 0.5,
    force_single: bool = False,
    min_ratio: float = 1/3,
    max_ratio: float = 3
):
    """
    提交图片生成任务
    :param prompt: 提示词（必选）
    :param image_urls: 输入图片URL列表（可选，0-10张）
    :param image_paths: 本地图片路径列表（可选），会自动上传到OSS并转换为URL
    :param size: 生成图片面积，如 4194304 (2048*2048)
    :param width: 生成图片宽度（需与height同时传入）
    :param height: 生成图片高度（需与width同时传入）
    :param scale: 文本描述影响程度，0-1，默认0.5
    :param force_single: 是否强制生成单图，默认False
    :param min_ratio: 最小宽高比，默认1/3
    :param max_ratio: 最大宽高比，默认3
    :return: task_id
    """
    body = {
        "req_key": "jimeng_t2i_v40",
        "prompt": prompt
    }
    
    # 处理图片输入：如果提供了本地路径，先上传到OSS
    if image_paths:
        print("📤 检测到本地图片路径，开始上传到OSS...")
        uploaded_urls = upload_images_to_oss(image_paths)
        if uploaded_urls:
            # 合并到image_urls
            if image_urls:
                image_urls.extend(uploaded_urls)
            else:
                image_urls = uploaded_urls
        else:
            print("❌ 图片上传失败，无法继续")
            return None
    
    # 可选参数
    if image_urls:
        body["image_urls"] = image_urls
    
    if size:
        body["size"] = size
    
    if width and height:
        body["width"] = width
        body["height"] = height
    
    if scale is not None:
        body["scale"] = scale
    
    if force_single:
        body["force_single"] = force_single
    
    if min_ratio is not None:
        body["min_ratio"] = min_ratio
    
    if max_ratio is not None:
        body["max_ratio"] = max_ratio
    
    resp = volc_post("CVSync2AsyncSubmitTask", body)
    print("提交任务响应:", json.dumps(resp, indent=2, ensure_ascii=False))
    
    if resp.get("code") != 10000:
        print(f"❌ 任务提交失败: {resp.get('message', '未知错误')}")
        return None
    
    task_id = resp.get("data", {}).get("task_id")
    if task_id:
        print(f"✅ 任务提交成功，task_id: {task_id}")
    else:
        print("❌ 未获取到task_id")
    
    return task_id

# 查询任务结果
def get_image_result(task_id: str, interval: int = 3, timeout: int = 600, return_url: bool = True, logo_info: dict = None):
    """
    轮询查询图片生成任务状态，直到生成完成或超时
    :param task_id: 提交任务时返回的 task_id
    :param interval: 轮询间隔（秒），默认3秒
    :param timeout: 超时时间（秒），默认600秒
    :param return_url: 是否返回图片链接（链接有效期为24小时），默认True
    :param logo_info: 水印信息，可选，格式如：{"add_logo":True, "position":0, "language":0, "opacity":1, "logo_text_content":"水印内容"}
    :return: 图片URL列表或None
    """
    start_time = time.time()
    
    while True:
        body = {
            "req_key": "jimeng_t2i_v40",
            "task_id": task_id
        }
        
        # 添加req_json参数，确保返回图片URL
        req_json_dict = {
            "return_url": return_url
        }
        if logo_info:
            req_json_dict["logo_info"] = logo_info
        
        body["req_json"] = json.dumps(req_json_dict, ensure_ascii=False)
        
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
            print(f"❌ 图片生成失败: {error_msg}")
            return None
        
        elif status in ["done", "succeeded", "success"]:
            # 图片生成成功，获取图片URL列表
            image_urls = data.get("image_urls")
            if not image_urls:
                # 尝试其他可能的字段名
                image_urls = data.get("images") or data.get("result", {}).get("image_urls")
            
            if image_urls:
                print(f"✅ 图片生成成功！共生成 {len(image_urls)} 张图片")
                for i, url in enumerate(image_urls, 1):
                    print(f"  图片 {i}: {url}")
                return image_urls
            else:
                print("⚠️ 任务已完成但未返回图片URL。")
                return None
        
        else:
            print(f"⚠️ 未知状态: {status}")
            time.sleep(interval)

# 下载图片
def download_images(image_urls: list, output_dir: str = "output_images"):
    """
    下载生成的图片到本地
    :param image_urls: 图片URL列表
    :param output_dir: 输出目录，默认 output_images
    :return: 下载的文件路径列表
    """
    if not image_urls:
        print("⚠️ 没有图片需要下载")
        return []
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    def detect_image_format(content: bytes) -> str:
        """根据文件内容检测图片格式"""
        if content.startswith(b'\xff\xd8\xff'):
            return 'jpg'
        elif content.startswith(b'\x89PNG\r\n\x1a\n'):
            return 'png'
        elif content.startswith(b'GIF87a') or content.startswith(b'GIF89a'):
            return 'gif'
        elif content.startswith(b'RIFF') and b'WEBP' in content[:12]:
            return 'webp'
        else:
            return 'jpg'  # 默认jpg
    
    downloaded_files = []
    for i, url in enumerate(image_urls, 1):
        print(f"🎨 正在下载图片 {i}/{len(image_urls)}")
        
        try:
            resp = requests.get(url, stream=True, timeout=30)
            resp.raise_for_status()
            
            # 先读取前几个字节来检测文件类型
            content = b''
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    content += chunk
                    # 读取足够多的字节来检测格式（至少16字节）
                    if len(content) >= 16:
                        break
            
            # 检测图片格式
            ext = detect_image_format(content)
            
            # 生成文件名
            timestamp = int(time.time())
            filename = f"jimeng_image_{timestamp}_{i}.{ext}"
            filepath = os.path.join(output_dir, filename)
            
            # 如果文件已存在，添加序号
            counter = 1
            while os.path.exists(filepath):
                filename = f"jimeng_image_{timestamp}_{i}_{counter}.{ext}"
                filepath = os.path.join(output_dir, filename)
                counter += 1
            
            # 继续下载剩余内容并保存
            with open(filepath, "wb") as f:
                # 先写入已读取的内容
                f.write(content)
                # 继续下载剩余内容
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"✅ 下载完成: {filepath} (格式: {ext.upper()})")
            downloaded_files.append(filepath)
        except Exception as e:
            print(f"❌ 下载失败: {e}")
    
    return downloaded_files

#%% 发送请求 - 提交图片生成任务
# 示例1: 文生图（取消注释使用）
# prompt = "一幅美丽的山水画，有青山绿水，云雾缭绕，中国传统风格"
# task_id = submit_image_task(
#     prompt=prompt,
#     width = 1440,
#     height = 2560,
#     force_single=True  # 强制只生成1张图片
# )

# 图生图示例1：使用图片URL（取消注释使用）
# image_urls_input = [
#     "https://example.com/input_image.jpg"
# ]
# prompt = "背景换成演唱会现场"
# task_id = submit_image_task(
#     prompt=prompt,
#     image_urls=image_urls_input,
#     scale=0.5,
#     width=2048,
#     height=2048
# )

# 图生图示例2：使用本地图片路径（会自动上传到OSS）
# 指定要参考的图片路径列表
image_paths_input = [
    "output_images/jimeng_image_1763361343_1.jpg"  # 替换为实际的图片路径，例如: "output_images/jimeng_image_1234567890_1.jpg"
]
prompt = "在画面中间加入漫威英雄全家福，画风要和原图一致"
task_id = submit_image_task(
    prompt=prompt,
    image_paths=image_paths_input,  # 使用image_paths参数，会自动上传到OSS
    scale=0.5,
    width=1440,
    height=2560,
    force_single=True
)

# 指定宽高比示例（取消注释使用）
# prompt = "一个现代化的办公室，宽敞明亮，有落地窗"
# task_id = submit_image_task(
#     prompt=prompt,
#     width=2560,  # 16:9 比例
#     height=1440,
#     force_single=True
# )

#%% 查询结果和下载图片
if task_id:
    image_urls = get_image_result(task_id)
    if image_urls:
        download_images(image_urls)
else:
    print("⚠️ 未获取到task_id，请先运行发送请求代码块")

# %%
