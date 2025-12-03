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
api_key = st.secrets
