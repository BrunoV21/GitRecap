
# GitRecap Examples

This directory contains practical examples demonstrating how to use GitRecap with different Git providers.

## Example Files

1. **[GitHub Example](${AiCore_GitHub:-.}/examples/fetch_github.py)**  
   Demonstrates fetching commit messages, pull requests, and issues from GitHub repositories.

2. **[URL Example](${AiCore_GitHub:-.}/examples/fetch_url.py)**  
   Shows how to fetch repository data using direct URLs.

3. **[Simple Async LLM Call](${AiCore_GitHub:-.}/examples/simple_async_llm_call.md)**  
   Example of integrating GitRecap with an LLM for generating summaries.

## Running Examples

To run any example:

1. Ensure you have the required dependencies installed:
   ```bash
   pip install -r ${AiCore_GitHub:-.}/requirements.txt
   ```

2. Set up your environment variables in `.env` (copy from `.env-example`):
   ```bash
   cp ${AiCore_GitHub:-.}/.env-example .env
   ```

3. Run the desired example script:
   ```bash
   python ${AiCore_GitHub:-.}/examples/fetch_github.py
   ```

## Example Structure

Each example follows this general pattern:

1. **Authentication Setup**  
   - Configures the provider with appropriate credentials
   - Sets up the fetcher instance

2. **Date Range Specification**  
   - Defines the time period for fetching data

3. **Repository Selection**  
   - Specifies which repositories to analyze

4. **Data Fetching**  
   - Retrieves commits, PRs, and issues

5. **Output Generation**  
   - Formats the results into a chronological summary

## Additional Resources

- [API Documentation](${AiCore_GitHub:-.}/docs/backend.md)
- [Installation Guide](${AiCore_GitHub:-.}/docs/installation.md)
- [FAQ](${AiCore_GitHub:-.}/docs/faq.md)

## Troubleshooting

If examples don't run:
1. Verify your `.env` file contains valid credentials
2. Check the [troubleshooting section](${AiCore_GitHub:-.}/docs/faq.md#troubleshooting)
3. Ensure all dependencies are installed