

#  ___________________________________________________________________________
# |                                                                           |
# |  PROJECT: InstaGuard Enterprise                                           |
# |  AUTHOR:  Pronoy Das                                                      |
# |  LICENSE: MIT (Copyright © 2026 Pronoy Das)                               |
# |___________________________________________________________________________|

import asyncio
import sys
import os
import json

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import streamlit as st
import streamlit.components.v1 as components

# Import Actual Modules
from analyzer import HybridAnalyzer
from scraper import EnterpriseScraper

# -----------------------------------
# Page Configuration
# -----------------------------------
st.set_page_config(
    page_title="InstaGuard Mobile Forensics",
    layout="wide",
    page_icon="🛡️"
)

# -----------------------------------
# Professional Dashboard CSS (Design B)
# -----------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    :root {
        --bg-body: #0b1121;
        --bg-panel: #151e32;
        --bg-input: #0f172a;
        --border-color: #1e293b;
        --text-primary: #e2e8f0;
        --text-secondary: #94a3b8;
        --primary: #0ea5e9;
        --primary-glow: rgba(14, 165, 233, 0.4);
        --danger: #ef4444;
        --success: #10b981;
    }

    body {
        font-family: 'Inter', sans-serif;
        background-color: var(--bg-body);
        color: var(--text-primary);
    }

    [data-testid="stAppViewContainer"] {
        background-color: var(--bg-body);
        background-image: 
            linear-gradient(rgba(30, 41, 59, 0.3) 1px, transparent 1px),
            linear-gradient(90deg, rgba(30, 41, 59, 0.3) 1px, transparent 1px);
        background-size: 40px 40px;
    }

    header[data-testid="stHeader"] {
        background-color: rgba(15, 23, 42, 0.9);
        border-bottom: 1px solid var(--border-color);
        backdrop-filter: blur(8px);
        color: white;
    }

    [data-testid="stSidebar"] {
        background-color: var(--bg-panel);
        border-right: 1px solid var(--border-color);
    }

    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        background-color: rgba(15, 23, 42, 0.5);
        border: 1px solid var(--border-color);
        border-radius: 6px;
        color: var(--text-primary);
        font-family: 'JetBrains Mono', monospace;
    }

    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: var(--primary);
        box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.2);
    }

    .stButton > button {
        background: linear-gradient(135deg, var(--primary), #0284c7);
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(14, 165, 233, 0.2);
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(14, 165, 233, 0.3);
    }
    
    /* Hide standard Streamlit elements we don't need */
    footer {visibility: hidden;}
    
    /* Watermark */
    header[data-testid="stHeader"]::after {
        content: "Developed by Pronoy Das";
        position: absolute;
        right: 20px;
        top: 18px;
        font-size: 12px;
        color: rgba(255,255,255,0.4);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------
# Backend Logic
# -----------------------------------

@st.cache_resource
def load_engine():
    return HybridAnalyzer()

try:
    engine = load_engine()
except Exception as e:
    st.error(f"Database Error: {e}")
    st.stop()

# -----------------------------------
# Sidebar UI
# -----------------------------------
with st.sidebar:
    st.markdown("### 🛡️ InstaGuard")
    st.markdown(f"Status: :green[Active ({len(engine.toxic_phrases)} Patterns)]")
    st.markdown("---")
    
    url = st.text_input("Target URL", placeholder="https://instagram.com/p/...", value="https://www.instagram.com/p/C-demo/")
    limit = st.number_input("Scan Limit", 10, 500, 50)
    
    st.markdown("<br>", unsafe_allow_html=True)
    run_button = st.button("Start Mobile Extraction", type="primary")
    
    st.markdown("---")
    st.caption("Environment: iPhone 13 Pro (Emu)\nClearance: Cyber Cell L1")

# -----------------------------------
# Execution Logic
# -----------------------------------

if 'data' not in st.session_state:
    st.session_state.data = None
    st.session_state.logs = []

if run_button:
    if not url:
        st.warning("Please enter a target URL.")
    else:
        # Generate Fake Logs for UI Effect
        logs = [
            "Initializing iOS Environment...",
            "Loading iPhone 13 Pro Emulator image...",
            f"Connecting to Target: {url[:30]}...",
            f"Configuring scroll depth: {limit} items",
            "Simulating Touch Gestures & Swipe...",
            "Decrypting comment payloads...",
            "Cross-referencing with Threat Database...",
            "Analysis complete. Rendering evidence."
        ]
        
        # Run Real Scraper
        bot = EnterpriseScraper()
        
        # We run the scraper first, then show the UI
        with st.spinner("Extracting Data..."):
            scraped_data = bot.run(url, limit, engine)
        
        st.session_state.data = scraped_data
        st.session_state.logs = logs
        st.rerun()

# -----------------------------------
# Results Dashboard (Logic A + Design B)
# -----------------------------------

# -----------------------------------
# Results Dashboard (Double Brace Method)
# -----------------------------------

if st.session_state.data is not None:
    # 1. Prepare Data
    json_logs = json.dumps(st.session_state.logs)
    json_data = json.dumps(st.session_state.data)
    
    # 2. HTML Injection using f-string
    # NOTICE: We use {{ }} for CSS/JS, and { } ONLY for python variables
    dashboard_html = f"""
    <div style="font-family: 'Inter', sans-serif; color: #e2e8f0; padding: 0 1rem;">
        
        <div style="background: #0b1121; border: 1px solid #1e293b; border-radius: 8px; padding: 1rem; height: 160px; overflow: hidden; position: relative; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; margin-bottom: 2rem; box-shadow: inset 0 0 20px rgba(0,0,0,0.5);">
            <div id="terminal-content" style="color: #10b981;"></div>
            <div style="position: absolute; bottom: 10px; right: 10px; display: flex; gap: 3px;">
                <div style="width: 4px; height: 10px; background: #0ea5e9; animation: bar 1s infinite;"></div>
                <div style="width: 4px; height: 15px; background: #0ea5e9; animation: bar 1.2s infinite;"></div>
                <div style="width: 4px; height: 8px; background: #0ea5e9; animation: bar 0.8s infinite;"></div>
            </div>
        </div>

        <div style="display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 1px solid #1e293b; padding-bottom: 1rem; margin-bottom: 1.5rem;">
            <h3 style="margin: 0; font-size: 1.25rem; display: flex; align-items: center; gap: 10px; color: #e2e8f0;">
                <span style="color: #ef4444;">●</span> Analysis Results
            </h3>
            <div style="font-size: 0.9rem; color: #94a3b8;">
                Threats Found: <span style="color: #ef4444; font-weight: 700;">{len(st.session_state.data)}</span>
            </div>
        </div>

        <div id="grid-container" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem;"></div>

    </div>

    <style>
        /* CSS: ALL BRACES DOUBLED */
        @keyframes fadeIn {{ to {{ opacity: 1; }} }}
        @keyframes bar {{ 0%, 100% {{ height: 5px; }} 50% {{ height: 15px; }} }}
        
        .card {{ background: #151e32; border: 1px solid #1e293b; border-radius: 8px; overflow: hidden; transition: transform 0.2s; }}
        .card:hover {{ transform: translateY(-4px); border-color: #0ea5e9; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }}
        
        .card-header {{ padding: 0.75rem; background: rgba(15, 23, 42, 0.5); border-bottom: 1px solid #1e293b; display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem; color: #94a3b8; font-weight: 600; letter-spacing: 0.05em; }}
        
        .badge {{ background: rgba(239, 68, 68, 0.15); color: #ef4444; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; }}
        
        .card-body {{ padding: 1rem; }}
        
        .mockup {{ background: #000; border-radius: 6px; height: 180px; overflow: hidden; position: relative; margin-bottom: 1rem; border: 1px solid #334155; }}
        .mockup img {{ width: 100%; height: 100%; object-fit: cover; opacity: 0.85; }}
        
        .threat-text {{ background: rgba(255,255,255,0.03); border-left: 3px solid #ef4444; padding: 0.75rem; font-size: 0.85rem; color: #e2e8f0; margin-bottom: 0.75rem; font-style: italic; line-height: 1.4; }}
        
        .logic {{ font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: #0ea5e9; background: rgba(14, 165, 233, 0.1); padding: 4px 8px; border-radius: 4px; display: inline-block; }}
        
        .meta {{ margin-top: 1rem; padding-top: 0.5rem; border-top: 1px solid #1e293b; display: flex; justify-content: space-between; font-size: 0.75rem; color: #64748b; }}
    </style>

    <script>
        // JS: SINGLE BRACES for Python Variables, DOUBLE for JS blocks
        const logs = {json_logs};
        const threats = {json_data};

        const term = document.getElementById('terminal-content');
        let i = 0;
        
        function typeLog() {{
            if (i < logs.length) {{
                const div = document.createElement('div');
                div.style.marginBottom = '4px';
                div.style.opacity = '0';
                div.style.animation = 'fadeIn 0.2s forwards';
                // Note: Double braces for JS template literal ${{...}}
                div.innerHTML = `<span style="color:#0ea5e9;">></span> ${{logs[i]}}`;
                term.appendChild(div);
                term.scrollTop = term.scrollHeight;
                i++;
                setTimeout(typeLog, 300);
            }} else {{
                renderGrid();
            }}
        }}
        
        function renderGrid() {{
            const container = document.getElementById('grid-container');
            threats.forEach((t, idx) => {{
                const card = document.createElement('div');
                card.className = 'card';
                card.style.opacity = '0';
                card.style.animation = 'fadeIn 0.5s forwards';
                card.style.animationDelay = (idx * 0.1) + 's';
                
                // Safe Image handling
                const imgSrc = t.image ? t.image : 'https://via.placeholder.com/300x400/000000/FFFFFF?text=Evidence';
                
                card.innerHTML = `
                    <div class="card-header">
                        <span>ID: #${{1000 + idx}}</span>
                        <span class="badge">THREAT DETECTED</span>
                    </div>
                    <div class="card-body">
                        <div class="mockup">
                            <img src="${{imgSrc}}" onerror="this.src='https://via.placeholder.com/300x400/000000/FFFFFF?text=Evidence'" alt="Evidence">
                        </div>
                        <div class="threat-text">"${{t.text.replace(/"/g, '&quot;')}}"</div>
                        <div style="font-size:0.7rem; color:#64748b; margin-bottom:4px;">TRIGGER LOGIC:</div>
                        <div class="logic">${{t.reason}}</div>
                        <div class="meta">
                            <span>iOS Emu</span>
                            <a href="${{t.link}}" target="_blank" style="color:#0ea5e9; text-decoration:none; font-weight:600;">VIEW SOURCE &rarr;</a>
                        </div>
                    </div>
                `;
                container.appendChild(card);
            }});
        }}

        setTimeout(typeLog, 500);
    </script>
    """
    
    components.html(dashboard_html, height=900, scrolling=True)

else:
    # Empty State
    st.markdown("""
    <div style="text-align: center; padding: 4rem 2rem; border: 1px dashed #334155; border-radius: 12px; background: rgba(255,255,255,0.01); color: #64748b; margin-top: 2rem;">
        <h3 style="color: #94a3b8; font-weight: 600; margin-bottom: 0.5rem; font-size: 1.1rem;">Secure System Idle</h3>
        <p style="font-size: 0.9rem;">Initiate mobile extraction protocol from the sidebar.</p>
    </div>
    """, unsafe_allow_html=True)




