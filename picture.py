import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import os

# --- 1. 核心配置 (必须放在最前面) ---
st.set_page_config(
    page_title="Lumina Portrait AI",
    page_icon="✨",
    layout="wide"
)

# --- 2. 注入硅谷顶流风格 CSS (Linear/Vercel Style) ---
# 这种风格特点：极致的黑背景、顶部光斑、微磨砂、1px 极细边框
linear_design_theme = """
<style>
    /* 引入顶级字体：Inter (正文) 和 Space Grotesk (标题) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Space+Grotesk:wght@400;600;700&display=swap');

    :root {
        --bg-color: #000000;
        --card-bg: rgba(255, 255, 255, 0.03);
        --border-color: rgba(255, 255, 255, 0.12);
        --accent-glow: radial-gradient(circle at 50% -20%, #5d3fd3 0%, rgba(0, 0, 0, 0) 50%);
        --text-primary: #EEEEEE;
        --text-secondary: #888888;
    }

    /* 全局背景：深邃黑 + 顶部聚光灯效果 */
    .stApp {
        background-color: var(--bg-color);
        background-image: var(--accent-glow);
        background-attachment: fixed;
        color: var(--text-primary);
        font-family: 'Inter', sans-serif;
    }

    /* 标题 typography：使用几何感强的 Space Grotesk */
    h1, h2, h3 {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
        color: #fff !important;
    }
    
    /* 侧边栏：透明磨砂质感 */
    section[data-testid="stSidebar"] {
        background-color: rgba(0, 0, 0, 0.2) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid var(--border-color);
    }
    
    section[data-testid="stSidebar"] .stMarkdown {
        color: var(--text-secondary);
    }

    /* 图片容器：增加极细边框和阴影 */
    .stImage {
        border: 1px solid var(--border-color);
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 20px 40px -10px rgba(0,0,0,0.5);
    }

    /* 上传组件：虚线框设计 */
    .stFileUploader > div {
        background-color: var(--card-bg);
        border: 1px dashed var(--border-color);
        border-radius: 12px;
        transition: border-color 0.3s;
    }
    .stFileUploader > div:hover {
        border-color: #666;
    }

    /* 核心按钮：高亮白反差色，模仿 Linear/Apple 设计 */
    .stButton > button {
        background: #FFFFFF !important;
        color: #000000 !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.6rem 1.2rem !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1), inset 0 0 0 1px rgba(255,255,255,0.5) !important;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        background: #F0F0F0 !important;
        transform: scale(0.98);
        box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.1) !important;
    }
    
    /* 下拉选框：深色玻璃态 */
    .stSelectbox > div > div {
        background-color: var(--card-bg) !important;
        border: 1px solid var(--border-color) !important;
        color: white !important;
        border-radius: 8px;
    }
    
    /* 文本说明颜色变淡 */
    .stCaption {
        color: #666 !important;
    }

    /* 隐藏多余元素 */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
</style>
"""
st.markdown(linear_design_theme, unsafe_allow_html=True)


# --- 3. API Key 配置 ---
api_key = st.secrets.get("GOOGLE_API_KEY")

# 侧边栏逻辑
with st.sidebar:
    st.title("Settings")
    if api_key:
        st.caption("Status: System Ready ●")
    else:
        st.warning("⚠️ API Key Missing")
        api_key = st.text_input("Enter API Key", type="password")

if not api_key:
    st.stop()

genai.configure(api_key=api_key)

# --- 4. 核心指令 & 风格库 ---
SYSTEM_INSTRUCTION = """
You are an expert AI photographer. 
Generate a high-fidelity 8k resolution, ultra-realistic image based on the provided reference images.
**CRITICAL:** Analyze ALL provided reference images to create a highly accurate composite of the subject's facial features. 
Strictly maintain the user's identity while applying the following style:
"""

