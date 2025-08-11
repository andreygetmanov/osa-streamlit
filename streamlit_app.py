import logging
import os
import tempfile

import streamlit as st
from dotenv import load_dotenv

from configuration_tab import render_configuration_tab
from login_screen import render_login_screen
from main_tab import render_main_tab
from sidebar_element import render_sidebar_element

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def setup_page_config() -> None:
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_icon=":bee:",
        page_title="OSA Tool",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "About": "https://github.com/ITMO-NSS-team/Open-Source-Advisor",
            "Get Help": "https://t.me/osa_helpdesk",
        },
    )


@st.cache_data(show_spinner=False)
def create_tmp_dir():
    return tempfile.TemporaryDirectory(delete=False).name


@st.cache_data(show_spinner=False)
def get_git_token():
    return os.getenv("GIT_TOKEN")


def main() -> None:
    """Run the Streamlit application."""

    setup_page_config()

    # if not st.experimental_user.is_logged_in:
    #     render_login_screen()
    #     st.stop()

    st.session_state.tmpdirname = create_tmp_dir()
    st.session_state.git_token = get_git_token()

    render_sidebar_element()

    tab1, tab2 = st.tabs(
        [
            ":material/home: Home",
            ":material/settings: Configuration",
        ]
    )
    with tab1:
        render_main_tab()

    with tab2:
        render_configuration_tab()


if __name__ == "__main__":
    main()
