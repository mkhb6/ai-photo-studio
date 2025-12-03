import streamlit as st
import google.generativeai as genai
from PIL import Image
import io

# ================= 配置区域 =================

import os

# 尝试从 Streamlit Secrets 获取，如果本地没有 secrets 文件，则尝试从环境变量获取
# 注意：上传到 GitHub 后，千万不要在代码里写死 Key
api_key = st.secrets.get("GOOGLE_API_KEY")

if not api_key:
    st.error("未找到 API Key，请在 Streamlit Cloud 的 Secrets 中配置 GOOGLE_API_KEY")
    st.stop()

genai.configure(api_key=api_key)

st.set_page_config(page_title="Lumina Portrait AI (免输入版)", layout="wide")

# 1. 核心指令
SYSTEM_INSTRUCTION = """
Generate a high-fidelity 8k resolution, ultra-realistic, highly detailed image based on the attached reference photo. 
Strictly maintain the user's facial identity and features while applying the following professional photography style:
"""

# 2. 完整风格字典
STYLE_OPTIONS = {
    "corporate": {
        "title": "Fortune 500 Headshot (商务巨擘)",
        "description": "自信、极具掌控力的 CEO 肖像，使用专业的蝴蝶光/蛤壳光。",
        "prompt": """Subject: A hyper-realistic, high-end corporate headshot of the subject. The expression is confident, approachable, and commanding, characteristic of a Fortune 500 CEO or top-tier creative director. Skin texture is ultra-detailed, showing natural pores and micro-details without excessive smoothing. Styling: Wearing a bespoke, sharp-cut navy or charcoal blazer with a high thread-count crisp white shirt. No tie (modern professional) or a subtle silk tie. Minimalist, expensive grooming. Lighting: Professional "Clamshell" lighting setup using a large Octabox overhead to create soft, sculpting light on the face, with a silver reflector underneath to fill in shadows under the chin and eyes. A subtle rim light separates the subject from the background. Environment: A clean, seamless dark grey or hand-painted canvas backdrop (Olapic style). Shallow depth of field to keep focus entirely on the eyes. Tech Specs: Shot on Phase One XF IQ4 150MP, 100mm macro lens, f/8 aperture for extreme sharpness. 8k resolution, raw photo format, commercial retouching standards, perfectly balanced white balance."""
    },
    "cinematic": {
        "title": "Cinematic Emotion (电影情绪)",
        "description": "像电影剧照一样充满故事感，冷暖对比色调。",
        "prompt": """Subject: A deeply emotional, cinematic close-up. The subject looks slightly away from the camera or directly into the soul of the viewer, conveying a complex mix of nostalgia and determination. The wind is gently catching the hair. Styling: Textured clothing, perhaps a vintage leather jacket or a heavy knit sweater that catches the light. The look is "lived-in" and authentic, not perfectly manicured. Lighting: Moody, motivated lighting inspired by cinematography (e.g., Roger Deakins). A mix of cool ambient moonlight (teal) and a warm practical light source (orange/tungsten) illuminating one side of the face. High contrast (chiaroscuro). Environment: An out-of-focus urban night scene with bokeh from neon signs and city lights, or a moody interior with dust motes dancing in a shaft of light. Tech Specs: Shot on Arri Alexa Mini LF with Panavision Anamorphic lenses. 2.39:1 aspect ratio composition. CineStill 800T film grain simulation. Halation around highlights. Color graded in DaVinci Resolve with a teal and orange LUT. 8k resolution, volumetric lighting."""
    },
    "fashion": {
        "title": "High-Fashion Editorial (先锋时尚)",
        "description": "90年代超模风格，硬闪光灯，色彩鲜艳。",
        "prompt": """Subject: A high-fashion editorial shot strictly preserving the subject's identity. The pose is dynamic, angular, and powerful—channeling the energy of 90s supermodels mixed with modern Bella Hadid sharp aesthetics. The gaze is fierce and piercing. Styling: Avant-garde high fashion. Think oversized shoulders, structural distinct fabrics like patent leather, silk, or metallic textures. Statement accessories (chunky gold earrings or bold eyewear). Makeup is editorial—clean skin with a bold lip or graphic eyeliner. Lighting: Direct, hard flash photography (Ring flash or bare bulb strobe) to create a sharp, defined shadow behind the subject. High-key lighting that makes colors pop and skin look glossy and hydrated (glass skin). Environment: A solid, vibrant colored background (electric blue, lime green, or hot pink) or a stark white studio cyclorama wall. Tech Specs: Shot on Hasselblad H6D-100c. Sharp focus, high saturation, high contrast. "Glossy magazine" print quality. 4k definition, hyper-fashion aesthetic."""
    },
    "bw-iconic": {
        "title": "Iconic Black & White (经典黑白)",
        "description": "永恒的经典黑白人像，伦勃朗光。",
        "prompt": """Subject: A timeless, iconic black and white portrait. The subject exudes an aura of "off-duty supermodel" or classic Hollywood star. The expression is neutral, serene, and effortlessly cool. Styling: Minimalist aesthetic. A simple black turtleneck, a white tank top, or an oversized blazer. The focus is on the silhouette and the person, not the clothes. Wet-look hair or a sleek bun. Lighting: Dramatic "Rembrandt lighting" to create a triangle of light on the cheek, highlighting the cheekbones and jawline. Deep, rich blacks and bright, pearlescent highlights. Environment: A textureless dark void or a simple textured grey muslin backdrop. Tech Specs: Shot on Leica M6 with Ilford HP5 Plus 400 black and white film. Fine, organic film grain. High contrast filter. Museum-quality monochrome photography. Focus on structural beauty and skin texture reality."""
    },
    "fine-art": {
        "title": "Painterly Fine Art (古典油画)",
        "description": "像文艺复兴时期的油画，柔和梦幻。",
        "prompt": """Subject: A surreal, painterly fine art portrait. The subject appears as a muse in a modern renaissance painting. The pose is fluid, elegant, and statuesque. The eyes hold a mysterious, calm story. Styling: Draped fabrics, tulle, or Victorian-inspired collars mixed with modern cuts. Colors are muted tones—sage green, dusty rose, slate blue, or deep burgundy. Lighting: Soft, diffused "North Window Light" simulation. No harsh shadows, just a gentle wrap-around light that makes the skin look like porcelain or marble. Environment: An abstract, hand-painted backdrop featuring cloudy textures or floral motifs, slightly out of focus to create a dreamlike atmosphere. Tech Specs: Medium format digital photography styled to look like an oil painting. Soft focus filters. Desaturated color palette with low contrast. Incredible detail in fabric folds and hair strands. 8k resolution, gallery exhibition quality."""
    },
    "lifestyle": {
        "title": "Quiet Luxury Lifestyle (松弛感生活)",
        "description": "自然抓拍，黄金时刻的逆光效果。",
        "prompt": """Subject: A candid, spontaneous lifestyle shot. The subject is caught in a moment of genuine laughter or thoughtful observation. Not looking directly at the camera. Radiating happiness, health, and an expensive but relaxed lifestyle. Styling: "Quiet Luxury" aesthetic. Cashmere sweaters, linen shirts, or subtle tenniscore outfits. Neutral palette (whites, beiges, creams). Minimal makeup, emphasizing natural beauty. Lighting: Natural backlight from the sun (Golden Hour), creating a halo effect (rim light) around the hair. Lens flares are natural and warm. Soft fill light on the face. Environment: A blurry, upscale outdoor setting—a Parisian cafe terrace, a Hamptons garden, or a clean, modern interior with plants and sunlight streaming in. Tech Specs: Shot on Canon R5 with a 50mm f/1.2 lens. Extremely shallow depth of field (creamy bokeh background). Warm color temperature (5600K-6000K). High dynamic range (HDR) to capture details in both shadows and highlights."""
    },
    "modern-luxury": {
        "title": "Modern Luxury Campaign (现代奢华)",
        "description": "高冷、极简、高锐度的广告大片。",
        "prompt": """Subject: A sleek, ultra-modern luxury fashion campaign image. The subject embodies sophistication, exclusivity, and cool detachment. Posture is erect, angular, and poised. The look implies "I have arrived." Styling: Minimalist luxury. Sharp tailoring, trench coats, or architectural fashion pieces. Focus on textures like leather, silk, or heavy wool. Sunglasses or a luxury handbag may be subtly included as props. Lighting: Cool, crisp, and shadowless daylight or high-tech studio lighting. The light is flat but extremely revealing of texture and quality. Environment: Brutalist architecture (concrete walls), a modern glass building, or a stark, empty studio space with sharp geometric lines. Tech Specs: Shot on Fujifilm GFX 100. Ultra-sharp, hyper-detailed. Color grading leans towards desaturated blues, cooler greys, and stark whites. No grain, pure digital clarity. 8k resolution, billboard print quality."""
    }
}

