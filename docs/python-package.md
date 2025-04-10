# Core Functionality of the `git_recap` Python Package

The `git_recap` Python package is the core of the git_recap GitHub app, handling all backend operations related to data fetching, processing, and interaction with Language Models (LLMs). This document describes the package's main functionalities and modules.

## Key Capabilities

### Fetching Data

The package's primary function is to fetch data from various Git hosting platforms. This involves:

-   **Connecting to Git Providers:** Establishing connections with different Git providers (e.g., GitHub, GitLab, Azure DevOps).
-   **Retrieving Repository Data:** Fetching relevant information such as commits, pull requests, issues, branches, and other activity details.

### Data Processing

Once the data is fetched, the package performs the following processing steps:

-   **Data Extraction:** Extracting the necessary information from the raw data retrieved from Git providers.
-   **Data Structuring:** Organizing and structuring the extracted information into a format suitable for LLM analysis.

### LLM Interaction

The package integrates with an LLM to generate insightful recaps:

-   **Prompting the LLM:** Sending structured data and carefully crafted prompts to the LLM to guide the summarization process.
-   **Receiving Summaries:** Receiving the generated recaps from the LLM.

## Modules

### `fetcher.py`

-   **Role:** The central module for coordinating the fetching process.
-   **Responsibilities:**
    -   Selecting the appropriate provider-specific fetcher based on configuration.
    -   Handling the overall data retrieval workflow.
    -   Orchestrating the flow of data to be processed.
    - It uses the classes present in `providers` folder to actually retrieve the data.

### `providers`

-   **Role:** Contains the provider-specific data fetching logic.
-   **Structure:**
    -   `base_fetcher.py`: Defines a base class (`BaseFetcher`) with an interface for fetching data, which other provider-specific classes inherit from.
    -   `github_fetcher.py`: Implements the logic for fetching data from GitHub.
    -   `gitlab_fetcher.py`: Implements the logic for fetching data from GitLab.
    -   `azure_fetcher.py`: Implements the logic for fetching data from Azure DevOps.
-   **Responsibilities:**
    -   Handling authentication for each provider.
    -   Making API requests to the provider's API.
    -   Parsing and formatting data received from the API.

### `utils.py`

-   **Role:** Provides utility functions used across the package.
-   **Responsibilities:**
    -   General purpose functions for data manipulation.
    -   Error handling.
    -   Other common tasks.

### `llm_service.py`

-   **Role:** Manages the interaction with the Language Model (LLM).
-   **Responsibilities:**
    -   Formatting the data and prompts for the LLM.
    -   Sending requests to the LLM API.
    -   Parsing and handling responses from the LLM.
    -   Error handling for LLM API interactions.

### `prompts.py`

-   **Role:** Contains predefined prompts used to guide the LLM.
-   **Responsibilities:**
    -   Defining a set of instructions for the LLM.
    -   Providing different prompts for different types of recaps or summarization tasks.
    -   Allowing for customization and fine-tuning of the prompts.

## Workflow

1.  The `fetcher.py` module is called to initiate data fetching.
2.  Based on the configured provider, the appropriate fetcher from the `providers` directory is selected.
3.  The provider-specific fetcher authenticates and retrieves data from the provider's API.
4.  The data is parsed and returned to `fetcher.py`.
5.  The fetched data is processed and formatted.
6.  The `llm_service.py` module is used to format the data and generate prompts using `prompts.py`.
7.  The request is sent to the LLM API.
8.  The LLM's response (the recap) is parsed and returned to the caller.
9. `utils.py` can be used along all the process to help.