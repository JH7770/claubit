"""
Theme utilities for dashboard

Provides dark mode CSS application across all pages.
"""

import streamlit as st
import streamlit.components.v1 as components


def initialize_dark_mode():
    """
    Initialize dark mode from localStorage on page load.
    This prevents white flash by applying CSS immediately.
    """
    # JavaScript to check localStorage and apply dark mode ASAP
    init_script = """
    <script>
        (function() {
            // Check localStorage for dark mode preference
            const darkMode = localStorage.getItem('claubit_dark_mode');

            if (darkMode === 'true') {
                // Apply dark mode class immediately to prevent flash
                document.body.classList.add('dark-mode-active');
                document.documentElement.style.backgroundColor = '#111827';
                document.body.style.backgroundColor = '#111827';
                document.body.style.color = '#f9fafb';
            }
        })();
    </script>
    """
    st.markdown(init_script, unsafe_allow_html=True)


def apply_dark_mode_css():
    """Apply dark mode CSS if dark mode is enabled in session state."""
    # Load dark mode preference from localStorage if not initialized
    if 'dark_mode' not in st.session_state:
        # Check localStorage via JavaScript
        check_storage = """
        <script>
            const savedDarkMode = localStorage.getItem('claubit_dark_mode');
            if (savedDarkMode === 'true') {
                // Send message to Streamlit (best effort)
                window.parent.postMessage({
                    type: 'claubit_dark_mode',
                    value: true
                }, '*');
            }
        </script>
        """
        st.markdown(check_storage, unsafe_allow_html=True)
        st.session_state.dark_mode = False

    # Sync with localStorage
    sync_script = f"""
    <script>
        localStorage.setItem('claubit_dark_mode', '{str(st.session_state.dark_mode).lower()}');
    </script>
    """
    st.markdown(sync_script, unsafe_allow_html=True)

    if st.session_state.dark_mode:
        st.markdown("""
        <style>
            /* ==================== Dark Mode Theme ==================== */

            /* App-level background */
            .stApp {
                background-color: #111827 !important;
            }

            /* Main containers */
            .main,
            [data-testid="stAppViewContainer"],
            [data-testid="stHeader"],
            .block-container {
                background-color: #111827 !important;
                color: #f9fafb !important;
            }

            /* Headers */
            .main-header {
                color: #f9fafb !important;
            }

            h1, h2, h3, h4, h5, h6 {
                color: #f9fafb !important;
            }

            /* All text elements */
            p, span, div, label {
                color: #f9fafb !important;
            }

            /* Metric Cards */
            .stMetric {
                background: #1f2937 !important;
                border: 1px solid #374151 !important;
                color: #f9fafb !important;
            }

            .stMetric label {
                color: #9ca3af !important;
            }

            .stMetric [data-testid="stMetricValue"] {
                color: #f9fafb !important;
            }

            /* Buttons */
            .stButton button {
                background-color: #374151 !important;
                color: #f9fafb !important;
            }

            .stButton button[kind="primary"] {
                background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
                color: #ffffff !important;
            }

            .stButton button:hover {
                background-color: #4b5563 !important;
            }

            /* Status Boxes */
            .stSuccess {
                background-color: #064e3b !important;
                border-left-color: #10b981 !important;
                color: #d1fae5 !important;
            }

            .stWarning {
                background-color: #78350f !important;
                border-left-color: #f59e0b !important;
                color: #fef3c7 !important;
            }

            .stError {
                background-color: #7f1d1d !important;
                border-left-color: #ef4444 !important;
                color: #fee2e2 !important;
            }

            .stInfo {
                background-color: #1e3a8a !important;
                border-left-color: #3b82f6 !important;
                color: #dbeafe !important;
            }

            /* Tabs */
            .stTabs [data-baseweb="tab-list"] {
                background-color: #1f2937 !important;
            }

            .stTabs [aria-selected="true"] {
                background-color: #374151 !important;
                color: #3b82f6 !important;
            }

            .stTabs [aria-selected="false"] {
                color: #9ca3af !important;
            }

            .stTabs [data-baseweb="tab-panel"] {
                background-color: #111827 !important;
            }

            /* Dataframes/Tables */
            .stDataFrame {
                background-color: #1f2937 !important;
            }

            .stDataFrame table {
                background-color: #1f2937 !important;
                color: #f9fafb !important;
            }

            .stDataFrame th {
                background-color: #374151 !important;
                color: #f9fafb !important;
            }

            .stDataFrame td {
                background-color: #1f2937 !important;
                color: #f9fafb !important;
            }

            /* Expanders */
            .streamlit-expanderHeader {
                background-color: #1f2937 !important;
                color: #f9fafb !important;
            }

            .streamlit-expanderContent {
                background-color: #1f2937 !important;
                border: 1px solid #374151 !important;
            }

            /* Sidebar */
            [data-testid="stSidebar"] {
                background-color: #1f2937 !important;
                border-right: 1px solid #374151 !important;
            }

            [data-testid="stSidebar"] .stMarkdown {
                color: #f9fafb !important;
            }

            [data-testid="stSidebar"] label {
                color: #f9fafb !important;
            }

            /* Input Fields */
            .stTextInput input,
            .stNumberInput input,
            .stSelectbox select,
            .stMultiSelect select,
            .stDateInput input,
            .stTimeInput input {
                background-color: #374151 !important;
                color: #f9fafb !important;
                border: 1px solid #4b5563 !important;
            }

            .stTextInput label,
            .stNumberInput label,
            .stSelectbox label,
            .stMultiSelect label,
            .stDateInput label,
            .stTimeInput label {
                color: #f9fafb !important;
            }

            /* Radio & Checkbox */
            .stRadio label,
            .stCheckbox label {
                color: #f9fafb !important;
            }

            /* Markdown */
            .stMarkdown {
                color: #f9fafb !important;
            }

            /* Code blocks */
            code {
                background-color: #374151 !important;
                color: #fbbf24 !important;
            }

            pre {
                background-color: #1f2937 !important;
                border: 1px solid #374151 !important;
            }

            /* Captions */
            .caption {
                color: #9ca3af !important;
            }

            /* Download button */
            .stDownloadButton button {
                background-color: #374151 !important;
                color: #f9fafb !important;
            }

            /* Dividers */
            hr {
                border-color: #374151 !important;
            }

            /* Scrollbar */
            ::-webkit-scrollbar {
                background-color: #1f2937 !important;
            }

            ::-webkit-scrollbar-thumb {
                background-color: #4b5563 !important;
            }

            ::-webkit-scrollbar-thumb:hover {
                background-color: #6b7280 !important;
            }
        </style>
        """, unsafe_allow_html=True)
