"""
Streamlit interface for the Course Planner application.

This module defines a simple interactive web interface using
Streamlit.  Users can enter their university name, major, desired
number of years to graduate and any additional preferences.  The
application performs a web search to find official degree
requirements and catalog information for the specified program and
uses an AI model (if an API key is provided) to generate a
semester‑by‑semester plan.

The interface displays the search results and the generated plan
directly in the browser.  All API keys and user data are handled
client-side and are not stored on the server.
"""

from __future__ import annotations

import os
import textwrap
from typing import List, Tuple

import streamlit as st

# Attempt to import the DuckDuckGo search library.  The package
# ``ddgs`` is preferred, but older environments may still use
# ``duckduckgo_search``.
try:
    from ddgs import DDGS  # type: ignore
except ImportError:
    try:
        from duckduckgo_search import DDGS  # type: ignore
    except ImportError:
        DDGS = None  # type: ignore

try:
    import openai  # type: ignore
except ImportError:
    openai = None  # type: ignore

# Attempt to import the Anthropic client.  This package must be
# installed to support Anthropic's Claude models.  If unavailable,
# ``anthropic`` will be None and Anthropic provider selection will
# result in an informative error.
try:
    from anthropic import Anthropic  # type: ignore
except ImportError:
    Anthropic = None  # type: ignore


def search_requirements(school: str, major: str, max_results: int = 5) -> List[Tuple[str, str, str]]:
    """Search the web for degree requirements for the given school and major.

    Returns a list of tuples containing (title, link, snippet) for
    each relevant search result.  If the DuckDuckGo library isn't
    available, returns an empty list.  This function attempts to use
    whichever parameter name is supported by the installed version of
    the search library.  The ``ddgs`` package uses ``query`` while the
    legacy ``duckduckgo_search`` expects ``keywords``.
    """
    results: List[Tuple[str, str, str]] = []
    if DDGS is None:
        return results
    # Compose a search string focusing on official curriculum pages
    query_str = f"{school} {major} degree requirements curriculum"
    try:
        with DDGS() as ddgs:
            try:
                # Preferred signature for the ddgs library (query argument)
                search_results = ddgs.text(query=query_str, max_results=max_results)
            except TypeError:
                # Fallback for duckduckgo_search library (keywords argument)
                search_results = ddgs.text(keywords=query_str, max_results=max_results)
            for item in search_results:
                title = item.get("title", "No title provided")
                link = item.get("href", "")
                snippet = item.get("body", "")
                # Filter for degree/curriculum related results
                if any(kw in title.lower() for kw in ["curriculum", "degree", "requirements", "major"]):
                    results.append((title, link, snippet))
    except Exception as exc:
        st.warning(f"Search failed: {exc}")
    return results


def search_electives(major: str, max_results: int = 3) -> List[Tuple[str, str, str]]:
    """Search the web for recommended elective courses for the given major.

    Returns a list of tuples containing (title, link, snippet) for
    each relevant search result.  This helps the language model
    suggest specific course names instead of generic placeholders.  If
    the search library isn't available, an empty list is returned.
    """
    results: List[Tuple[str, str, str]] = []
    if DDGS is None:
        return results
    query_str = f"best elective courses {major} degree"
    try:
        with DDGS() as ddgs:
            try:
                search_results = ddgs.text(query=query_str, max_results=max_results)
            except TypeError:
                search_results = ddgs.text(keywords=query_str, max_results=max_results)
            for item in search_results:
                title = item.get("title", "No title provided")
                link = item.get("href", "")
                snippet = item.get("body", "")
                # Consider results with words like "elective" or "course"
                if any(kw in title.lower() for kw in ["elective", "course", "recommended"]):
                    results.append((title, link, snippet))
    except Exception as exc:
        # Log the error via a Streamlit warning, but keep processing
        st.warning(f"Elective search failed: {exc}")
    return results


