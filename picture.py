import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import os

# --- 1. 核心配置 (必须放在最前面) ---
st.set_page_config(
    page_title="Lumina Portrait AI",
    page_icon="📸",
    layout="wide"
)

# --- 2. 注入高级黑紫主题 CSS ---
dark_purple_theme = """
            <style>
            /* 引入现代无衬线字体 */
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

            :root {
                /* --- 核心色板定义 --- */
                --bg-deep: #0A0A0F;      /* 极深午夜黑背景 */
                --bg-card: #13131A;      /* 稍微浅一点的卡片背景 */
                --text-primary: #E0E0E0; /* 柔和的灰白文字，不刺眼 */
                --text-secondary: #A0A0B0; /* 次要文字颜色 */

                /* --- 奢华紫色渐变 --- */
                /* 从深皇家紫渐变到稍微亮一点的紫罗兰色 */
                --purple-gradient: linear-gradient(135deg, #4A00E0 0%, #8E2DE2 100%);
                /* 按钮激活时的发光效果 */
                --purple-glow: 0 8px 32px rgba(142, 45, 226, 0.4);
            }

            /* --- 全局基础设定 --- */
            .stApp {
                background-color: var(--bg-deep);
                font-family: 'Inter', sans-serif;
                color: var(--text-primary);
            }

            h1, h2, h3 {
                color: #FFFFFF !important; /* 标题用纯白突出 */
                font-weight: 600 !important;
                letter-spacing: 0.05em !important;
            }

            /* --- 侧边栏美化 --- */
            section[data-testid="stSidebar"] {
                background-color: var(--bg-card);
                border-right: 1px solid rgba(255, 255, 255, 0.05); /* 极细微的边框 */
            }

            /* 侧边栏里的文字颜色调整 */
            section[data-testid="stSidebar"] .stMarkdown, 
            section[data-testid="stSidebar"] label {
                color: var(--text-secondary) !important;
            }

            /* --- 核心组件：大气高档按钮 --- */
            .stButton > button {
                /* 使用紫色渐变背景 */
                background: var(--purple-gradient) !important;
                color: #FFFFFF !important;
                border: none !important;

                /* 大气感：增加内边距，让按钮看起来更宽厚 */
                padding: 0.75rem 2rem !important;
                font-size: 1.1rem !important;
                border-radius: 12px !important; /* 柔和的稍大圆角 */

                font-weight: 600 !important;
                letter-spacing: 0.08em !important;
                text-transform: uppercase; /* 字母大写增加气势 (可选) */

                transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
                /* 初始状态带有轻微的紫色光晕 */
                box-shadow: 0 4px 15px rgba(142, 45, 226, 0.2) !important;
            }

            .stButton > button:hover {
                /* 悬浮时，按钮上浮，光晕变强，仿佛充能 */
                transform: translateY(-3px) scale(1.02);
                box-shadow: var(--purple-glow) !important;
                /* 稍微提亮渐变，增加互动感 */
                filter: brightness(1.1);
            }

            /* --- 输入框与上传组件暗色化处理 --- */
            /* 让输入框融入深色背景，而不是突兀的白色 */
            .stTextInput > div > div > input,
            .stFileUploader > div > div > button /* 上传区域的那个小按钮 */
            {
                background-color: rgba(255, 255, 255, 0.05) !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                color: var(--text-primary) !important;
                border-radius: 8px;
            }

            /* 输入框聚焦时，边框亮起紫色 */
            .stTextInput > div > div > input:focus {
                border-color: #8E2DE2 !important;
                box-shadow: 0 0 0 1px #8E2DE2 !important;
            }
            
            /* 图片说明文字颜色 */
            .stCaption {
                color: #888 !important;
            }

            /* 隐藏默认元素 */
            header {visibility: hidden;}
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}

            </style>
            """
st.markdown(dark_purple_theme, unsafe_allow_html=True)


# --- 3. API Key 配置与逻辑 ---
api_key = st.secrets.get("GOOGLE_API_KEY")

