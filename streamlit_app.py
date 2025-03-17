import asyncio
import logging
import os
import subprocess
import tempfile

import streamlit as st

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


TITLE = "README-AI"
DESCRIPTION = ""

SUPPORTED_MODELS = {
    "ITMO": ["wq_gemma3_27b_8q"],
}

BADGE_STYLES = [
    "default",
    "flat",
    "flat-square",
    "plastic",
    "for-the-badge",
    "skills",
    "skills-light",
    "social",
]

LOGO_OPTIONS = [
    "blue",
    "gradient",
    "black",
    "cloud",
    "purple",
    "grey",
    "custom",
    "llm",
]

HEADER_STYLES = ["classic", "modern", "compact", "ascii", "ascii_box", "svg"]

TOC_STYLES = ["bullet", "fold", "links", "number", "roman"]

class ReadmeAIApp:
    """
    Streamlit web app serving the readme-ai CLI.
    """

    def __init__(self):
        self.init_session_state()
        self.setup_page_config()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def init_session_state(self) -> None:
        if "readme_generated" not in st.session_state:
            st.session_state.readme_generated = False
        if "readme_content" not in st.session_state:
            st.session_state.readme_content = ""
        if "selected_provider" not in st.session_state:
            st.session_state.selected_provider = "ITMO"

    def setup_page_config(self) -> None:
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title="OSA Tool",
            layout="wide",
            initial_sidebar_state="expanded",
            menu_items={
                "Get Help": "https://t.me/osa_helpdesk",
                "About": "https://github.com/ITMO-NSS-team/Open-Source-Advisor",
            },
        )

    def render_header(self) -> None:
        """Render application header."""
        col1, col2, col3 = st.columns([1, 1, 1])  # Создаем три колонки
        with col2:  # Используем центральную колонку
            st.image(
                "assets/osa_logo.png",
                width=500,  # Настройте ширину по вашему усмотрению
                use_container_width=False,
            )

    def render_sidebar(self) -> tuple[str, str, dict]:
        """Render sidebar with configuration options."""
        with st.sidebar:
            st.title("Configuration")
            st.subheader("Repository Settings")
            repo_path = st.text_input(
                "Repository URL/Path",
                help="Enter a GitHub repository URL or local path",
            )

            st.subheader("LLM Provider")
            selected_provider = st.radio(
                "Select Provider",
                options=list(SUPPORTED_MODELS.keys()),
                horizontal=True,
            )
            st.session_state.selected_provider = selected_provider

            return (
                repo_path,
                None,
                self.get_model_config(selected_provider, None),
            )

    def render_output_section(self) -> None:
        """Render README output section."""
        if st.session_state.readme_generated:
            tabs = st.tabs(["Preview", "Markdown", "Download"])

            with tabs[0]:
                st.markdown(
                    st.session_state.readme_content, unsafe_allow_html=True
                )

            with tabs[1]:
                st.code(st.session_state.readme_content, language="markdown")

            with tabs[2]:
                st.download_button(
                    "Download README.md",
                    st.session_state.readme_content,
                    file_name="README.md",
                    mime="text/markdown",
                    use_container_width=True,
                )

    def get_model_config(self, provider: str, model: str) -> dict:
        """Get model configuration based on provider."""
        return {
            "provider": provider.lower(),
            "model": model,
        }

    def build_command(
        self, repo_path: str, output_path: str, config: dict, options: dict
    ) -> list[str]:
        """Build command for readme-ai CLI."""
        cmd = [
            "readmeai",
            "--repository",
            repo_path,
            "--output",
            output_path,
            "--api",
            config["provider"],
        ]

        return cmd

    async def run_osa(
        self, repo_path: str, api_key: str, config: dict, options: dict
    ) -> None:
        """Run OSA using provided configuration."""
        try:
            with tempfile.NamedTemporaryFile(
                suffix=".md", mode="w+", delete=False
            ) as tmp:
                command = self.build_command(
                    repo_path, tmp.name, config, options
                )
                await self.execute_command(command, api_key, tmp.name)

                with open(tmp.name) as f:
                    st.session_state.readme_content = f.read()
                    st.session_state.readme_generated = True

        except Exception as e:
            st.error(f"Error generating README: {e!s}")
            logger.error(f"README generation failed: {e!s}", exc_info=True)

    async def execute_command(
        self, command: list[str], api_key: str, output_path: str
    ) -> None:
        """Execute the command and handle its output."""
        with st.spinner("Generating README..."):
            env = os.environ.copy()

            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            output_container = st.empty()
            stderr_accumulated = ""

            while True:
                try:
                    stderr_line = await process.stderr.readline()
                    if not stderr_line:
                        break

                    if line := stderr_line.decode().strip():
                        stderr_accumulated += line + "\n"
                        output_container.text_area(
                            "Generation Logs",
                            value=stderr_accumulated,
                            height=150,
                        )
                except Exception as e:
                    logger.error(f"Error reading process output: {e}")
                    break

            returncode = await process.wait()
            if returncode != 0:
                raise subprocess.CalledProcessError(
                    returncode, command, stderr_accumulated
                )

    def run(self) -> None:
        """Run the Streamlit application."""
        self.render_header()

        repo_path, api_key, model_config = self.render_sidebar()

        col1, _ = st.columns(2)
        with col1:
            if st.button("Run OSA", use_container_width=True):
                self.loop.run_until_complete(
                    self.run_osa(
                        repo_path, api_key, model_config, {}
                    )
                )

        self.render_output_section()

    def __del__(self):
        """Cleanup the event loop on deletion."""
        if hasattr(self, "loop") and self.loop is not None:
            try:
                self.loop.close()
            except Exception as e:
                logger.error(f"Error closing event loop: {e}")


if __name__ == "__main__":
    app = ReadmeAIApp()
    app.run()