import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import os

# --- 1. 核心配置 (必须放在最前面) ---
st.set_page_config(
    page_title="NANO BANANA | Hyper-Glass UI",
    page_icon="🍌",
    layout="wide"
)

# --- 2. 风格缩略图 Base64 占位符 (⚠️ 请务必替换这里的字符串) ---
# 获取 Base64 字符串时，只需要图片数据部分，不需要 'data:image/png;base64,' 头部
BASE64_THUMBS = {
    "bw-kendall": "PLACEHOLDER_KENDALL_BASE64",
    "corporate": "PLACEHOLDER_CORPORATE_BASE64",
    "fashion": "PLACEHOLDER_FASHION_BASE64",
    "cinematic": "PLACEHOLDER_CINEMATIC_BASE64",
    "fine-art": "PLACEHOLDER_FINEART_BASE64",
    "lifestyle": "PLACEHOLDER_LIFESTYLE_BASE64",
    "modern-luxury": "PLACEHOLDER_MODERNLUXURY_BASE64",
}

# --- 3. 注入 Hyper-Glass CSS (整合并动态注入 Base64) ---

# 动态生成风格卡片的 CSS 样式（将 Base64 注入为背景）
style_background_css = ""
for key, base64_code in BASE64_THUMBS.items():
    if base64_code.startswith("PLACEHOLDER"):
        # 如果是占位符，使用默认渐变背景
        style_background_css += f"""
            .style-opt[data-style="{key}"] {{
                background: linear-gradient(135deg, #1A1A1A, #0A0A0A);
            }}
        """
    else:
        # 否则使用 Base64 图片
        style_background_css += f"""
            .style-opt[data-style="{key}"] {{
                background-image: url('data:image/jpeg;base64,{base64_code}');
                background-size: cover;
                background-position: center;
            }}
        """