if not api_key:
    st.warning("⚠️ 检测到 API Key 未配置。请在 Streamlit Cloud 后台设置 Secrets。")
    api_key = st.text_input("或者在这里临时输入 API Key:", type="password")
    if not api_key:
        st.stop()

genai.configure(api_key=api_key)

# 1. 核心指令 (支持多图参考)
SYSTEM_INSTRUCTION = """
You are an expert AI photographer. 
Generate a high-fidelity 8k resolution, ultra-realistic image based on the provided reference images.
**CRITICAL:** Analyze ALL provided reference images to create a highly accurate composite of the subject's facial features. 
Strictly maintain the user's identity while applying the following style:
"""

# 2. 完整风格字典 (⚠️ 已更新肯豆风 Prompt)
STYLE_OPTIONS = {
    "bw-kendall": {
        "title": "Kendall Style B&W (肯豆风·黑白超模)",
        "description": "全身黑白街拍大片，聚焦黑丝长腿，演绎肯达尔·詹娜式的清冷超模感。",
        "prompt": """Subject: A full-body, high-contrast black and white photograph strictly preserving the subject's face. The vibe is "Kendall Jenner off-duty supermodel" – cool, confident, aloof, and effortless. The central focus is on her long legs styled in sheer black stockings (pantyhose) and sleek pointed-toe heels or chic loafers. Styling: Wearing an oversized, structured blazer (e.g., black or pinstripe) over a minimalist mini outfit (like tailored shorts or a mini skirt) to showcase the legs. Sleek, pulled-back hair or effortless model-off-duty waves. Pose: Caught mid-stride on a city street, or a confident, powerful standing pose emphasizing vertical proportions. Lighting: Harsh, direct sunlight creating deep shadows and bright highlights (chiaroscuro street photography style), mimicking a high-end paparazzi or street style shot. Environment: An upscale urban street pavement, concrete architecture, or a chic minimalist doorway. Grainy film texture (Ilford HP5). 8k resolution."""
    },
    "corporate": {
        "title": "Fortune 500 Headshot (商务巨擘)",
        "description": "自信、极具掌控力的 CEO 肖像，使用专业的蝴蝶光/蛤壳光。",
        "prompt": """Subject: A hyper-realistic, high-end corporate headshot of the subject. The expression is confident, approachable, and commanding, characteristic of a Fortune 500 CEO or top-tier creative director. Skin texture is ultra-detailed, showing natural pores and micro-details without excessive smoothing. Styling: Wearing a bespoke, sharp-cut navy or charcoal blazer with a high thread-count crisp white shirt. No tie (modern professional) or a subtle silk tie. Minimalist, expensive grooming. Lighting: Professional "Clamshell" lighting setup using a large Octabox overhead to create soft, sculpting light on the face, with a silver reflector underneath to fill in shadows under the chin and eyes. A subtle rim light separates the subject from the background. Environment: A clean, seamless dark grey or hand-painted canvas backdrop (Olapic style). Shallow depth of field to keep focus entirely on the eyes. Tech Specs: Shot on Phase One XF IQ4 150MP, 100mm macro lens, f/8 aperture for extreme sharpness. 8k resolution, raw photo format, commercial retouching standards, perfectly balanced white balance."""
    },
    "fashion": {
        "title": "High-Fashion Editorial (先锋时尚)",
        "description": "90年代超模风格，硬闪光灯，色彩鲜艳。",
        "prompt": """Subject: A high-fashion editorial shot strictly preserving the subject's identity. The pose is dynamic, angular, and powerful—channeling the energy of 90s supermodels mixed with modern Bella Hadid sharp aesthetics. The gaze is fierce and piercing. Styling: Avant-garde high fashion. Think oversized shoulders, structural distinct fabrics like patent leather, silk, or metallic textures. Statement accessories (chunky gold earrings or bold eyewear). Makeup is editorial—clean skin with a bold lip or graphic eyeliner. Lighting: Direct, hard flash photography (Ring flash or bare bulb strobe) to create a sharp, defined shadow behind the subject. High-key lighting that makes colors pop and skin look glossy and hydrated (glass skin). Environment: A solid, vibrant colored background (electric blue, lime green, or hot pink) or a stark white studio cyclorama wall. Tech Specs: Shot on Hasselblad H6D-100c. Sharp focus, high saturation, high contrast. "Glossy magazine" print quality. 4k definition, hyper-fashion aesthetic."""
    },
    "cinematic": {
        "title": "Cinematic Emotion (电影情绪)",
        "description": "像电影剧照一样充满故事感，冷暖对比色调。",
        "prompt": """Subject: A deeply emotional, cinematic close-up. The subject looks slightly away from the camera or directly into the soul of the viewer, conveying a complex mix of nostalgia and determination. The wind is gently catching the hair. Styling: Textured clothing, perhaps a vintage leather jacket or a heavy knit sweater that catches the light. The look is "lived-in" and authentic, not perfectly manicured. Lighting: Moody, motivated lighting inspired by cinematography (e.g., Roger Deakins). A mix of cool ambient moonlight (teal) and a warm practical light source (orange/tungsten) illuminating one side of the face. High contrast (chiaroscuro). Environment: An out-of-focus urban night scene with bokeh from neon signs and city lights, or a moody interior with dust motes dancing in a shaft of light. Tech Specs: Shot on Arri Alexa Mini LF with Panavision Anamorphic lenses. 2.39:1 aspect ratio composition. CineStill 800T film grain simulation. Halation around highlights. Color graded in DaVinci Resolve with a teal and orange LUT. 8k resolution, volumetric lighting."""
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
    
    # 状态指示灯
    if st.secrets.get("GOOGLE_API_KEY"):
        st.success("API Key 已配置 ✅")
    elif api_key:
         st.success("API Key 已临时输入 ✅")
    else:
        st.error("未检测到 API Key ❌")

    st.markdown("---")
    st.markdown("**💡 小贴士:**\n上传 3-5 张不同角度的照片，能让 AI 更好地捕捉您的神态。")

# ================= 主界面 =================
st.title("Lumina Portrait AI 📸")
st.caption("基于 Google Gemini 2.0 Flash 的专业级 AI 写真馆")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("1. 上传参考照片")
    uploaded_files = st.file_uploader(
        "请上传 1-5 张清晰的头像 (建议多角度)", 
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )
    
    # 处理上传的图片列表
    reference_images = []
    if uploaded_files:
        if len(uploaded_files) > 5:
            st.warning("⚠️ 最多支持 5 张图片，已自动选取前 5 张。")
            uploaded_files = uploaded_files[:5]
            
        for uploaded_file in uploaded_files:
            image = Image.open(uploaded_file)
            reference_images.append(image)
            
        st.success(f"已加载 {len(reference_images)} 张参考图 ✅")
    
    st.subheader("2. 选择写真风格")
    style_names = list(STYLE_OPTIONS.keys())
    # 让新的肯豆风格排在第一个作为默认
    if "bw-kendall" in style_names:
        style_names.remove("bw-kendall")
        style_names.insert(0, "bw-kendall")

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

    if reference_images:
        # 优化：显示小图预览
        st.caption("参考图预览：")
        cols = st.columns(len(reference_images))
        for idx, img in enumerate(reference_images):
            with cols[idx]:
                st.image(img, use_container_width=True)

        if generate_btn:
            with st.spinner("正在融合特征，按 8K 超模标准生成中... (约 15 秒)"):
                try:
                    # 核心逻辑：构造多模态请求列表
                    full_prompt = SYSTEM_INSTRUCTION + "\n" + current_style["prompt"]
                    input_content = [full_prompt]
                    input_content.extend(reference_images)

                    # 调用 Gemini 模型
                    model = genai.GenerativeModel('gemini-2.0-flash-exp') 

                    response = model.generate_content(input_content)

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
                            file_name="lumina_portrait_kendall.png",
                            mime="image/png"
                        )
                    else:
                        st.error("生成失败，请重试。")

                except Exception as e:
                    st.error(f"发生错误: {str(e)}")
                    st.info("提示：请确保你的 API Key 正确且有权限访问当前模型。")
    else:
        st.info("👈 请先在左侧上传照片")
