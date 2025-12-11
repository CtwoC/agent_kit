#%%
# 基本测试
import time
from google import genai
from google.genai import types


client = genai.Client(api_key="AIzaSyAkhPAHGCC1xezr44uwwg6O2lsxwVpFwl0")

prompt = """Drone shot following a classic red convertible driven by a man along a winding coastal road at sunset, waves crashing against the rocks below.
The convertible accelerates fast and the engine roars loudly."""

operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt=prompt,
)

# Poll the operation status until the video is ready.
while not operation.done:
    print("Waiting for video generation to complete...")
    time.sleep(10)
    operation = client.operations.get(operation)

# Download the generated video.
generated_video = operation.response.generated_videos[0]
client.files.download(file=generated_video.video)
generated_video.video.save("realism_example.mp4")
print("Generated video saved to realism_example.mp4")


#%%
# 竖屏对话视频测试 (9:16 适合手机)
import time
from google import genai
from google.genai import types

client = genai.Client(api_key="AIzaSyAkhPAHGCC1xezr44uwwg6O2lsxwVpFwl0")

# 精心设计的对话场景：咖啡店里的朋友对话
prompt = """A vertical shot of a cozy coffee shop interior with warm lighting and soft jazz music playing in the background.
Two young friends sitting at a wooden table, steaming coffee cups between them.
The camera slowly pushes in to a medium close-up.

The woman with curly brown hair leans forward excitedly and says, "You won't believe what happened today!"
Her friend, wearing glasses, smiles curiously and responds, "Tell me everything! I'm all ears."
The woman laughs softly and continues, "I finally got that job offer I've been waiting for!"
Her friend's eyes light up as she exclaims, "That's amazing! I'm so proud of you!"

Soft ambient coffee shop sounds: gentle chatter in the background, espresso machine hissing, cups clinking.
Warm afternoon sunlight streaming through the window, creating a golden glow."""

# 使用 config 设置竖屏比例
operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt=prompt,
    config=types.GenerateVideosConfig(
        aspect_ratio="9:16",  # 竖屏比例，适合手机
        negative_prompt="dark, blurry, low quality, distorted faces, text overlay"
    )
)

# 轮询操作状态直到视频生成完成
while not operation.done:
    print("正在生成竖屏对话视频，请稍候...")
    time.sleep(10)
    operation = client.operations.get(operation)

# 下载生成的视频
generated_video = operation.response.generated_videos[0]
client.files.download(file=generated_video.video)
generated_video.video.save("coffee_shop_dialogue_vertical.mp4")
print("竖屏对话视频已保存至 coffee_shop_dialogue_vertical.mp4")

#%%
# 用合成的竖屏图片生成 6 秒视频
import time
from google import genai
from google.genai import types
from PIL import Image

client = genai.Client(api_key="AIzaSyAkhPAHGCC1xezr44uwwg6O2lsxwVpFwl0")

print("=" * 60)
print("使用合成图片生成竖屏视频 (6秒)")
print("=" * 60)

# 读取合成图片并转换为 base64 格式（Veo 需要 base64 编码）
print("\n正在准备合成图片...")
import base64

with open('combined_three_images_vertical.png', 'rb') as f:
    image_bytes = f.read()
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')

# 创建图片对象
combined_image = types.Image(
    image_bytes=image_bytes,
    mime_type="image/png"
)
print(f"✓ 图片准备完成")

# 视频动画 prompt（描述动作和音效）
video_prompt = """A vertical portrait shot of an elegant woman in a stunning high-fashion dress and stylish sunglasses.
She walks gracefully through crystal-clear shallow turquoise water, the camera slowly pulling back to reveal the full scene.
Her dress train glides beautifully on the water surface, creating a dreamlike, cinematic atmosphere.
She turns her head gently toward the camera with a confident, radiant smile.
Soft water splashing sounds, gentle breeze rustling, serene ambient music in the background.
Golden hour lighting casting warm glow, vibrant colors against minimalist turquoise backdrop."""

print("\n正在用 Veo 3.1 生成竖屏视频...")

operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt=video_prompt,
    image=combined_image,  # 使用 types.Image 对象
    config=types.GenerateVideosConfig(
        aspect_ratio="9:16",       # ✅ 竖屏
        duration_seconds=6,        # ✅ 6 秒视频
        negative_prompt="distorted face, blurry, low quality, unnatural motion, jerky movement"
    )
)

