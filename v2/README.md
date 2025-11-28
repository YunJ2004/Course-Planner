# Course Planner

Course Planner is a simple web application designed to help
undergraduates organise their degree schedules.  Given the name of a
university, the major or programme of study, the number of years
until graduation and any additional preferences, the app searches the
web for official curriculum or degree requirement pages and, if
provided with an API key for a language model (such as OpenAI’s),
generates a semester‑by‑semester plan.

The application is built using [Streamlit](https://streamlit.io),
which means it runs entirely in your browser once launched.  All
API keys and personal data remain on your machine.

## Features

* Collects curriculum information from official sources using
  DuckDuckGo search.  Only high‑relevance results (pages containing
  words like “curriculum”, “degree” or “requirements”) are shown.
* Generates a structured course plan with the help of a language
  model.  The plan respects general education requirements and
  prerequisites and can adapt to the desired graduation timeline.
* Does not persist sensitive information; API keys are only used in
  memory during a request.

## Getting Started

### Prerequisites

* Python 3.8 or newer installed on your computer.
* An OpenAI API key (optional) if you wish to generate a plan using a
  language model.  Without a key you can still view the collected
  curriculum resources.

### Running the App

1. Open a terminal (or command prompt on Windows) and navigate to the
   directory containing the files in this repository.

2. Use one of the provided convenience scripts to launch the app:

   - On Linux or macOS:

     ```bash
     bash start.sh
     ```

   - On Windows:

     ```cmd
     start.bat
     ```

   These scripts call `install_and_run.py`, which installs any
   missing dependencies (Streamlit, ddgs, duckduckgo_search and
   OpenAI) and then launches the Streamlit interface.  If you prefer
   to run the installer manually, you can execute `python
   install_and_run.py` yourself.

3. After a few moments a URL will appear in the terminal (usually
   `http://localhost:8501`).  Open this address in your web browser to
   use the application.

4. Select your AI provider from the drop‑down (OpenAI or Anthropic),
   then enter the corresponding API key.  The API key is required to
   generate a plan.  Next provide your university name, major and
   desired number of years to graduation.  You can also add any
   additional preferences such as elective focus areas.  Click
   **Generate Plan** to get a recommended semester‑by‑semester schedule.

## Development Notes

This project includes a simple Flask version (`app.py`) and
corresponding templates in the original source tree.  The Streamlit
interface (`streamlit_app.py`) is currently recommended for ease of
use.  If you wish to customise or extend the behaviour, edit the
Streamlit module and the helper functions defined therein.  Pull
requests are welcome!