hyper_glass_theme = f"""
<style>
    /* === 核心变量 === */
    :root {{
        --bg-void: #020202;
        --glass-surface: rgba(30, 30, 30, 0.25);
        --neon-core: #b026ff;
        --neon-sec: #00d2ff;
        --font-stack: "Inter", -apple-system, sans-serif;
    }}
    .stApp {{
        background-color: var(--bg-void); 
        color: #eee; 
        font-family: var(--font-stack);
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.05'/%3E%3C/rect%3E%3C/svg%3E");
    }}
    /* 全局背景呼吸灯 */
    .stApp::before {{
        content: ""; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
        background: radial-gradient(circle at center, rgba(100, 50, 200, 0.2), transparent 60%); 
        z-index: -1; 
        animation: tri-color-drift 30s ease-in-out infinite alternate; 
        filter: blur(80px); 
        pointer-events: none;
    }}
    @keyframes tri-color-drift {{
        0% {{ transform: translate(0, 0) scale(1); }} 33% {{ transform: translate(-5%, 5%) scale(1.05) rotate(5deg); }}
        66% {{ transform: translate(5%, -5%) scale(1.1) rotate(-5deg); }} 100% {{ transform: translate(0, 0) scale(1); }}
    }}
    /* 底部流光 */
    .global-flow-layer {{
        position: absolute; bottom: 0; left: 0; width: 100%; height: 30%; pointer-events: none; z-index: 0;
        background: radial-gradient(ellipse at center bottom, rgba(176, 38, 255, 0.15), transparent 70%);
        filter: blur(40px); animation: pulse-ground 6s ease-in-out infinite alternate;
    }}
    @keyframes pulse-ground {{ 0% {{ opacity: 0.5; transform: scaleY(1); }} 100% {{ opacity: 0.8; transform: scaleY(1.2); }} }}

    /* Logo/Header */
    .logo-style {{
        font-weight: 700 !important; font-size: 18px !important; letter-spacing: 2px; color: #fff !important; opacity: 0.9;
        padding: 20px 40px 10px 40px; border-bottom: 1px solid rgba(255,255,255,0.03);
    }}
    
    /* 模块主体样式: Hyper-Glass Card */
    .nano-card-container {{
        position: relative; border-radius: 24px; background: var(--glass-surface);
        backdrop-filter: blur(60px) saturate(190%); -webkit-backdrop-filter: blur(60px) saturate(190%);
        box-shadow: 
            inset 0 1px 0 0 rgba(255, 255, 255, 0.1), 0 20px 40px rgba(0,0,0,0.4);
        display: flex; flex-direction: column; overflow: hidden;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        padding: 24px;
        margin-bottom: 24px !important; /* 增加卡片间距 */
    }}
    .stContainer:hover > div > div > div.nano-card-container {{
        transform: scale(1.005);
        box-shadow: 
            inset 0 1px 0 0 rgba(255, 255, 255, 0.15), 0 0 30px rgba(176, 38, 255, 0.2), 0 0 50px rgba(0, 210, 255, 0.15), 0 20px 40px rgba(0,0,0,0.5);
    }}
    
    /* 标题样式 */
    h1, h2, h3 {{ color: #fff !important; }}
    .card-title {{ font-size: 13px; font-weight: 600; color: rgba(255,255,255,0.6); text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 16px; }}

    /* 按钮系统: Neon 主按钮 */
    .stButton > button {{
        background: var(--neon-core) !important; color: #000 !important; border: none !important;
        border-radius: 22px !important; font-size: 14px; font-weight: 600; 
        box-shadow: 0 0 15px rgba(176, 38, 255, 0.4); transition: all 0.3s ease;
    }}
    .stButton > button:hover {{ 
        background: #c35eff !important; 
        box-shadow: 0 0 30px rgba(176, 38, 255, 0.6) !important; 
        transform: scale(1.02); 
    }}

    /* Select/Input 样式 */
    .stSelectbox > div > div, .stFileUploader > div > div > button {{
        background: rgba(0,0,0,0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: #eee !important;
    }}

    /* --- 风格卡片样式 --- */
    .style-card-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
        gap: 16px;
        padding-top: 10px;
        padding-bottom: 20px;
    }}
    .style-opt {{ 
        min-height: 120px; 
        border-radius: 16px; 
        position: relative; 
        overflow: hidden; 
        cursor: pointer; 
        border: 1px solid transparent; 
        transition: all 0.4s cubic-bezier(0.2, 0.8, 0.2, 1);
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }}
    .style-opt.selected {{ 
        border-color: var(--neon-core); 
        box-shadow: 0 0 20px rgba(176, 38, 255, 0.4); 
    }}
    .style-name {{ 
        position: absolute; bottom: 10px; left: 10px; 
        font-size: 13px; font-weight: 700; color: #fff; 
        text-shadow: 0 2px 4px rgba(0,0,0,0.8); 
    }}
    
    {style_background_css}

    /* 隐藏 Streamlit 默认 Header/Footer */
    #MainMenu, footer, .stApp > header {{ visibility: hidden; }}
</style>
"""

st.markdown(hyper_glass_theme, unsafe_allow_html=True)
st.markdown('<div class="global-flow-layer"></div>', unsafe_allow_html=True)
st.markdown('<div class="logo-style">NANO BANANA | Hyper-Glass UI</div>', unsafe_allow_html=True)


# --- 4. API Key 配置 ---
api_key = st.secrets.get("GOOGLE_API_KEY")

if not api_key:
    st.markdown('<div style="padding: 20px 40px;">', unsafe_allow_html=True)
    st.error("⚠️ API Key Missing. Please enter your key below.")
    api_key = st.text_input("Enter API Key", type="password", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)
    if not api_key:
        st.stop()

genai.configure(api_key=api_key)


# --- 5. 核心指令 & 风格库 (使用完整的 Prompt) ---
SYSTEM_INSTRUCTION = """
You are an expert AI photographer. 
Generate a high-fidelity 8k resolution, ultra-realistic image based on the provided reference images.
**CRITICAL:** Analyze ALL provided reference images to create a highly accurate composite of the subject's facial features. 
Strictly maintain the user's identity while applying the following style:
"""

