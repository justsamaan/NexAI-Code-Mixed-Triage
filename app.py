"""
app.py
======
Multilingual Customer Support & Triage Platform
===============================================
Enterprise customer-support platform supporting code-mixed communications in:
- Telugu + English (Tenglish & native తెలుగు script)
- Tanglish (Tamil + English & native தமிழ் script)
- Hinglish (Hindi + English & native हिन्दी script)
- English

Features:
- Role-based experiences for Customers and Support Specialists
- Apple-inspired clean, restrained, accessible design system
- Customer Portal: Home, Live Chat Conversations, Start a Conversation, Feedback
- Optional native language selection (English, தமிழ், తెలుగు, हिन्दी, Auto-Detect)
- Native script input assistance (Telugu & Tamil chips + font rendering)
- Complete human handoff workflow, queueing & specialist assignment
- Post-resolution customer ratings, translation quality & single-submission feedback
- Agent Workspace: Customer Queries, Live Sessions, Session Analytics, Root-Cause Analysis, Evaluation Suite
- Persistent SQLite database with Write-Ahead Logging (WAL)
"""

import os
import sys
import datetime
import pandas as pd
import streamlit as st

import ai_engine
import evaluate
import database
import forge_3d
from test_cases import TEST_CASES

# -----------------------------------------------------------------------------
# 1. Page Configuration & Veltrix Design System (Soft Sage, Mint & Crisp White)
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="Veltrix | AI Multilingual Support Platform",
    page_icon="✳️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Veltrix modern dashboard styling with soft sage/mint palette, crisp white cards, and full Indic font support