# ================= 侧边栏 =================
with st.sidebar:
    st.title("⚙️ 设置")
    st.success("API Key 已配置 ✅")
    st.info("提示：你已在代码中内置了密钥，无需手动输入。")

    st.markdown("---")
    st.markdown("**关于 Prompt:**\n此版本已集成完整的高保真摄影指令，确保输出 8K 级画质。")

# ================= 主界面 =================
st.title("Lumina Portrait AI 📸")
st.caption("基于 Google Gemini 3 Pro 的专业级 AI 写真馆")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("1. 上传你的照片")
    uploaded_file = st.file_uploader("请上传一张清晰的头像 (JPG/PNG)", type=["jpg", "jpeg", "png"])

    st.subheader("2. 选择写真风格")
    style_names = list(STYLE_OPTIONS.keys())
    selected_style_key = st.selectbox(
        "选择风格预设",
        style_names,
        format_func=lambda x: STYLE_OPTIONS[x]["title"]
    )

    # 显示当前风格的详细描述
    current_style = STYLE_OPTIONS[selected_style_key]
    with st.expander("查看完整的 Prompt 细节 (已启用)"):
        st.code(current_style["prompt"], language="text")

    generate_btn = st.button("✨ 生成高清写真", type="primary", use_container_width=True)

with col2:
    st.subheader("预览与结果")

    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="参考原图", width=300)

        if generate_btn:
            # 这里不再检查 api_key 输入框，因为已经硬编码配置了
            with st.spinner("正在根据 8K 摄影标准生成中... (约 15 秒)"):
                try:
                    # 核心逻辑：拼接 系统指令 + 具体风格 Prompt
                    full_prompt = SYSTEM_INSTRUCTION + "\n" + current_style["prompt"]

                    # 调用 Gemini 3 Pro Vision 模型
                    model = genai.GenerativeModel('gemini-3-pro-image-preview')

                    response = model.generate_content([
                        full_prompt,
                        image
                    ])

                    if response.parts:
                        img_data = response.parts[0].inline_data.data
                        generated_image = Image.open(io.BytesIO(img_data))
                        st.image(generated_image, caption=f"生成结果：{current_style['title']}",
                                 use_container_width=True)

                        # 提供下载按钮
                        buf = io.BytesIO()
                        generated_image.save(buf, format="PNG")
                        st.download_button(
                            label="⬇️ 下载高清原图",
                            data=buf.getvalue(),
                            file_name="lumina_portrait.png",
                            mime="image/png"
                        )
                    else:
                        st.error("生成失败，请重试。")

                except Exception as e:
                    st.error(f"发生错误: {str(e)}")
                    st.info("提示：请确保你的 API Key 有权限访问 gemini-3-pro-image-preview 模型。")
    else:
        st.info("👈 请先在左侧上传照片")