import asyncio
import logging
import os
import tempfile

import streamlit as st
from dotenv import load_dotenv

from configuration_page import render_configuration_page

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class OsaToolApp:
    """
    Streamlit web app serving the OSA tool CLI.
    """

    def __init__(self):
        self.setup_page_config()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        st.session_state.git_token = os.getenv("GIT_TOKEN")
        if not st.session_state.git_token:
            logger.warning("GIT_TOKEN not found in environment variables")

    def setup_page_config(self) -> None:
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

    def render_login_screen(self) -> None:
        """Render application login screen."""
        _, center, _ = st.columns(3)
        with center:

            _, center, _ = st.columns([0.1, 0.8, 0.1])

            with center:
                st.image(
                    "assets/osa_logo.png",
                    use_container_width=True,
                )
                st.container(height=20, border=False)

            with st.container(border=True, height=250):
                st.markdown(
                    '<h2 style="text-align: center;">Sign in to OSA</h2>',
                    unsafe_allow_html=True,
                )

                with st.container(border=True):
                    if st.button(
                        "Log in with AimClub",
                        use_container_width=True,
                        type="primary",
                    ):
                        st.login("aimclub")
                    if st.button(
                        "Log in with Google", use_container_width=True, disabled=True
                    ):
                        st.login("google")

            st.markdown(
                '<h6 style="text-align: center;">Created by ITMO with ❤️</h6>',
                unsafe_allow_html=True,
            )

    def render_sidebar(self) -> None:
        """Render sidebar with configuration options."""
        with st.sidebar:
            username = st.experimental_user.get("name", "Username")
            st.markdown(
                f'<h1 style="text-align: center;">Welcome, {username} 👋</h1>',
                unsafe_allow_html=True,
            )

            st.divider()

            _, center, _ = st.columns([0.2, 0.6, 0.2])
            with center:
                st.link_button(
                    "About",
                    url="https://github.com/ITMO-NSS-team/Open-Source-Advisor",
                    use_container_width=True,
                    icon=":material/info:",
                )
                st.link_button(
                    "Get Help",
                    url="https://t.me/osa_helpdesk",
                    use_container_width=True,
                    icon=":material/help:",
                )
                st.container(height=10, border=False)
                st.button(
                    "Log out",
                    on_click=st.logout,
                    use_container_width=True,
                    type="primary",
                    icon=":material/logout:",
                )
            style = """
            <style>
            button[data-baseweb="tab"] {
            font-size: 24px;
            margin: 0;
            width: 100%;
            }
            </style>
            """
            st.write(style, unsafe_allow_html=True)

    def render_main_block(self) -> None:
        _, center, _ = st.columns([0.1, 0.8, 0.1])
        with center:

            st.markdown(
                f'<h3 style="text-align: center;">To start processing a repository, please enter a GitHub repository URL: </h3>',
                unsafe_allow_html=True,
            )
            repo_path = st.text_input(
                "Repository URL",
                help="""Enter a GitHub repository URL  
                Example: https://github.com/aimclub/OSA""",
                placeholder="https://github.com/aimclub/OSA",
            )
            st.container(height=5, border=False)

            st.selectbox(
                label="Mode",
                key="mode_select",
                options=("basic", "auto", "advanced"),
                help="""
                    Operation mode for repository processing  
                    Default: basic
                    """,
            )
            _, right = st.columns([0.02, 0.95])
            with right:
                multi = """ Currently, three modes are available:  
                        - **Basic:** *Uses a predefined plan of actions*.  
                        - **Auto**: *Automatically detects and creates the best plan for the entered repository.*  
                        - **Advanced**: *Highly customizable; build your own plan.*  
                    """
                st.markdown(multi)

            if (
                "run_osa_button" in st.session_state
                and st.session_state.run_osa_button == True
            ):
                st.session_state.osa_running = True
            else:
                st.session_state.osa_running = False

            st.container(height=5, border=False)
            if st.button(
                "Run OSA",
                icon=":material/emoji_nature:",
                use_container_width=True,
                disabled=len(repo_path) == 0 or st.session_state.osa_running,
                type="secondary" if len(repo_path) == 0 else "primary",
                key="run_osa_button",
            ):
                if not st.session_state.git_token:
                    st.warning(
                        "GIT_TOKEN not found in .env file. The tool may not work correctly with private repositories."
                    )
                self.loop.run_until_complete(self.run_osa_tool(repo_path))
                st.session_state.osa_running = False

    def get_model_config(self, provider: str, model: str) -> dict:
        """Get model configuration based on provider."""
        return {
            "provider": provider.lower(),
            "model": model,
        }

    async def run_osa_tool(self, repo_path: str) -> None:
        """Run the osa-tools application."""
        try:
            # Создаем копию текущих переменных окружения
            env = os.environ.copy()

            # Убедимся, что GIT_TOKEN передается в процесс
            if st.session_state.git_token:
                env["GIT_TOKEN"] = st.session_state.git_token

            cmd = [
                "osa-tool",
                "-r",
                repo_path,
                "-m",
                st.session_state.mode_select,
                "--web-mode",
                "--delete-dir",
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            output_container = st.empty()
            stdout_accumulated = ""

            while True:
                stdout_line = await process.stdout.readline()
                if not stdout_line:
                    break

                if line := stdout_line.decode().strip():
                    stdout_accumulated += line + "\n"
                    output_container.text_area(
                        "Console Output",
                        value=stdout_accumulated,
                        height=350,
                    )

            returncode = await process.wait()
            if returncode == 0:
                st.success("Everything is alright")
            else:
                stderr_output = await process.stderr.read()
                error_message = stderr_output.decode().strip()
                st.error(f"Error running OSA tool: {error_message}")
                logger.error(
                    f"OSA tool execution failed with code {returncode}: {error_message}"
                )

        except Exception as e:
            st.error(f"Error executing OSA tool: {e!s}")
            logger.error(f"OSA tool execution failed: {e!s}", exc_info=True)

    def run(self) -> None:
        """Run the Streamlit application."""

        # if not st.experimental_user.is_logged_in:
        #     self.render_login_screen()
        #     st.stop()

        self.render_sidebar()

        tab1, tab2 = st.tabs(
            [
                ":material/home: Home",
                ":material/settings: Configuration",
            ]
        )
        with tab1:
            self.render_main_block()

        with tab2:
            render_configuration_page()

    def __del__(self):
        """Cleanup the event loop on deletion."""
        if hasattr(self, "loop") and self.loop is not None:
            try:
                self.loop.close()
            except Exception as e:
                logger.error(f"Error closing event loop: {e}")


if __name__ == "__main__":
    app = OsaToolApp()
    app.run()
