"""Shared visual styles and small presentation helpers for Streamlit pages."""

from datetime import datetime

import streamlit as st

BACKGROUND = "#F6F5FC"


def inject_theme() -> None:
    st.markdown(
        f"""
        <style>
            .stApp {{ background-color: {BACKGROUND}; }}

            section[data-testid="stSidebar"] {{
                background-color: #FFFFFF;
                border-right: 1px solid #EFEDFB;
            }}
            section[data-testid="stSidebar"] .stRadio > label {{ display: none; }}
            section[data-testid="stSidebar"] div[role="radiogroup"] label {{
                padding: 10px 14px;
                border-radius: 12px;
                margin-bottom: 4px;
            }}
            section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
                background: linear-gradient(135deg, #7C6FEF, #6C5CE7);
            }}
            section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {{
                color: white !important;
                font-weight: 600;
            }}

            .smms-topbar {{
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                padding: 4px 4px 22px 4px;
            }}
            .smms-greeting h1 {{ font-size: 26px; margin: 0; color: #1E1B3A; }}
            .smms-greeting p {{ margin: 2px 0 0 0; color: #8A8AA3; font-size: 14px; }}
            .smms-date-badge {{
                background: white;
                border-radius: 14px;
                padding: 8px 16px;
                color: #4B4B63;
                font-size: 13px;
                box-shadow: 0 4px 12px rgba(90, 79, 207, 0.08);
            }}

            .stat-card {{
                border-radius: 20px;
                padding: 18px 20px;
                color: white;
                min-height: 112px;
                box-shadow: 0 10px 24px rgba(108, 92, 231, 0.18);
                margin-bottom: 10px;
            }}
            .stat-card h3 {{ margin: 6px 0 2px 0; font-weight: 500; font-size: 13px; opacity: 0.92; }}
            .stat-card .value {{ font-size: 30px; font-weight: 700; line-height: 1.1; }}
            .stat-card .delta {{ font-size: 11px; opacity: 0.85; margin-top: 2px; }}
            .stat-purple {{ background: linear-gradient(135deg, #8B7CF6, #5A4FCF); }}
            .stat-pink {{ background: linear-gradient(135deg, #FB7CA0, #F5576C); }}
            .stat-blue {{ background: linear-gradient(135deg, #74C7EC, #4FACFE); }}
            .stat-pink2 {{ background: linear-gradient(135deg, #F78CA2, #F9748F); }}

            .smms-card {{
                background: white;
                border-radius: 18px;
                padding: 20px 22px;
                box-shadow: 0 4px 14px rgba(90, 79, 207, 0.07);
                margin-bottom: 16px;
            }}

            .stButton > button {{
                background: linear-gradient(135deg, #8B7CF6, #6C5CE7);
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: 600;
            }}
            .stButton > button:hover {{ opacity: 0.92; color: white; }}

            .badge-taken {{
                color: #16A34A;
                background: #DCFCE7;
                padding: 3px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
            }}
            .badge-pending {{
                color: #D97706;
                background: #FEF3C7;
                padding: 3px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
            }}

            #MainMenu {{ visibility: hidden; }}
            footer {{ visibility: hidden; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(greeting: str, subtitle: str) -> None:
    now = datetime.now()
    st.markdown(
        f"""
        <div class="smms-topbar">
            <div class="smms-greeting">
                <h1>{greeting}</h1>
                <p>{subtitle}</p>
            </div>
            <div class="smms-date-badge">
                {now.strftime('%Y-%m-%d')} &nbsp;|&nbsp; {now.strftime('%H:%M')}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def stat_card(col, style: str, marker: str, label: str, value, delta: str = "") -> None:
    marker_html = f'<div style="font-size:11px; font-weight:700; letter-spacing:.08em;">{marker}</div>' if marker else ""
    with col:
        st.markdown(
            f"""
            <div class="stat-card {style}">
                {marker_html}
                <h3>{label}</h3>
                <div class="value">{value}</div>
                <div class="delta">{delta}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
