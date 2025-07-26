import streamlit as st


def render_git_settings_block() -> None:
    with st.container(border=True):
        st.markdown(
            '<h5 style="text-align: center;">Git settings</h5>',
            unsafe_allow_html=True,
        )
        st.text_input(
            label="Branch",
            help="""
                Branch name of the GitHub repository  
                Default: Default branch""",
        )
        left, right = st.columns(2)
        with left:
            st.checkbox(
                label="No pull request",
                help="""
                Avoid create pull request for target repository  
                Default: False""",
            )
        with right:
            st.checkbox(
                label="Delete directory",
                help="""
                Enable deleting the downloaded repository after processing (Linux only)  
                Default: False""",
            )
        st.checkbox(
            label="No fork",
            help="""
                    Avoid create fork for target repository  
                    Default: False""",
        )


def render_llm_settings_block() -> None:
    with st.container(border=True):
        st.markdown(
            '<h5 style="text-align: center;">LLM settings</h5>',
            unsafe_allow_html=True,
        )
        st.selectbox(
            label="API",
            options=("llama", "openai", "ollama"),
            help="""
                LLM API service provider  
                Default: llama
                """,
        )
        st.text_input(
            label="Base URL",
            value="https://api.openai.com/v1",
            help="""
                URL of the provider compatible with OpenAI API  
                Default: https://api.openai.com/v1""",
        )
        st.text_input(
            label="Model",
            value="gpt-3.5-turbo",
            help="""
                Specific LLM model to use  
                Default: gpt-3.5-turbo""",
        )


def render_configuration_page() -> None:
    left, center, right = st.columns([1, 1, 1])

    with left:
        token_status = (
            "✅ Found" if st.session_state.git_token else "❌ Not found in .env"
        )
        st.info(f"GIT_TOKEN status: {token_status}")

        if not st.session_state.git_token:
            st.warning(
                "GIT_TOKEN not found in .env file. Some features may not work correctly."
            )

        render_git_settings_block()

    with center:
        render_llm_settings_block()
