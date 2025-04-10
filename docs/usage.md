# Usage

This page outlines how to use the `git_recap` app to generate and view summaries of your repository activity.

## Navigating the App

1.  **Access the App:** After installing the `git_recap` app from the GitHub Marketplace, you can access it through your GitHub account or organization settings.
2.  **Dashboard:** Upon entering the app, you'll be taken to the main dashboard, where you can manage connections and generate recaps.

## Configuring Providers

Before you can generate recaps, you need to configure the Git providers you want to use.

1.  **Go to the Connections Page:** Click on the "Connections" or "Providers" link in the app's navigation menu.
2.  **Choose a Provider:** Select the Git provider you want to connect (e.g., GitHub, GitLab, Azure DevOps).
3.  **Authentication:** Follow the authentication steps for the chosen provider:
    *   **GitHub:** You may need to authorize the `git_recap` app to access your repositories or install the app in your org.
    *   **GitLab:** You will need to provide a GitLab API token.
    *   **Azure DevOps:** You will need to provide a Personal Access Token (PAT).
4.  **Save:** Once you've provided the necessary credentials, save the configuration.
5. **Add more**: If you want to add more provider just repeat steps 2 to 4.

## Generating Recaps

1.  **Select a Repository:** On the main dashboard or a designated "Generate Recap" page, you'll see a list of your repositories (or those you have access to). Select the repository for which you want to generate a recap.
2.  **Choose a Timeframe:** Specify the timeframe for the recap. You might have options like "Last Week," "Last Month," "Custom Range," or others.
3.  **Generate:** Click the "Generate Recap" button.
4. **Wait**: The recap could take some time to generate, please wait until it is finished.

## Viewing Recaps

1.  **Accessing Recaps:** Once the recap has been generated, you can view it on the same page where you requested it.
2.  **Recap Format:** The recap will be displayed in a clear and concise format, summarizing the key activity within the selected repository and timeframe.
3.  **Drill-Down (Optional):** Some recaps might have options to drill down into more detail, such as viewing specific commits, pull requests, or issues.
4. **Save or export**: There will be an option to save the recap or export it to a pdf.

## Managing Connections

1.  **View Connections:** Return to the "Connections" page to view all configured providers.
2.  **Update:** You can update the credentials or settings for an existing connection.
3.  **Delete:** Remove a connection if you no longer need it.

## Troubleshooting

*   If a recap fails to generate, ensure you've correctly configured the provider and have the necessary permissions.
*   If you encounter errors or issues, check the app's logs or contact support.