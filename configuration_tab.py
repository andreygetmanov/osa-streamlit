import tempfile

import streamlit as st


@st.dialog("Add an Article")
def add_article(type) -> None:
    article = None
    if type == "URL":
        article = st.text_input("Paste URL")
    elif type == "File":
        article = st.file_uploader("Upload Article", ["pdf"])

    st.container(height=5, border=False)

    if st.button(
        "Submit",
        disabled=not article,
        use_container_width=True,
        type="primary",
    ):
        if type == "File":
            tmpfilename = tempfile.NamedTemporaryFile(
                delete=False, dir=st.session_state.tmpdirname, suffix=".pdf"
            )
            tmpfilename.write(article.getvalue())
            article = tmpfilename.name
        st.session_state.article = {"data": article, "type": type}
        st.rerun()


@st.fragment
def render_article_block() -> None:
    with st.container(border=True):
        st.markdown(
            '<h5 style="text-align: center;">Article</h5>',
            unsafe_allow_html=True,
        )
        if "article" not in st.session_state:
            left, right = st.columns(2)
            with left:
                if st.button(
                    "Paste URL",
                    icon=":material/globe:",
                    use_container_width=True,
                ):
                    add_article("URL")
            with right:
                if st.button(
                    "Upload Article",
                    icon=":material/upload_file:",
                    use_container_width=True,
                ):
                    add_article("File")
        else:
            st.success(
                f"Article added via {st.session_state.article.get("type")}:  \n{st.session_state.article.get("data")}"
            )
            if st.button("Remove", use_container_width=True):
                del st.session_state["article"]
                st.rerun()


@st.fragment
def render_git_settings_block() -> None:
    with st.container(border=True):
        st.markdown(
            '<h5 style="text-align: center;">Git settings</h5>',
            unsafe_allow_html=True,
        )
        st.text_input(
            label="Branch",
            key="branch",
            help="""
                Branch name of the GitHub repository  
                Default: Default branch""",
        )
        left, right = st.columns(2)
        with left:
            st.checkbox(
                label="No pull request",
                key="no_pull_request",
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
                value=True,
                disabled=True,
            )
        st.checkbox(
            label="No fork",
            key="no_fork",
            help="""
                    Avoid create fork for target repository  
                    Default: False""",
        )


@st.fragment
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


def render_configuration_tab() -> None:
    left, center, right = st.columns([1, 1, 1])

    with left:
        render_article_block()

    with center:
        token_status = (
            "✅ Found" if st.session_state.git_token else "❌ Not found in .env"
        )
        st.info(f"GIT_TOKEN status: {token_status}")

        if not st.session_state.git_token:
            st.warning(
                "GIT_TOKEN not found in .env file. Some features may not work correctly."
            )

        render_git_settings_block()

    with right:
        render_llm_settings_block()
