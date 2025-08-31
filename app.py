
import streamlit as st
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import folium_static
import re
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
import numpy as np
import streamlit.components.v1 as components
import logging
from psycopg2.pool import SimpleConnectionPool
from functools import lru_cache
import time
import html
from st_aggrid import AgGrid, GridOptionsBuilder
import seaborn as sns
from geopy.distance import geodesic
from scipy import interpolate, stats
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import warnings
from dataclasses import dataclass
from typing import Dict, Any, Optional

warnings.filterwarnings('ignore')

# Set page configuration
st.set_page_config(
    page_title="Marinex - ARGO Data Explorer",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enhanced CSS with Ocean Waves and Yellow-White Floating Buttons
st.markdown("""
<style>
    /* Hide Streamlit UI elements */
    #MainMenu {visibility: hidden;}
    .stDeployButton {display: none;}
    footer {visibility: hidden;}
    .stActionButton {display: none;}
    header {visibility: hidden;}
    .viewerBadge_container__1QSob {display: none;}
    .stAppViewContainer > .main > div {padding-top: 1rem;}
    
    /* Import fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    /* Global styles with ocean background */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        box-sizing: border-box;
    }
    
    /* Ocean wave background */
    body, .stApp {
        background: linear-gradient(180deg, #87CEEB 0%, #4682B4 25%, #1E90FF 50%, #0066CC 75%, #003D82 100%);
        min-height: 100vh;
        position: relative;
        overflow-x: hidden;
    }
    
    /* Animated ocean waves */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 200%;
        height: 100%;
        background: 
            radial-gradient(ellipse 800px 50px at 400px 50px, rgba(255,255,255,0.3), transparent),
            radial-gradient(ellipse 600px 40px at 200px 150px, rgba(255,255,255,0.2), transparent),
            radial-gradient(ellipse 700px 45px at 600px 250px, rgba(255,255,255,0.25), transparent),
            radial-gradient(ellipse 500px 35px at 800px 350px, rgba(255,255,255,0.2), transparent),
            radial-gradient(ellipse 900px 60px at 300px 450px, rgba(255,255,255,0.3), transparent);
        animation: oceanWaves 12s ease-in-out infinite;
        pointer-events: none;
        z-index: -2;
        opacity: 0.6;
    }
    
    @keyframes oceanWaves {
        0%, 100% { 
            transform: translateX(0) translateY(0);
        }
        25% { 
            transform: translateX(-100px) translateY(-20px);
        }
        50% { 
            transform: translateX(-200px) translateY(-40px);
        }
        75% { 
            transform: translateX(-300px) translateY(-20px);
        }
    }
    
    /* Deeper wave layers */
    .stApp::after {
        content: '';
        position: fixed;
        top: 50px;
        left: 0;
        width: 200%;
        height: 100%;
        background: 
            radial-gradient(ellipse 600px 30px at 500px 100px, rgba(255,255,255,0.15), transparent),
            radial-gradient(ellipse 800px 40px at 100px 200px, rgba(255,255,255,0.1), transparent),
            radial-gradient(ellipse 400px 25px at 700px 300px, rgba(255,255,255,0.12), transparent),
            radial-gradient(ellipse 650px 35px at 200px 400px, rgba(255,255,255,0.08), transparent);
        animation: deepWaves 18s ease-in-out infinite reverse;
        pointer-events: none;
        z-index: -3;
        opacity: 0.4;
    }
    
    @keyframes deepWaves {
        0%, 100% { 
            transform: translateX(0) translateY(10px);
        }
        33% { 
            transform: translateX(-150px) translateY(-10px);
        }
        66% { 
            transform: translateX(-250px) translateY(5px);
        }
    }
    
    /* Underwater bubbles */
    .ocean-bubbles {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            radial-gradient(circle 3px at 10% 20%, rgba(255,255,255,0.3), transparent),
            radial-gradient(circle 2px at 80% 30%, rgba(255,255,255,0.2), transparent),
            radial-gradient(circle 4px at 40% 70%, rgba(255,255,255,0.25), transparent),
            radial-gradient(circle 2px at 90% 80%, rgba(255,255,255,0.2), transparent),
            radial-gradient(circle 3px at 20% 90%, rgba(255,255,255,0.3), transparent);
        background-size: 400px 400px, 300px 300px, 500px 500px, 200px 200px, 350px 350px;
        animation: bubbleRise 15s linear infinite;
        pointer-events: none;
        z-index: -1;
    }
    
    @keyframes bubbleRise {
        0% { 
            background-position: 0% 100%, 0% 100%, 0% 100%, 0% 100%, 0% 100%;
            opacity: 0.6;
        }
        50% {
            opacity: 0.8;
        }
        100% { 
            background-position: 100% -100%, -100% -100%, 50% -100%, 200% -100%, -50% -100%;
            opacity: 0.6;
        }
    }
    
    /* Enhanced main header */
    .main-header {
        background: linear-gradient(135deg, rgba(255,215,0,0.9) 0%, rgba(255,255,255,0.8) 50%, rgba(255,235,59,0.9) 100%);
        backdrop-filter: blur(20px);
        padding: 3rem;
        border-radius: 25px;
        margin-bottom: 2rem;
        color: #003D82;
        box-shadow: 0 20px 60px rgba(255, 215, 0, 0.3);
        position: relative;
        overflow: hidden;
        border: 2px solid rgba(255,255,255,0.3);
        animation: headerFloat 6s ease-in-out infinite;
    }
    
    @keyframes headerFloat {
        0%, 100% { 
            transform: translateY(0) rotate(0deg);
            box-shadow: 0 20px 60px rgba(255, 215, 0, 0.3);
        }
        50% { 
            transform: translateY(-10px) rotate(0.5deg);
            box-shadow: 0 30px 80px rgba(255, 215, 0, 0.4);
        }
    }
    
    .header-title {
        font-size: 3.2rem;
        font-weight: 900;
        margin: 0 0 0.5rem 0;
        letter-spacing: -0.03em;
        text-shadow: 0 4px 8px rgba(0,0,0,0.2);
        position: relative;
        color: #003D82;
        animation: titleWave 4s ease-in-out infinite;
    }
    
    @keyframes titleWave {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-5px); }
    }
    
    .header-subtitle {
        font-size: 1.3rem;
        font-weight: 500;
        opacity: 0.8;
        margin: 0;
        color: #004080;
        animation: subtitleFloat 5s ease-in-out infinite;
    }
    
    @keyframes subtitleFloat {
        0%, 100% { transform: translateY(0) translateX(0); }
        33% { transform: translateY(-3px) translateX(2px); }
        66% { transform: translateY(3px) translateX(-2px); }
    }
    
    /* Unified button styling - all buttons same size with yellow-white theme */
    .query-button, 
    .stButton > button, 
    .stDownloadButton > button,
    .sample-query {
        background: linear-gradient(135deg, #FFD700 0%, #FFFFFF 30%, #FFF8DC 60%, #FFEB3B 100%);
        background-size: 300% 300%;
        border: 2px solid rgba(255,215,0,0.4);
        border-radius: 18px;
        padding: 1.2rem 2rem;
        color: #004080;
        font-weight: 700;
        font-size: 1rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        cursor: pointer;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        box-shadow: 0 8px 25px rgba(255, 215, 0, 0.3);
        position: relative;
        overflow: hidden;
        min-height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        animation: buttonFloat 4s ease-in-out infinite;
        backdrop-filter: blur(10px);
    }
    
    @keyframes buttonFloat {
        0%, 100% { 
            transform: translateY(0) rotate(0deg);
            background-position: 0% 50%;
            box-shadow: 0 8px 25px rgba(255, 215, 0, 0.3);
        }
        25% { 
            transform: translateY(-5px) rotate(0.5deg);
            background-position: 50% 0%;
            box-shadow: 0 12px 35px rgba(255, 215, 0, 0.4);
        }
        50% { 
            transform: translateY(-8px) rotate(0deg);
            background-position: 100% 50%;
            box-shadow: 0 15px 40px rgba(255, 215, 0, 0.5);
        }
        75% { 
            transform: translateY(-3px) rotate(-0.5deg);
            background-position: 50% 100%;
            box-shadow: 0 12px 35px rgba(255, 215, 0, 0.4);
        }
    }
    
    /* Wave animation on button surfaces */
    .query-button::before, 
    .stButton > button::before, 
    .stDownloadButton > button::before,
    .sample-query::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(255,255,255,0.4), 
            transparent);
        animation: waveRipple 3s ease-in-out infinite;
        transition: left 0.6s ease;
    }
    
    @keyframes waveRipple {
        0% { left: -100%; }
        50% { left: 0%; }
        100% { left: 100%; }
    }
    
    /* Enhanced hover effects for floating in waves */
    .query-button:hover, 
    .stButton > button:hover, 
    .stDownloadButton > button:hover,
    .sample-query:hover {
        transform: translateY(-12px) scale(1.05) rotate(1deg);
        box-shadow: 0 20px 50px rgba(255, 215, 0, 0.6);
        background: linear-gradient(135deg, #FFEB3B 0%, #FFFFFF 50%, #FFD700 100%);
        border-color: rgba(255,255,255,0.8);
        animation: floatingWave 2s ease-in-out infinite;
    }
    
    @keyframes floatingWave {
        0%, 100% { 
            transform: translateY(-12px) scale(1.05) rotate(1deg);
        }
        50% { 
            transform: translateY(-18px) scale(1.08) rotate(-0.5deg);
        }
    }
    
    .query-button:active, 
    .stButton > button:active, 
    .stDownloadButton > button:active,
    .sample-query:active {
        transform: translateY(-6px) scale(1.02);
        animation: buttonSplash 0.3s ease-out;
    }
    
    @keyframes buttonSplash {
        0% { box-shadow: 0 8px 25px rgba(255, 215, 0, 0.3); }
        50% { box-shadow: 0 15px 40px rgba(255, 255, 255, 0.6); }
        100% { box-shadow: 0 8px 25px rgba(255, 215, 0, 0.3); }
    }
    
    /* Enhanced stats grid - single line layout */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin: 2rem 0;
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 1.5rem;
        color: white;
        border: 2px solid rgba(255,255,255,0.2);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        box-shadow: 0 15px 35px rgba(0,0,0,0.2);
        position: relative;
        overflow: hidden;
        cursor: pointer;
        animation: cardFloat 8s ease-in-out infinite;
        height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    @keyframes cardFloat {
        0%, 100% { 
            transform: translateY(0) rotate(0deg);
        }
        25% { 
            transform: translateY(-8px) rotate(0.5deg);
        }
        50% { 
            transform: translateY(-15px) rotate(0deg);
        }
        75% { 
            transform: translateY(-5px) rotate(-0.5deg);
        }
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 5px;
        background: linear-gradient(90deg, #FFD700, #FFFFFF, #FFEB3B);
        background-size: 200% 100%;
        animation: waveShimmer 4s linear infinite;
    }
    
    @keyframes waveShimmer {
        0% { background-position: 0% 0%; }
        100% { background-position: 200% 0%; }
    }
    
    .metric-card:hover {
        transform: translateY(-15px) scale(1.03) rotate(1deg);
        box-shadow: 0 25px 60px rgba(255, 215, 0, 0.3);
        border-color: rgba(255,255,255,0.5);
        animation: cardWaveFloat 3s ease-in-out infinite;
    }
    
    @keyframes cardWaveFloat {
        0%, 100% { 
            transform: translateY(-15px) scale(1.03) rotate(1deg);
        }
        50% { 
            transform: translateY(-22px) scale(1.05) rotate(-0.5deg);
        }
    }
    
    .metric-label {
        font-size: 0.9rem;
        font-weight: 700;
        color: #E6F3FF;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.6rem;
        transition: color 0.3s ease;
    }
    
    .metric-card:hover .metric-label {
        color: #FFD700;
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 900;
        background: linear-gradient(45deg, #FFD700, #FFFFFF);
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1;
        margin-bottom: 0.5rem;
        text-shadow: 0 4px 8px rgba(0,0,0,0.3);
        transition: transform 0.3s ease;
        animation: valueGlow 3s ease-in-out infinite;
    }
    
    @keyframes valueGlow {
        0%, 100% { filter: brightness(1); }
        50% { filter: brightness(1.2); }
    }
    
    .metric-card:hover .metric-value {
        transform: scale(1.08);
        animation: valueWave 1.5s ease-in-out infinite;
    }
    
    @keyframes valueWave {
        0%, 100% { transform: scale(1.08) translateY(0); }
        50% { transform: scale(1.1) translateY(-3px); }
    }
    
    .metric-description {
        font-size: 0.85rem;
        color: #B3D9FF;
        margin: 0;
        line-height: 1.4;
        transition: color 0.3s ease;
    }
    
    .metric-card:hover .metric-description {
        color: #FFFFFF;
    }
    
    /* Dynamic live indicator with ocean theme */
    .live-indicator {
        display: inline-block;
        width: 14px;
        height: 14px;
        background: radial-gradient(circle, #00FF88, #00CC66);
        border-radius: 50%;
        margin-right: 10px;
        animation: oceanPulse 2.5s ease-in-out infinite;
        box-shadow: 0 0 0 rgba(0, 255, 136, 0.6);
        position: relative;
    }
    
    .live-indicator::after {
        content: '';
        position: absolute;
        top: -3px;
        left: -3px;
        right: -3px;
        bottom: -3px;
        border-radius: 50%;
        background: radial-gradient(circle, transparent 40%, #00FF88 80%);
        animation: oceanRipple 2.5s ease-in-out infinite 0.8s;
    }
    
    @keyframes oceanPulse {
        0% {
            transform: scale(0.9);
            box-shadow: 0 0 0 0 rgba(0, 255, 136, 0.8);
        }
        50% {
            transform: scale(1.2);
            box-shadow: 0 0 0 20px rgba(0, 255, 136, 0);
        }
        100% {
            transform: scale(0.9);
            box-shadow: 0 0 0 0 rgba(0, 255, 136, 0);
        }
    }
    
    @keyframes oceanRipple {
        0% {
            transform: scale(0.5);
            opacity: 1;
        }
        100% {
            transform: scale(2);
            opacity: 0;
        }
    }
    
    /* Sample queries with consistent sizing and wave floating */
    .sample-queries {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1.5rem;
        margin-top: 2rem;
    }
    
    .sample-query {
        height: 100px;
        animation-delay: calc(var(--index, 0) * 0.2s);
    }
    
    .sample-query:nth-child(1) { --index: 0; }
    .sample-query:nth-child(2) { --index: 1; }
    .sample-query:nth-child(3) { --index: 2; }
    .sample-query:nth-child(4) { --index: 3; }
    
    /* Enhanced input fields with ocean theme */
    .query-input {
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(20px);
        border: 2px solid rgba(255,215,0,0.3);
        border-radius: 18px;
        padding: 1.5rem;
        color: white;
        width: 100%;
        margin-bottom: 1.5rem;
        font-size: 1.1rem;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        position: relative;
        animation: inputFloat 6s ease-in-out infinite;
    }
    
    @keyframes inputFloat {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-5px); }
    }
    
    .query-input:focus {
        outline: none;
        border-color: #FFD700;
        box-shadow: 0 0 0 4px rgba(255, 215, 0, 0.25), 0 15px 35px rgba(255,215,0,0.2);
        transform: translateY(-8px) scale(1.02);
        background: rgba(255, 255, 255, 0.25);
    }
    
    .query-input::placeholder {
        color: rgba(255,255,255,0.7);
    }
    
    /* Enhanced panels with ocean glass effect */
    .data-panel {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(25px);
        border-radius: 25px;
        padding: 2.5rem;
        color: white;
        border: 2px solid rgba(255,255,255,0.2);
        margin: 2rem 0;
        box-shadow: 0 20px 50px rgba(0,0,0,0.15);
        position: relative;
        overflow: hidden;
        transition: all 0.4s ease;
        animation: panelFloat 10s ease-in-out infinite;
    }
    
    @keyframes panelFloat {
        0%, 100% { 
            transform: translateY(0) rotate(0deg);
        }
        33% { 
            transform: translateY(-8px) rotate(0.3deg);
        }
        66% { 
            transform: translateY(-12px) rotate(-0.3deg);
        }
    }
    
    .data-panel:hover {
        transform: translateY(-15px) rotate(0.5deg);
        box-shadow: 0 30px 70px rgba(255, 215, 0, 0.2);
        border-color: rgba(255,215,0,0.4);
    }
    
    .panel-title {
        background: linear-gradient(45deg, #FFD700, #FFFFFF);
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 1.6rem;
        font-weight: 800;
        margin-bottom: 2rem;
        border-bottom: 3px solid rgba(255,215,0,0.3);
        padding-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 1rem;
        animation: titleShimmer 4s ease-in-out infinite;
    }
    
    @keyframes titleShimmer {
        0%, 100% { filter: brightness(1); }
        50% { filter: brightness(1.3); }
    }
    
    /* Enhanced tabs with wave theme */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(20px);
        border-bottom: 2px solid rgba(255,215,0,0.3);
        padding: 0.5rem;
        border-radius: 20px 20px 0 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, #FFD700 0%, #FFFFFF 30%, #FFF8DC 60%, #FFEB3B 100%);
        color: #004080;
        border-radius: 15px;
        border: 2px solid rgba(255,215,0,0.4);
        padding: 1rem 2rem;
        font-weight: 700;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        position: relative;
        overflow: hidden;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        min-height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: tabFloat 5s ease-in-out infinite;
    }
    
    @keyframes tabFloat {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-5px); }
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: linear-gradient(135deg, #FFEB3B 0%, #FFFFFF 50%, #FFD700 100%);
        color: #003D82;
        transform: translateY(-8px) scale(1.05);
        box-shadow: 0 15px 35px rgba(255, 215, 0, 0.4);
        animation: tabWaveFloat 2s ease-in-out infinite;
    }
    
    @keyframes tabWaveFloat {
        0%, 100% { 
            transform: translateY(-8px) scale(1.05);
        }
        50% { 
            transform: translateY(-15px) scale(1.08);
        }
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #FFFFFF 0%, #FFD700 50%, #FFEB3B 100%);
        color: #003D82;
        border-color: #FFD700;
        transform: translateY(-10px);
        box-shadow: 0 20px 45px rgba(255, 215, 0, 0.5);
        animation: activeTabWave 3s ease-in-out infinite;
    }
    
    @keyframes activeTabWave {
        0%, 100% { 
            transform: translateY(-10px) rotate(0deg);
            box-shadow: 0 20px 45px rgba(255, 215, 0, 0.5);
        }
        50% { 
            transform: translateY(-18px) rotate(0.5deg);
            box-shadow: 0 25px 55px rgba(255, 215, 0, 0.7);
        }
    }
    
    /* Enhanced cesium container */
    .cesium-container {
        height: 650px;
        border-radius: 25px;
        overflow: hidden;
        box-shadow: 0 25px 70px rgba(0,0,0,0.3);
        border: 3px solid rgba(255,215,0,0.4);
        background: rgba(0, 0, 0, 0.1);
        margin: 2rem 0;
        position: relative;
        transition: all 0.4s ease;
        animation: containerFloat 15s ease-in-out infinite;
    }
    
    @keyframes containerFloat {
        0%, 100% { 
            transform: translateY(0) rotate(0deg);
        }
        33% { 
            transform: translateY(-12px) rotate(0.3deg);
        }
        66% { 
            transform: translateY(-20px) rotate(-0.3deg);
        }
    }
    
    .cesium-container:hover {
        transform: translateY(-25px) scale(1.02);
        box-shadow: 0 35px 90px rgba(255, 215, 0, 0.3);
        border-color: #FFD700;
    }
    
    /* Enhanced chat interface */
    .chat-interface {
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(25px);
        border-radius: 25px;
        padding: 2.5rem;
        margin: 2.5rem 0;
        border: 2px solid rgba(255,215,0,0.3);
        color: white;
        box-shadow: 0 20px 60px rgba(0,0,0,0.2);
        position: relative;
        overflow: hidden;
        animation: chatFloat 9s ease-in-out infinite;
    }
    
    @keyframes chatFloat {
        0%, 100% { 
            transform: translateY(0) rotate(0deg);
        }
        50% { 
            transform: translateY(-12px) rotate(0.3deg);
        }
    }
    
    /* Split screen layout */
    .split-container {
        display: flex;
        gap: 2rem;
        margin: 2rem 0;
    }
    
    .globe-section {
        flex: 3;
        min-width: 0;
    }
    
    .chat-section {
        flex: 2;
        min-width: 0;
    }
    
    .square-globe {
        width: 100%;
        aspect-ratio: 1 / 1;
        border-radius: 25px;
        overflow: hidden;
        box-shadow: 0 25px 70px rgba(0,0,0,0.3);
        border: 3px solid rgba(255,215,0,0.4);
    }
</style>
""", unsafe_allow_html=True)

# Database configuration
DB_CONFIGS = [
    # Primary pooled connection
    {
        "host": "ep-still-field-a17hi4xm-pooler.ap-southeast-1.aws.neon.tech",
        "database": "neondb",
        "user": "neondb_owner",
        "password": "npg_qV9a3dQRAeBm",
        "port": "5432",
        "sslmode": "require"
    },
    # Alternative direct connection
    {
        "host": "ep-still-field-a17hi4xm.ap-southeast-1.aws.neon.tech",
        "database": "neondb",
        "user": "neondb_owner",
        "password": "npg_qV9a3dQRAeBm",
        "port": "5432",
        "sslmode": "require"
    }
]

# Use the first config as default
DB_CONFIG = DB_CONFIGS[0]

# Reference coordinates for major locations
REFERENCE_LOCATIONS = {
    "Chennai": (13.0827, 80.2707),
    "Mumbai": (19.0760, 72.8777),
    "Kochi": (9.9312, 76.2673),
    "Kolkata": (22.5726, 88.3639),
    "Visakhapatnam": (17.6868, 83.2185),
    "Bengaluru": (12.9716, 77.5946),
    "Arabian Sea": (15.0, 65.0),
    "Bay of Bengal": (15.0, 87.0),
    "Indian Ocean": (-20.0, 80.0),
    "Equator": (0.0, 80.0),
    "Maldives": (3.2028, 73.2207),
    "Sri Lanka": (7.8731, 80.7718)
}

@dataclass
class OceanographicAnalysis:
    """Class to hold oceanographic analysis results"""
    mixed_layer_depth: Optional[float] = None
    thermocline_depth: Optional[float] = None
    halocline_depth: Optional[float] = None
    temperature_gradient: Optional[float] = None
    salinity_gradient: Optional[float] = None
    water_mass_classification: Optional[str] = None

class ArgoAIIntelligence:
    def __init__(self):
        self.db_connection = None
        
        # Enhanced schema with oceanographic context
        self.schema_info = """
        ARGO Floats Database Schema:
        
        Table: argo_floats
        Core Columns:
        - platform_number (integer): Unique ARGO float identifier
        - cycle_number (integer): Profile cycle number
        - measurement_time (timestamp): UTC measurement time
        - latitude (float): Decimal degrees (-90 to 90)
        - longitude (float): Decimal degrees (-180 to 180)
        - pressure (float): Water pressure in decibars (dbar)
        - temperature (float): In-situ temperature in Celsius
        - salinity (float): Practical Salinity Units (PSU)
        - data_quality (text): Quality control flag
        
        Oceanographic Context:
        - Indian Ocean coverage with 85 active floats
        - Depth profiles from surface to ~2000m
        - Temperature range: ~15-35°C
        - Salinity range: ~33-37 PSU
        - Mixed layer depth typically 20-100m
        - Thermocline at 100-500m depth
        """

    def connect_db(self) -> bool:
        """Establish database connection"""
        try:
            if self.db_connection is None or self.db_connection.closed:
                self.db_connection = psycopg2.connect(**DB_CONFIG)
            return True
        except Exception as e:
            st.error(f"Database connection failed: {str(e)}")
            return False

    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute SQL query and return DataFrame"""
        try:
            if self.connect_db():
                df = pd.read_sql_query(query, self.db_connection)
                return df
        except Exception as e:
            st.error(f"Query execution failed: {str(e)}")
            return pd.DataFrame()

    def advanced_nlp_to_sql(self, user_query: str, api_key: str = None) -> Dict[str, Any]:
        """Advanced natural language to SQL with pattern matching"""
        
        # Enhanced pattern matching with oceanographic domain knowledge
        patterns = {
            # Location-based queries
            r"(?:nearest|closest|near)\s+(?:to\s+)?(.+)": self._handle_location_query,
            r"floats?\s+(?:in|around|near)\s+(.+)": self._handle_area_query,
            
            # Oceanographic analysis
            r"(?:t-s|temperature.salinity)\s+diagram": self._handle_ts_diagram,
            r"(?:mixed\s+layer|mld)\s+depth": self._handle_mixed_layer_depth,
            r"(?:depth\s+profile|vertical\s+profile)": self._handle_depth_profile,
            r"(?:thermocline|halocline)": self._handle_cline_analysis,
            r"water\s+mass": self._handle_water_mass,
            
            # Temporal queries
            r"(?:seasonal|monthly)\s+(?:trend|cycle|variation)": self._handle_seasonal_analysis,
            r"(?:recent|latest|last\s+\d+)\s+(?:days?|weeks?|months?)": self._handle_recent_data,
            r"(?:compare|comparison)\s+.*(?:between|vs)": self._handle_comparison,
            
            # Parameter-based queries
            r"temperature\s+(?:above|greater than|>)\s+([\d.]+)": self._handle_temp_threshold,
            r"temperature\s+(?:below|less than|<)\s+([\d.]+)": self._handle_temp_threshold,
            r"salinity\s+(?:above|greater than|>)\s+([\d.]+)": self._handle_sal_threshold,
            r"salinity\s+(?:below|less than|<)\s+([\d.]+)": self._handle_sal_threshold,
            
            # Statistical queries
            r"(?:statistics|stats|summary)": self._handle_statistics,
            r"(?:correlation|relationship)\s+between": self._handle_correlation,
            
            # Default patterns
            r"(?:show|display|get|find)\s+all\s+floats?": lambda x: self._get_all_floats_query(),
            r"(?:count|how many)\s+floats?": lambda x: "SELECT COUNT(DISTINCT platform_number) as total_floats FROM argo_floats;",
        }
        
        query_lower = user_query.lower().strip()
        sql_query = None
        analysis_type = "general"
        
        # Try pattern matching
        for pattern, handler in patterns.items():
            match = re.search(pattern, query_lower)
            if match:
                if callable(handler):
                    result = handler(match.groups()[0] if match.groups() else None)
                    if isinstance(result, dict):
                        sql_query = result.get('sql', '')
                        analysis_type = result.get('type', 'general')
                    else:
                        sql_query = result
                        analysis_type = pattern.split(r"\s+")[0] if r"\s+" in pattern else "general"
                break
        
        # Fallback for API-based generation
        if not sql_query and api_key:
            sql_query = self._generate_with_openai(user_query, api_key)
        
        # Final fallback
        if not sql_query:
            sql_query = "SELECT * FROM argo_floats ORDER BY measurement_time DESC LIMIT 20;"
            analysis_type = "general"
        
        return {
            "sql": sql_query,
            "analysis_type": analysis_type,
            "query_interpretation": self._interpret_query(user_query, analysis_type)
        }

    def _handle_location_query(self, location: str) -> Dict[str, Any]:
        """Handle location-based queries with proper geodesic distance calculation"""
        location_clean = location.strip().title()
        
        if location_clean in REFERENCE_LOCATIONS:
            lat, lon = REFERENCE_LOCATIONS[location_clean]
            
            # Use the Haversine formula for accurate distance calculation
            sql = f"""
            SELECT 
                platform_number, 
                latitude, 
                longitude, 
                temperature, 
                salinity,
                pressure,
                measurement_time,
                -- Haversine formula for accurate distance in km
                6371 * 2 * ASIN(SQRT(
                    POWER(SIN(RADIANS(latitude - {lat}) / 2), 2) +
                    COS(RADIANS({lat})) * COS(RADIANS(latitude)) *
                    POWER(SIN(RADIANS(longitude - {lon}) / 2), 2)
                )) as distance_km
            FROM argo_floats 
            ORDER BY distance_km ASC 
            LIMIT 20;
            """
            return {"sql": sql, "type": "location_analysis"}
        
        return {"sql": "SELECT * FROM argo_floats LIMIT 20;", "type": "general"}

    def _handle_area_query(self, location: str) -> Dict[str, Any]:
        """Handle area-based queries"""
        return self._handle_location_query(location)

    def _handle_ts_diagram(self, _) -> Dict[str, Any]:
        """Handle T-S diagram requests"""
        sql = """
        SELECT 
            platform_number,
            temperature,
            salinity,
            pressure,
            latitude,
            longitude,
            measurement_time
        FROM argo_floats 
        WHERE temperature IS NOT NULL 
        AND salinity IS NOT NULL
        ORDER BY platform_number, pressure;
        """
        return {"sql": sql, "type": "ts_diagram"}

    def _handle_mixed_layer_depth(self, _) -> Dict[str, Any]:
        """Handle mixed layer depth analysis"""
        sql = """
        WITH depth_profiles AS (
            SELECT 
                platform_number,
                cycle_number,
                pressure as depth,
                temperature,
                salinity,
                ROW_NUMBER() OVER (PARTITION BY platform_number, cycle_number ORDER BY pressure) as depth_rank
            FROM argo_floats
            WHERE pressure <= 200  -- Focus on upper ocean
            AND temperature IS NOT NULL
        )
        SELECT * FROM depth_profiles
        ORDER BY platform_number, cycle_number, depth;
        """
        return {"sql": sql, "type": "mixed_layer_depth"}

    def _handle_depth_profile(self, _) -> Dict[str, Any]:
        """Handle depth profile visualization"""
        sql = """
        SELECT 
            platform_number,
            cycle_number,
            pressure as depth,
            temperature,
            salinity,
            measurement_time,
            latitude,
            longitude
        FROM argo_floats
        ORDER BY platform_number, cycle_number, pressure;
        """
        return {"sql": sql, "type": "depth_profile"}

    def _handle_cline_analysis(self, _) -> Dict[str, Any]:
        """Handle thermocline/halocline analysis"""
        return self._handle_depth_profile(_)

    def _handle_water_mass(self, _) -> Dict[str, Any]:
        """Handle water mass identification"""
        return self._handle_ts_diagram(_)

    def _handle_seasonal_analysis(self, _) -> Dict[str, Any]:
        """Handle seasonal trend analysis"""
        sql = """
        SELECT 
            EXTRACT(MONTH FROM measurement_time) as month,
            EXTRACT(YEAR FROM measurement_time) as year,
            platform_number,
            AVG(temperature) as avg_temperature,
            AVG(salinity) as avg_salinity,
            COUNT(*) as measurements,
            AVG(latitude) as avg_lat,
            AVG(longitude) as avg_lon
        FROM argo_floats
        GROUP BY year, month, platform_number
        ORDER BY year, month, platform_number;
        """
        return {"sql": sql, "type": "seasonal_analysis"}

    def _handle_recent_data(self, _) -> Dict[str, Any]:
        """Handle recent data queries"""
        sql = """
        SELECT * FROM argo_floats 
        WHERE measurement_time >= CURRENT_DATE - INTERVAL '30 days'
        ORDER BY measurement_time DESC
        LIMIT 50;
        """
        return {"sql": sql, "type": "recent_data"}

    def _handle_comparison(self, _) -> Dict[str, Any]:
        """Handle comparison queries"""
        return self._handle_seasonal_analysis(_)

    def _handle_temp_threshold(self, temp: str) -> Dict[str, Any]:
        """Handle temperature threshold queries"""
        try:
            temp_val = float(temp)
            sql = f"SELECT * FROM argo_floats WHERE temperature > {temp_val} ORDER BY temperature DESC LIMIT 50;"
            return {"sql": sql, "type": "temperature_analysis"}
        except:
            return {"sql": "SELECT * FROM argo_floats WHERE temperature > 25 ORDER BY temperature DESC LIMIT 50;", "type": "temperature_analysis"}

    def _handle_sal_threshold(self, sal: str) -> Dict[str, Any]:
        """Handle salinity threshold queries"""
        try:
            sal_val = float(sal)
            sql = f"SELECT * FROM argo_floats WHERE salinity > {sal_val} ORDER BY salinity DESC LIMIT 50;"
            return {"sql": sql, "type": "salinity_analysis"}
        except:
            return {"sql": "SELECT * FROM argo_floats WHERE salinity > 35 ORDER BY salinity DESC LIMIT 50;", "type": "salinity_analysis"}

    def _handle_statistics(self, _) -> Dict[str, Any]:
        """Handle statistical summary requests"""
        sql = """
        SELECT 
            COUNT(DISTINCT platform_number) as unique_floats,
            COUNT(*) as total_measurements,
            AVG(temperature) as mean_temperature,
            STDDEV(temperature) as std_temperature,
            MIN(temperature) as min_temperature,
            MAX(temperature) as max_temperature,
            AVG(salinity) as mean_salinity,
            STDDEV(salinity) as std_salinity,
            MIN(salinity) as min_salinity,
            MAX(salinity) as max_salinity,
            AVG(pressure) as mean_pressure,
            MAX(pressure) as max_pressure,
            MIN(measurement_time) as earliest_measurement,
            MAX(measurement_time) as latest_measurement
        FROM argo_floats;
        """
        return {"sql": sql, "type": "statistics"}

    def _handle_correlation(self, _) -> Dict[str, Any]:
        """Handle correlation analysis"""
        sql = """
        SELECT temperature, salinity, pressure, latitude, longitude 
        FROM argo_floats 
        WHERE temperature IS NOT NULL AND salinity IS NOT NULL;
        """
        return {"sql": sql, "type": "correlation"}

    def _get_all_floats_query(self) -> str:
        """Get all floats query"""
        return "SELECT DISTINCT platform_number, AVG(latitude) as avg_lat, AVG(longitude) as avg_lon FROM argo_floats GROUP BY platform_number ORDER BY platform_number;"

    def _generate_with_openai(self, query: str, api_key: str) -> str:
        """Generate SQL using OpenAI API"""
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            prompt = f"""
            You are an expert oceanographer and SQL developer. Generate a PostgreSQL query for ARGO float data.

            Database Schema:
            {self.schema_info}

            User Query: "{query}"

            Generate a SQL query that:
            1. Answers the user's question accurately
            2. Uses proper oceanographic terminology
            3. Includes relevant columns for visualization
            4. Handles NULL values appropriately
            5. Uses appropriate LIMIT clauses for performance

            Return only the SQL query, no explanations.
            """
            
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 300,
                "temperature": 0.3
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content'].strip()
            else:
                st.warning(f"OpenAI API error: {response.status_code}")
                
        except Exception as e:
            st.warning(f"AI query generation failed: {e}")
        
        return "SELECT * FROM argo_floats ORDER BY measurement_time DESC LIMIT 20;"

    def _interpret_query(self, query: str, analysis_type: str) -> str:
        """Provide human-readable interpretation of the query"""
        interpretations = {
            "location_analysis": f"Finding ARGO floats nearest to the specified location with distance calculations.",
            "ts_diagram": "Generating Temperature-Salinity diagram data for water mass analysis.",
            "mixed_layer_depth": "Analyzing mixed layer depth from temperature and salinity profiles.",
            "depth_profile": "Creating vertical ocean profiles showing temperature and salinity vs depth.",
            "seasonal_analysis": "Examining seasonal trends and cycles in oceanographic parameters.",
            "statistics": "Computing comprehensive statistical summary of all ARGO float measurements.",
            "general": f"Processing general query: {query}"
        }
        
        return interpretations.get(analysis_type, f"Analyzing: {query}")

    def create_ts_diagram(self, df: pd.DataFrame) -> go.Figure:
        """Create Temperature-Salinity diagram"""
        if df.empty or 'temperature' not in df.columns or 'salinity' not in df.columns:
            return go.Figure().add_annotation(text="No T-S data available", 
                                            xref="paper", yref="paper", 
                                            x=0.5, y=0.5, showarrow=False)
        
        fig = go.Figure()
        
        # Color by depth (pressure)
        if 'pressure' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['salinity'],
                y=df['temperature'],
                mode='markers',
                marker=dict(
                    size=4,
                    color=df['pressure'],
                    colorscale='Viridis',
                    colorbar=dict(title="Pressure (dbar)"),
                    opacity=0.7
                ),
                text=df.apply(lambda row: f"Float: {row.get('platform_number', 'N/A')}<br>"
                                        f"Depth: {row.get('pressure', 'N/A')} dbar<br>"
                                        f"T: {row['temperature']:.2f}°C<br>"
                                        f"S: {row['salinity']:.2f} PSU", axis=1),
                hovertemplate="%{text}<extra></extra>",
                name="T-S Data"
            ))
        else:
            fig.add_trace(go.Scatter(
                x=df['salinity'],
                y=df['temperature'],
                mode='markers',
                marker=dict(size=4, opacity=0.7),
                name="T-S Data"
            ))
        
        fig.update_layout(
            title="Temperature-Salinity Diagram",
            xaxis_title="Salinity (PSU)",
            yaxis_title="Temperature (°C)",
            hovermode='closest',
            template='plotly_white'
        )
        
        return fig

    def create_depth_profile(self, df: pd.DataFrame) -> go.Figure:
        """Create depth profile visualization"""
        if df.empty:
            return go.Figure()
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Temperature Profile', 'Salinity Profile'),
            shared_yaxes=True
        )
        
        # Group by float and cycle
        colors = px.colors.qualitative.Set3
        color_idx = 0
        
        for (platform, cycle), group in df.groupby(['platform_number', 'cycle_number']):
            if color_idx > 20:  # Limit number of profiles for readability
                break
                
            group = group.sort_values('pressure')
            color = colors[color_idx % len(colors)]
            
            if 'temperature' in group.columns:
                fig.add_trace(
                    go.Scatter(
                        x=group['temperature'],
                        y=-group['pressure'],  # Negative for depth
                        mode='lines+markers',
                        name=f"Float {platform} Cycle {cycle}",
                        line=dict(color=color),
                        showlegend=(color_idx < 10)  # Only show legend for first 10
                    ),
                    row=1, col=1
                )
            
            if 'salinity' in group.columns:
                fig.add_trace(
                    go.Scatter(
                        x=group['salinity'],
                        y=-group['pressure'],
                        mode='lines+markers',
                        name=f"Float {platform} Cycle {cycle}",
                        line=dict(color=color),
                        showlegend=False
                    ),
                    row=1, col=2
                )
            
            color_idx += 1
        
        fig.update_xaxes(title_text="Temperature (°C)", row=1, col=1)
        fig.update_xaxes(title_text="Salinity (PSU)", row=1, col=2)
        fig.update_yaxes(title_text="Depth (m)", row=1, col=1)
        
        fig.update_layout(
            title="Ocean Depth Profiles",
            height=600,
            hovermode='closest'
        )
        
        return fig

# Database connection pool with better error handling
@st.cache_resource
def init_db_pool():
    try:
        # Try the pooled connection first
        pool = SimpleConnectionPool(
            1, 10,
            "postgresql://neondb_owner:npg_qV9a3dQRAeBm@ep-still-field-a17hi4xm-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
        )
        
        # Test the connection
        conn = pool.getconn()
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        cursor.close()
        pool.putconn(conn)
        
        logger.info("Database connection pool established successfully")
        return pool
        
    except Exception as e:
        logger.warning(f"Database connection pool failed: {e}. Using fallback connection.")
        
        # Try direct connection as fallback
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            conn.close()
            logger.info("Direct database connection successful")
            # Create a simple pool wrapper for direct connections
            return SimpleDirectConnectionPool(DB_CONFIG)
        except Exception as direct_error:
            logger.error(f"Direct connection also failed: {direct_error}. Using sample data.")
            st.warning("Database connection unavailable. Using sample data for demonstration.")
            return None

# Fallback connection pool class for direct connections
class SimpleDirectConnectionPool:
    def __init__(self, db_config):
        self.db_config = db_config
        self.connections = 0
        self.max_connections = 5
    
    def getconn(self):
        if self.connections >= self.max_connections:
            raise Exception("Connection limit reached")
        self.connections += 1
        return psycopg2.connect(**self.db_config)
    
    def putconn(self, conn):
        conn.close()
        self.connections -= 1

# Sample ARGO float data
@st.cache_data
def get_sample_argo_data():
    np.random.seed(42)
    
    # Indian Ocean focused data
    indian_ocean_floats = [
        {'id': '2902755', 'lat': 15.234, 'lon': 68.456, 'temp': 28.5, 'salinity': 35.2, 'depth': 1847, 'status': 'Active'},
        {'id': '2902756', 'lat': 12.891, 'lon': 72.123, 'temp': 29.1, 'salinity': 34.8, 'depth': 1923, 'status': 'Active'},
        {'id': '2902757', 'lat': 8.567, 'lon': 76.789, 'temp': 30.2, 'salinity': 34.5, 'depth': 1756, 'status': 'Active'},
        {'id': '2902758', 'lat': 18.234, 'lon': 84.567, 'temp': 27.8, 'salinity': 35.6, 'depth': 1998, 'status': 'Active'},
        {'id': '2902759', 'lat': 5.789, 'lon': 80.123, 'temp': 31.1, 'salinity': 34.2, 'depth': 1678, 'status': 'Active'},
        {'id': '2902760', 'lat': 22.456, 'lon': 88.789, 'temp': 26.5, 'salinity': 35.8, 'depth': 2034, 'status': 'Active'},
        {'id': '2902761', 'lat': 13.678, 'lon': 65.234, 'temp': 28.9, 'salinity': 35.1, 'depth': 1845, 'status': 'Active'},
        {'id': '2902762', 'lat': 9.345, 'lon': 79.567, 'temp': 29.8, 'salinity': 34.6, 'depth': 1712, 'status': 'Active'},
    ]
    
    # Create expanded dataset
    all_floats = []
    base_time = datetime.now()
    
    for i, float_data in enumerate(indian_ocean_floats):
        for cycle in range(1, 51):  # 50 cycles per float
            measurement_time = base_time - timedelta(days=np.random.randint(0, 365))
            
            all_floats.append({
                'platform_number': float_data['id'],
                'cycle_number': cycle,
                'measurement_time': measurement_time,
                'latitude': float_data['lat'] + np.random.normal(0, 0.1),
                'longitude': float_data['lon'] + np.random.normal(0, 0.1),
                'pressure': np.random.uniform(0, float_data['depth']),
                'temperature': float_data['temp'] + np.random.normal(0, 2),
                'salinity': float_data['salinity'] + np.random.normal(0, 0.5),
                'region': 'Indian Ocean'
            })
    
    return pd.DataFrame(all_floats)

# Database connection function with connection pool and retry logic
def get_db_connection():
    pool = init_db_pool()
    if pool is None:
        return None
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            conn = pool.getconn()
            # Test the connection
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            cursor.close()
            return conn
        except Exception as e:
            logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                logger.error(f"All connection attempts failed: {e}")
                st.warning(f"Database connection failed: {e}. Using sample data.")
                return None
            time.sleep(1)  # Wait before retrying
    
    return None

# Enhanced Cesium component with proper configuration
def create_enhanced_cesium_map(df=None, highlight_city=None):
    """Create Cesium map with ARGO float locations"""
    # Get all float locations if no specific data provided
    if df is None:
        float_locations = get_all_float_locations()
    else:
        float_locations = df
    
    # Prepare data for Cesium
    float_data_for_cesium = []
    
    for _, row in float_locations.iterrows():
        float_data_for_cesium.append({
            'id': row['platform_number'],
            'lat': row['latitude'],
            'lon': row['longitude'],
            'temp': round(row['temperature'], 1) if pd.notna(row['temperature']) else 'N/A',
            'salinity': round(row['salinity'], 1) if pd.notna(row['salinity']) else 'N/A'
        })
    
    # Set initial camera position - default to Indian Ocean overview
    center_lon, center_lat = 75.0, 15.0
    camera_height = 8000000.0
    
    # If a specific city is highlighted and exists in reference locations, center on it
    if highlight_city and 'REFERENCE_LOCATIONS' in globals() and highlight_city in REFERENCE_LOCATIONS:
        try:
            center_lat, center_lon = REFERENCE_LOCATIONS[highlight_city]
            camera_height = 2000000.0  # Zoom in closer for city view
        except (KeyError, TypeError, ValueError):
            # Fall back to default if there's any issue with city coordinates
            center_lon, center_lat = 75.0, 15.0
            camera_height = 8000000.0
    
    cesium_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cesium.com/downloads/cesiumjs/releases/1.95/Build/Cesium/Cesium.js"></script>
        <link href="https://cesium.com/downloads/cesiumjs/releases/1.95/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
        <style>
            html, body, #cesiumContainer {{
                width: 100%; height: 100%; margin: 0; padding: 0; overflow: hidden;
                font-family: 'Inter', sans-serif;
                background: #1a1a1a;
            }}
            .cesium-widget-credits {{ display: none !important; }}
            .cesium-infoBox-description {{
                font-family: 'Inter', sans-serif;
            }}
        </style>
    </head>
    <body>
        <div id="cesiumContainer"></div>
        
        <script>
            // Set your Cesium Ion token - REPLACE WITH YOUR ACTUAL TOKEN
            Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI3YTEzNTA0Yy0zYTQ5LTRiNDktYjNlOC03Y2ZkMTVkZDYyZjgiLCJpZCI6MzM2ODU4LCJpYXQiOjE3NTY2MTYxMjZ9.0vZQSC8KBvZBEHEleN_4V7T4CMYcyRQz4M5dZm4bARo';
            
            // Add error handling for initialization
            try {{
                // Initialize viewer with minimal configuration for reliability
                const viewer = new Cesium.Viewer('cesiumContainer', {{
                    terrainProvider: Cesium.createWorldTerrain(),
                    baseLayerPicker: false,
                    geocoder: false,
                    homeButton: false,
                    sceneModePicker: false,
                    navigationHelpButton: false,
                    animation: false,
                    timeline: false,
                    fullscreenButton: false,
                    infoBox: false,
                    selectionIndicator: false
                }});
                
                // Ensure globe lighting is enabled
                viewer.scene.globe.enableLighting = true;
                
                // Ensure globe lighting is enabled
                viewer.scene.globe.enableLighting = true;
                
                // Disable all default click-to-zoom behaviors
                viewer.cesiumWidget.screenSpaceEventHandler.removeInputAction(Cesium.ScreenSpaceEventType.LEFT_DOUBLE_CLICK);
                viewer.cesiumWidget.screenSpaceEventHandler.removeInputAction(Cesium.ScreenSpaceEventType.LEFT_CLICK);
                
                // Disable entity tracking
                viewer.trackedEntityChanged.addEventListener(function() {{
                    viewer.trackedEntity = undefined;
                }});
                // Set initial view to show the region
                viewer.camera.setView({{
                    destination: Cesium.Cartesian3.fromDegrees({center_lon}, {center_lat}, {camera_height}),
                    orientation: {{
                        heading: 0,
                        pitch: -1.57,  // Less steep angle than -1.57
                        roll: 0
                    }}
                }});
                
                // Add major city labels for reference (only if highlighting a city)
                {f'''
                const majorCities = [
                    {{name: "Mumbai", lon: 72.8777, lat: 19.0760}},
                    {{name: "Chennai", lon: 80.2707, lat: 13.0827}},
                    {{name: "Kolkata", lon: 88.3639, lat: 22.5726}},
                    {{name: "Hyderabad", lon: 78.4867, lat: 17.3850}},
                    {{name: "Bengaluru", lon: 77.5946, lat: 12.9716}},
                    {{name: "Visakhapatnam", lon: 83.2185, lat: 17.6868}},
                    {{name: "Kochi", lon: 76.2673, lat: 9.9312}},
                    {{name: "Arabian Sea", lon: 65.0, lat: 15.0}},
                    {{name: "Bay of Bengal", lon: 87.0, lat: 15.0}},
                    {{name: "Maldives", lon: 73.2207, lat: 3.2028}},
                    {{name: "Sri Lanka", lon: 80.7718, lat: 7.8731}}
                ];
                
                // Add city labels with special highlighting for the searched city
                majorCities.forEach(city => {{
                    const isHighlighted = city.name === "{highlight_city if highlight_city else ''}";
                    viewer.entities.add({{
                        position: Cesium.Cartesian3.fromDegrees(city.lon, city.lat),
                        label: {{
                            text: city.name,
                            font: isHighlighted ? 'bold 16pt Inter, sans-serif' : '14pt Inter, sans-serif',
                            fillColor: isHighlighted ? Cesium.Color.YELLOW : Cesium.Color.WHITE,
                            outlineColor: Cesium.Color.BLACK,
                            outlineWidth: 2,
                            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                            pixelOffset: new Cesium.Cartesian2(0, 20),
                            heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
                            distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0.0, 2000000.0)
                        }},
                        point: isHighlighted ? {{
                            pixelSize: 15,
                            color: Cesium.Color.YELLOW,
                            outlineColor: Cesium.Color.BLACK,
                            outlineWidth: 2
                        }} : null
                    }});
                }});
                ''' if highlight_city else '// No city highlighting requested'}
                
                // Float data from Python
                const floatData = {json.dumps(float_data_for_cesium)};
                
                // Only add floats if we have data
                if (floatData && floatData.length > 0) {{
                    // Batch create entities for better performance
                    const dataSource = new Cesium.CustomDataSource('floats');
                    viewer.dataSources.add(dataSource);
                    
                    floatData.forEach(floatItem => {{
                        const position = Cesium.Cartesian3.fromDegrees(floatItem.lon, floatItem.lat);
                        
                        const entity = dataSource.entities.add({{
                            position: position,
                            point: {{
                                pixelSize: 10,
                                color: Cesium.Color.fromCssColorString('#ff8c42'),
                                outlineColor: Cesium.Color.WHITE,
                                outlineWidth: 2,
                                heightReference: Cesium.HeightReference.CLAMP_TO_GROUND
                            }},
                            label: {{
                                text: floatItem.id,
                                font: '12pt Inter, sans-serif',
                                pixelOffset: new Cesium.Cartesian2(0, -20),
                                fillColor: Cesium.Color.WHITE,
                                outlineColor: Cesium.Color.BLACK,
                                outlineWidth: 2,
                                style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                                heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
                                distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0.0, 500000.0),
                                scale: 0.5,
                                translucencyByDistance: new Cesium.NearFarScalar(100000, 1.0, 500000, 0.2)
                            }},
                            description: `
                                <div style="font-family: 'Inter', sans-serif; min-width: 200px;">
                                    <b>Float ${{floatItem.id}}</b><br>
                                    <hr style="margin: 5px 0;">
                                    <b>Temperature:</b> ${{floatItem.temp}}°C<br>
                                    <b>Salinity:</b> ${{floatItem.salinity}} PSU<br>
                                    <b>Position:</b> ${{floatItem.lat.toFixed(3)}}, ${{floatItem.lon.toFixed(3)}}
                                </div>
                            `
                        }});
                    }});
                    
                    // Add click event to zoom to float
                    viewer.selectedEntityChanged.addEventListener(function(entity) {{
                        if (Cesium.defined(entity) && entity.point) {{ // Only handle float entities
                            viewer.trackedEntity = entity;
                            
                            // Fly to the selected entity with a smooth animation
                            viewer.camera.flyTo({{
                                destination: entity.position.getValue(viewer.clock.currentTime),
                                duration: 1.0,
                                offset: {{
                                    heading: 0,
                                    pitch: -1.57,
                                    range: 100000.0
                                }}
                            }});
                        }}
                    }});
                    
                    // Add event listener for camera changes to dynamically adjust label visibility
                    viewer.camera.moveEnd.addEventListener(function() {{
                        const cameraHeight = viewer.camera.positionCartographic.height;
                        
                        // Adjust label visibility based on camera height
                        dataSource.entities.values.forEach(function(entity) {{
                            if (entity.label) {{
                                // Show labels when zoomed in (camera height less than 1,000,000 meters)
                                const showLabels = cameraHeight < 1000000;
                                entity.label.show = showLabels;
                                
                                // Adjust label scale based on zoom level
                                if (showLabels) {{
                                    const scale = Math.max(0.3, Math.min(1.0, 1000000 / cameraHeight));
                                    entity.label.scale = scale;
                                }}
                            }}
                        }});
                    }});
                }} else {{
                    console.log('No float data available to display');
                }}
                
            }} catch (error) {{
                console.error('Error initializing Cesium viewer:', error);
                document.getElementById('cesiumContainer').innerHTML = 
                    '<div style="color: white; padding: 20px; text-align: center;">Error loading 3D globe. Please check your internet connection and Cesium Ion token.</div>';
            }}
        </script>
    </body>
    </html>
    """
    return cesium_html

def get_all_float_locations():
    """Fetch all float locations from the database"""
    conn = get_db_connection()
    if conn is None:
        # Return sample data if DB connection fails
        sample_data = get_sample_argo_data()
        latest_positions = sample_data.groupby('platform_number').last().reset_index()
        return latest_positions[['platform_number', 'latitude', 'longitude', 'temperature', 'salinity']]
    
    try:
        # Query to get the latest position for each float
        query = """
        SELECT DISTINCT ON (platform_number) 
            platform_number, latitude, longitude, temperature, salinity
        FROM argo_floats 
        ORDER BY platform_number, measurement_time DESC
        """
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        logger.error(f"Error fetching float locations: {e}")
        st.error(f"Error fetching float locations: {e}")
        # Return sample data as fallback
        sample_data = get_sample_argo_data()
        latest_positions = sample_data.groupby('platform_number').last().reset_index()
        return latest_positions[['platform_number', 'latitude', 'longitude', 'temperature', 'salinity']]
    finally:
        # Return connection to pool
        pool = init_db_pool()
        if pool and conn:
            pool.putconn(conn)

# Input sanitization function
def sanitize_input(user_input):
    return html.escape(user_input.strip())

# Enhanced execute_sql_query with better error handling and fallback
def execute_sql_query(sql_query):
    conn = get_db_connection()
    
    # If no connection, use sample data
    if conn is None:
        logger.info("Using sample data due to connection issues")
        return execute_sql_query_on_sample(sql_query)
    
    try:
        df = pd.read_sql_query(sql_query, conn)
        logger.info(f"Query executed successfully, returned {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Error executing SQL query: {e}")
        st.error(f"Error executing SQL query: {e}")
        
        # Provide helpful suggestions based on error type
        if "syntax" in str(e).lower():
            st.info("Try simplifying your query or check for syntax errors")
        elif "connection" in str(e).lower():
            st.warning("Database connection issue. Using sample data.")
            return execute_sql_query_on_sample(sql_query)
        
        # Return connection to pool in case of error
        pool = init_db_pool()
        if pool and conn:
            try:
                pool.putconn(conn)
            except:
                pass
                
        return execute_sql_query_on_sample(sql_query)
    finally:
        # Always try to return connection to pool
        pool = init_db_pool()
        if pool and conn:
            try:
                pool.putconn(conn)
            except:
                pass

# Execute query on sample data when DB is unavailable
def execute_sql_query_on_sample(sql_query):
    df = get_sample_argo_data()
    
    # Simple query simulation for common patterns
    try:
        query_lower = sql_query.lower()
        
        # Handle WHERE clauses
        if "where" in query_lower:
            # Temperature conditions
            if "temperature" in query_lower:
                if ">" in query_lower:
                    match = re.search(r'temperature\s*>\s*(\d+(?:\.\d+)?)', query_lower)
                    if match:
                        temp_threshold = float(match.group(1))
                        df = df[df['temperature'] > temp_threshold]
                elif "<" in query_lower:
                    match = re.search(r'temperature\s*<\s*(\d+(?:\.\d+)?)', query_lower)
                    if match:
                        temp_threshold = float(match.group(1))
                        df = df[df['temperature'] < temp_threshold]
            
            # Salinity conditions
            if "salinity" in query_lower:
                if ">" in query_lower:
                    match = re.search(r'salinity\s*>\s*(\d+(?:\.\d+)?)', query_lower)
                    if match:
                        sal_threshold = float(match.group(1))
                        df = df[df['salinity'] > sal_threshold]
                elif "<" in query_lower:
                    match = re.search(r'salinity\s*<\s*(\d+(?:\.\d+)?)', query_lower)
                    if match:
                        sal_threshold = float(match.group(1))
                        df = df[df['salinity'] < sal_threshold]
            
            # Time conditions
            if "recent" in query_lower or "last" in query_lower:
                days_match = re.search(r'last\s+(\d+)\s+days?', query_lower)
                if days_match:
                    days = int(days_match.group(1))
                else:
                    days = 7  # Default to 7 days
                df = df[df['measurement_time'] > (datetime.now() - timedelta(days=days))]
        
        # Handle ORDER BY
        if "order by" in query_lower:
            if "temperature" in query_lower and "desc" in query_lower:
                df = df.sort_values('temperature', ascending=False)
            elif "temperature" in query_lower:
                df = df.sort_values('temperature', ascending=True)
            elif "salinity" in query_lower and "desc" in query_lower:
                df = df.sort_values('salinity', ascending=False)
            elif "salinity" in query_lower:
                df = df.sort_values('salinity', ascending=True)
            elif "measurement_time" in query_lower and "desc" in query_lower:
                df = df.sort_values('measurement_time', ascending=False)
            elif "measurement_time" in query_lower:
                df = df.sort_values('measurement_time', ascending=True)
        
        # Handle LIMIT
        limit_match = re.search(r'limit\s+(\d+)', query_lower)
        if limit_match:
            limit = int(limit_match.group(1))
            df = df.head(limit)
        else:
            df = df.head(100)  # Default limit for sample data
            
    except Exception as e:
        logger.error(f"Error simulating query on sample data: {e}")
        # Return limited sample data as fallback
        return df.head(100)
    
    return df

# Function to display dataframe with pagination
def display_dataframe_with_pagination(df):
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_side_bar()
    gb.configure_selection('multiple', use_checkbox=True, groupSelectsChildren="Group checkbox select children")
    gridOptions = gb.build()
    
    AgGrid(df, gridOptions=gridOptions, enable_enterprise_modules=True, height=400)

# Cached and rate-limited version of process_user_query
@lru_cache(maxsize=100)
@st.cache_data(ttl=300)  # Cache for 5 minutes
def process_user_query_cached(user_query, openai_key=None):
    # Add a small delay to prevent rate limiting
    time.sleep(0.5)
    return process_user_query(user_query, openai_key)

def process_user_query(user_query, openai_key=None):
    try:
        # Initialize the assistant if not already in session state
        if 'assistant' not in st.session_state:
            st.session_state.assistant = ArgoAIIntelligence()
        
        assistant = st.session_state.assistant
        
        # Generate enhanced query
        query_result = assistant.advanced_nlp_to_sql(user_query, openai_key)
        sql_query = query_result['sql']
        analysis_type = query_result['analysis_type']
        interpretation = query_result['query_interpretation']
        
        # Extract location for map highlighting
        highlight_city = None
        if analysis_type == "location_analysis":
            # Try to extract the location name from the query
            location_match = re.search(r'(?:near|closest to|around|in)\s+([\w\s]+)', user_query.lower())
            if location_match:
                potential_city = location_match.group(1).strip().title()
                if potential_city in REFERENCE_LOCATIONS:
                    highlight_city = potential_city
        
        # Execute query using your existing execute_sql_query function
        df = execute_sql_query(sql_query)
        
        if df is None or df.empty:
            st.warning("No data found for your query.")
            return None, None, None, None, None
        
        return interpretation, df, sql_query, analysis_type, highlight_city
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        st.error(f"Error processing request: {str(e)}")
        return None, None, None, None, None

# Main function with all enhancements
# ... (all your existing imports and CSS code remains the same)

# Main function with all enhancements
def main():
    # Initialize session state
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    
    if 'chat_minimized' not in st.session_state:
        st.session_state.chat_minimized = False
    
    if 'realtime_updates' not in st.session_state:
        st.session_state.realtime_updates = False
    
    if 'assistant' not in st.session_state:
        st.session_state.assistant = ArgoAIIntelligence()
    
    if 'current_data' not in st.session_state:
        st.session_state.current_data = pd.DataFrame()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1 class="header-title">Marinex</h1>
        <p class="header-subtitle">AI-Powered ARGO Float Discovery & Analysis Platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Statistics grid - single line with specified values
    st.markdown(f"""
    <div class="stats-grid">
        <div class="metric-card">
            <div class="metric-label">Active Floats</div>
            <div class="metric-value">85</div>
            <div class="metric-description">Currently deployed platforms</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Total Records</div>
            <div class="metric-value">27,450</div>
            <div class="metric-description">Oceanographic measurements</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Recent Data</div>
            <div class="metric-value"><span class="live-indicator"></span>27</div>
            <div class="metric-description">Last 24 hours</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Avg Temperature</div>
            <div class="metric-value">28.7°C</div>
            <div class="metric-description">Current ocean conditions</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Split screen layout
    st.markdown('<div class="panel-title">🌍 Global ARGO Float Network - 3D Visualization</div>', unsafe_allow_html=True)
    
    # Create split columns
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Create a container for the Cesium map that will be updated
        cesium_container = st.container()
        
        # Initialize the map in session state if not already present
        if 'cesium_html' not in st.session_state:
            st.session_state.cesium_html = create_enhanced_cesium_map()
        
        # Display the Cesium map in the container
        with cesium_container:
            components.html(st.session_state.cesium_html, height=600)
    
    with col2:
        # AI Chat Interface
        st.markdown('<div class="panel-title"> AI-Powered Query Interface</div>', unsafe_allow_html=True)
        
        # Query input with tooltip
        user_query = st.text_input(
            label="",
            placeholder="e.g., Show temperature profiles near Chennai",
            key="main_query",
            label_visibility="collapsed"
        )
        
        # Execute button
        execute_query = st.button(" Execute Prompt", key="execute_main", help="Execute your query", use_container_width=True)
        
        # Sample queries
        st.markdown("**Sample Queries:**")
        
        sample_queries = [
            "Show floats closest to Mumbai",
            "Temperature greater than 28 degrees",
            "Create temperature-salinity diagram", 
            "Show floats near arabian sea",
            "salinity greater than 35"
        ]
        
        for i, query in enumerate(sample_queries):
            if st.button(query, key=f"sample_{i}", use_container_width=True):
                user_query = query
                execute_query = True
        
        # Add OpenAI API key to sidebar
        with st.expander("🔑 API Configuration"):
            openai_key = st.text_input("OpenAI API Key (optional)", type="password", 
                                      help="Optional for enhanced AI capabilities")
        
        # Process query if submitted
        if execute_query and user_query:
            # Sanitize input
            user_query = sanitize_input(user_query)
            
            # Add to query history
            st.session_state.query_history.append({
                'query': user_query,
                'timestamp': datetime.now()
            })
            
            # Process query with caching (pass openai_key)
            natural_response, df, sql_query, analysis_type, highlight_city = process_user_query_cached(user_query, openai_key)
            
            # Store the current data in session state
            st.session_state.current_data = df
            
            # Store analysis_type in session state for later use
            if analysis_type:
                st.session_state.last_analysis_type = analysis_type
            
            if df is not None:
                # Display results
                st.markdown(f"""
                <div class="data-panel">
                    <div class="panel-title"> Query Results</div>
                    <p style="margin-bottom: 1rem;">{natural_response}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Update the Cesium map with query results
                st.session_state.cesium_html = create_enhanced_cesium_map(df, highlight_city)
                
                # Rerun to update the map
                st.rerun()
    
    # Data Table Section - Placed below the 3D map
    if not st.session_state.current_data.empty:
        st.markdown("---")
        st.markdown('<div class="panel-title">📊 Query Results Data Table</div>', unsafe_allow_html=True)
        
        # Show SQL query if available
        if 'sql_query' in st.session_state:
            with st.expander("View Generated SQL Query"):
                st.code(st.session_state.sql_query, language="sql")
        
        # Data summary
        df = st.session_state.current_data
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Records Found", len(df))
        with col_b:
            if 'temperature' in df.columns:
                st.metric("Avg Temperature", f"{df['temperature'].mean():.1f}°C")
        with col_c:
            if 'platform_number' in df.columns:
                st.metric("Unique Floats", df['platform_number'].nunique())
        
        # Data table with pagination
        display_dataframe_with_pagination(df)
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv,
            file_name=f"argo_query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        # Enhanced Plotting Section
        st.markdown("---")
        st.markdown('<div class="panel-title">📈 Advanced Data Visualization</div>', unsafe_allow_html=True)
        
        # Create tabs for different visualizations
        plot_tab1, plot_tab2, plot_tab3 = st.tabs(["🌡️ Temperature-Salinity", "📊 Custom Plots", "🗺️ Spatial Analysis"])
        
        with plot_tab1:
            # Temperature-Salinity diagram
            if 'temperature' in df.columns and 'salinity' in df.columns:
                st.subheader("Water Mass Analysis (T-S Diagram)")
                assistant = st.session_state.assistant
                ts_fig = assistant.create_ts_diagram(df)
                if ts_fig:
                    st.plotly_chart(ts_fig, use_container_width=True)
            else:
                st.info("Temperature and salinity data required for T-S diagram")
        
        with plot_tab2:
            # Custom plotting options
            st.subheader("Create Custom Visualizations")
            
            # Select parameters for plotting
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if len(numeric_cols) >= 2:
                col1, col2 = st.columns(2)
                
                with col1:
                    x_axis = st.selectbox("X-axis parameter", numeric_cols, index=0)
                
                with col2:
                    y_axis = st.selectbox("Y-axis parameter", numeric_cols, index=min(1, len(numeric_cols)-1))
                
                # Plot type selection
                plot_type = st.radio("Plot type", ["Scatter", "Line", "Histogram"], horizontal=True)
                
                # Generate plot button
                if st.button("Generate Plot", use_container_width=True):
                    if plot_type == "Scatter":
                        fig = px.scatter(df, x=x_axis, y=y_axis, 
                                        color='platform_number' if 'platform_number' in df.columns else None,
                                        title=f"{y_axis} vs {x_axis}")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    elif plot_type == "Line":
                        # For line plots, we need to sort by x-axis
                        sorted_df = df.sort_values(by=x_axis)
                        fig = px.line(sorted_df, x=x_axis, y=y_axis, 
                                     color='platform_number' if 'platform_number' in df.columns else None,
                                     title=f"{y_axis} vs {x_axis}")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    elif plot_type == "Histogram":
                        fig = px.histogram(df, x=x_axis, title=f"Distribution of {x_axis}")
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Need at least 2 numeric columns for plotting")
        
        with plot_tab3:
            # Spatial analysis
            st.subheader("Spatial Distribution")
            
            if 'latitude' in df.columns and 'longitude' in df.columns:
                # Create a map visualization
                st.map(df[['latitude', 'longitude']].dropna(), zoom=3)
                
                # Add some statistics about the spatial distribution
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Spatial Coverage", f"{df['latitude'].nunique()}×{df['longitude'].nunique()}")
                with col2:
                    if 'temperature' in df.columns:
                        st.metric("Temp Range", f"{df['temperature'].min():.1f}°C - {df['temperature'].max():.1f}°C")
            else:
                st.info("Latitude and longitude data required for spatial analysis")
    
    # Sample plotting for demonstration (when no query has been executed yet)
    else:
        st.markdown("---")
        st.markdown('<div class="panel-title"> Data Visualization</div>', unsafe_allow_html=True)
        st.info("plot with temperature-salinity diagram")
        
        # Generate sample data for demonstration
        sample_df = get_sample_argo_data().head(100)
        
        # Create a sample T-S diagram
        fig = px.scatter(sample_df, x='salinity', y='temperature', 
                        color='pressure', 
                        title=" Temperature-Salinity Diagram",
                        labels={'salinity': 'Salinity (PSU)', 'temperature': 'Temperature (°C)', 'pressure': 'Pressure (dbar)'})
        
        st.plotly_chart(fig, use_container_width=True)

    # Query History Sidebar
    with st.sidebar:
        st.markdown("### 📋 Query History")
        if st.session_state.query_history:
            for i, query_item in enumerate(reversed(st.session_state.query_history[-10:])):
                with st.expander(f"Query {len(st.session_state.query_history) - i}"):
                    st.write(f"**Query:** {query_item['query']}")
                    st.write(f"**Time:** {query_item['timestamp'].strftime('%Y-%m-%d %H:%M')}")
                    if st.button("🔄 Run Again", key=f"rerun_{i}"):
                        st.session_state.main_query = query_item['query']
                        st.rerun()
        else:
            st.info("No queries yet. Try asking something above!")
        
        # API Status
        st.markdown("### 🔌 System Status")
        
        # Database status
        pool = init_db_pool()
        if pool:
            db_status = "🟢 Connected"
        else:
            db_status = "🟡 Sample Data"
        
        st.markdown(f"**Database:** {db_status}")
        st.markdown("**AI Model:** 🟢 Online")
        st.markdown("**Cesium Maps:** 🟢 Active")
        
        # Help section
        st.markdown("### ❓ Help & Tips")
        with st.expander("How to use this platform"):
            st.write("""
            1. **Ask questions** in natural language about ARGO float data
            2. **Explore results** through interactive visualizations
            3. **Download data** for further analysis
            4. **Use sample queries** to get started quickly
            """)
        
        with st.expander("Sample query examples"):
            st.write("""
            - "Show floats near Chennai"
            - "Temperature above 28°C"
            - "Salinity profiles from last month"
            - "Deepest measurements in Indian Ocean"
            - "Find thermocline depth in Bay of Bengal"
            - "Compare water masses in different regions"
            - "Show monsoon effects on surface temperature"
            """)

if __name__ == "__main__":
    main()