STYLE_OPTIONS = {
    "bw-kendall": {
        "title": "肯豆风·黑白超模",
        "prompt": """Subject: A full-body, high-contrast black and white photograph strictly preserving the subject's face. The vibe is "Kendall Jenner off-duty supermodel" – cool, confident, aloof, and effortless. The central focus is on her long legs styled in sheer black stockings (pantyhose) and sleek pointed-toe heels or chic loafers. Styling: Wearing an oversized, structured blazer (e.g., black or pinstripe) over a minimalist mini outfit (like tailored shorts or a mini skirt) to showcase the legs. Pose: Caught mid-stride on a city street, emphasizing vertical proportions. Lighting: Harsh, direct sunlight creating deep shadows and bright highlights. Environment: Upscale urban street pavement. 8k resolution."""
    },
    "corporate": {
        "title": "商务巨擘",
        "prompt": """Subject: A hyper-realistic, high-end corporate headshot. The expression is confident, approachable, and commanding. Styling: bespoke, sharp-cut navy or charcoal blazer, crisp white shirt. Lighting: Professional "Clamshell" lighting. Environment: clean, seamless dark grey backdrop. Shot on Phase One XF IQ4."""
    },
    "fashion": {
        "title": "先锋时尚",
        "prompt": """Subject: A high-fashion editorial shot. The pose is dynamic, angular, and powerful. Styling: Avant-garde high fashion, structural distinct fabrics. Lighting: Direct, hard flash photography (Ring flash). Environment: A solid, vibrant colored background or a stark white studio cyclorama wall. Shot on Hasselblad H6D-100c. High saturation."""
    },
    "cinematic": {
        "title": "电影情绪",
        "prompt": """Subject: A deeply emotional, cinematic close-up. Styling: Textured clothing, vintage leather or heavy knit sweater. Lighting: Moody, motivated lighting (cool ambient moonlight and warm practical light). High contrast (chiaroscuro). Environment: Out-of-focus urban night scene with bokeh. Shot on Arri Alexa Mini LF."""
    },
    "fine-art": {
        "title": "古典油画",
        "prompt": """Subject: A surreal, painterly fine art portrait. The subject appears as a muse in a modern renaissance painting. Styling: Draped fabrics, tulle, or Victorian-inspired collars. Lighting: Soft, diffused "North Window Light" simulation. Environment: An abstract, hand-painted backdrop. Desaturated color palette."""
    },
    "lifestyle": {
        "title": "松弛感生活",
        "prompt": """Subject: A candid, spontaneous lifestyle shot. Radiating happiness and relaxed luxury. Styling: "Quiet Luxury" aesthetic (Cashmere, linen). Lighting: Natural backlight from the sun (Golden Hour), creating a halo effect. Environment: A blurry, upscale outdoor setting. Shallow depth of field."""
    },
    "modern-luxury": {
        "title": "现代奢华",
        "prompt": """Subject: A sleek, ultra-modern luxury fashion campaign image. The subject embodies sophistication and cool detachment. Styling: Minimalist luxury, sharp tailoring. Lighting: Cool, crisp, and shadowless daylight. Environment: Brutalist architecture or a modern glass building. Ultra-sharp, pure digital clarity."""
    }
}


# --- 6. 主界面布局 ---
st.markdown('<div style="padding: 0 40px 40px 40px;">', unsafe_allow_html=True) # 包装整个主区域，模拟 Grid Padding

main_col1, main_col2 = st.columns([4, 6], gap="large")

