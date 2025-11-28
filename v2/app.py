"""
Course Planner Web Application
================================

This module implements a simple Flask‐based web application called
``course planner``.  Users can provide an API key for a language model
service (for example, OpenAI's ChatGPT) and specify one or more learning
topics.  The application uses the DuckDuckGo search API to discover
relevant online courses for the given topics, then asks the language
model to organise those courses into a coherent learning plan.  The
resulting plan is displayed back to the user in a separate page.

The application avoids persisting any sensitive information (such as
API keys) on the server.  All data is passed directly to the
underlying libraries during each request.  See the accompanying
``README.md`` for instructions on installing dependencies and running
the app locally.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Dict, Any

from flask import Flask, render_template, request, redirect, url_for, flash

try:
    import openai  # type: ignore
except ImportError:
    openai = None  # Placeholder if openai isn't installed yet

try:
    # DuckDuckGo search library; renamed from ``duckduckgo_search`` to ``ddgs``
    from ddgs import DDGS  # type: ignore
except ImportError:
    try:
        from duckduckgo_search import DDGS  # type: ignore
    except ImportError:
        DDGS = None  # type: ignore


app = Flask(__name__)
app.secret_key = os.environ.get("COURSE_PLANNER_SECRET_KEY", "please_change_me")


@dataclass
class CourseResult:
    """Lightweight container for a single search result describing a course."""

    title: str
    link: str
    snippet: str

    def to_prompt_string(self, index: int) -> str:
        """Format the result as a numbered bullet for inclusion in a prompt."""
        return f"{index}. {self.title} ({self.link}) - {self.snippet}"


def search_courses(topic: str, max_results: int = 5) -> List[CourseResult]:
    """
    Perform a web search for courses related to ``topic`` using DuckDuckGo.

    Returns a list of ``CourseResult`` objects containing the title,
    hyperlink and snippet for each result.  If the ``ddgs`` package is not
    available, an empty list will be returned.

    :param topic: The learning topic to search for (e.g. "Python programming").
    :param max_results: Maximum number of results to return per topic.
    :returns: A list of ``CourseResult`` instances.
    """
    results: List[CourseResult] = []
    if DDGS is None:
        # ddgs library not installed; log and return empty list
        print("Warning: DuckDuckGo search library is not installed. Returning no results.")
        return results
    query = f"best {topic} online course"
    try:
        with DDGS() as ddgs:
            search_results = ddgs.text(keywords=query, max_results=max_results)
            for item in search_results:
                title = item.get("title", "No title provided")
                link = item.get("href", "")
                snippet = item.get("body", "")
                # Filter out results without course‐related keywords to reduce noise
                if any(keyword in title.lower() for keyword in ["course", "program", "tutorial", "certificate"]):
                    results.append(CourseResult(title=title, link=link, snippet=snippet))
    except Exception as exc:
        # If the search fails, log the error for debugging
        print(f"Error during DuckDuckGo search: {exc}")
    return results


def generate_plan(api_key: str, topic: str, courses: List[CourseResult]) -> str:
    """
    Use the provided language model API to generate a learning plan.

    This function constructs a conversational prompt that lists the
    discovered courses and asks the language model to produce a
    structured learning path.  The plan includes suggested course
    sequencing, recommended durations and any insights gleaned from the
    snippets.  If the ``openai`` library is not installed or no API key is
    provided, a placeholder message is returned.

    :param api_key: Secret key for authenticating with the language model API.
    :param topic: The overarching topic requested by the user.
    :param courses: A list of ``CourseResult`` objects.
    :returns: A string containing the generated learning plan.
    """
    if openai is None:
        return (
            "The OpenAI Python library is not installed. Please install the"
            " `openai` package to enable plan generation."
        )
    if not api_key:
        return "No API key provided. Please supply a valid API key to generate a plan."
    # Compose the prompt with numbered search results
    courses_prompt = "\n".join(result.to_prompt_string(i + 1) for i, result in enumerate(courses))
    system_message = (
        "You are a helpful educational advisor. Based on the search results,"
        " recommend a structured learning plan for the user. Your plan should"
        " list the courses in a logical order, summarise the unique aspects of"
        " each course, and suggest approximate durations. Include any relevant"
        " notes about prerequisites or progression."
    )
    user_message = (
        f"The user wants to learn about '{topic}'. Here are some course descriptions:\n"
        f"{courses_prompt}\n\n"
        "Using these descriptions as a starting point, generate a clear and"
        " actionable learning plan."
    )
    try:
        # Initialize the OpenAI client using the provided API key
        openai.api_key = api_key
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            max_tokens=800,
            temperature=0.5,
            top_p=0.95,
        )
        plan = completion.choices[0].message.content.strip()
        return plan
    except Exception as exc:
        return f"Error generating plan with the language model: {exc}"


@app.route("/", methods=["GET", "POST"])
def index() -> Any:
    """Display the home page and handle form submissions."""
    if request.method == "POST":
        api_key = request.form.get("api_key", "").strip()
        topic = request.form.get("topic", "").strip()
        if not topic:
            flash("Please enter a topic to search for courses.")
            return redirect(url_for("index"))
        # Fetch courses
        courses = search_courses(topic)
        if not courses:
            flash("No courses were found for the specified topic. Please try a different keyword.")
            return redirect(url_for("index"))
        # Generate the learning plan using the AI model
        plan = generate_plan(api_key, topic, courses)
        return render_template(
            "plan.html",
            topic=topic,
            courses=courses,
            plan=plan,
        )
    return render_template("index.html")


if __name__ == "__main__":
    # Only for local development; when deploying to a platform such as Heroku
    # or Azure, use a proper WSGI server instead of ``app.run``.
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))