STYLE_OPTIONS = {
    "bw-kendall": {
        "title": "Kendall Style B&W (肯豆风·黑白超模)",
        "description": "全身黑白街拍大片，聚焦黑丝长腿，演绎肯达尔·詹娜式的清冷超模感。",
        "prompt": """Subject: A full-body, high-contrast black and white photograph strictly preserving the subject's face. The vibe is "Kendall Jenner off-duty supermodel" – cool, confident, aloof, and effortless. The central focus is on her long legs styled in sheer black stockings (pantyhose) and sleek pointed-toe heels or chic loafers. Styling: Wearing an oversized, structured blazer (e.g., black or pinstripe) over a minimalist mini outfit (like tailored shorts or a mini skirt) to showcase the legs. Sleek, pulled-back hair or effortless model-off-duty waves. Pose: Caught mid-stride on a city street, or a confident, powerful standing pose emphasizing vertical proportions. Lighting: Harsh, direct sunlight creating deep shadows and bright highlights (chiaroscuro street photography style), mimicking a high-end paparazzi or street style shot. Environment: An upscale urban street pavement, concrete architecture, or a chic minimalist doorway. Grainy film texture (Ilford HP5). 8k resolution."""
    },
    "corporate": {
        "title": "Fortune 500 Headshot (商务巨擘)",
        "description": "自信、极具掌控力的 CEO 肖像。",
        "prompt": """Subject: A hyper-realistic, high-end corporate headshot. Expression is confident and commanding. Styling: Bespoke navy/charcoal blazer, crisp white shirt, no tie. Lighting: Professional "Clamshell" lighting. Environment: Seamless dark grey backdrop. Shot on Phase One XF IQ4."""
    },
    "fashion": {
        "title": "High-Fashion Editorial (先锋时尚)",
        "description": "90年代超模风格，硬闪光灯，色彩鲜艳。",
        "prompt": """Subject: High-fashion editorial shot. Dynamic, angular pose channeling 90s supermodels. Styling: Avant-garde, oversized shoulders, patent leather or silk. Lighting: Direct hard flash (Ring flash) for sharp shadows. Environment: Vibrant colored background or stark white cyclorama. Shot on Hasselblad H6D-100c."""
    },
    "cinematic": {
        "title": "Cinematic Emotion (电影情绪)",
        "description": "像电影剧照一样充满故事感。",
        "prompt": """Subject: Deeply emotional cinematic close-up. Styling: Textured clothing, vintage leather or knit. Lighting: Moody, cinematography inspired (teal and orange). Environment: Out-of-focus urban night scene with bokeh. Shot on Arri Alexa Mini LF."""
    },
    "lifestyle": {
        "title": "Quiet Luxury Lifestyle (松弛感生活)",
        "description": "自然抓拍，黄金时刻的逆光效果。",
        "prompt": """Subject: Candid, spontaneous lifestyle shot. Radiating happiness and wealth ("Quiet Luxury"). Styling: Cashmere, linen, neutral palette. Lighting: Natural backlight (Golden Hour). Environment: Blurry upscale outdoor setting (Parisian cafe or garden). Shot on Canon R5."""
    }
}

# --- 5. 主界面布局 ---
st.title("Lumina Portrait AI")
st.caption("Professional AI Photography Studio")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("Reference")
    uploaded_files = st.file_uploader(
        "Upload 1-5 photos (JPG/PNG)", 
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )
    
    reference_images = []
    if uploaded_files:
        if len(uploaded_files) > 5:
            st.warning("Limit: 5 images max. Using first 5.")
            uploaded_files = uploaded_files[:5]
        for f in uploaded_files:
            reference_images.append(Image.open(f))
        st.success(f"{len(reference_images)} images loaded")

    st.markdown("---")
    st.subheader("Style")
    
    # 将肯豆风置顶
    style_names = list(STYLE_OPTIONS.keys())
    if "bw-kendall" in style_names:
        style_names.remove("bw-kendall")
        style_names.insert(0, "bw-kendall")
        
    selected_style_key = st.selectbox(
        "Select Preset",
        style_names,
        format_func=lambda x: STYLE_OPTIONS[x]["title"]
    )
    
    current_style = STYLE_OPTIONS[selected_style_key]
    with st.expander("View Prompt Details"):
        st.code(current_style["prompt"], language="text")
        
    generate_btn = st.button("Generate Artwork", type="primary", use_container_width=True)

with col2:
    st.subheader("Preview & Result")
    
    if reference_images:
        # 小图预览网格
        cols = st.columns(5)
        for i, img in enumerate(reference_images):
            with cols[i]:
                st.image(img, use_container_width=True)
                
        if generate_btn:
            with st.spinner("Processing High-Fidelity Image..."):
                try:
                    full_prompt = SYSTEM_INSTRUCTION + "\n" + current_style["prompt"]
                    input_content = [full_prompt]
                    input_content.extend(reference_images)
                    
                    # 使用 Gemini 2.0 Flash (视觉能力极强且快)
                    model = genai.GenerativeModel('gemini-2.0-flash-exp')
                    
                    response = model.generate_content(input_content)
                    
                    if response.parts:
                        img_data = response.parts[0].inline_data.data
                        generated_image = Image.open(io.BytesIO(img_data))
                        
                        st.image(generated_image, caption=current_style['title'], use_container_width=True)
                        
                        buf = io.BytesIO()
                        generated_image.save(buf, format="PNG")
                        st.download_button(
                            label="Download High-Res",
                            data=buf.getvalue(),
                            file_name="lumina_portrait.png",
                            mime="image/png",
                            type="secondary" # 使用次级样式让下载按钮不抢视觉
                        )
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    else:
        # 空状态占位符
        st.info("Upload photos to start.")