def generate_plan(provider: str, api_key: str, school: str, major: str, years: str, preferences: str,
                   search_results: List[Tuple[str, str, str]],
                   elective_results: List[Tuple[str, str, str]]) -> str:
    """Generate a semester‑by‑semester plan using the selected AI provider.

    Constructs a prompt incorporating the search results and user
    preferences.  If the necessary library isn't installed or no key is
    provided, returns a message instructing the user to install the
    library or provide a key.  For OpenAI, this function supports
    both legacy and v1.x versions of the OpenAI Python library.  For
    Anthropic, it uses the messages API of the `anthropic` package.
    """
    if not api_key:
        return (
            "No API key provided. Please enter a valid API key to generate a plan."
        )

    # Compose a prompt summarising the search results and elective suggestions.
    resources_text = "\n".join(
        [f"{i+1}. {title} ({url}) - {snippet}" for i, (title, url, snippet) in enumerate(search_results)]
    )
    electives_text = "\n".join(
        [f"{i+1}. {title} ({url}) - {snippet}" for i, (title, url, snippet) in enumerate(elective_results)]
    )
    user_message = textwrap.dedent(
        f"""
        A student is planning their {major} degree at {school}. They wish to graduate in {years} years.
        Here are some snippets from official curriculum or degree requirement pages:
        {resources_text}

        Here are some search snippets listing recommended elective courses for {major}:
        {electives_text}

        Based on the above resources, generate a semester-by-semester course plan that satisfies the degree requirements.
        Include general education courses as appropriate and note any prerequisites. When suggesting elective courses,
        provide specific example courses relevant to the major using the elective snippets rather than generic placeholders.
        Respect the desired graduation timeline. {preferences}
        """
    ).strip()
    system_message = (
        "You are an academic advisor tasked with creating a realistic and actionable course plan. "
        "Use the provided degree requirement snippets to inform your plan."
    )

    if provider == "OpenAI":
        if openai is None:
            return (
                "The OpenAI Python library is not installed. Please install the "
                "`openai` package to enable plan generation."
            )
        try:
            # Attempt to use the modern v1.x API via the OpenAI client
            if hasattr(openai, "OpenAI"):
                client = openai.OpenAI(api_key=api_key)
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message},
                    ],
                    max_tokens=1024,
                    temperature=0.5,
                )
                return completion.choices[0].message.content.strip()
            else:
                # Legacy API style
                openai.api_key = api_key
                completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message},
                    ],
                    max_tokens=1024,
                    temperature=0.5,
                )
                return completion.choices[0].message.content.strip()
        except Exception as exc:
            err_text = str(exc)
            if "insufficient_quota" in err_text or "You exceeded your current quota" in err_text:
                return (
                    "Your API key does not have sufficient quota to generate a plan. "
                    "Please check your usage or billing status with your AI provider and try again."
                )
            return f"Error generating plan: {err_text}"
    elif provider == "Anthropic":
        # Use Anthropic's messages API to generate the plan.
        if Anthropic is None:
            return (
                "The Anthropic Python library is not installed. Please install the "
                "`anthropic` package to enable plan generation with Anthropic."
            )
        try:
            client = Anthropic(api_key=api_key)
            # Choose a default Claude model; Claude-3 Haiku is widely available and cost‑efficient.
            model_name = "claude-3-haiku-20240307"
            message = client.messages.create(
                max_tokens=1024,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                model=model_name,
            )
            # Anthropic messages API returns an object with a ``content`` property.
            return message.content.strip()
        except Exception as exc:
            err_text = str(exc)
            if "insufficient_quota" in err_text:
                return (
                    "Your API key does not have sufficient quota to generate a plan. "
                    "Please check your usage or billing status with your AI provider and try again."
                )
            return f"Error generating plan: {err_text}"
    else:
        return (
            "Unsupported AI provider. Please select a supported provider such as OpenAI or Anthropic."
        )


def main() -> None:
    """Run the Streamlit interface."""
    st.set_page_config(page_title="Course Planner", page_icon="📚")
    # Simple title without emoji
    st.title("Course Planner")
    st.write(
        "Plan your university courses with the help of AI and official degree information."
    )

    with st.form("planner_form"):
        # Provider selection and API key at the top of the form
        provider = st.selectbox(
            "AI provider",
            options=["OpenAI", "Anthropic"],
            index=0,
            help="Select which AI service to use."
        )
        api_key = st.text_input(
            "API key",
            type="password",
            help="Enter your API key for the selected provider.",
        )
        school = st.text_input(
            "University name",
            placeholder="e.g. University of Illinois Urbana-Champaign",
        )
        major = st.text_input(
            "Major/Program name",
            placeholder="e.g. Computer Science",
        )
        years = st.text_input(
            "Number of years until graduation",
            placeholder="4",
        )
        preferences = st.text_area(
            "Additional preferences (optional)",
            placeholder="e.g. emphasise machine learning electives",
        )
        submitted = st.form_submit_button("Generate Plan")

    if submitted:
        # Validate required fields
        missing_fields = []
        if not api_key:
            missing_fields.append("API key")
        if not school:
            missing_fields.append("university name")
        if not major:
            missing_fields.append("major/program")
        if not years:
            missing_fields.append("number of years")
        if missing_fields:
            st.error(
                "Please provide the following required fields: " + ", ".join(missing_fields)
            )
            return
        with st.spinner("Searching for degree requirements and electives..."):
            search_results = search_requirements(school, major)
            elective_results = search_electives(major)
        # Do not show curriculum or elective resources to the user; they are used internally
        with st.spinner("Generating course plan..."):
            plan = generate_plan(
                provider,
                api_key,
                school,
                major,
                years,
                preferences,
                search_results,
                elective_results,
            )
        st.subheader("Recommended Course Plan")
        st.write(plan)


if __name__ == "__main__":
    main()