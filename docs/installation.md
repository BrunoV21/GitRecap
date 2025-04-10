# Installation and Setup

This guide provides step-by-step instructions for installing and setting up the `git_recap` GitHub app.

## 1. Install the GitHub App

1.  **Visit the GitHub Marketplace:** Navigate to the `git_recap` app listing in the GitHub Marketplace.
2.  **Install the App:** Click the "Install" button.
3.  **Choose Installation Target:** Select whether you want to install the app on your personal account or on an organization.
4.  **Select Repositories:** Choose the repositories you want `git_recap` to have access to. You can select specific repositories or all repositories.
5.  **Grant Permissions:** Review the permissions the app is requesting and click "Install" to proceed.

## 2. Configure the Backend

1.  **Set Up Environment:**
    *   Ensure you have Python and the required dependencies installed. You can find the dependencies listed in the `requirements.txt` file in the project's root directory.
    *   Create a virtual environment (recommended) to isolate the project's dependencies.
    *   Activate your virtual environment.
    *   Install the required dependencies using `pip`:
```
bash
        pip install -r requirements.txt
        
```
2.  **Environment Variables:**
    *   Create a `.env` file in your backend project directory.
    *   Add the following environment variables to your `.env` file:
        *   `GITHUB_APP_ID`: Your GitHub App ID.
        *   `GITHUB_PRIVATE_KEY`: The private key for your GitHub App.
        *   `GITHUB_CLIENT_ID`: Your GitHub OAuth client ID (if applicable).
        *   `GITHUB_CLIENT_SECRET`: Your GitHub OAuth client secret (if applicable).
        * `OPENAI_API_KEY`: Your OpenAI API key (if you want to use openAI).
        *   `GITLAB_TOKEN`: Your Gitlab token (if applicable).
        *   `AZURE_PAT`: Your Azure DevOps PAT (if applicable).
        *   Any other API keys or credentials needed for your setup.
    *   Ensure your backend code is configured to read these environment variables.

3.  **Deploy the Backend:**
    *   Deploy your backend application to a server. You can use platforms like Heroku, AWS, Google Cloud, or any other server of your choice.
    *   Ensure the server is running and accessible.
    *   Note the URL of your backend API (e.g., `https://your-git-recap-backend.com/`).

## 3. Connect the Frontend

1.  **Frontend Configuration:**
    *   Open the frontend project directory.
    *   Locate the configuration file (e.g., `vite.config.ts` or similar).
    *   Find the section where the backend API URL is configured.
    *   Update the API URL to point to the URL of your deployed backend. For example:
```
typescript
        // In vite.config.ts or similar
        const API_URL = "https://your-git-recap-backend.com/";
        
```
2. **Run the frontend:**
    * Execute the command to run the frontend app, probably `npm run dev` or `npm run start`
3.  **Test:**
    *   Open the frontend in your browser.
    *   Verify that the frontend can communicate with the backend by attempting to connect a provider or generate a recap.

## 4. Final Steps

1.  **Testing:** Thoroughly test the entire setup, including the installation, configuration, authentication, recap generation, and viewing.
2.  **Troubleshooting:** If you encounter any issues, check the backend logs, browser console, and ensure all the environment variables and configurations are correct.

Once you've completed these steps, your `git_recap` app should be fully installed, configured, and ready to use!