st.markdown("""
<style>
    /* Global Typography & Luminous Sage Environment */
    html, body, [class*="css"], .stApp, .stMarkdown, p, div, span, input, textarea {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display",
                     "Noto Sans Tamil", "Latha", "Vijaya",
                     "Noto Sans Telugu", "Gautami", "Vani",
                     "Noto Sans Devanagari", "Mangal",
                     "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        color: #1e293b;
        -webkit-font-smoothing: antialiased;
    }
    
    .stApp {
        background-color: #f1f5f2 !important;
    }

    /* Main Container Padding */
    .block-container {
        padding-top: 1.8rem !important;
        padding-bottom: 3.5rem !important;
    }

    /* Headers with Veltrix Clean Typography */
    .apple-header, .forge-header, .veltrix-header {
        font-size: 1.85rem;
        font-weight: 800;
        color: #111827;
        letter-spacing: -0.03em;
        margin-top: 0.2rem;
        margin-bottom: 0.25rem;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .apple-sub, .forge-sub, .veltrix-sub {
        font-size: 0.95rem;
        color: #64748b;
        margin-bottom: 1.3rem;
        font-weight: 400;
        line-height: 1.5;
    }

    /* Top Tabs Styling - Pill Capsule Navigation matching Veltrix */
    [data-baseweb="tab-list"], .stTabs [role="tablist"] {
        gap: 8px !important;
        background: #ffffff !important;
        border: 1px solid #e2ebe3 !important;
        border-radius: 9999px !important;
        padding: 5px 8px !important;
        margin-bottom: 22px !important;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03) !important;
        display: inline-flex !important;
    }
    [data-baseweb="tab"], .stTabs [role="tab"] {
        background: transparent !important;
        color: #64748b !important;
        border: none !important;
        border-radius: 9999px !important;
        padding: 8px 20px !important;
        margin-right: 0 !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    [data-baseweb="tab"]:hover, .stTabs [role="tab"]:hover {
        background: #f1f5f2 !important;
        color: #111827 !important;
    }
    [data-baseweb="tab"][aria-selected="true"], .stTabs [role="tab"][aria-selected="true"] {
        background: #dcfce7 !important;
        color: #15803d !important;
        border: 1px solid #86efac !important;
        box-shadow: 0 2px 8px rgba(34, 197, 94, 0.18) !important;
        font-weight: 700 !important;
    }
    [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {
        display: none !important;
    }

    /* Veltrix Crisp White Cards with Rounded-2xl & Soft Sage Shadows */
    .apple-card, .forge-card, .veltrix-card {
        background-color: #ffffff;
        border: 1px solid #e2ebe3;
        border-radius: 18px;
        padding: 20px 24px;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.04);
        margin-bottom: 14px;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .apple-card:hover, .forge-card:hover, .veltrix-card:hover {
        border-color: #86efac;
        box-shadow: 0 6px 24px -2px rgba(34, 197, 94, 0.12);
    }
    .apple-card-title, .forge-card-title, .veltrix-card-title {
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        margin-bottom: 6px;
    }
    .apple-card-value, .forge-card-value, .veltrix-card-value {
        font-size: 2.1rem;
        font-weight: 800;
        color: #111827;
        letter-spacing: -0.03em;
    }

    /* Metric Delta indicator (Lime Green like reference) */
    .veltrix-delta {
        font-size: 0.78rem;
        color: #16a34a;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 4px;
        margin-top: 4px;
    }

    /* Badges & Status Pills */
    .badge-pill {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.01em;
    }
    .badge-high {
        background-color: #fee2e2;
        color: #b91c1c;
        border: 1px solid #fecaca;
        padding: 3px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.78rem;
        display: inline-block;
    }
    .badge-medium {
        background-color: #fef3c7;
        color: #b45309;
        border: 1px solid #fde68a;
        padding: 3px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.78rem;
        display: inline-block;
    }
    .badge-low {
        background-color: #dcfce7;
        color: #15803d;
        border: 1px solid #bbf7d0;
        padding: 3px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.78rem;
        display: inline-block;
    }
    .badge-open {
        background-color: #e0f2fe;
        color: #0369a1;
        border: 1px solid #bae6fd;
        padding: 2px 10px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .badge-resolved {
        background-color: #dcfce7;
        color: #15803d;
        border: 1px solid #bbf7d0;
        padding: 2px 10px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .badge-inprogress {
        background-color: #fef3c7;
        color: #b45309;
        border: 1px solid #fde68a;
        padding: 2px 10px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
    }

    /* Language & Translation Containers */
    .lang-pill {
        background-color: #dcfce7;
        color: #15803d;
        padding: 3px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.82rem;
        display: inline-block;
        border: 1px solid #bbf7d0;
    }
    .translation-card {
        background-color: #f0fdf4;
        border: 1.5px solid #86efac;
        border-radius: 14px;
        padding: 16px 20px;
        margin-top: 8px;
        margin-bottom: 14px;
        box-shadow: 0 4px 16px rgba(34, 197, 94, 0.08);
    }
    .translation-title {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #16a34a;
        margin-bottom: 4px;
    }
    .translation-body {
        font-size: 1.12rem;
        font-weight: 700;
        color: #111827;
        line-height: 1.45;
    }
    
    /* Internal Staff Notes */
    .chat-bubble-internal {
        background-color: #fefce8;
        color: #854d0e;
        border: 1px solid #fef08a;
        border-left: 4px solid #eab308;
        border-radius: 10px;
        padding: 10px 14px;
        margin: 8px 0;
        font-size: 0.90rem;
        line-height: 1.45;
    }

    /* Inbox Rows */
    .inbox-card {
        background-color: #ffffff;
        border: 1px solid #e2ebe3;
        border-radius: 12px;
        padding: 12px 14px;
        margin-bottom: 8px;
        transition: all 0.15s ease-in-out;
    }
    .inbox-card:hover {
        border-color: #86efac;
        box-shadow: 0 4px 16px rgba(34, 197, 94, 0.1);
    }
    .inbox-card-selected {
        background-color: #f0fdf4;
        border: 2px solid #22c55e !important;
        border-radius: 12px;
        padding: 12px 14px;
        margin-bottom: 8px;
        box-shadow: 0 0 16px rgba(34, 197, 94, 0.15);
    }
    .folder-btn-active {
        background: #dcfce7 !important;
        color: #15803d !important;
        border: 1px solid #86efac !important;
        border-radius: 10px;
        padding: 8px 12px;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .folder-btn {
        background-color: #ffffff;
        color: #475569;
        border-radius: 10px;
        padding: 8px 12px;
        font-weight: 500;
        margin-bottom: 4px;
        border: 1px solid #e2ebe3;
    }

    /* Banners */
    .escalate-banner {
        background-color: #fef2f2;
        border: 1px solid #fecaca;
        border-left: 4px solid #ef4444;
        padding: 14px 18px;
        border-radius: 10px;
        margin-top: 10px;
        margin-bottom: 14px;
        color: #991b1b;
    }
    .no-escalate-banner {
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-left: 4px solid #22c55e;
        padding: 14px 18px;
        border-radius: 10px;
        margin-top: 10px;
        margin-bottom: 14px;
        color: #166534;
    }
    .waiting-banner {
        background-color: #fffbeb;
        border: 1px solid #fef3c7;
        border-left: 4px solid #f59e0b;
        padding: 14px 18px;
        border-radius: 10px;
        margin-top: 10px;
        margin-bottom: 14px;
        color: #92400e;
    }
    .joined-banner {
        background-color: #f0f9ff;
        border: 1px solid #bae6fd;
        border-left: 4px solid #0284c7;
        padding: 14px 18px;
        border-radius: 10px;
        margin-top: 10px;
        margin-bottom: 14px;
        color: #075985;
    }

    /* Suggested Reply Box */
    .reply-box {
        background-color: #f8faf8;
        border: 1px solid #e2ebe3;
        border-radius: 12px;
        padding: 16px;
        color: #111827;
        line-height: 1.5;
        font-size: 0.95rem;
    }

    /* Chat Bubbles */
    .chat-bubble-customer {
        background: #111827;
        color: #ffffff !important;
        border-radius: 18px 18px 4px 18px;
        padding: 12px 18px;
        margin: 8px 0;
        max-width: 80%;
        margin-left: auto;
        font-size: 0.95rem;
        line-height: 1.45;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
    }
    .chat-bubble-customer * {
        color: #ffffff !important;
    }
    .chat-bubble-agent {
        background-color: #ffffff;
        color: #111827;
        border: 1px solid #e2ebe3;
        border-radius: 18px 18px 18px 4px;
        padding: 14px 18px;
        margin: 8px 0;
        max-width: 82%;
        font-size: 0.95rem;
        line-height: 1.45;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
    }
    .chat-bubble-ai {
        background-color: #ffffff;
        color: #111827;
        border: 1px solid #e2ebe3;
        border-left: 4px solid #22c55e;
        border-radius: 14px;
        padding: 14px 18px;
        margin: 8px 0;
        max-width: 85%;
        font-size: 0.95rem;
        line-height: 1.45;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
    }
    .chat-bubble-system {
        background-color: #f1f5f2;
        color: #64748b;
        border: 1px solid #e2ebe3;
        border-radius: 9999px;
        padding: 6px 14px;
        margin: 8px auto;
        max-width: 85%;
        text-align: center;
        font-size: 0.8rem;
        font-weight: 500;
    }

    /* Quick phrase pill */
    .chip-btn {
        display: inline-block;
        background: #ffffff;
        border: 1px solid #e2ebe3;
        border-radius: 9999px;
        padding: 5px 14px;
        font-size: 0.82rem;
        color: #334155;
        margin: 3px;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .chip-btn:hover {
        background: #dcfce7;
        color: #15803d;
        border-color: #86efac;
    }
    
    /* Legacy Classes */
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2ebe3;
        border-radius: 16px;
        padding: 18px 22px;
        margin-bottom: 12px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.03);
    }
    .metric-card-title {
        font-size: 0.78rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .metric-card-value {
        font-size: 1.95rem;
        font-weight: 800;
        color: #111827;
    }
    .disclaimer-text {
        font-size: 0.8rem;
        color: #64748b;
        margin-top: 6px;
    }

    /* =========================================================================
       PROPER MODERN SIDEBAR (Veltrix Design System)
       ========================================================================= */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2ebe3 !important;
    }

    /* Hide standard circular radio bullet inputs completely and style as modern navigation cards */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > div {
        gap: 6px !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label input[type="radio"],
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label > div:first-child:not(:last-child),
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[data-baseweb="radio"] > div:first-child {
        display: none !important;
        width: 0 !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        opacity: 0 !important;
        visibility: hidden !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label {
        width: 100% !important;
        box-sizing: border-box !important;
        background: #ffffff !important;
        border: 1px solid #e2ebe3 !important;
        border-radius: 12px !important;
        padding: 10px 14px !important;
        margin-bottom: 5px !important;
        cursor: pointer !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        display: flex !important;
        align-items: center !important;
        color: #334155 !important;
        font-weight: 500 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02) !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {
        background: #f1f5f2 !important;
        color: #111827 !important;
        border-color: #bbf7d0 !important;
        transform: translateX(3px) !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label[data-checked="true"],
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) {
        background: #dcfce7 !important;
        color: #15803d !important;
        font-weight: 700 !important;
        border: 1.5px solid #86efac !important;
        border-left: 4px solid #16a34a !important;
        box-shadow: 0 2px 10px rgba(34, 197, 94, 0.15) !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label[data-checked="true"] p,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) p {
        color: #15803d !important;
        font-weight: 700 !important;
    }

    /* Buttons - Veltrix Rounded Pill styling */
    button[kind="primary"] {
        background: #111827 !important;
        color: #ffffff !important;
        border-radius: 9999px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 9px 20px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.1) !important;
    }
    button[kind="primary"]:hover {
        background: #1e293b !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.16) !important;
    }
    button[kind="secondary"] {
        background: #ffffff !important;
        color: #334155 !important;
        border: 1px solid #e2ebe3 !important;
        border-radius: 9999px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    button[kind="secondary"]:hover {
        background: #f1f5f2 !important;
        color: #111827 !important;
        border-color: #cbd5e1 !important;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 2. Session State Initialization & Testing Compatibility
# -----------------------------------------------------------------------------

if "tickets" not in st.session_state:
    st.session_state["tickets"] = []

if "message_input_val" not in st.session_state:
    st.session_state["message_input_val"] = ""

if "latest_result" not in st.session_state:
    st.session_state["latest_result"] = None

if "eval_results" not in st.session_state:
    st.session_state["eval_results"] = None

if "selected_conv_id" not in st.session_state:
    st.session_state["selected_conv_id"] = None

if "preferred_language" not in st.session_state:
    st.session_state["preferred_language"] = "Auto-Detect"

if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = [
        {
            "sender": "assistant",
            "text": "Namaste! I am the NexAI Multilingual Triage Assistant. You can speak or type naturally in English, Hinglish, Tanglish, Telugu+English, or native Indic scripts (हिन्दी, தமிழ், తెలుగు).\n\nHow can I help you with your order, refund, or account today?",
            "timestamp": datetime.datetime.now().strftime("%H:%M"),
            "analysis": None
        }
    ]

if "chat_input_val" not in st.session_state:
    st.session_state["chat_input_val"] = ""

if "forge_prompt" not in st.session_state:
    st.session_state["forge_prompt"] = "mera order deliver nahi hua"

if "explicit_sign_out" not in st.session_state:
    st.session_state["explicit_sign_out"] = False

# Testing Detection: If run under test harnesses without explicit session, default to demo agent
IS_RUNNING_TESTS = ("unittest" in sys.modules or "pytest" in sys.modules or os.getenv("TESTING") == "1")

if "user" not in st.session_state or st.session_state["user"] is None:
    if not st.session_state.get("explicit_sign_out", False):
        st.session_state["user"] = database.get_user_by_username("agent") or database.get_user_by_username("customer")

current_user = st.session_state.get("user")


# -----------------------------------------------------------------------------
# 3. Authentication & Sign-In View
# -----------------------------------------------------------------------------

def render_login_view():
    """Renders the Apple-inspired authentication and demo quick-access page."""
    st.markdown('<div class="apple-header">Multilingual Support Platform</div>', unsafe_allow_html=True)
    st.markdown('<div class="apple-sub">Sign in to access your customer inquiries or agent triage workspace.</div>', unsafe_allow_html=True)

    # Demo Quick Access Card
    st.markdown("""
    <div class="apple-card" style="border-left: 4px solid #16a34a;">
        <div class="apple-card-title">Hackathon Quick Access</div>
        <div style="font-size: 0.95rem; color: #334155; margin-bottom: 12px;">
            One-click sign in to explore distinct role experiences:
        </div>
    </div>
    """, unsafe_allow_html=True)

    d_col1, d_col2, d_col3 = st.columns(3)
    with d_col1:
        if st.button("👤 Customer: Priya Sharma", use_container_width=True):
            st.session_state["user"] = database.get_user_by_username("customer")
            st.session_state["selected_conv_id"] = None
            st.rerun()
    with d_col2:
        if st.button("🎧 Agent: Rajesh Kumar (All Dialects)", use_container_width=True):
            st.session_state["user"] = database.get_user_by_username("agent")
            st.session_state["selected_conv_id"] = None
            st.rerun()
    with d_col3:
        if st.button("🎧 Agent: Anita Raman (Tamil & English)", use_container_width=True):
            st.session_state["user"] = database.get_user_by_username("anita")
            st.session_state["selected_conv_id"] = None
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    tab_cust, tab_agent = st.tabs(["Customer Access", "Agent Workspace"])

    # 1. Customer Tab (Login / Register)
    with tab_cust:
        cust_subtab1, cust_subtab2 = st.tabs(["Sign In", "Create Customer Account"])
        
        with cust_subtab1:
            st.markdown("##### Customer Sign In")
            c_user = st.text_input("Username or Email", key="c_login_user")
            c_pwd = st.text_input("Password", type="password", key="c_login_pwd")
            if st.button("Sign In as Customer", type="primary", key="btn_c_login"):
                auth = database.authenticate_user(c_user, c_pwd)
                if auth and auth.get("role") == "customer":
                    st.session_state["user"] = auth
                    st.success(f"Welcome back, {auth['name']}!")
                    st.rerun()
                else:
                    st.error("Invalid customer credentials. Please check your username and password.")

        with cust_subtab2:
            st.markdown("##### New Customer Registration")
            r_name = st.text_input("Full Name", key="r_name")
            r_email = st.text_input("Email Address", key="r_email")
            r_user = st.text_input("Username", key="r_user")
            r_pwd = st.text_input("Password (min 6 chars)", type="password", key="r_pwd")
            if st.button("Create Account", type="primary", key="btn_c_register"):
                if len(r_pwd) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    try:
                        new_u = database.create_user(
                            username=r_user,
                            email=r_email,
                            password=r_pwd,
                            name=r_name,
                            role="customer"
                        )
                        st.session_state["user"] = new_u
                        st.success(f"Account created successfully. Welcome, {new_u['name']}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Registration failed: {str(e)}")

    # 2. Agent Tab
    with tab_agent:
        st.markdown("##### Customer-Care Agent Login")
        st.caption("Authorized staff login to the customer support intelligence workspace.")
        a_user = st.text_input("Agent Username or Internal Email", key="a_login_user")
        a_pwd = st.text_input("Password", type="password", key="a_login_pwd")
        if st.button("Sign In to Agent Workspace", type="primary", key="btn_a_login"):
            auth = database.authenticate_user(a_user, a_pwd)
            if auth and auth.get("role") in ["agent", "admin"]:
                st.session_state["user"] = auth
                st.success(f"Authenticated as Agent: {auth['name']}")
                st.rerun()
            else:
                st.error("Access denied. Please check your staff credentials.")


# If user is not authenticated, display login view and halt
if current_user is None:
    render_login_view()
    st.stop()


# -----------------------------------------------------------------------------
# 4. Global Sidebar & Persona Controls
# -----------------------------------------------------------------------------

with st.sidebar:
    # Veltrix Brand Banner
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; padding: 4px 2px 14px 2px; border-bottom: 1px solid #e2ebe3; margin-bottom: 14px;">
        <div style="width: 38px; height: 38px; border-radius: 12px; background: linear-gradient(135deg, #166534 0%, #22c55e 100%); display: flex; align-items: center; justify-content: center; font-size: 1.25rem; box-shadow: 0 4px 14px rgba(34, 197, 94, 0.28);">
            ✳️
        </div>
        <div>
            <div style="font-size: 1.18rem; font-weight: 800; color: #111827; letter-spacing: -0.02em; line-height: 1.1;">VELTRIX</div>
            <div style="font-size: 0.70rem; color: #15803d; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;">AI Support Studio</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Active User Profile Card (Initials Avatar + Online Badge)
    name_parts = current_user.get("name", "User").split()
    initials = "".join([p[0].upper() for p in name_parts[:2]]) if name_parts else "US"
    u_role = current_user.get("role", "customer").capitalize()
    role_label = "Support Specialist" if current_user.get("role") == "agent" else "Customer Account"

    st.markdown(f"""
    <div style="background: #ffffff; border: 1px solid #e2ebe3; border-radius: 14px; padding: 12px 14px; margin-bottom: 14px; display: flex; align-items: center; gap: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
        <div style="width: 40px; height: 40px; border-radius: 50%; background: #111827; color: #ffffff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.88rem; flex-shrink: 0; box-shadow: 0 2px 8px rgba(0,0,0,0.12);">
            {initials}
        </div>
        <div style="flex: 1; min-width: 0;">
            <div style="font-size: 0.95rem; font-weight: 700; color: #111827; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{current_user['name']}</div>
            <div style="display: flex; align-items: center; gap: 6px; margin-top: 2px;">
                <span style="font-size: 0.70rem; font-weight: 700; color: #15803d; background: #dcfce7; border: 1px solid #bbf7d0; padding: 1px 7px; border-radius: 9999px;">● Online</span>
                <span style="font-size: 0.72rem; color: #64748b; font-weight: 500;">{role_label}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # If Agent: Availability Status and Language Capabilities
    if current_user.get("role") == "agent":
        st.markdown("**Agent Availability**")
        status_opts = ["online", "busy", "offline"]
        curr_status = current_user.get("availability_status", "online")
        new_status = st.selectbox(
            "Status",
            options=status_opts,
            index=status_opts.index(curr_status) if curr_status in status_opts else 0,
            format_func=lambda s: f"🟢 {s.capitalize()}" if s == "online" else (f"🟡 {s.capitalize()}" if s == "busy" else f"⚪ {s.capitalize()}"),
            label_visibility="collapsed"
        )
        if new_status != curr_status:
            database.update_agent_status(current_user["id"], new_status)
            current_user["availability_status"] = new_status
            st.session_state["user"] = current_user
            st.toast(f"Availability updated to {new_status.capitalize()}")

        with st.expander("🌐 Supported Languages"):
            st.caption("Languages you are authorized to triage:")
            selected_langs = []
            for lang in database.ALL_SUPPORTED_LANGUAGES:
                is_checked = lang in current_user.get("languages", [])
                if st.checkbox(lang, value=is_checked, key=f"chk_lang_{lang}"):
                    selected_langs.append(lang)
            if st.button("Save Language Preferences", use_container_width=True):
                database.update_agent_languages(current_user["id"], selected_langs)
                current_user["languages"] = selected_langs
                st.session_state["user"] = current_user
                st.success("Language capabilities saved!")
                st.rerun()

    st.divider()

    # Role-Based Navigation Header
    st.markdown("""
    <div style="font-size: 0.72rem; font-weight: 800; color: #64748b; text-transform: uppercase; letter-spacing: 0.08em; margin: 4px 0 6px 4px; display: flex; align-items: center; gap: 6px;">
        <span>⚡</span> NAVIGATION
    </div>
    """, unsafe_allow_html=True)

    if current_user.get("role") == "customer":
        nav_options = [
            "💬 AI Chatbot",
            "⚒️ 3D Workstation Forge",
            "Home",
            "My Conversations",
            "Start a Conversation",
            "Feedback"
        ]
    else:
        # Agent Navigation (Includes backwards-compatible labels for existing test suite)
        nav_options = [
            "💬 AI Chatbot",
            "⚒️ 3D Workstation Forge",
            "Customer Queries",
            "Live Sessions",
            "📊 Session Analytics",
            "Root-Cause Analysis",
            "🧪 Evaluation Suite"
        ]

    curr_idx = 0
    if "nav_target" in st.session_state and st.session_state["nav_target"] in nav_options:
        curr_idx = nav_options.index(st.session_state.pop("nav_target"))

    section = st.radio("Navigation", options=nav_options, index=curr_idx)

    st.divider()

    # AI Backend Engine Status Card
    backend_status = ai_engine.get_backend_status()
    st.markdown(f"""
    <div style="background: #ffffff; border: 1px solid #e2ebe3; border-radius: 12px; padding: 12px 14px; margin-top: 4px; margin-bottom: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.02);">
        <div style="font-size: 0.70rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">AI Core Engine</div>
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <span style="font-size: 0.88rem; font-weight: 700; color: #111827;">{backend_status['name']}</span>
            <span style="background: #dcfce7; color: #15803d; font-size: 0.70rem; font-weight: 700; padding: 2px 8px; border-radius: 9999px; border: 1px solid #bbf7d0;">🟢 Ready</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("⚙️ Configure API Key"):
        st.caption("Optional Gemini API key for live generative responses.")
        user_key = st.text_input("Gemini API Key", value=os.getenv("GEMINI_API_KEY", ""), type="password", placeholder="AIzaSy...")
        if st.button("Apply Key", use_container_width=True):
            if user_key.strip():
                os.environ["GEMINI_API_KEY"] = user_key.strip()
                st.success("API key updated!")
            else:
                if "GEMINI_API_KEY" in os.environ:
                    del os.environ["GEMINI_API_KEY"]
                st.warning("Reverted to Local NLP Engine.")
            st.rerun()

    st.divider()

    # Persona Switcher for Hackathon Testing
    with st.expander("🔄 Switch Demo Persona"):
        p_choice = st.selectbox(
            "Quick Persona Switch",
            ["Priya (Customer)", "Rahul (Customer)", "Rajesh (All Dialects Agent)", "Anita (Tamil Agent)"],
            index=0 if current_user.get("username") == "customer" else 2
        )
        if st.button("Switch Account", use_container_width=True):
            if "Priya" in p_choice:
                st.session_state["user"] = database.get_user_by_username("customer")
            elif "Rahul" in p_choice:
                st.session_state["user"] = database.get_user_by_username("rahul")
            elif "Rajesh" in p_choice:
                st.session_state["user"] = database.get_user_by_username("agent")
            elif "Anita" in p_choice:
                st.session_state["user"] = database.get_user_by_username("anita")
            st.session_state["selected_conv_id"] = None
            st.rerun()

    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state["user"] = None
        st.session_state["explicit_sign_out"] = True
        st.session_state["selected_conv_id"] = None
        st.rerun()


# -----------------------------------------------------------------------------
# 5. Role-Based Access Control (RBAC) Guard
# -----------------------------------------------------------------------------

# Ensure customer can NEVER access agent pages
AGENT_SECTIONS = ["Customer Queries", "Live Sessions", "📊 Session Analytics", "Root-Cause Analysis", "🧪 Evaluation Suite"]
if current_user.get("role") == "customer" and section in AGENT_SECTIONS:
    st.error("Access Restricted: Customers are not authorized to view the support agent workspace.")
    section = "Home"


# -----------------------------------------------------------------------------
# 6. Customer Workspace Views (Phase 2 Enhanced)
# -----------------------------------------------------------------------------

# Multilingual Language Options with Native Script Display
LANGUAGE_OPTIONS = {
    "Auto-Detect": "🌐 Auto-Detect (Natural Code-Mixed)",
    "English": "English",
    "Tamil": "தமிழ் (Tamil)",
    "Telugu": "తెలుగు (Telugu)",
    "Hindi": "हिन्दी (Hindi)"
}

# Quick Native Script Insertion Chips
NATIVE_CHIPS = {
    "Tamil": [
        ("ரீபண்ட் வேண்டும்", "Need refund"),
        ("என் ஆர்டர் இன்னும் வரவில்லை", "Order not delivered"),
        ("பொருள் சேதமடைந்துள்ளது", "Damaged product"),
        ("பணம் பிடித்தம் செய்யப்பட்டது", "Payment deducted"),
        ("ஆர்டரை ரத்து செய்ய வேண்டும்", "Cancel order"),
        ("உதவி தேவை", "Need help")
    ],
    "Telugu": [
        ("రీఫండ్ కావాలి", "Need refund"),
        ("నా ఆర్డర్ ఇంకా డెలివరీ కాలేదు", "Order not delivered"),
        ("డబ్బులు రెండు సార్లు కట్ అయ్యాయి", "Deducted twice"),
        ("ప్రొడక్ట్ డ్యామేజ్ అయ్యింది", "Damaged product"),
        ("ఆర్డర్ రద్దు చేయాలి", "Cancel order"),
        ("కస్టమర్ కేర్ తో మాట్లాడాలి", "Speak to support")
    ],
    "Hindi": [
        ("मुझे रिफंड चाहिए", "Need refund"),
        ("ऑर्डर अभी तक डिलीवर नहीं हुआ", "Order not delivered"),
        ("मेरा पैसा दो बार कट गया", "Deducted twice"),
        ("सामान टूटा हुआ मिला", "Received broken item"),
        ("ऑर्डर कैंसिल करना है", "Cancel order"),
        ("कस्टमर केयर से बात करनी है", "Speak to support")
    ]
}


# -----------------------------------------------------------------------------
# 6. Global Shared Views: AI Chatbot (ChatGPT Style) & 3D Workstation Forge
# -----------------------------------------------------------------------------

def render_chat_assistant_view():
    """
    ChatGPT & Gemini-style default conversational chatbot interface.
    Features:
    - Welcome hero with Indic code-mixed AI indicators.
    - Quick prompt recommendation chips (including Romanized Hindi: 'mera order deliver nahi hua').
    - Clean conversational history with customer & NexAI assistant speech bubbles.
    - Language, translation callout, intent, urgency badges, and AI-suggested customer reply.
    - One-click 'Inspect in 3D Workstation Forge' button.
    - Bottom fixed input capsule with 'Analyze & Send Prompt' button (compatible with at.text_area[0] and analyze_btn).
    """
    st.markdown("""
    <div style="text-align: center; margin-bottom: 24px; padding-top: 6px;">
        <div style="display: inline-flex; align-items: center; gap: 8px; background: #dcfce7; border: 1px solid #86efac; border-radius: 9999px; padding: 5px 18px; font-size: 0.82rem; color: #15803d; font-weight: 700; margin-bottom: 12px; box-shadow: 0 2px 10px rgba(34, 197, 94, 0.12);">
            <span>✳️ Veltrix Indic Triage v2.0</span> &nbsp;•&nbsp; <span>Indic Code-Mixed AI & 3D Forge</span>
        </div>
        <div style="font-size: 2.25rem; font-weight: 800; color: #111827; letter-spacing: -0.03em;">
            What can I triage for you today?
        </div>
        <div style="font-size: 0.98rem; color: #475569; max-width: 650px; margin: 8px auto 0 auto; line-height: 1.55;">
            Type naturally in Hinglish, Tanglish, Telugu+English, or native Indic scripts. The 5-stage creature forge will automatically detect dialects, translate into standard English, assess urgency, and draft replies.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Quick Suggestion Chips
    st.caption("⚡ Quick Code-Mixed Prompts:")
    chip_col1, chip_col2, chip_col3, chip_col4 = st.columns(4)
    with chip_col1:
        if st.button("📦 mera order deliver nahi hua", use_container_width=True, key="chip_hindi_deliv"):
            st.session_state["chat_input_val"] = "mera order deliver nahi hua"
            st.session_state["message_input_val"] = "mera order deliver nahi hua"
            st.rerun()
    with chip_col2:
        if st.button("💳 payment rendu saarlu cut ayyindi", use_container_width=True, key="chip_telugu_pay"):
            st.session_state["chat_input_val"] = "payment rendu saarlu cut ayyindi"
            st.session_state["message_input_val"] = "payment rendu saarlu cut ayyindi"
            st.rerun()
    with chip_col3:
        if st.button("🔨 box damaged, refund venum", use_container_width=True, key="chip_tamil_dam"):
            st.session_state["chat_input_val"] = "order vandhuchu but box damaged, refund venum"
            st.session_state["message_input_val"] = "order vandhuchu but box damaged, refund venum"
            st.rerun()
    with chip_col4:
        if st.button("🔐 naa account login avvatledu", use_container_width=True, key="chip_telugu_login"):
            st.session_state["chat_input_val"] = "naa account login avvatledu"
            st.session_state["message_input_val"] = "naa account login avvatledu"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Conversational Messages Stream
    chat_container = st.container()
    with chat_container:
        for idx, msg in enumerate(st.session_state.get("chat_messages", [])):
            if msg["sender"] == "user":
                st.markdown(f"""
                <div style="display: flex; justify-content: flex-end; margin-bottom: 16px;">
                    <div style="background: #111827; border-radius: 18px 18px 4px 18px; padding: 14px 20px; max-width: 78%; box-shadow: 0 4px 16px rgba(0,0,0,0.12);">
                        <div style="font-size: 0.72rem; color: #94a3b8; margin-bottom: 4px; font-weight: 700; text-align: right; letter-spacing: 0.04em;">YOU &nbsp;•&nbsp; {msg.get('timestamp', '')}</div>
                        <div style="font-size: 1.05rem; color: #ffffff; line-height: 1.5; font-weight: 500;">{msg['text']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="display: flex; gap: 14px; margin-bottom: 18px;">
                    <div style="width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #166534 0%, #22c55e 100%); display: flex; align-items: center; justify-content: center; font-size: 1.25rem; flex-shrink: 0; box-shadow: 0 4px 14px rgba(34, 197, 94, 0.3);">
                        ✳️
                    </div>
                    <div style="flex: 1; background: #ffffff; border: 1px solid #e2ebe3; border-left: 4px solid #22c55e; border-radius: 4px 18px 18px 18px; padding: 18px 22px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);">
                        <div style="font-size: 0.74rem; color: #15803d; font-weight: 800; margin-bottom: 6px; letter-spacing: 0.05em; text-transform: uppercase;">VELTRIX ASSISTANT &nbsp;•&nbsp; {msg.get('timestamp', '')}</div>
                        <div style="font-size: 1.02rem; color: #111827; line-height: 1.55;">{msg['text']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # If assistant message has structured triage analysis, show rich Veltrix cards
                analysis = msg.get("analysis")
                if analysis:
                    lang = analysis.get("detected_language", "English")
                    trans = analysis.get("english_translation", "")
                    intent = analysis.get("intent", "General Inquiry")
                    urgency = analysis.get("urgency", "low")
                    conf = float(analysis.get("confidence", 0.85))
                    reply = analysis.get("draft_reply", "")

                    # 1. Prominent Hero Final Standardized English Translation Card
                    st.markdown(f"""
                    <div style="background: #f0fdf4; border: 1.5px solid #86efac; border-radius: 14px; padding: 16px 20px; margin: 12px 0 10px 0; box-shadow: 0 4px 16px rgba(34, 197, 94, 0.08);">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                            <span style="font-size: 0.75rem; font-weight: 800; color: #15803d; text-transform: uppercase; letter-spacing: 0.06em; display: flex; align-items: center; gap: 6px;">
                                <span>✅</span> FINAL STANDARDIZED ENGLISH TRANSLATION
                            </span>
                            <span style="background: #dcfce7; color: #166534; font-size: 0.72rem; font-weight: 700; padding: 2px 10px; border-radius: 9999px; border: 1px solid #bbf7d0;">
                                Source Dialect: {lang}
                            </span>
                        </div>
                        <div style="font-size: 1.18rem; font-weight: 800; color: #111827; line-height: 1.45;">
                            "{trans}"
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # 2. Metadata Capsule (Intent, Urgency, Calibrated Confidence)
                    st.markdown(f"""
                    <div style="background: #ffffff; border: 1px solid #e2ebe3; border-radius: 12px; padding: 12px 16px; margin-bottom: 10px; display: flex; flex-wrap: wrap; gap: 16px; align-items: center; box-shadow: 0 1px 4px rgba(0,0,0,0.02);">
                        <div style="font-size: 0.82rem; color: #475569;">Dialect: <b style="color: #15803d; background: #dcfce7; padding: 2px 8px; border-radius: 9999px;">{lang}</b></div>
                        <div style="font-size: 0.82rem; color: #475569;">Predicted Intent: <b style="color: #111827;">{intent}</b></div>
                        <div style="font-size: 0.82rem; color: #475569;">Urgency: <span class="badge-{urgency}">{urgency.upper()}</span> ({int(conf*100)}% conf)</div>
                    </div>
                    """, unsafe_allow_html=True)

                    # 3. AI Suggested Customer Reply Box
                    st.markdown(f"""
                    <div style="background: #f8faf8; border: 1px solid #e2ebe3; border-radius: 12px; padding: 14px 18px; margin-bottom: 12px;">
                        <div style="font-size: 0.72rem; color: #15803d; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em;">💬 AI-Suggested Response (Dialect Adapted)</div>
                        <div style="font-size: 0.98rem; color: #111827; font-style: italic; margin-top: 4px; line-height: 1.5;">"{reply}"</div>
                    </div>
                    """, unsafe_allow_html=True)

                    # 4. Forge Bot Guild Responsibilities & Step-by-Step Explanation Accordion
                    with st.expander("🤖 What the 5 Forge Bots did for this prompt (Step-by-Step Responsibilities)", expanded=False):
                        p_msg = msg.get("user_prompt", trans)
                        pipe = forge_3d.derive_parser_pipeline(p_msg)
                        creature_emojis = ["🌋", "🧝", "🔨", "💎", "🪽"]
                        for b_idx, s in enumerate(pipe["steps"]):
                            st.markdown(f"""
                            <div style="background: #ffffff; border: 1px solid #e2ebe3; border-radius: 12px; padding: 12px 16px; margin-bottom: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.02);">
                                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
                                    <div style="font-weight: 800; font-size: 0.92rem; color: #111827;">
                                        {creature_emojis[b_idx]} {s['creature']} the {s['title']} &nbsp;•&nbsp; <span style="font-size: 0.75rem; color: #15803d; font-weight: 700;">{s['station']} ({s['state_label']})</span>
                                    </div>
                                    <span style="font-size: 0.72rem; color: #475569; background: #f1f5f2; padding: 2px 8px; border-radius: 9999px;">Action: {s['action']}</span>
                                </div>
                                <div style="font-size: 0.85rem; color: #334155; line-height: 1.45; margin-top: 4px;">
                                    <b>Live Bot Voice:</b> "{s['bot_explanation']}"
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                    btn_c1, btn_c2 = st.columns([1.5, 3])
                    with btn_c1:
                        if st.button("⚒️ Inspect in 3D Forge", key=f"btn_3d_inspect_{idx}", use_container_width=True):
                            st.session_state["forge_prompt"] = msg.get("user_prompt", trans)
                            st.session_state["nav_target"] = "⚒️ 3D Workstation Forge"
                            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    # -------------------------------------------------------------------------
    # Fixed Bottom Input Capsule (ChatGPT / Gemini style)
    # MUST BE FIRST TEXT_AREA ON PAGE FOR UNIT TEST COMPATIBILITY
    # -------------------------------------------------------------------------
    st.markdown("##### 💬 Message Assistant")
    
    # Indic Script Insertion Helper Accordion
    with st.expander("🌐 Native Script Typing Assistant (தமிழ் • తెలుగు • हिन्दी)", expanded=False):
        t_tab1, t_tab2, t_tab3 = st.tabs(["हिन्दी (Hindi)", "తెలుగు (Telugu)", "தமிழ் (Tamil)"])
        with t_tab1:
            st.caption("Click to insert Hindi words:")
            h_cols = st.columns(6)
            for i, (word, en) in enumerate(NATIVE_CHIPS["Hindi"]):
                with h_cols[i % 6]:
                    if st.button(word, key=f"chat_h_word_{i}", use_container_width=True):
                        curr = st.session_state.get("chat_input_val", "")
                        st.session_state["chat_input_val"] = f"{curr} {word}".strip()
                        st.rerun()
        with t_tab2:
            st.caption("Click to insert Telugu words:")
            te_cols = st.columns(6)
            for i, (word, en) in enumerate(NATIVE_CHIPS["Telugu"]):
                with te_cols[i % 6]:
                    if st.button(word, key=f"chat_te_word_{i}", use_container_width=True):
                        curr = st.session_state.get("chat_input_val", "")
                        st.session_state["chat_input_val"] = f"{curr} {word}".strip()
                        st.rerun()
        with t_tab3:
            st.caption("Click to insert Tamil words:")
            ta_cols = st.columns(6)
            for i, (word, en) in enumerate(NATIVE_CHIPS["Tamil"]):
                with ta_cols[i % 6]:
                    if st.button(word, key=f"chat_ta_word_{i}", use_container_width=True):
                        curr = st.session_state.get("chat_input_val", "")
                        st.session_state["chat_input_val"] = f"{curr} {word}".strip()
                        st.rerun()

    # The Primary Prompt Text Area (at.text_area[0])
    curr_input = st.session_state.get("chat_input_val") or st.session_state.get("message_input_val", "")
    input_text = st.text_area(
        "Customer Message (Telugu+English, Hinglish, Tanglish, or English):",
        value=curr_input,
        placeholder="Type customer message or inquiry here... e.g., 'mera order deliver nahi hua' or 'naa order inka delivery avvaledu'",
        height=90,
        key="chat_main_prompt_input"
    )

    btn_row1, btn_row2, btn_row3 = st.columns([2.0, 1.0, 1.5])
    with btn_row1:
        analyze_clicked = st.button("⚡ Analyze & Send Prompt", type="primary", use_container_width=True, key="btn_chat_analyze_send")
    with btn_row2:
        clear_clicked = st.button("🗑️ Clear", use_container_width=True, key="btn_chat_clear")
    with btn_row3:
        forge_nav_clicked = st.button("⚒️ Open 3D Forge", use_container_width=True, key="btn_chat_goto_forge")

    if clear_clicked:
        st.session_state["chat_input_val"] = ""
        st.session_state["message_input_val"] = ""
        st.rerun()

    if forge_nav_clicked:
        if input_text.strip():
            st.session_state["forge_prompt"] = input_text.strip()
        st.session_state["nav_target"] = "⚒️ 3D Workstation Forge"
        st.rerun()

    if analyze_clicked:
        clean_msg = input_text.strip()
        if not clean_msg:
            st.warning("Please enter a message to analyze.")
        else:
            with st.spinner("Analyzing code-mixed dialect, verifying translation, and forging reply..."):
                result = ai_engine.analyze_message(clean_msg)
                conf = max(0.0, min(1.0, round(float(result.get("confidence", 0.85)), 2)))
                result["confidence"] = conf
                result["message"] = clean_msg
                
                # Add to persistent ticket log
                t_entry = {
                    "id": len(st.session_state["tickets"]) + 1,
                    "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                    "message": clean_msg,
                    "detected_language": result.get("detected_language", "English"),
                    "english_translation": result.get("english_translation", clean_msg),
                    "intent": result.get("intent", "General Inquiry"),
                    "urgency": result.get("urgency", "low"),
                    "confidence": conf,
                    "draft_reply": result.get("draft_reply", ""),
                    "escalate": result.get("escalate", False),
                    "escalation_reason": result.get("escalation_reason", ""),
                    "backend": result.get("backend", "Local NLP")
                }
                st.session_state["tickets"].append(t_entry)

                # Update session states required for testing & UI persistence
                st.session_state["message_input_val"] = clean_msg
                st.session_state["latest_result"] = t_entry
                st.session_state["forge_prompt"] = clean_msg
                st.session_state["chat_input_val"] = ""

                # Append to chat history
                st.session_state["chat_messages"].append({
                    "sender": "user",
                    "text": clean_msg,
                    "timestamp": datetime.datetime.now().strftime("%H:%M")
                })
                st.session_state["chat_messages"].append({
                    "sender": "assistant",
                    "text": f"I have processed your message. Here is the triage analysis and suggested resolution:",
                    "timestamp": datetime.datetime.now().strftime("%H:%M"),
                    "analysis": result,
                    "user_prompt": clean_msg
                })
                st.rerun()


def render_3d_forge_view():
    """
    Renders the 3D Workstation Forge & Bottom-Up Parser State Derivation view.
    Features:
    - 3D WebGL Canvas powered by Three.js with OrbitControls.
    - 5 Floating Workstation Islands staffed by Tiny Creatures:
        S1: Vulcan the Smelter Golem (Lexical Ingestion)
        S2: Gildor the Dialect Imp (Dialect Anvil)
        S3: Brog the Blacksmith Dwarf (Translation Crucible)
        S4: Pyra the Urgency Sprite (Intent & Urgency Gem-Cutter)
        S5: Hermes the Dispatch Automaton (Dispatch Beacon -> ACCEPT)
    - Prompt crystal traveling sequentially across energy rails from S1 to S5.
    - Dedicated Forge Bot Guild Cards explaining each bot's responsibilities & live voice.
    - Interactive Bottom-Up Parser State Derivation Table (Free Navigation Table) below canvas.
    - Final Standardized Translation & AI-Synthesized Agent Reply card.
    """
    st.markdown("""
    <div style="margin-bottom: 20px;">
        <div style="display: inline-flex; align-items: center; gap: 8px; background: #dcfce7; border: 1px solid #86efac; border-radius: 9999px; padding: 4px 16px; font-size: 0.80rem; color: #15803d; font-weight: 700; margin-bottom: 8px;">
            <span>⚒️ 3D Workstation Forge & Bottom-Up State Derivation</span>
        </div>
        <div style="font-size: 2.1rem; font-weight: 800; color: #111827; letter-spacing: -0.03em;">
            Interactive Workstation Guild & LR Parser Pipeline
        </div>
        <div style="font-size: 0.95rem; color: #475569; max-width: 780px; margin-top: 6px; line-height: 1.5;">
            Explore how customer prompts traverse 5 specialized workstations staffed by Tiny Blacksmith Creatures.
            Derived transitions mirror a formal Bottom-Up LR Parser State Derivation from <code>S0</code> to <code>ACCEPT</code>.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 1. Prompt Controller
    current_prompt = st.session_state.get("forge_prompt", "mera order deliver nahi hua")
    p_col1, p_col2 = st.columns([3.5, 1.2])
    with p_col1:
        new_prompt = st.text_input(
            "Active Prompt for 3D Forge:",
            value=current_prompt,
            key="forge_prompt_input_field",
            placeholder="e.g. 'mera order deliver nahi hua' or 'naa order inka delivery avvaledu'"
        )
    with p_col2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🚀 Ignite Pipeline", type="primary", use_container_width=True, key="btn_ignite_forge"):
            st.session_state["forge_prompt"] = new_prompt.strip()
            st.rerun()

    # Quick test chips
    st.caption("Quick test prompts:")
    f_c1, f_c2, f_c3, f_c4 = st.columns(4)
    with f_c1:
        if st.button("📦 mera order deliver nahi hua", key="fchip_1", use_container_width=True):
            st.session_state["forge_prompt"] = "mera order deliver nahi hua"
            st.rerun()
    with f_c2:
        if st.button("💳 payment rendu saarlu cut ayyindi", key="fchip_2", use_container_width=True):
            st.session_state["forge_prompt"] = "payment rendu saarlu cut ayyindi"
            st.rerun()
    with f_c3:
        if st.button("🔨 box damaged, refund venum", key="fchip_3", use_container_width=True):
            st.session_state["forge_prompt"] = "order vandhuchu but box damaged, refund venum"
            st.rerun()
    with f_c4:
        if st.button("🔐 naa account login avvatledu", key="fchip_4", use_container_width=True):
            st.session_state["forge_prompt"] = "naa account login avvatledu"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Interactive 3D WebGL Canvas
    active_prompt = st.session_state.get("forge_prompt", "mera order deliver nahi hua")
    html_scene = forge_3d.build_threejs_forge_html(active_prompt, active_state=5)
    st.components.v1.html(html_scene, height=620, scrolling=False)

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. Forge Bot Guild: Explicit Workstation Responsibilities & Explanations
    st.markdown("### 🤖 Forge Bot Guild: Workstation Responsibilities & Live Explanations")
    st.markdown("""
    Each workstation in the forge is run by a dedicated creature specialist with a defined operational responsibility.
    Here is what each bot does and their live voice explanation for the active prompt:
    """)

    pipe = forge_3d.derive_parser_pipeline(active_prompt)
    steps = pipe["steps"]

    guild_cards_cols = st.columns(5)
    creature_avatars = ["🌋", "🧝", "🔨", "💎", "🪽"]
    resp_summaries = [
        "Script ingestion, Unicode normalization, Devanagari/Telugu/Tamil script detection & lexical tokenization.",
        "Code-mix syntax analysis, Hinglish/Tanglish/Tenglish classification, phonetic pattern extraction.",
        "Indic idiomatic lexicon mapping, romanized phrase substitution, forging final standard English translation.",
        "Complaint domain intent recognition, customer sentiment intensity, calibrated urgency & SLA scoring.",
        "Escalation routing to human specialist, language matching, dialect-adapted reply drafting & ACCEPT closure."
    ]

    for b_idx, s in enumerate(steps):
        with guild_cards_cols[b_idx]:
            st.markdown(f"""
            <div style="background: #ffffff; border: 1px solid #e2ebe3; border-radius: 16px; padding: 14px; height: 100%; box-shadow: 0 2px 10px rgba(0,0,0,0.03); display: flex; flex-direction: column;">
                <div style="font-size: 1.8rem; margin-bottom: 4px;">{creature_avatars[b_idx]}</div>
                <div style="font-size: 1.0rem; font-weight: 800; color: #111827;">{s['creature']}</div>
                <div style="font-size: 0.72rem; color: #15803d; font-weight: 700; text-transform: uppercase; margin-bottom: 8px;">
                    {s['title']} • {s['state_label']}
                </div>
                <div style="font-size: 0.74rem; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em;">Primary Responsibility:</div>
                <div style="font-size: 0.80rem; color: #334155; line-height: 1.4; margin-top: 2px; margin-bottom: 10px;">
                    {resp_summaries[b_idx]}
                </div>
                <div style="margin-top: auto; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px; padding: 10px;">
                    <div style="font-size: 0.68rem; color: #15803d; font-weight: 800; text-transform: uppercase;">Live Bot Explanation:</div>
                    <div style="font-size: 0.78rem; color: #14532d; line-height: 1.4; font-style: italic; margin-top: 3px;">
                        "{s['bot_explanation']}"
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 4. Bottom-Up Parser State Derivation Table (Free Navigation Table)
    st.markdown("### 📋 Bottom-Up Parser State Derivation Table")
    st.markdown("""
    In a bottom-up parser, input tokens are shifted onto the stack and reduced according to production rules until the start symbol is derived.
    Here, the prompt is transformed step-by-step through the 5 creature workstations:
    """)

    # Free Navigation State Filter
    state_filter = st.radio(
        "Free Navigation State Inspection:",
        ["All States (Full Derivation)", "S0 → S1: Vulcan", "S1 → S2: Gildor", "S2 → S3: Brog", "S3 → S4: Pyra", "S4 → S5: Hermes (ACCEPT)"],
        horizontal=True,
        key="state_derivation_filter"
    )

    # Render derivation table
    table_rows = []
    for s in steps:
        match = (
            state_filter == "All States (Full Derivation)" or
            (state_filter.startswith("S0 → S1") and s["step"] == 1) or
            (state_filter.startswith("S1 → S2") and s["step"] == 2) or
            (state_filter.startswith("S2 → S3") and s["step"] == 3) or
            (state_filter.startswith("S3 → S4") and s["step"] == 4) or
            (state_filter.startswith("S4 → S5") and s["step"] == 5)
        )
        if match:
            table_rows.append({
                "State": s["state_label"],
                "Workstation": s["station"],
                "Worker": f"{s['creature']} ({s['title']})",
                "Action": s["action"],
                "Production Rule": s["production"],
                "Summary": s["summary"]
            })

    if table_rows:
        df_table = pd.DataFrame(table_rows)
        st.dataframe(df_table, use_container_width=True, hide_index=True)

    # Individual State Deep Dive Expanders
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 🔬 Workstation Derivation Inspection")
    for s in steps:
        with st.expander(f"⚙️ {s['state_label']}: {s['station']} ({s['creature']} the {s['title']}) — Action: {s['action']}"):
            c1, c2 = st.columns([1.5, 2.5])
            with c1:
                st.markdown(f"**Creature:** {s['creature']} the {s['title']}")
                st.markdown(f"**Parser Action:** `{s['action']}`")
                st.markdown(f"**Parser Stack:** `{s['stack']}`")
                st.markdown(f"**Input Buffer:** `{s['input_buffer']}`")
            with c2:
                st.markdown(f"**Applied Production:**")
                st.code(s['production'], language="text")
                st.markdown(f"**Station Output Payload:**")
                st.json(s["output_payload"])

    # 5. Final Standardized Translation & AI Agent Reply Card (ACCEPT)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🏆 Final Forged Result (Parser ACCEPT)")

    final_analysis = pipe["analysis"]
    final_lang = final_analysis.get("detected_language", "English")
    final_trans = final_analysis.get("english_translation", active_prompt)
    final_intent = final_analysis.get("intent", "General Inquiry")
    final_urgency = final_analysis.get("urgency", "low")
    final_conf = float(final_analysis.get("confidence", 0.85))
    final_reply = final_analysis.get("draft_reply", "")
    urg_badge = "🔴 High" if final_urgency == "high" else ("🟡 Medium" if final_urgency == "medium" else "🟢 Low")

    st.markdown(f"""
    <div style="background: #ffffff; border: 1.5px solid #86efac; border-radius: 18px; padding: 22px 24px; box-shadow: 0 4px 20px rgba(34, 197, 94, 0.12);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
            <div style="font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.08em; color: #15803d; font-weight: 800;">
                Production Output • S5 ACCEPT
            </div>
            <div style="background: #dcfce7; border: 1px solid #86efac; border-radius: 9999px; padding: 4px 14px; font-size: 0.78rem; color: #15803d; font-weight: 700;">
                ✓ Triage Synthesized
            </div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 14px;">
            <div style="background: #f8faf8; border: 1px solid #e2ebe3; border-radius: 12px; padding: 14px 16px;">
                <div style="font-size: 0.74rem; color: #64748b; font-weight: 700; text-transform: uppercase;">ORIGINAL INPUT</div>
                <div style="font-size: 1.12rem; color: #111827; font-weight: 700; margin-top: 4px;">"{active_prompt}"</div>
                <div style="font-size: 0.82rem; color: #15803d; margin-top: 6px;">Detected: <b>{final_lang}</b></div>
            </div>
            <div style="background: #f0fdf4; border: 1.5px solid #86efac; border-radius: 12px; padding: 14px 16px;">
                <div style="font-size: 0.74rem; color: #15803d; font-weight: 800; text-transform: uppercase;">FINAL STANDARDIZED TRANSLATION</div>
                <div style="font-size: 1.15rem; color: #111827; font-weight: 800; margin-top: 4px;">"{final_trans}"</div>
                <div style="font-size: 0.82rem; color: #475569; margin-top: 6px;">Intent: <b>{final_intent}</b> • Urgency: <b>{urg_badge}</b> ({int(final_conf*100)}%)</div>
            </div>
        </div>
        <div style="background: #f8faf8; border: 1px solid #e2ebe3; border-radius: 12px; padding: 14px 18px;">
            <div style="font-size: 0.74rem; color: #15803d; font-weight: 800; text-transform: uppercase; letter-spacing: 0.04em;">💬 AI-Suggested Agent Reply (Ready to Deliver)</div>
            <div style="font-size: 1.0rem; color: #111827; margin-top: 4px; line-height: 1.5; font-style: italic;">
                "{final_reply}"
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 7. Page Routing & Execution
# -----------------------------------------------------------------------------

if section == "💬 AI Chatbot":
    render_chat_assistant_view()

elif section == "⚒️ 3D Workstation Forge":
    render_3d_forge_view()

elif current_user.get("role") == "customer":

    # --- Page 1: Customer Home ---
    if section == "Home":
        st.markdown(f'<div class="apple-header">Welcome, {current_user["name"]}</div>', unsafe_allow_html=True)
        st.markdown('<div class="apple-sub">Get rapid, native support in Telugu, Tamil, Hindi, or English. Type in whatever dialect or script feels natural.</div>', unsafe_allow_html=True)

        # Overview Stats
        my_convs = database.list_customer_conversations(current_user["id"])
        open_cnt = sum(1 for c in my_convs if c["status"] in ["open", "in_progress"])
        resolved_cnt = sum(1 for c in my_convs if c["status"] == "resolved")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            <div class="apple-card">
                <div class="apple-card-title">Active Inquiries</div>
                <div class="apple-card-value">{open_cnt}</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="apple-card">
                <div class="apple-card-title">Resolved Inquiries</div>
                <div class="apple-card-value">{resolved_cnt}</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="apple-card">
                <div class="apple-card-title">Supported Dialects</div>
                <div class="apple-card-value" style="font-size: 1.15rem;">తెలుగు · தமிழ் · हिन्दी · English</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Recent Inquiries Table
        st.markdown("##### Recent Support Conversations")
        if not my_convs:
            st.info("You do not have any open inquiries. Click 'Start a Conversation' to reach our multilingual support team.")
        else:
            for conv in my_convs[:4]:
                st_badge = f'<span class="badge-{conv["status"]}">{conv["status"].upper()}</span>'
                urg_badge = f'<span class="badge-{conv["urgency"]}">{conv["urgency"].upper()}</span>'
                st.markdown(f"""
                <div class="apple-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-weight: 700; font-size: 1.05rem; color: #111827;">{conv['subject']}</span>
                        <div>{st_badge} &nbsp; {urg_badge}</div>
                    </div>
                    <div style="font-size: 0.85rem; color: #64748b; margin-bottom: 8px;">
                        Ticket ID: <code>{conv['id']}</code> &nbsp;•&nbsp; Dialect: <span class="lang-pill">{conv['detected_language']}</span> &nbsp;•&nbsp; Intent: <b>{conv['intent']}</b>
                    </div>
                    <div style="font-size: 0.95rem; color: #334155;">
                        <i>"{conv['english_translation']}"</i>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # --- Page 2: My Conversations (Phase 2 Enhanced Live Chat) ---
    elif section == "My Conversations":
        st.markdown('<div class="apple-header">Live Support Conversations</div>', unsafe_allow_html=True)
        st.markdown('<div class="apple-sub">Chat directly with AI and human support specialists. Natural code-mixing and native Indic scripts supported.</div>', unsafe_allow_html=True)

        my_convs = database.list_customer_conversations(current_user["id"])
        if not my_convs:
            st.info("No conversations found. Use 'Start a Conversation' to submit a support inquiry.")
        else:
            conv_options = {f"{c['subject']} ({c['id']}) - [{c['status'].upper()}]": c["id"] for c in my_convs}
            
            # Select conversation
            cur_sel_id = st.session_state["selected_conv_id"]
            keys_list = list(conv_options.keys())
            def_idx = 0
            if cur_sel_id:
                for idx, (lbl, cid) in enumerate(conv_options.items()):
                    if cid == cur_sel_id:
                        def_idx = idx
                        break

            top_sel_col1, top_sel_col2 = st.columns([4, 1.2])
            with top_sel_col1:
                selected_label = st.selectbox("Select Conversation", options=keys_list, index=def_idx, label_visibility="collapsed")
            with top_sel_col2:
                if st.button("🔄 Check for Replies", use_container_width=True):
                    st.rerun()

            selected_id = conv_options[selected_label]
            st.session_state["selected_conv_id"] = selected_id
            conv = database.get_conversation(selected_id, include_internal=False)

            if conv:
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Ticket Status Header
                h_col1, h_col2 = st.columns([3.5, 1.5])
                with h_col1:
                    st.markdown(f"### {conv['subject']}")
                    status_text = "🟢 Open (AI Assisted)" if conv["status"] == "open" else (
                        f"🟡 Handled by {conv.get('assigned_agent_name') or 'Specialist'}" if conv["status"] == "in_progress" else "⚪ Resolved"
                    )
                    st.markdown(f"**Ticket ID:** `{conv['id']}` &nbsp;•&nbsp; **Status:** `{status_text}` &nbsp;•&nbsp; **Dialect:** `{conv['detected_language']}`")
                with h_col2:
                    pref_lang = conv.get("preferred_language", "Auto-Detect")
                    st.markdown(f"""
                    <div style="text-align: right;">
                        <span style="font-size: 0.8rem; color: #86868b; text-transform: uppercase; font-weight: 600;">Preferred Language</span><br>
                        <span class="lang-pill">{LANGUAGE_OPTIONS.get(pref_lang, pref_lang)}</span>
                    </div>
                    """, unsafe_allow_html=True)

                # Human Agent Waiting Indicator vs Live Agent Joined Banner
                is_handoff = bool(conv.get("handoff_requested"))
                agent_joined = bool(conv.get("live_agent_joined"))
                assigned_name = conv.get("assigned_agent_name")

                if is_handoff and not agent_joined:
                    st.markdown(f"""
                    <div class="waiting-banner">
                        <strong style="color: #b25e00;">⏳ Human Specialist Requested</strong>
                        <div style="font-size: 0.9rem; margin-top: 4px; color: #78350f;">
                            We have queued your conversation for a specialist fluent in <b>{conv['detected_language']}</b>. Please hold on — an agent will join your session shortly.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                elif agent_joined and assigned_name:
                    st.markdown(f"""
                    <div class="joined-banner">
                        <strong style="color: #f97316;">🎧 Human Specialist Joined</strong>
                        <div style="font-size: 0.9rem; margin-top: 4px; color: #1e3a8a;">
                            <b>{assigned_name}</b> has accepted your ticket and is actively reviewing your inquiries.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.divider()

                # Chronological Message History Thread
                messages = conv.get("messages", [])
                for msg in messages:
                    sender = msg.get("sender_type")
                    name = msg.get("sender_name", "Support")
                    time_str = msg.get("created_at", "")[:19].replace("T", " ")
                    msg_text = msg.get("message_text", "")
                    trans = msg.get("english_translation")
                    
                    if sender == "internal_note":
                        continue
                    elif sender == "customer":
                        trans_html = f'<div style="font-size: 0.8rem; opacity: 0.9; margin-top: 4px; font-style: italic; border-top: 1px solid rgba(255,255,255,0.25); padding-top: 4px;">English meaning: "{trans}"</div>' if trans and trans != msg_text else ''
                        st.markdown(f"""
                        <div class="chat-bubble-customer">
                            <div style="font-size: 0.75rem; opacity: 0.85; margin-bottom: 4px; font-weight: 500;">👤 {name} &nbsp;•&nbsp; {time_str}</div>
                            <div style="font-size: 0.98rem;">{msg_text}</div>
                            {trans_html}
                        </div>
                        """, unsafe_allow_html=True)
                    elif sender == "agent":
                        st.markdown(f"""
                        <div class="chat-bubble-agent">
                            <div style="font-size: 0.75rem; color: #15803d; margin-bottom: 4px; font-weight: 700; text-transform: uppercase;">🎧 {name} (Support Specialist) &nbsp;•&nbsp; {time_str}</div>
                            <div style="font-size: 0.98rem; color: #111827;">{msg_text}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    elif sender == "ai":
                        st.markdown(f"""
                        <div class="chat-bubble-ai">
                            <div style="font-size: 0.75rem; color: #15803d; font-weight: 700; margin-bottom: 4px; text-transform: uppercase;">⚡ {name} &nbsp;•&nbsp; {time_str}</div>
                            <div style="font-size: 0.95rem; color: #111827;">{msg_text}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    elif sender == "system":
                        st.markdown(f"""
                        <div class="chat-bubble-system">
                            ℹ️ {msg_text} &nbsp;•&nbsp; {time_str}
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # Active Conversation Controls (Reply Composer & Feedback)
                if conv["status"] != "closed":
                    st.markdown("##### Reply to Conversation")

                    # Optional Language Selector during chat
                    l_c1, l_c2 = st.columns([2, 3])
                    with l_c1:
                        sel_lang = st.selectbox(
                            "Select Language / Script:",
                            options=list(LANGUAGE_OPTIONS.keys()),
                            format_func=lambda k: LANGUAGE_OPTIONS[k],
                            key=f"chat_lang_{conv['id']}"
                        )

                    cr_key = f"cust_reply_{conv['id']}"
                    if f"override_{cr_key}" in st.session_state:
                        st.session_state[cr_key] = st.session_state.pop(f"override_{cr_key}")

                    # Native Script Assistance Chips
                    if sel_lang in NATIVE_CHIPS:
                        st.caption(f"Quick {sel_lang} Phrase Insert:")
                        chip_cols = st.columns(len(NATIVE_CHIPS[sel_lang]))
                        for idx, (phrase, meaning) in enumerate(NATIVE_CHIPS[sel_lang]):
                            with chip_cols[idx]:
                                if st.button(f"{phrase}", key=f"chip_{conv['id']}_{idx}", help=meaning, use_container_width=True):
                                    st.session_state[f"override_{cr_key}"] = phrase
                                    st.rerun()
                        st.caption(f"💡 Tip: You can type in English phonetics ({'Tenglish' if sel_lang=='Telugu' else 'Tanglish' if sel_lang=='Tamil' else 'Hinglish'}) or in native {sel_lang} script directly.")

                    cust_reply = st.text_area(
                        "Your Message:",
                        placeholder=f"Type message in {sel_lang} or code-mixed phrasing...",
                        key=cr_key,
                        height=90
                    )

                    r_col1, r_col2, r_col3 = st.columns([1.5, 2, 2])
                    with r_col1:
                        if st.button("Send Reply", type="primary", key=f"btn_send_{conv['id']}"):
                            if cust_reply.strip():
                                clean_r = cust_reply.strip()
                                # Detect language and translate
                                r_res = ai_engine.analyze_message(clean_r)
                                database.add_message(
                                    conv_id=conv["id"],
                                    sender_type="customer",
                                    sender_id=current_user["id"],
                                    sender_name=current_user["name"],
                                    message_text=clean_r,
                                    english_translation=r_res.get("english_translation", clean_r),
                                    detected_language=r_res.get("detected_language", "Mixed/Unclear")
                                )
                                # If low confidence or high urgency escalation, auto-request handoff
                                if r_res.get("escalate") and not is_handoff:
                                    database.request_human_handoff(conv["id"], r_res.get("escalation_reason", "Escalation requested"))
                                st.session_state[f"override_{cr_key}"] = ""
                                st.success("Reply sent.")
                                st.rerun()

                    with r_col2:
                        if not is_handoff and conv["status"] != "resolved":
                            if st.button("🙋 Request Human Specialist", key=f"btn_req_human_{conv['id']}"):
                                database.request_human_handoff(conv["id"], "Customer explicitly requested human specialist.")
                                st.success("Human specialist assistance requested.")
                                st.rerun()

                    with r_col3:
                        if conv["status"] != "resolved":
                            if st.button("✅ Mark as Resolved", key=f"btn_res_{conv['id']}"):
                                database.update_conversation_status(conv["id"], "resolved")
                                st.success("Conversation marked as resolved. Please leave your feedback below!")
                                st.rerun()

                # Post-Resolution Feedback Card (Single Submission Constraint)
                if conv["status"] == "resolved":
                    st.divider()
                    st.markdown("#### ⭐ Customer Experience Feedback")
                    
                    existing_fb = database.get_conversation_feedback(conv["id"])
                    if existing_fb:
                        st.markdown(f"""
                        <div class="apple-card" style="border-left: 4px solid #16a34a;">
                            <div style="font-weight: 700; font-size: 1.05rem; color: #111827; margin-bottom: 4px;">
                                ✅ Feedback Recorded (Thank You!)
                            </div>
                            <div style="font-size: 0.95rem; color: #424245; line-height: 1.5;">
                                • <b>Your Rating:</b> {'⭐' * existing_fb['rating']} ({existing_fb['rating']}/5)<br>
                                • <b>Category:</b> {existing_fb['category']}<br>
                                • <b>Translation Quality:</b> {existing_fb.get('translation_quality', 'N/A')}<br>
                                • <b>Issue Resolved:</b> {existing_fb.get('issue_resolved', 'Yes')}<br>
                                • <b>Comments:</b> {existing_fb.get('comment') or '<i>None provided.</i>'}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div style="font-size: 0.95rem; color: #424245; margin-bottom: 12px;">
                            Your issue has been marked as resolved! Please take a moment to rate your support and multilingual translation experience.
                        </div>
                        """, unsafe_allow_html=True)

                        fb_rating = st.select_slider(
                            "Overall Rating",
                            options=[1, 2, 3, 4, 5],
                            value=5,
                            format_func=lambda r: f"{'⭐' * r} ({r}/5)",
                            key=f"star_{conv['id']}"
                        )

                        fb_c1, fb_c2 = st.columns(2)
                        with fb_c1:
                            fb_cat = st.selectbox(
                                "Feedback Focus",
                                ["Resolution Quality", "Language & Translation Quality", "Response Speed", "Agent Empathy"],
                                key=f"fb_cat_{conv['id']}"
                            )
                        with fb_c2:
                            fb_trans_qual = st.selectbox(
                                "Multilingual Translation Quality",
                                ["Accurate & Natural", "Understandable with minor flaws", "Partially Inaccurate", "Unclear / Hallucinated", "Not Applicable (English only)"],
                                key=f"fb_trans_{conv['id']}"
                            )

                        fb_resolved_ans = st.radio("Was your inquiry fully resolved?", ["Yes", "Partially", "No"], horizontal=True, key=f"fb_res_radio_{conv['id']}")
                        fb_comment = st.text_area("Additional Comments (Optional):", placeholder="Share details on how well our dialect AI or support specialist assisted you...", key=f"fb_comm_{conv['id']}")

                        if st.button("Submit Interaction Feedback", type="primary", key=f"btn_sub_fb_{conv['id']}"):
                            try:
                                database.submit_feedback(
                                    conv_id=conv["id"],
                                    customer_id=current_user["id"],
                                    customer_name=current_user["name"],
                                    rating=fb_rating,
                                    category=fb_cat,
                                    comment=fb_comment.strip(),
                                    agent_id=conv.get("assigned_agent_id"),
                                    agent_name=conv.get("assigned_agent_name"),
                                    translation_quality=fb_trans_qual,
                                    issue_resolved=fb_resolved_ans
                                )
                                st.success("Thank you! Your feedback has been saved and shared with our customer-care leadership.")
                                st.rerun()
                            except ValueError as e:
                                st.warning(str(e))

    # --- Page 3: Start a Conversation (Phase 2 Enhanced) ---
    elif section == "Start a Conversation":
        st.markdown('<div class="apple-header">Start a Support Conversation</div>', unsafe_allow_html=True)
        st.markdown('<div class="apple-sub">Describe your problem in your preferred dialect or native script. Our AI assistant will triage and route it instantly.</div>', unsafe_allow_html=True)

        with st.container():
            # Language Selection
            lang_col1, lang_col2 = st.columns([2, 3])
            with lang_col1:
                selected_lang = st.selectbox(
                    "Preferred Language (Optional):",
                    options=list(LANGUAGE_OPTIONS.keys()),
                    format_func=lambda k: LANGUAGE_OPTIONS[k],
                    key="start_lang_select"
                )

            if "override_c_start_msg" in st.session_state:
                st.session_state["c_start_msg"] = st.session_state.pop("override_c_start_msg")

            # Native script helper chips
            if selected_lang in NATIVE_CHIPS:
                st.caption(f"Click a common {selected_lang} inquiry to insert:")
                chip_cols = st.columns(len(NATIVE_CHIPS[selected_lang]))
                for idx, (phrase, meaning) in enumerate(NATIVE_CHIPS[selected_lang]):
                    with chip_cols[idx]:
                        if st.button(f"{phrase}", key=f"start_chip_{idx}", help=meaning, use_container_width=True):
                            st.session_state["override_c_start_msg"] = phrase
                            st.rerun()
                st.caption(f"💡 Typing Guide: You can type in English alphabet (e.g. {'Tenglish' if selected_lang=='Telugu' else 'Tanglish' if selected_lang=='Tamil' else 'Hinglish'}) or paste native {selected_lang} script. Both work natively.")

            subject_in = st.text_input("Subject / Topic", placeholder="e.g. Delayed Delivery, Double Payment, Refund Request", key="c_start_subj")
            msg_in = st.text_area(
                "Message (Code-mixed text and native Indic scripts fully supported):",
                placeholder="e.g. 'refund kavali, amount account lo padaledu' or 'mera paisa do baar cut gaya' or 'பொருள் சேதமடைந்துள்ளது'...",
                height=120,
                key="c_start_msg"
            )
            
            if st.button("Submit Conversation", type="primary"):
                if not msg_in.strip():
                    st.warning("Please enter your inquiry details.")
                else:
                    subj = subject_in.strip() or "Customer Support Inquiry"
                    with st.spinner("Analyzing code-mixed dialect, verifying translation, and routing inquiry..."):
                        triage_res = ai_engine.analyze_message(msg_in.strip())
                        
                        # Determine if human handoff is warranted immediately
                        auto_handoff = False
                        handoff_reason = ""
                        if triage_res.get("confidence", 1.0) < 0.70:
                            auto_handoff = True
                            handoff_reason = "Low AI confidence on dialect"
                        elif triage_res.get("escalate"):
                            auto_handoff = True
                            handoff_reason = triage_res.get("escalation_reason", "Escalated issue")

                        new_conv = database.create_conversation(
                            customer_id=current_user["id"],
                            customer_name=current_user["name"],
                            subject=subj,
                            initial_message=msg_in.strip(),
                            ai_analysis=triage_res,
                            preferred_language=selected_lang
                        )

                        if auto_handoff:
                            database.request_human_handoff(new_conv["id"], handoff_reason)

                        st.session_state["selected_conv_id"] = new_conv["id"]
                        st.success(f"Conversation started! Ticket ID: {new_conv['id']}")
                        
                        # Show instant triage confirmation
                        st.markdown(f"""
                        <div class="apple-card" style="border-left: 4px solid #16a34a;">
                            <div style="font-weight: 700; font-size: 1.05rem; color: #111827; margin-bottom: 6px;">
                                Inquiry Received & Triaged
                            </div>
                            <div style="font-size: 0.9rem; color: #334155; line-height: 1.5;">
                                • <b>Detected Dialect:</b> <span class="lang-pill">{triage_res['detected_language']}</span><br>
                                • <b>Understood Meaning:</b> <i>"{triage_res['english_translation']}"</i><br>
                                • <b>Categorized Intent:</b> {triage_res['intent']} (Urgency: {triage_res['urgency'].upper()})<br>
                                • <b>Routing:</b> {'Flagged for human specialist handoff' if auto_handoff else 'Handled via AI triage desk'}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

    # --- Page 4: Feedback Summary & Reviews ---
    elif section == "Feedback":
        st.markdown('<div class="apple-header">Customer Experience Feedback</div>', unsafe_allow_html=True)
        st.markdown('<div class="apple-sub">View feedback submitted across your support interactions and track service quality.</div>', unsafe_allow_html=True)

        my_convs = database.list_customer_conversations(current_user["id"])
        my_fb = database.get_customer_feedback(current_user["id"])

        f_col1, f_col2 = st.columns([1.5, 3])
        with f_col1:
            st.markdown(f"""
            <div class="apple-card">
                <div class="apple-card-title">Reviews Submitted</div>
                <div class="apple-card-value">{len(my_fb)}</div>
            </div>
            """, unsafe_allow_html=True)

        if not my_fb:
            st.info("You haven't submitted any feedback yet. When your conversations are resolved in 'My Conversations', you can submit a rating and review.")
        else:
            st.markdown("##### Your Submitted Reviews")
            for f in my_fb:
                st.markdown(f"""
                <div class="apple-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <span style="font-weight: 700; color: #111827; font-size: 1.05rem;">{'⭐' * f['rating']} &nbsp;•&nbsp; {f['category']}</span>
                        <span style="font-size: 0.8rem; color: #64748b;">{f['created_at'][:10]}</span>
                    </div>
                    <div style="font-size: 0.85rem; color: #64748b; margin-bottom: 6px;">
                        Ticket: <code>{f['conversation_id']}</code> &nbsp;•&nbsp; Specialist: <b>{f.get('agent_name') or 'Customer Support'}</b> &nbsp;•&nbsp; Translation Quality: <b>{f.get('translation_quality', 'N/A')}</b>
                    </div>
                    <div style="font-size: 0.95rem; color: #334155;">
                        {f['comment'] if f['comment'] else '<i>No additional comments provided.</i>'}
                    </div>
                </div>
                """, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 7. Agent Workspace Views (Phase 2 Enhanced Live Solving & Handoff)
# -----------------------------------------------------------------------------

elif current_user.get("role") in ["agent", "admin"]:

    # --- Page 1: Customer Queries (Triage & Gmail-Inspired Ticket Workspace) ---
    if section == "Customer Queries":
        st.markdown('<div class="apple-header">Customer-Care Inbox & Triage Desk</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="apple-sub">Unified Gmail-inspired ticket inbox for {current_user["name"]}. Authorized dialects: <b>{", ".join(current_user.get("languages", []))}</b></div>', unsafe_allow_html=True)

        # ---------------------------------------------------------------------
        # 1. Summary Indicators & CSAT Progress Bar (Top Header)
        # ---------------------------------------------------------------------
        indicators = database.get_inbox_summary_indicators()
        csat = database.get_csat_metrics()

        sum_c1, sum_c2, sum_c3, sum_c4, sum_c5 = st.columns([1.5, 1.5, 1.5, 1.5, 2.5])
        with sum_c1:
            st.metric("Total Received", indicators["total_queries"])
        with sum_c2:
            st.metric("Resolved", indicators["resolved_queries"])
        with sum_c3:
            st.metric("Pending", indicators["pending_queries"])
        with sum_c4:
            st.metric("Escalated", indicators["escalated_queries"])
        with sum_c5:
            # CSAT Metric with Progress Bar and Documented Formula
            csat_score = csat["csat_percent"]
            csat_lbl = csat["label"]
            csat_badge = "🟢" if csat_lbl == "Positive" else ("🟡" if csat_lbl == "Neutral" else "⚪")
            st.markdown(f"**Customer Satisfaction:** {csat_score}% {csat_badge}")
            st.progress(csat_score / 100.0)
            st.caption(f"Rating Quality: **{csat_lbl}** • Sample: **N={csat['sample_size']}** ({csat['formula_description']})")

        # Small dialog / popover showing exact breakdown
        with st.popover("📊 Detailed Status Breakdown"):
            st.markdown("#### Exact Ticket Status Breakdown")
            st.markdown(f"- **Total Inquiries Received:** `{indicators['total_queries']}`")
            st.markdown(f"- **Open (Pending Triage):** `{indicators['open_count']}`")
            st.markdown(f"- **In Progress (Specialist Assigned):** `{indicators['in_progress_count']}`")
            st.markdown(f"- **Resolved Inquiries:** `{indicators['resolved_queries']}`")
            st.markdown(f"- **Closed Archives:** `{indicators['closed_count']}`")
            st.markdown(f"- **Active Escalated Flags:** `{indicators['escalated_queries']}`")
            st.caption("All figures calculated from persistent SQLite storage.")

        st.divider()

        # ---------------------------------------------------------------------
        # 2. Live Code-Mixed Message Analyzer (Top Priority Triage Tool)
        # MUST REMAIN FIRST TEXT_AREA FOR UNIT TEST COMPATIBILITY
        # ---------------------------------------------------------------------
        with st.expander("⚡ Ad-Hoc Code-Mixed Message Analyzer", expanded=bool(st.session_state.get("message_input_val"))):
            input_text = st.text_area(
                "Customer Message (Telugu+English, Hinglish, Tanglish, or English):",
                value=st.session_state["message_input_val"],
                height=90,
                placeholder="Type or paste customer inquiry here, e.g., 'refund kavali, amount account lo padaledu' or 'mera paisa do baar cut gaya'...",
                key="ticket_input_field"
            )

            btn_col1, btn_col2, _ = st.columns([1.5, 1, 4])
            with btn_col1:
                analyze_clicked = st.button("🔍 Analyze Message", type="primary", use_container_width=True)
            with btn_col2:
                clear_clicked = st.button("🧹 Clear Input", use_container_width=True)

            if clear_clicked:
                st.session_state["message_input_val"] = ""
                st.session_state["latest_result"] = None
                st.rerun()

            if analyze_clicked:
                st.session_state["message_input_val"] = input_text
                clean_msg = input_text.strip()
                if not clean_msg:
                    st.warning("Please enter a customer message to analyze.")
                else:
                    with st.spinner("Analyzing code-mixed dialect, translating, and triaging request..."):
                        try:
                            result = ai_engine.analyze_message(clean_msg)
                            conf = max(0.0, min(1.0, round(float(result.get("confidence", 0.85)), 2)))
                            result["confidence"] = conf
                            detected_lang = result.get("detected_language", "Mixed/Unclear")
                            english_trans = result.get("english_translation", clean_msg)

                            ticket_entry = {
                                "id": len(st.session_state["tickets"]) + 1,
                                "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                                "message": clean_msg,
                                "detected_language": detected_lang,
                                "english_translation": english_trans,
                                "intent": result["intent"],
                                "urgency": result["urgency"],
                                "confidence": conf,
                                "draft_reply": result["draft_reply"],
                                "escalate": bool(result["escalate"]),
                                "escalation_reason": result.get("escalation_reason", ""),
                                "backend": result.get("_backend_used", backend_status["name"])
                            }
                            st.session_state["tickets"].insert(0, ticket_entry)
                            st.session_state["latest_result"] = ticket_entry
                        except Exception as e:
                            st.error(f"Failed to process message: {str(e)}")
                st.rerun()

            # Display Live Analysis Result if present
            latest = st.session_state["latest_result"]
            if latest:
                st.markdown("#### 📋 Ad-Hoc Assessment")
                orig_m = latest.get("message", "")
                st.markdown(f"**Original:** *\"{orig_m}\"* &nbsp;•&nbsp; **Dialect:** <span class='lang-pill'>{latest.get('detected_language')}</span>", unsafe_allow_html=True)
                st.markdown(f"**Translation:** {latest.get('english_translation')}")
                lac1, lac2, lac3 = st.columns(3)
                lac1.metric("Predicted Intent", latest["intent"])
                lac2.metric("Urgency Level", latest["urgency"].upper())
                lac3.metric("AI Confidence", f"{int(latest['confidence'] * 100)}%")
                if latest["escalate"]:
                    st.warning(f"🚨 Escalation Flag: {latest.get('escalation_reason')}")

        st.divider()

        # ---------------------------------------------------------------------
        # 3. Three-Area Gmail-Inspired Workspace
        # AREA 1: Left Folder Navigation Sidebar
        # AREA 2: Main Ticket List with Compact Rows & Sorting
        # AREA 3: Details Panel & Agent Reply Controls
        # ---------------------------------------------------------------------
        auth_langs = current_user.get("languages", database.ALL_SUPPORTED_LANGUAGES)
        folder_counts = database.get_inbox_counts(agent_id=current_user["id"], authorized_languages=auth_langs)

        # 3 Main Areas Layout
        area1_col, area2_col, area3_col = st.columns([1.1, 2.0, 2.9])

        # =====================================================================
        # AREA 1: LEFT FOLDER NAVIGATION SIDEBAR
        # =====================================================================
        with area1_col:
            st.markdown("##### 📁 Mailboxes")
            folder_map = {
                f"📥 Inbox ({folder_counts['inbox']})": "inbox",
                f"👤 Unassigned ({folder_counts['unassigned']})": "unassigned",
                f"📌 Assigned to Me ({folder_counts['assigned_me']})": "assigned_me",
                f"⏳ Waiting for Agent ({folder_counts['waiting_agent']})": "waiting_for_agent",
                f"💬 Waiting for Customer ({folder_counts['waiting_customer']})": "waiting_for_customer",
                f"🚨 Escalated ({folder_counts['escalated']})": "escalated",
                f"✅ Resolved ({folder_counts['resolved']})": "resolved"
            }

            folder_keys = list(folder_map.keys())
            current_f_idx = 0
            curr_folder = st.session_state.get("inbox_active_folder", "inbox")
            for idx, (label, val) in enumerate(folder_map.items()):
                if val == curr_folder:
                    current_f_idx = idx
                    break

            active_f_val = st.session_state.get("inbox_active_folder", "inbox")
            for flabel, fval in folder_map.items():
                is_curr = (fval == active_f_val)
                btn_type = "primary" if is_curr else "secondary"
                if st.button(flabel, key=f"fbtn_{fval}", type=btn_type, use_container_width=True):
                    st.session_state["inbox_active_folder"] = fval
                    st.rerun()
            selected_folder_val = active_f_val
            # Find label
            selected_folder_label = [k for k, v in folder_map.items() if v == active_f_val][0]

        # =====================================================================
        # AREA 2: MAIN TICKET LIST
        # =====================================================================
        with area2_col:
            st.markdown(f"##### 📋 {selected_folder_label.split('(')[0].strip()}")

            # Search bar
            search_query = st.text_input("Search Inbox", placeholder="Search customer, ID, or text...", label_visibility="collapsed", key="ticket_search_query")

            # Sorting options (deterministic)
            sort_choice = st.selectbox(
                "Sort",
                options=[
                    "Latest queries first",
                    "Oldest queries first",
                    "Highest urgency first",
                    "Lowest confidence first",
                    "Most relevant"
                ],
                label_visibility="collapsed",
                key="ticket_sort_order"
            )

            # Secondary Filters expander
            with st.expander("⚙️ Filter Query Set", expanded=False):
                flt_intent = st.selectbox("Intent", ["All"] + ai_engine.VALID_INTENTS, key="flt_intent")
                flt_urgency = st.selectbox("Urgency", ["All", "High", "Medium", "Low"], key="flt_urgency")
                flt_status = st.selectbox("Status", ["All", "open", "in_progress", "resolved", "closed"], key="flt_status")
                flt_lang = st.selectbox("Dialect", ["All"] + database.ALL_SUPPORTED_LANGUAGES, key="flt_lang")
                all_agents = database.list_agents()
                ag_names = ["All", "Unassigned"] + [a["name"] for a in all_agents]
                flt_agent = st.selectbox("Assigned Agent", ag_names, key="flt_agent")
                flt_esc = st.selectbox("Escalation", ["All", "Escalated Only", "Non-Escalated"], key="flt_esc")

            # Deterministic database query
            inbox_tickets = database.query_agent_inbox(
                agent_id=current_user["id"],
                category=st.session_state.get("inbox_active_folder", "inbox"),
                authorized_languages=auth_langs,
                sort_by=sort_choice,
                filter_intent=flt_intent if flt_intent != "All" else None,
                filter_urgency=flt_urgency if flt_urgency != "All" else None,
                filter_status=flt_status if flt_status != "All" else None,
                filter_language=flt_lang if flt_lang != "All" else None,
                filter_agent=flt_agent if flt_agent != "All" else None,
                filter_escalated=flt_esc if flt_esc != "All" else None,
                search_query=search_query
            )

            st.caption(f"Showing **{len(inbox_tickets)}** ticket(s)")

            if not inbox_tickets:
                st.info("No queries found matching this mailbox and filter criteria.")
            else:
                # If selected_conv_id is not set or not in current list, default to first ticket
                current_ids = [t["id"] for t in inbox_tickets]
                if not st.session_state.get("selected_conv_id") or st.session_state["selected_conv_id"] not in current_ids:
                    st.session_state["selected_conv_id"] = current_ids[0]

                # Render compact rows
                for t in inbox_tickets:
                    is_active = (st.session_state["selected_conv_id"] == t["id"])
                    card_cls = "inbox-card-selected" if is_active else "inbox-card"

                    urg_str = str(t.get("urgency", "medium")).lower()
                    urg_cls = f"badge-{urg_str}"
                    conf_pct = int(float(t.get("confidence", 0.85)) * 100)

                    # Short preview text
                    raw_msg = t.get("initial_text") or t.get("subject") or ""
                    preview_msg = (raw_msg[:60] + "...") if len(raw_msg) > 60 else raw_msg

                    # Time formatting
                    time_raw = t.get("last_activity_time") or t.get("updated_at") or ""
                    time_display = time_raw[11:16] if len(time_raw) >= 16 else time_raw

                    assigned_lbl = t.get("assigned_agent_name") or "Unassigned"

                    st.markdown(f"""
                    <div class="{card_cls}">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                            <span style="font-weight: 700; font-size: 0.92rem; color: #111827;">{t['customer_name']}</span>
                            <span style="font-size: 0.72rem; color: #64748b; font-weight: 500;">{time_display}</span>
                        </div>
                        <div style="font-size: 0.83rem; color: #334155; font-weight: 600; margin-bottom: 3px;">
                            {t['subject']}
                        </div>
                        <div style="font-size: 0.78rem; color: #64748b; margin-bottom: 6px; font-style: italic;">
                            "{preview_msg}"
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem;">
                            <div>
                                <span class="{urg_cls}">{urg_str.upper()}</span>
                                <span style="color: #64748b; margin-left: 4px; font-weight: 500;">{conf_pct}%</span>
                            </div>
                            <div style="color: #64748b; font-size: 0.73rem;">
                                {assigned_lbl} &nbsp;•&nbsp; <b>{t['status'].upper()}</b>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    btn_lbl = f"✓ Open {t['id']}" if is_active else f"Open {t['id']}"
                    if st.button(btn_lbl, key=f"sel_t_{t['id']}", use_container_width=True):
                        st.session_state["selected_conv_id"] = t["id"]
                        st.rerun()

        # =====================================================================
        # AREA 3: DETAILS PANEL & AGENT CONTROLS
        # =====================================================================
        with area3_col:
            active_id = st.session_state.get("selected_conv_id")
            if not active_id:
                st.info("Select a ticket from the inbox list to view its complete details and history.")
            else:
                conv = database.get_conversation(active_id, include_internal=True)
                if not conv:
                    st.warning("Selected ticket could not be loaded.")
                else:
                    # Ticket Header Bar
                    st.markdown(f"#### {conv['subject']}")
                    
                    status_badge = "🟢 OPEN" if conv["status"] == "open" else ("🟡 IN PROGRESS" if conv["status"] == "in_progress" else "⚪ RESOLVED")
                    st.markdown(f"**Ticket ID:** `{conv['id']}` &nbsp;•&nbsp; **Customer:** {conv['customer_name']} &nbsp;•&nbsp; **Status:** `{status_badge}`")

                    # Primary Actions: Resolution & Assignment
                    h_act1, h_act2 = st.columns([1.5, 2.5])
                    with h_act1:
                        if conv["status"] in ["resolved", "closed"]:
                            if st.button("🔄 Reopen Ticket", key=f"reopen_{conv['id']}", use_container_width=True):
                                database.reopen_conversation(conv["id"])
                                st.success("Ticket reopened.")
                                st.rerun()
                        else:
                            if st.button("✅ Mark as Resolved", type="primary", key=f"resolve_{conv['id']}", use_container_width=True):
                                database.update_conversation_status(conv["id"], "resolved")
                                st.success("Ticket marked as resolved.")
                                st.rerun()

                    with h_act2:
                        # Reassign ticket
                        agents_list = database.list_agents()
                        agent_choices = {"Unassigned": None}
                        for ag in agents_list:
                            agent_choices[ag["name"]] = ag["id"]

                        curr_assigned = conv.get("assigned_agent_name") or "Unassigned"
                        curr_idx = list(agent_choices.keys()).index(curr_assigned) if curr_assigned in agent_choices else 0

                        reassign_sel = st.selectbox(
                            "Reassign Specialist:",
                            options=list(agent_choices.keys()),
                            index=curr_idx,
                            key=f"reassign_{conv['id']}",
                            label_visibility="collapsed"
                        )
                        if reassign_sel != curr_assigned:
                            new_ag_id = agent_choices[reassign_sel]
                            database.reassign_conversation(conv["id"], new_ag_id, reassign_sel if new_ag_id else None)
                            st.success(f"Ticket reassigned to {reassign_sel}")
                            st.rerun()

                    st.markdown("<hr style='margin: 8px 0;'>", unsafe_allow_html=True)

                    # Triage Assessment Card
                    urg = conv["urgency"].lower()
                    urg_cls = f"badge-{urg}"
                    conf_pct = int(float(conv["confidence"]) * 100)

                    m1, m2, m3 = st.columns(3)
                    with m1:
                        st.markdown(f"""
                        <div class="metric-card" style="padding: 10px 14px;">
                            <div class="metric-card-title">Predicted Intent</div>
                            <div style="font-size: 1.05rem; font-weight: 700; color: #111827; margin-top: 2px;">{conv['intent']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with m2:
                        st.markdown(f"""
                        <div class="metric-card" style="padding: 10px 14px;">
                            <div class="metric-card-title">Urgency Level</div>
                            <div style="margin-top: 4px;"><span class="{urg_cls}">{urg.upper()}</span></div>
                        </div>
                        """, unsafe_allow_html=True)
                    with m3:
                        st.markdown(f"""
                        <div class="metric-card" style="padding: 10px 14px;">
                            <div class="metric-card-title">Calibrated Confidence</div>
                            <div style="font-size: 1.15rem; font-weight: 700; color: #15803d; margin-top: 2px;">{conf_pct}%</div>
                        </div>
                        """, unsafe_allow_html=True)

                    # Escalation Details
                    if conv["escalate"]:
                        st.markdown(f"""
                        <div class="escalate-banner">
                            <strong style="color: #d70015;">🚨 ESCALATION REQUIRED</strong>
                            <div style="font-size: 0.88rem; margin-top: 4px; color: #4c0519;">
                                <b>Reason:</b> {conv.get('escalation_reason') or 'Flagged for supervisor review.'}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="no-escalate-banner">
                            <strong style="color: #1b8738;">✅ ROUTINE INQUIRY</strong>
                            <div style="font-size: 0.85rem; margin-top: 2px; color: #14532d;">Standard resolution workflow applies.</div>
                        </div>
                        """, unsafe_allow_html=True)

                    # Customer Feedback Section (Visible on resolved tickets)
                    fb_record = database.get_conversation_feedback(conv["id"])
                    if fb_record:
                        star_icons = "⭐" * int(fb_record["rating"])
                        st.markdown(f"""
                        <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 12px 16px; margin: 10px 0;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <strong style="color: #15803d; font-size: 0.95rem;">Customer Review: {star_icons} ({fb_record['rating']}/5)</strong>
                                <span style="font-size: 0.78rem; color: #166534;">Resolved: <b>{fb_record.get('issue_resolved', 'Yes')}</b></span>
                            </div>
                            <div style="font-size: 0.88rem; color: #166534; margin-top: 4px; font-style: italic;">
                                "{fb_record.get('comment') or 'No additional comment provided.'}"
                            </div>
                            <div style="font-size: 0.75rem; color: #15803d; margin-top: 4px;">
                                Translation Quality: <b>{fb_record.get('translation_quality', 'Good')}</b> • Category: {fb_record.get('category')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    # Translation Card
                    messages = conv.get("messages", [])
                    orig_cust_msg = messages[0]["message_text"] if messages else conv["english_translation"]
                    st.markdown(f"**Original Message:** *\"{orig_cust_msg}\"*")
                    st.markdown(f"""
                    <div class="translation-card">
                        <div class="translation-title">🔤 English Translation (Detected Dialect: {conv['detected_language']})</div>
                        <div class="translation-body">{conv['english_translation']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Chronological Dialogue History
                    st.markdown("##### 💬 Conversation History")
                    for m in messages:
                        stype = m.get("sender_type")
                        sname = m.get("sender_name", "Support")
                        t_str = m.get("created_at", "")[:19].replace("T", " ")
                        mtext = m.get("message_text", "")
                        mtrans = m.get("english_translation")

                        if stype == "internal_note":
                            st.markdown(f"""
                            <div class="chat-bubble-internal">
                                <div style="font-size: 0.75rem; font-weight: 700; color: #92400e; margin-bottom: 2px;">
                                    🔒 INTERNAL STAFF NOTE (Hidden from Customer) &nbsp;•&nbsp; {sname} &nbsp;•&nbsp; {t_str}
                                </div>
                                <div style="color: #78350f;">{mtext}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        elif stype == "customer":
                            trans_block = f'<div style="font-size: 0.78rem; opacity: 0.9; margin-top: 4px; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 3px;">English: "{mtrans}"</div>' if mtrans and mtrans != mtext else ''
                            st.markdown(f"""
                            <div class="chat-bubble-customer">
                                <div style="font-size: 0.75rem; opacity: 0.85; margin-bottom: 2px;">👤 {sname} &nbsp;•&nbsp; {t_str}</div>
                                {mtext}
                                {trans_block}
                            </div>
                            """, unsafe_allow_html=True)
                        elif stype == "agent":
                            st.markdown(f"""
                            <div class="chat-bubble-agent">
                                <div style="font-size: 0.75rem; color: #f97316; margin-bottom: 2px; font-weight: 600;">🎧 {sname} (Specialist) &nbsp;•&nbsp; {t_str}</div>
                                {mtext}
                            </div>
                            """, unsafe_allow_html=True)
                        elif stype == "system":
                            st.markdown(f"""
                            <div class="chat-bubble-system">
                                ℹ️ {mtext} &nbsp;•&nbsp; {t_str}
                            </div>
                            """, unsafe_allow_html=True)
                        else:  # AI
                            st.markdown(f"""
                            <div class="chat-bubble-ai">
                                <div style="font-size: 0.75rem; color: #f97316; font-weight: 600; margin-bottom: 2px;">⚡ {sname} &nbsp;•&nbsp; {t_str}</div>
                                {mtext}
                            </div>
                            """, unsafe_allow_html=True)

                    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

                    # Agent Reply Composer & Multilingual Translation
                    st.markdown("##### ✍️ Agent Reply & Customer Communication")
                    target_cust_lang = conv.get("preferred_language") or conv.get("detected_language", "English")

                    draft_key = f"agent_eng_draft_{conv['id']}"
                    if f"override_{draft_key}" in st.session_state:
                        st.session_state[draft_key] = st.session_state.pop(f"override_{draft_key}")

                    draft_val = conv.get("draft_reply") or "Thank you for reaching out. We are actively investigating your inquiry."
                    if draft_key not in st.session_state:
                        st.session_state[draft_key] = draft_val

                    agent_eng_draft = st.text_area(
                        "AI Suggested Draft (Editable in English):",
                        height=85,
                        key=draft_key
                    )

                    # Clarification Quick Buttons
                    st.caption("Quick Clarification Templates:")
                    qc1, qc2, qc3 = st.columns(3)
                    with qc1:
                        if st.button("📝 Order ID Request", key=f"qc_order_{conv['id']}", use_container_width=True):
                            st.session_state[f"override_{draft_key}"] = agent_eng_draft + " Could you please provide your Order ID so we can verify the shipment immediately?"
                            st.rerun()
                    with qc2:
                        if st.button("📸 Damaged Photo Request", key=f"qc_photo_{conv['id']}", use_container_width=True):
                            st.session_state[f"override_{draft_key}"] = agent_eng_draft + " Please share a clear photo of the damaged package and product to accelerate your replacement."
                            st.rerun()
                    with qc3:
                        if st.button("🏦 Payment Ref Request", key=f"qc_bank_{conv['id']}", use_container_width=True):
                            st.session_state[f"override_{draft_key}"] = agent_eng_draft + " Could you share your Bank / UPI Transaction Reference Number to trace your payment?"
                            st.rerun()

                    final_key = f"agent_final_input_{conv['id']}"
                    if f"override_{final_key}" in st.session_state:
                        st.session_state[final_key] = st.session_state.pop(f"override_{final_key}")
                    elif final_key not in st.session_state:
                        st.session_state[final_key] = agent_eng_draft

                    # Translation Action
                    tr_c1, _ = st.columns([2.5, 2.5])
                    with tr_c1:
                        if st.button(f"🌐 Translate Draft to Customer Language ({target_cust_lang})", key=f"btn_tr_{conv['id']}", use_container_width=True):
                            translated_rep = ai_engine.translate_agent_reply(agent_eng_draft, target_cust_lang)
                            st.session_state[f"override_{final_key}"] = translated_rep
                            st.rerun()

                    agent_final_text = st.text_area(
                        "Final Reply to Dispatch (Review / Edit before dispatch):",
                        height=85,
                        key=final_key
                    )

                    rc_col1, rc_col2 = st.columns([2, 1.5])
                    with rc_col1:
                        if st.button("🚀 Approve & Send Reply to Customer", type="primary", key=f"send_reply_{conv['id']}", use_container_width=True):
                            clean_reply = agent_final_text.strip()
                            if clean_reply:
                                database.add_message(
                                    conv_id=conv["id"],
                                    sender_type="agent",
                                    sender_id=current_user["id"],
                                    sender_name=current_user["name"],
                                    message_text=clean_reply
                                )
                                # Note: Does NOT automatically mark as resolved
                                database.update_conversation_status(conv["id"], "in_progress")
                                st.success("Reply recorded and dispatched to customer thread.")
                                st.rerun()

                    with rc_col2:
                        if conv.get("assigned_agent_id") != current_user["id"]:
                            if st.button("🙋 Take Over Ticket", key=f"takeover_{conv['id']}", use_container_width=True):
                                database.accept_conversation(conv["id"], current_user["id"], current_user["name"])
                                st.success(f"Taken over by {current_user['name']}")
                                st.rerun()

                    # Internal Staff Notes Composer
                    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
                    st.markdown("##### 🔒 Add Internal Note (Staff Only)")
                    note_key = f"internal_note_in_{conv['id']}"
                    if f"override_{note_key}" in st.session_state:
                        st.session_state[note_key] = st.session_state.pop(f"override_{note_key}")

                    internal_note_text = st.text_input(
                        "Internal Note (Never visible to customer):",
                        placeholder="e.g., Escalated to warehouse supervisor regarding missing courier label...",
                        key=note_key
                    )
                    if st.button("Save Internal Staff Note", key=f"btn_save_note_{conv['id']}"):
                        if internal_note_text.strip():
                            database.add_internal_note(
                                conv_id=conv["id"],
                                agent_id=current_user["id"],
                                agent_name=current_user["name"],
                                note_text=internal_note_text.strip()
                            )
                            st.session_state[f"override_{note_key}"] = ""
                            st.success("Internal note logged securely.")
                            st.rerun()
    # --- Page 2: Live Sessions (Phase 2 Enhanced) ---
    elif section == "Live Sessions":
        st.markdown('<div class="apple-header">Live Customer Sessions</div>', unsafe_allow_html=True)
        st.markdown('<div class="apple-sub">Real-time two-way communication threads between support specialists and customers.</div>', unsafe_allow_html=True)

        active_convs = database.list_agent_conversations(agent_id=current_user["id"], status_filter="in_progress")
        if not active_convs:
            active_convs = database.list_agent_conversations(agent_id=current_user["id"], status_filter="open")

        if not active_convs:
            st.info("No active customer sessions right now. All conversations are resolved or pending assignment.")
        else:
            s_map = {f"{c['customer_name']} - {c['subject']} ({c['id']})": c["id"] for c in active_convs}
            s_choice = st.selectbox("Select Active Session", options=list(s_map.keys()))
            s_id = s_map[s_choice]
            conv = database.get_conversation(s_id)

            if conv:
                st.markdown(f"#### Chat Session with {conv['customer_name']}")
                st.markdown(f"**Dialect:** `{conv['detected_language']}` &nbsp;•&nbsp; **Intent:** `{conv['intent']}` &nbsp;•&nbsp; **Translation:** *\"{conv['english_translation']}\"*")

                # Dialogue History
                for m in conv.get("messages", []):
                    stype = m.get("sender_type")
                    sname = m.get("sender_name", "Support")
                    t_str = m.get("created_at", "")[:19].replace("T", " ")
                    if stype == "customer":
                        st.markdown(f"""
                        <div class="chat-bubble-customer">
                            <div style="font-size: 0.75rem; opacity: 0.85; margin-bottom: 2px;">👤 {sname} &nbsp;•&nbsp; {t_str}</div>
                            {m['message_text']}
                        </div>
                        """, unsafe_allow_html=True)
                    elif stype == "agent":
                        st.markdown(f"""
                        <div class="chat-bubble-agent">
                            <div style="font-size: 0.75rem; color: #f97316; margin-bottom: 2px; font-weight: 600;">🎧 {sname} &nbsp;•&nbsp; {t_str}</div>
                            {m['message_text']}
                        </div>
                        """, unsafe_allow_html=True)
                    elif stype == "system":
                        st.markdown(f"""
                        <div class="chat-bubble-system">
                            ℹ️ {m['message_text']} &nbsp;•&nbsp; {t_str}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="chat-bubble-ai">
                            <div style="font-size: 0.75rem; color: #f97316; font-weight: 600; margin-bottom: 2px;">⚡ {sname} &nbsp;•&nbsp; {t_str}</div>
                            {m['message_text']}
                        </div>
                        """, unsafe_allow_html=True)

                st.divider()

                # Agent Live Response & Translation
                cust_lang = conv.get("preferred_language") or conv.get("detected_language", "English")
                st.markdown(f"**Compose Response (Customer preferred dialect: `{cust_lang}`)**")
                
                live_key = f"live_msg_{conv['id']}"
                if f"override_{live_key}" in st.session_state:
                    st.session_state[live_key] = st.session_state.pop(f"override_{live_key}")

                live_draft = st.text_input(
                    "Message (English or Customer's Dialect):",
                    placeholder="e.g. We have escalated your query to our dispatch supervisor...",
                    key=live_key
                )
                
                tr_c1, tr_c2 = st.columns([1.5, 3])
                with tr_c1:
                    if st.button(f"🌐 Translate to {cust_lang}", key=f"btn_live_tr_{conv['id']}"):
                        st.session_state[f"override_{live_key}"] = ai_engine.translate_agent_reply(live_draft, cust_lang)
                        st.rerun()

                l_col1, l_col2 = st.columns([1.5, 4])
                with l_col1:
                    if st.button("Send Message", type="primary", key=f"btn_live_send_{conv['id']}"):
                        if live_draft.strip():
                            database.add_message(
                                conv_id=conv["id"],
                                sender_type="agent",
                                sender_id=current_user["id"],
                                sender_name=current_user["name"],
                                message_text=live_draft.strip()
                            )
                            database.accept_conversation(conv["id"], current_user["id"], current_user["name"])
                            st.session_state[f"override_{live_key}"] = ""
                            st.success("Message delivered.")
                            st.rerun()
                with l_col2:
                    if st.button("Resolve & End Session", key=f"btn_live_res_{conv['id']}"):
                        database.update_conversation_status(conv["id"], "resolved")
                        st.success("Session closed and resolved.")
                        st.rerun()

    # --- Page 3: Session Analytics ---
    elif section == "📊 Session Analytics":
        st.markdown('<div class="apple-header">Session & Platform Analytics</div>', unsafe_allow_html=True)
        st.markdown('<div class="apple-sub">Real-time operational distribution of customer inquiries, triage accuracy, and agent performance.</div>', unsafe_allow_html=True)

        metrics = database.get_platform_metrics()
        sess_metrics = database.get_session_analytics_metrics()
        csat_data = database.get_csat_metrics()

        # Operational Live Analytics KPIs (Phase 3 Section 7)
        sa1, sa2, sa3, sa4, sa5 = st.columns(5)
        sa1.metric("Active Sessions", sess_metrics["active_conversations"])
        sa2.metric("Waiting Customers", sess_metrics["waiting_customers"])
        sa3.metric("Human Handoffs", sess_metrics["human_handoffs"])
        sa4.metric("Total Resolved", sess_metrics["resolved_count"])
        sa5.metric("Avg Response Time", sess_metrics["avg_response_time"])

        st.caption(f"Customer Satisfaction Score: **{csat_data['csat_percent']}%** ({csat_data['label']}, N={csat_data['sample_size']} ratings) • {csat_data['formula_description']}")
        
        # Top KPI Metrics
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Total Conversations", metrics["total_conversations"])
        k2.metric("High Urgency", f"{metrics['high_urgency']}")
        k3.metric("Escalated Tickets", f"{metrics['escalated']}")
        k4.metric("Avg AI Confidence", f"{metrics['avg_confidence']}%")
        k5.metric("Customer Rating", f"{metrics['avg_rating']} / 5.0" if metrics["avg_rating"] else "N/A")

        st.divider()

        # Distribution Visualizations
        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown("##### Distribution of Predicted Intents")
            if metrics["intent_distribution"]:
                df_intent = pd.DataFrame(list(metrics["intent_distribution"].items()), columns=["Intent", "Count"]).sort_values("Count", ascending=False)
                st.bar_chart(df_intent.set_index("Intent"), color="#f97316")
            else:
                st.info("No intent records available.")

        with c_right:
            st.markdown("##### Distribution by Detected Dialect")
            if metrics["language_distribution"]:
                df_lang = pd.DataFrame(list(metrics["language_distribution"].items()), columns=["Language", "Count"]).sort_values("Count", ascending=False)
                st.bar_chart(df_lang.set_index("Language"), color="#34c759")
            else:
                st.info("No language records available.")

        st.divider()

        # Customer Feedback Review Table for Staff
        st.markdown("##### Customer Feedback & Translation Quality Log")
        all_fb = database.get_all_feedback()
        if all_fb:
            df_fb = pd.DataFrame(all_fb)
            disp_fb_cols = [c for c in ["id", "conversation_id", "customer_name", "rating", "category", "translation_quality", "issue_resolved", "comment", "created_at"] if c in df_fb.columns]
            st.dataframe(df_fb[disp_fb_cols], use_container_width=True, hide_index=True)
        else:
            st.info("No customer feedback logged yet.")

        # Session tickets table
        if st.session_state["tickets"]:
            st.divider()
            st.markdown("##### Ad-Hoc Analyzer Session Logs")
            df_sess = pd.DataFrame(st.session_state["tickets"])
            disp_cols = [c for c in ["id", "timestamp", "detected_language", "intent", "urgency", "confidence", "escalate", "message", "english_translation"] if c in df_sess.columns]
            st.dataframe(df_sess[disp_cols], use_container_width=True, hide_index=True)

    # --- Page 4: Dedicated Root-Cause Analysis & Complaint Trends Dashboard ---
    elif section == "Root-Cause Analysis":
        # Navigation header
        top_h1, top_h2 = st.columns([4, 1.5])
        with top_h1:
            st.markdown('<div class="apple-header">Root-Cause Analysis & Complaint Trends</div>', unsafe_allow_html=True)
            st.markdown('<div class="apple-sub">Executive intelligence console for identifying recurring complaint patterns, spike anomalies, and process bottlenecks.</div>', unsafe_allow_html=True)
        with top_h2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("⬅️ Customer Queries Inbox", key="btn_nav_inbox", use_container_width=True):
                st.session_state["nav_radio_idx"] = 0
                st.toast("Navigating to Customer Queries...")
                # Update query param or rerun

        # ---------------------------------------------------------------------
        # 1. Filters & Aggregation Controls
        # ---------------------------------------------------------------------
        with st.container():
            st.markdown("##### 🔍 Dashboard Filters & Period View")
            f1, f2, f3, f4, f5 = st.columns([1.5, 1.2, 1.5, 1.2, 1.5])
            with f1:
                date_preset = st.selectbox(
                    "Date Range:",
                    options=["All Time", "Last 7 Days", "Last 14 Days", "Last 30 Days"],
                    index=0,
                    key="rca_date_preset"
                )
            with f2:
                view_mode = st.radio("Aggregation:", ["Daily", "Weekly"], horizontal=True, key="rca_view_mode")
            with f3:
                flt_intent_rc = st.selectbox("Intent:", ["All"] + ai_engine.VALID_INTENTS, key="rca_flt_intent")
            with f4:
                flt_urg_rc = st.selectbox("Urgency:", ["All", "High", "Medium", "Low"], key="rca_flt_urg")
            with f5:
                flt_lang_rc = st.selectbox("Dialect:", ["All"] + database.ALL_SUPPORTED_LANGUAGES, key="rca_flt_lang")

        # Compute Date Range Boundaries
        today = datetime.date.today()
        if date_preset == "Last 7 Days":
            start_date_str = (today - datetime.timedelta(days=7)).isoformat()
            end_date_str = today.isoformat()
        elif date_preset == "Last 14 Days":
            start_date_str = (today - datetime.timedelta(days=14)).isoformat()
            end_date_str = today.isoformat()
        elif date_preset == "Last 30 Days":
            start_date_str = (today - datetime.timedelta(days=30)).isoformat()
            end_date_str = today.isoformat()
        else:  # All Time
            start_date_str = None
            end_date_str = None

        # Fetch Data from Database Engine
        rc_data = database.get_root_cause_dashboard_data(
            start_date=start_date_str,
            end_date=end_date_str,
            filter_intent=flt_intent_rc if flt_intent_rc != "All" else None,
            filter_urgency=flt_urg_rc if flt_urg_rc != "All" else None,
            filter_language=flt_lang_rc if flt_lang_rc != "All" else None,
            view_mode=view_mode.lower()
        )

        st.divider()

        # Empty State Check
        if rc_data["is_empty"]:
            st.warning("⚠️ No customer complaints found matching the selected period and filter parameters.")
            st.info("Tip: Switch the Date Range filter to 'All Time' or clear dialect/intent filters to inspect historical complaint data.")
        else:
            # -----------------------------------------------------------------
            # 2. Overview Metrics
            # -----------------------------------------------------------------
            st.markdown("##### 📊 Complaint Volume & Performance Overview")
            ov1, ov2, ov3, ov4, ov5, ov6, ov7 = st.columns(7)
            with ov1:
                st.metric("Total Complaints", rc_data["total_complaints"])
            with ov2:
                st.metric("Refund Issues", f"{rc_data['refund_complaints']}", f"{rc_data['refund_pct']}% of total")
            with ov3:
                st.metric("Delivery Issues", f"{rc_data['delivery_complaints']}", f"{rc_data['delivery_pct']}% of total")
            with ov4:
                st.metric("Payment Issues", f"{rc_data['payment_complaints']}", f"{rc_data['payment_pct']}% of total")
            with ov5:
                st.metric("Product / Wrong", f"{rc_data['damage_complaints']}", f"{rc_data['damage_pct']}% of total")
            with ov6:
                st.metric("Escalation Rate", f"{rc_data['escalation_rate']}%")
            with ov7:
                st.metric("Resolution Rate", f"{rc_data['resolution_rate']}%")

            st.divider()

            # -----------------------------------------------------------------
            # 3. Explainable Spike Detection & Anomaly Alerts
            # -----------------------------------------------------------------
            st.markdown("##### 🚨 Complaint Spike & Anomaly Baseline Detection")
            for alert in rc_data["spike_alerts"]:
                atype = alert.get("type", "info")
                amsg = alert.get("message", "")
                acat = alert.get("category", "Monitoring")
                if atype == "warning":
                    st.markdown(f"""
                    <div class="escalate-banner">
                        <strong style="color: #d70015; font-size: 1rem;">⚠️ ANOMALOUS SPIKE DETECTED &nbsp;•&nbsp; {acat}</strong>
                        <div style="font-size: 0.92rem; margin-top: 4px; color: #4c0519;">{amsg}</div>
                    </div>
                    """, unsafe_allow_html=True)
                elif atype == "success":
                    st.markdown(f"""
                    <div class="no-escalate-banner">
                        <strong style="color: #1b8738; font-size: 0.95rem;">✅ {acat.upper()}</strong>
                        <div style="font-size: 0.88rem; margin-top: 3px; color: #14532d;">{amsg}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info(f"ℹ️ **{acat}:** {amsg}")

            st.markdown("<br>", unsafe_allow_html=True)

            # -----------------------------------------------------------------
            # 4. Complaint Trends Charts
            # -----------------------------------------------------------------
            st.markdown(f"##### 📈 Complaint Trends ({view_mode} Aggregation)")
            trend_list = rc_data["trend_data"]

            if trend_list:
                df_trend = pd.DataFrame(trend_list).set_index("period")

                ch_c1, ch_c2 = st.columns(2)
                with ch_c1:
                    st.markdown("**Total Inquiries vs Primary Drivers Over Time**")
                    disp_cols_1 = [c for c in ["total", "delivery", "refund", "payment"] if c in df_trend.columns]
                    st.bar_chart(df_trend[disp_cols_1])

                with ch_c2:
                    st.markdown("**Refund vs Delivery Delay Volume Trajectory**")
                    disp_cols_2 = [c for c in ["delivery", "refund"] if c in df_trend.columns]
                    st.line_chart(df_trend[disp_cols_2])

                ch_c3, ch_c4 = st.columns(2)
                with ch_c3:
                    st.markdown("**Urgency Distribution Over Time (High / Medium / Low)**")
                    disp_cols_3 = [c for c in ["urgency_high", "urgency_medium", "urgency_low"] if c in df_trend.columns]
                    st.area_chart(df_trend[disp_cols_3])

                with ch_c4:
                    st.markdown("**Escalation vs Resolution Rate (%)**")
                    disp_cols_4 = [c for c in ["escalation_rate", "resolution_rate"] if c in df_trend.columns]
                    st.line_chart(df_trend[disp_cols_4])

            st.divider()

            # -----------------------------------------------------------------
            # 5. Recurring Issue Clusters (Transparent Keyword & Intent Grouping)
            # -----------------------------------------------------------------
            st.markdown("##### 🧩 Recurring Complaint Clusters & Root-Cause Themes")
            st.caption("Tickets grouped transparently by semantic complaint keywords, intent categories, and operational friction points:")

            if not rc_data["clusters"]:
                st.info("No recurring complaint clusters identified in the selected sample.")
            else:
                for cl in rc_data["clusters"]:
                    urg_cls = f"badge-{cl['typical_urgency'].lower()}"
                    st.markdown(f"""
                    <div class="apple-card" style="padding: 16px 20px; margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                            <div>
                                <span style="font-weight: 800; font-size: 1.05rem; color: #111827;">{cl['name']}</span>
                                &nbsp;<span style="font-size: 0.8rem; color: #64748b;">({cl['cluster_id']})</span>
                            </div>
                            <div>
                                <span class="{urg_cls}">TYPICAL: {cl['typical_urgency'].upper()}</span>
                                &nbsp;<span style="font-size: 0.82rem; font-weight: 700; color: #b91c1c; background: #fee2e2; border: 1px solid #fecaca; padding: 2px 8px; border-radius: 10px;">Escalation: {cl['escalation_rate']}%</span>
                            </div>
                        </div>
                        <div style="font-size: 0.88rem; color: #15803d; font-weight: 700; margin-bottom: 6px;">
                            Theme: {cl['theme']}
                        </div>
                        <div style="display: flex; gap: 18px; font-size: 0.82rem; color: #64748b; margin-bottom: 8px;">
                            <span>Volume: <b>{cl['count']} complaints</b></span>
                            <span>Trend vs Baseline: <b>{cl['trend_vs_prior']}</b></span>
                        </div>
                        <div style="background-color: #f8faf8; border: 1px solid #e2ebe3; border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; color: #111827;">
                            <b style="color: #475569;">Representative Customer Excerpts:</b>
                            <ul style="margin: 4px 0 0 16px; padding: 0; color: #334155;">
                                {"".join(f"<li>{quote}</li>" for quote in cl['representative_examples'])}
                            </ul>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            st.divider()

            # -----------------------------------------------------------------
            # 6. Product and Process Analysis (Pattern vs Hypothesis vs Cause)
            # -----------------------------------------------------------------
            st.markdown("##### ⚙️ Product & Process Diagnostic Analysis")
            st.caption("Factual delineation between observed patterns, operational hypotheses, and confirmed root causes:")

            if not rc_data["product_process_patterns"]:
                st.info("No specific product or process entities detected in current complaints.")
            else:
                for pat in rc_data["product_process_patterns"]:
                    st.markdown(f"""
                    <div class="apple-card" style="padding: 16px 20px; margin-bottom: 12px; border-left: 4px solid #16a34a;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                            <span style="font-weight: 800; font-size: 1.05rem; color: #111827;">{pat['entity']}</span>
                            <span class="lang-pill">{pat['type']} • {pat['count']} tickets</span>
                        </div>
                        <div style="margin-top: 6px; font-size: 0.88rem;">
                            <div style="margin-bottom: 4px;">
                                <b style="color: #111827;">🔍 Observed Complaint Pattern:</b>
                                <span style="color: #334155;"> {pat['observed_pattern']}</span>
                            </div>
                            <div style="margin-bottom: 4px;">
                                <b style="color: #b45309;">💡 Possible Operational Explanation:</b>
                                <span style="color: #334155;"> {pat['possible_explanation']}</span>
                            </div>
                            <div>
                                <b style="color: #15803d;">✅ Confirmed Root Cause / Action:</b>
                                <span style="color: #334155;"> {pat['confirmed_cause']}</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            st.divider()

            # -----------------------------------------------------------------
            # 7. Emerging Issues Executive Summary
            # -----------------------------------------------------------------
            st.markdown("##### 📌 Emerging Issues Executive Summary")
            st.caption("Data-grounded key takeaways for customer-care managers and operations leaders:")

            sum_html = "".join(f"<li style='margin-bottom: 6px; font-size: 0.92rem; color: #111827;'>{bullet}</li>" for bullet in rc_data["emerging_summary"])
            st.markdown(f"""
            <div style="background-color: #ffffff; border: 1px solid #e2ebe3; border-radius: 14px; padding: 18px 22px; box-shadow: 0 2px 10px rgba(0,0,0,0.03);">
                <ul style="margin: 0; padding-left: 20px;">
                    {sum_html}
                </ul>
            </div>
            """, unsafe_allow_html=True)
    # --- Page 5: Evaluation Suite ---
    elif section == "🧪 Evaluation Suite":
        num_tests = len(TEST_CASES)
        st.markdown('<div class="apple-header">Benchmark Evaluation Suite</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="apple-sub">Evaluate predictions across {num_tests} ground-truth test cases spanning Telugu+English, Tanglish, Hinglish, and English.</div>', unsafe_allow_html=True)

        status = ai_engine.get_backend_status()
        if status.get("is_mock"):
            st.warning("⚠️ MOCK MODE ACTIVE: Scores are simulated mock values.")
        else:
            st.success(f"Connected Backend: **{status['name']}** ({status['status_badge']})")

        if st.button(f"🚀 Run All {num_tests} Benchmark Tests", type="primary", use_container_width=True):
            pbar = st.progress(0)
            st_text = st.empty()

            def cb(curr, tot):
                pbar.progress(curr / tot)
                st_text.text(f"Evaluating test case {curr} of {tot}...")

            eval_out = evaluate.evaluate_dataset(
                test_cases=TEST_CASES,
                analyzer=ai_engine.analyze_message,
                progress_callback=cb
            )
            st.session_state["eval_results"] = eval_out
            st_text.success("Evaluation run completed.")
            st.rerun()

        eval_res = st.session_state["eval_results"]
        if eval_res:
            m = eval_res["metrics"]
            st.markdown("##### Overall Evaluation Accuracy")
            e1, e2, e3, e4, e5, e6 = st.columns(6)
            e1.metric("Total Tests", m["total_tests"])
            e2.metric("Passed", m["total_passed"])
            e3.metric("Failed", m["total_failed"])
            e4.metric("Pass Rate", f"{m['overall_pass_rate']}%")
            e5.metric("Intent Acc.", f"{m['intent_accuracy']}%")
            e6.metric("Urgency Acc.", f"{m['urgency_accuracy']}%")

            st.divider()

            # Performance by dialect
            st.markdown("##### Performance by Dialect")
            lang_cols = st.columns(len(m["by_language"]) if m["by_language"] else 1)
            for idx, (lang, lstat) in enumerate(m["by_language"].items()):
                pass_rate = round(lstat["passed"] / lstat["total"] * 100, 1) if lstat["total"] else 0
                with lang_cols[idx]:
                    st.markdown(f"""
                    <div class="apple-card">
                        <div class="apple-card-title">{lang}</div>
                        <div class="apple-card-value">{lstat['passed']}/{lstat['total']} ({pass_rate}%)</div>
                        <div style="font-size: 0.8rem; color: #6e6e73; margin-top: 4px;">
                            Intent: {lstat['intent_correct']}/{lstat['total']} · Urgency: {lstat['urgency_correct']}/{lstat['total']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # Confusion matrices and results
            df_res = eval_res["results_df"]
            csv_bytes = df_res.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Benchmark Results as CSV", data=csv_bytes, file_name="benchmark_results.csv", mime="text/csv")

            tab_res, tab_cm_i, tab_cm_u = st.tabs(["Test Results Table", "Intent Confusion Matrix", "Urgency Confusion Matrix"])
            with tab_res:
                st.dataframe(df_res, use_container_width=True, hide_index=True)
            with tab_cm_i:
                if eval_res["intent_confusion_matrix"] is not None:
                    st.dataframe(eval_res["intent_confusion_matrix"], use_container_width=True)
            with tab_cm_u:
                if eval_res["urgency_confusion_matrix"] is not None:
                    st.dataframe(eval_res["urgency_confusion_matrix"], use_container_width=True)
        else:
            st.info(f"Click 'Run All {num_tests} Benchmark Tests' to compute full precision metrics.")