with main_col1:
    # 模拟 Source Material Card
    with st.container(border=False):
        st.markdown('<div class="nano-card-container">', unsafe_allow_html=True)
        st.markdown('<span class="card-title">Source Material</span>', unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader(
            "Upload 1-5 photos (Max 5)", 
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
        
        reference_images = []
        if uploaded_files:
            if len(uploaded_files) > 5:
                st.warning("Limit: 5 images max. Using first 5.")
                uploaded_files = uploaded_files[:5]
            for f in uploaded_files:
                reference_images.append(Image.open(f))
            st.caption(f"Loaded {len(reference_images)} images.")
            
        st.markdown('</div>', unsafe_allow_html=True)

    # 模拟 Aesthetics Model Card
    with st.container(border=False):
        st.markdown('<div class="nano-card-container">', unsafe_allow_html=True)
        st.markdown('<span class="card-title">Aesthetics Model</span>', unsafe_allow_html=True)
        
        # 1. 使用 Selectbox 获取选择，并用 CSS 隐藏它
        style_names = list(STYLE_OPTIONS.keys())
        # 将肯豆风置顶
        if "bw-kendall" in style_names:
            style_names.remove("bw-kendall")
            style_names.insert(0, "bw-kendall")
            
        selected_style_key = st.selectbox(
            "Select Preset",
            style_names,
            format_func=lambda x: STYLE_OPTIONS[x]["title"],
            key="final_style_select",
            label_visibility="collapsed"
        )
        
        # 2. 注入风格卡片 UI (使用 HTML 和 CSS 呈现视觉效果)
        style_cards_html = f'<div class="style-card-grid">'
        for key, details in STYLE_OPTIONS.items():
            is_selected = "selected" if selected_style_key == key else ""
            style_cards_html += f"""
                <div class="style-opt {is_selected}" data-style="{key}" title="{details['title']}">
                    <div class="style-name">{details['title'].split('(')[0].strip()}</div>
                </div>
            """
        style_cards_html += '</div>'
        st.markdown(style_cards_html, unsafe_allow_html=True)
        
        # Prompt 预览
        with st.expander("Prompt Details"):
            st.code(STYLE_OPTIONS[selected_style_key]["prompt"], language="text")

        st.markdown('</div>', unsafe_allow_html=True)

with main_col2:
    # 模拟 Canvas Card
    with st.container(border=False):
        st.markdown('<div class="nano-card-container" style="height: 100%;">', unsafe_allow_html=True)
        st.markdown('<span class="card-title">Output Canvas</span>', unsafe_allow_html=True)
        
        if reference_images:
            st.caption("Reference Images:")
            cols = st.columns(len(reference_images))
            for i, img in enumerate(reference_images):
                with cols[i]:
                    st.image(img, use_container_width=True)

        generate_btn = st.button("Initialise Generation", key="generate_btn", type="primary", use_container_width=True)
        st.markdown("---") # 分割线

        if reference_images and generate_btn:
            with st.spinner("Processing High-Fidelity Image..."):
                try:
                    full_prompt = SYSTEM_INSTRUCTION + "\n" + STYLE_OPTIONS[selected_style_key]["prompt"]
                    input_content = [full_prompt]
                    input_content.extend(reference_images)
                    
                    model = genai.GenerativeModel('gemini-2.0-flash-exp')
                    response = model.generate_content(input_content)
                    
                    if response.parts:
                        img_data = response.parts[0].inline_data.data
                        generated_image = Image.open(io.BytesIO(img_data))
                        
                        st.image(generated_image, caption=STYLE_OPTIONS[selected_style_key]['title'], use_container_width=True)
                        
                        buf = io.BytesIO()
                        generated_image.save(buf, format="PNG")
                        st.download_button(
                            label="Download Image",
                            data=buf.getvalue(),
                            file_name=f"lumina_portrait_{selected_style_key}.png",
                            mime="image/png",
                            type="secondary"
                        )
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        else:
             st.markdown('<div style="height: 400px; display: flex; justify-content: center; align-items: center; border: 1px dashed rgba(255,255,255,0.1); border-radius: 16px;"><div style="text-align:center; opacity:0.4;"><div style="font-size:24px; margin-bottom:8px;">❖</div><div style="font-size:12px; letter-spacing:1px;">OUTPUT CANVAS</div></div></div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
        
st.markdown('</div>', unsafe_allow_html=True)