# 轮询操作状态直到视频生成完成
while not operation.done:
    print("生成中，请稍候... (预计需要几分钟)")
    time.sleep(10)
    operation = client.operations.get(operation)

# 下载生成的视频
video = operation.response.generated_videos[0]
client.files.download(file=video.video)
video.video.save("fashion_combined_vertical_6s.mp4")

print("\n" + "=" * 60)
print("✓ 完成！竖屏视频已保存: fashion_combined_vertical_6s.mp4")
print("  - 时长: 6 秒")
print("  - 比例: 9:16 (竖屏)")
print("  - 音频: 包含环境音和音效")
print("=" * 60)

#%%
# 仙侠风格：男子挥刀劈开古楼
import time
from google import genai
from google.genai import types

client = genai.Client(api_key="AIzaSyAkhPAHGCC1xezr44uwwg6O2lsxwVpFwl0")

print("=" * 60)
print("仙侠风格视频：剑气劈开古楼")
print("=" * 60)

# 读取仙侠人物图片并创建 Image 对象
print("\n正在准备图片...")
with open('imgs/first_img.png', 'rb') as f:
    image_bytes = f.read()

wuxia_image = types.Image(
    image_bytes=image_bytes,
    mime_type="image/png"
)
print("✓ 图片准备完成")

# 仙侠风格视频 prompt（一镜到底 + 焦点转移 - 精简版）
wuxia_prompt = """Vertical 9:16 cinematic martial arts shot. Single continuous take with focus pull technique.

Camera and Action:
Single continuous shot. Low-angle starting from behind the swordsman in traditional Chinese robes, who stands with sword raised overhead in both hands.
Pauses for one second. Then slashes downward forcefully like chopping wood, with rough powerful motion and downward weight.
After the strike, sword hangs naturally down, body leaning slightly forward.

Camera shifts slightly to the right while focus gradually transitions from the swordsman's back to the distant ancient multi-tiered pagoda tower.
Camera movement is minimal, primarily using depth of field changes to bring the distant tower from blur to sharp focus.

During the focus transition, the ancient tower begins shaking, tilting, then collapses with a thunderous crash.
Roof and floors pancake down layer by layer in devastating progressive collapse.
Massive dust clouds explode upward, rolling and expanding like a mushroom cloud, spreading in all directions.
Roof tiles, wooden beams, and debris scatter with the collapse.

Swordsman remains in foreground slightly out of focus throughout.
Distant ruins and rising dust in sharp focus, sunset obscured by smoke.

Visual Elements:
Earthquake-like total structural collapse, building losing support and crumbling floor by floor.
Dense rolling gray-brown dust clouds.
Massive amounts of flying tiles, wood splinters, rubble.
Sunset obscured by smoke.

Camera Movement:
Single continuous shot throughout, slight horizontal shift combined with focus pull, from foreground swordsman to distant tower.
Duration approximately 6-8 seconds, emphasizing depth of field change rather than large panning movement.

Sound Design:
Heavy chopping sound of blade through air → Brief silence (0.5 seconds) → Deep rumbling →
Massive thunderous collapse (continuous like rolling thunder) → Continuous crashing of tiles and wood →
Roaring sound of dust explosion → Lingering echoes.
Tragic orchestral soundtrack with heavy taiko drums, building to devastating crescendo at collapse.

Atmospheric Elements:
Amber sunset sky, falling maple leaves, sky-filling dust, emphasizing destruction and tragic atmosphere.
Realistic physics: progressive structural collapse, dust dynamics, debris scatter patterns."""

print("\n正在生成仙侠视频... (预计 3-5 分钟)")

operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt=wuxia_prompt,
    image=wuxia_image,
    config=types.GenerateVideosConfig(
        aspect_ratio="9:16",       # 竖屏
        duration_seconds=6,        # 6 秒史诗时刻
        negative_prompt="glowing sword energy, magical auras, colored light beams, fantasy effects, neon colors, cartoon, anime, CGI look, fake effects, peaceful scene, static image"
    )
)

# 轮询操作状态
while not operation.done:
    print("生成中... 正在制作史诗级剑气特效...")
    time.sleep(10)
    operation = client.operations.get(operation)

# 下载生成的视频
video = operation.response.generated_videos[0]
client.files.download(file=video.video)
video.video.save("wuxia_sword_slash_vertical.mp4")

print("\n" + "=" * 60)
print("✓ 仙侠视频生成完成！")
print("   文件: wuxia_sword_slash_vertical.mp4")