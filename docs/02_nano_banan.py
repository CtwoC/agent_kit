#%%
# 测试：两张图片组合生成新图片
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

client = genai.Client(api_key="AIzaSyAkhPAHGCC1xezr44uwwg6O2lsxwVpFwl0")

# 方案1：上传文件获取 File 对象（需要指定 mime_type）
print("正在上传两张图片到 API...")
with open("imgs/dress_img.png", "rb") as f:
    dress_file = client.files.upload(
        file=f,
        config=types.UploadFileConfig(mime_type="image/png")
    )
with open("imgs/woman_img.png", "rb") as f:
    woman_file = client.files.upload(
        file=f,
        config=types.UploadFileConfig(mime_type="image/png")
    )
print("✓ 图片上传完成")

# 组合 prompt
text_input = """Create a professional vertical portrait fashion photo (9:16 aspect ratio).
Take the dress from the first image and let the woman from the second image wear it.
Generate a realistic, full-body shot of the woman wearing the dress.
The setting should be elegant with soft lighting. Vertical composition suitable for mobile."""

print("\n正在用 Gemini 2.5 Flash Image 合成图片...")
response = client.models.generate_content(
    model="gemini-2.5-flash-image-preview",
    contents=[dress_file, woman_file, text_input],
)

# 提取生成的图片
image_parts = [
    part.inline_data.data
    for part in response.candidates[0].content.parts
    if part.inline_data
]

if image_parts:
    combined_image = Image.open(BytesIO(image_parts[0]))
    combined_image.save('test_combined_two_images.png')
    print("✓ 成功！合成图片已保存: test_combined_two_images.png")
else:
    print("❌ 未能生成图片")

#%%
# 测试：三张图片组合生成竖屏图片
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

client = genai.Client(api_key="AIzaSyAkhPAHGCC1xezr44uwwg6O2lsxwVpFwl0")

# 上传三张图片到 API
print("正在上传三张图片到 API...")
with open("imgs/dress_img.png", "rb") as f:
    dress_file = client.files.upload(
        file=f,
        config=types.UploadFileConfig(mime_type="image/png")
    )
with open("imgs/glasses_img.png", "rb") as f:
    glasses_file = client.files.upload(
        file=f,
        config=types.UploadFileConfig(mime_type="image/png")
    )
with open("imgs/woman_img.png", "rb") as f:
    woman_file = client.files.upload(
        file=f,
        config=types.UploadFileConfig(mime_type="image/png")
    )
print("✓ 三张图片上传完成")

# 三图组合竖屏 prompt
prompt = """Create a professional fashion portrait photo.
Take the elegant dress from the first image, the stylish sunglasses from the second image, and the beautiful woman from the third image.
Combine them into one cohesive image: the woman wearing both the dress and the sunglasses.
She should be standing gracefully in a dreamy turquoise shallow water setting with golden hour lighting.
The dress should have a flowing train. Full-body shot, cinematic high-fashion style."""

print("\n正在用 Gemini 2.5 Flash Image 合成三图竖屏图片...")
response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents=[dress_file, glasses_file, woman_file, prompt],
    config=types.GenerateContentConfig(
        image_config=types.ImageConfig(
            aspect_ratio="9:16",  # 竖屏比例
            image_size="1K"
        )
    )
)

print("图片生成已完成，开始提取图片")
# 提取生成的图片
image_parts = [
    part.inline_data.data
    for part in response.candidates[0].content.parts
    if part.inline_data
]

if image_parts:
    combined_image = Image.open(BytesIO(image_parts[0]))
    combined_image.save('combined_three_images_vertical.png')
    print("✓ 成功！三图合成竖屏图片已保存: combined_three_images_vertical.png")
    print(f"   图片尺寸: {combined_image.size}")
    print(f"   宽高比: {combined_image.size[0]/combined_image.size[1]:.2f} (目标 9:16 ≈ 0.56)")
else:
    print("❌ 未能生成图片")