import asyncio
import logging
import os

import streamlit as st

logger = logging.getLogger(__name__)


def render_input_block() -> None:
    st.markdown(
        f'<h3 style="text-align: center;">To start processing a repository, please enter a GitHub repository URL: </h3>',
        unsafe_allow_html=True,
    )
    st.text_input(
        label="Repository URL",
        key="repo_url",
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
        multi = """Select the operation mode for repository processing:  
                    - **Basic:** *run a minimal predefined set of tasks.*  
                    - **Auto**: *automatically determine necessary actions based on repository analysis.*  
                    - **Advanced**: *run all enabled features based on a provided configuration.*  
                """
        st.markdown(multi)


def render_run_block() -> None:
    if "run_osa_button" in st.session_state and st.session_state.run_osa_button == True:
        st.session_state.running = True
    else:
        st.session_state.running = False

    st.container(height=5, border=False)
    if st.button(
        "Run OSA",
        icon=":material/emoji_nature:",
        use_container_width=True,
        disabled=len(st.session_state.repo_url) == 0 or st.session_state.running,
        type="secondary" if len(st.session_state.repo_url) == 0 else "primary",
        key="run_osa_button",
    ):
        if not st.session_state.git_token:
            st.warning(
                "GIT_TOKEN not found in .env file. The tool may not work correctly with private repositories."
            )
        asyncio.run(run_osa_tool())
        st.rerun()


@st.fragment
def render_output_block() -> None:
    if "output_logs" in st.session_state:
        st.divider()
        if st.session_state.output_exit_code == 0:
            left, right = st.columns([0.8, 0.2], vertical_alignment="center")
            with left:
                st.success(st.session_state.output_message)
            with right:
                st.download_button(
                    label="Download Report",
                    data="test",
                    file_name="data.csv",
                    mime="text/csv",
                    icon=":material/download:",
                    use_container_width=True,
                )
        else:
            st.error(st.session_state.output_message)
        with st.expander("See console output"):
            st.code(
                st.session_state.output_logs,
                height=350,
            )


def render_main_tab() -> None:
    _, center, _ = st.columns([0.1, 0.8, 0.1])
    with center:
        render_input_block()
        render_run_block()
    render_output_block()


async def run_osa_tool() -> None:
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
            st.session_state.repo_url,
            "-m",
            st.session_state.mode_select,
            "--web-mode",
            "--delete-dir",
        ]

        if "article" in st.session_state:
            cmd.extend(("--article", st.session_state.article.get("data")))
        if "branch" in st.session_state:
            cmd.extend(("--branch", st.session_state.branch))
        if st.session_state.no_fork:
            cmd.append("--no-fork")
        if st.session_state.no_pull_request:
            cmd.append("--no-pull-request")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        output_container = st.empty()
        st.session_state.output_logs = f"{cmd}\n"
        last_line = None

        while True:
            stdout_line = await process.stdout.readline()
            if not stdout_line:
                break

            if line := stdout_line.decode().strip():
                last_line = line
                st.session_state.output_logs += line + "\n"
                output_container.code(
                    st.session_state.output_logs,
                    height=350,
                )
                await asyncio.sleep(0.5)

        st.session_state.output_exit_code = await process.wait()
        if st.session_state.output_exit_code == 0:
            st.session_state.output_message = "Everything is alright"
        else:
            stderr_output = await process.stderr.read()
            error_message = stderr_output.decode().strip()
            st.session_state.output_message = f"**Error running OSA tool**: `{last_line}`"
            logger.error(
                f"OSA tool execution failed with code {st.session_state.output_exit_code}: {last_line}"
            )

    except Exception as e:
        st.error(f"Error executing OSA tool: {e!s}")
        logger.error(f"OSA tool execution failed: {e!s}", exc_info=True)
