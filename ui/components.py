"""Reusable Streamlit presentation helpers for FactoryZero AI."""
from __future__ import annotations
import streamlit as st


def agent_card(name: str, status: str, summary: str = "") -> None:
    st.markdown(
        f"<div class='agent'><b>{name}</b> "
        f"<span class='pill'>{status}</span><br>"
        f"<span class='muted'>{summary}</span></div>",
        unsafe_allow_html=True,
    )


def evidence_card(document: str, page, support: str, score: float, passage: str) -> None:
    page_label = page if page is not None else "Page not available"
    st.markdown(f"**{document}** • Page: {page_label} • {support} • score {score:.2f}")
    st.info(passage)
