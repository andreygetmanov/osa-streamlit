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

            return repo_path

    def get_model_config(self, provider: str, model: str) -> dict:
        """Get model configuration based on provider."""
        return {
            "provider": provider.lower(),
            "model": model,
        }

    async def run_osa_tool(self, repo_path: str) -> None:
        """Run the osa-tools application."""
        try:
            # Разделяем команду на отдельные аргументы для create_subprocess_exec
            process = await asyncio.create_subprocess_exec(
                "python",
                "Open-Source-Advisor/main.py",
                "-r",
                repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
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
                        height=150,
                    )

            returncode = await process.wait()
            if returncode == 0:
                st.success("Everything is alright")
            else:
                stderr_output = await process.stderr.read()
                error_message = stderr_output.decode().strip()
                st.error(f"Error running OSA tool: {error_message}")
                logger.error(f"OSA tool execution failed with code {returncode}: {error_message}")

        except Exception as e:
            st.error(f"Error executing OSA tool: {e!s}")
            logger.error(f"OSA tool execution failed: {e!s}", exc_info=True)

    def run(self) -> None:
        """Run the Streamlit application."""
        self.render_header()

        repo_path = self.render_sidebar()

        col1, _ = st.columns(2)
        with col1:
            if st.button("Run OSA", use_container_width=True):
                self.loop.run_until_complete(self.run_osa_tool(repo_path))


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