import asyncio
import logging
import os
import subprocess
import tempfile

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


SUPPORTED_MODELS = {
    "ITMO": ["wq_gemma3_27b_8q"],
}


class OsaToolApp:
    """
    Streamlit web app serving the OSA tool CLI.
    """

    def __init__(self):
        self.init_session_state()
        self.setup_page_config()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.git_token = os.getenv("GIT_TOKEN")
        if not self.git_token:
            logger.warning("GIT_TOKEN not found in environment variables")

    def init_session_state(self) -> None:
        if "readme_generated" not in st.session_state:
            st.session_state.readme_generated = False
        if "readme_content" not in st.session_state:
            st.session_state.readme_content = ""
        if "selected_provider" not in st.session_state:
            st.session_state.selected_provider = "ITMO"
        if "translate_dirs" not in st.session_state:
            st.session_state.translate_dirs = False
        if "generate_workflows" not in st.session_state:
            st.session_state.generate_workflows = False
        if "ensure_license" not in st.session_state:
            st.session_state.ensure_license = False

    def setup_page_config(self) -> None:
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_icon=":bee:",
            page_title="OSA Tool",
            layout="wide",
            initial_sidebar_state="collapsed",
            menu_items={
                "Get Help": "https://t.me/osa_helpdesk",
                "About": "https://github.com/ITMO-NSS-team/Open-Source-Advisor",
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

    def render_logout_block(self) -> None:
        """Render application logout block"""
        left, right = st.columns([0.9, 0.1], vertical_alignment="center")

        with left:
            username = "User" or st.experimental_user.name
            st.markdown(
                f'<h5 style="text-align: left;">Welcome, {username} 👋</h5>',
                unsafe_allow_html=True,
            )

        with right:
            st.button(
                "Log out",
                on_click=st.logout,
                use_container_width=True,
                type="primary",
                icon=":material/logout:",
            )

    def render_sidebar(self) -> None:
        """Render sidebar with configuration options."""
        with st.sidebar:
            token_status = "✅ Found" if self.git_token else "❌ Not found in .env"
            st.info(f"GIT_TOKEN status: {token_status}")

            if not self.git_token:
                st.warning(
                    "GIT_TOKEN not found in .env file. Some features may not work correctly."
                )
            # st.title("Configuration")
            # st.subheader("Repository Settings")

            # st.subheader("LLM Provider")
            # selected_provider = st.radio(
            #     "Select Provider",
            #     options=list(SUPPORTED_MODELS.keys()),
            #     horizontal=True,
            # )
            # st.session_state.selected_provider = selected_provider
            # st.subheader("Additional Options")
            # st.session_state.translate_dirs = st.checkbox(
            #     "Translate dirs", value=st.session_state.translate_dirs
            # )
            # st.session_state.generate_workflows = st.checkbox(
            #     "Generate workflows", value=st.session_state.generate_workflows
            # )
            # st.session_state.ensure_license = st.checkbox(
            #     "Ensure license", value=st.session_state.ensure_license
            # )

    def render_main_block(self) -> None:
        _, center, _ = st.columns([0.2, 0.6, 0.2])
        with center:
            repo_path = st.text_input(
                "Repository URL/Path",
                help="Enter a GitHub repository URL or local path",
            )
            st.selectbox(
                label="Mode",
                options=("base", "auto", "advanced"),
                help="""
                    Operation mode for repository processing  
                    Default: base
                    """,
            )
            st.container(height=20, border=False)
            if st.button(
                "Run OSA", use_container_width=True, disabled=len(repo_path) == 0
            ):
                if not self.git_token:
                    st.warning(
                        "GIT_TOKEN not found in .env file. The tool may not work correctly with private repositories."
                    )
                self.loop.run_until_complete(self.run_osa_tool(repo_path))

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
            if self.git_token:
                env["GIT_TOKEN"] = self.git_token

            cmd = [
                "osa-tool",
                "-r",
                repo_path,
                "--delete-dir",
            ]

            if st.session_state.translate_dirs:
                cmd.append("--translate-dirs")
            if st.session_state.generate_workflows:
                cmd.append("--generate-workflows")
            if st.session_state.ensure_license:
                cmd.append("--ensure-license")

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

    def render_main_page(self) -> None:
        self.render_logout_block()
        self.render_main_block()

    def run(self) -> None:
        """Run the Streamlit application."""

        # if not st.experimental_user.is_logged_in:
        #     self.render_login_screen()
        #     st.stop()

        pg = st.navigation(
            [
                st.Page(
                    self.render_main_page,
                    title="Home",
                    icon=":material/home:",
                    default=True,
                ),
                st.Page(
                    "configuration_page.py",
                    title="Configuration",
                    icon=":material/settings:",
                ),
            ],
        )
        pg.run()

        self.render_sidebar()

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
