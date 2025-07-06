# NEET Notice Alert Bot

A Telegram bot designed to monitor the official NEET website for new notices, process PDF documents using the Gemini API for text extraction and summarization, and send timely alerts to subscribed users via Telegram.

## Features

- **Automated Monitoring:** Continuously checks the NEET website for new notice releases at configurable intervals.
- **PDF Processing:** Downloads new notice PDFs and converts their content to text using the Google Gemini API.
- **Intelligent Summarization:** Generates concise summaries of the notice content for quick understanding.
- **Instant Alerts:** Sends immediate Telegram notifications to subscribed users with the notice summary and a link to the original PDF.
- **Duplicate Prevention:** Tracks previously processed notices to avoid sending redundant alerts.
- **Easy Deployment:** Designed for straightforward setup and deployment using Docker and Docker Compose.
- **Background Operation:** Runs as a daemonized service using Docker Compose.
- **Clean-up:** Automatically manages temporary files created during PDF processing.

## Prerequisites

Before deploying the bot, ensure you have the following installed:

- **Docker:** [Get Docker](https://www.docker.com/get-started)
- **Docker Compose:** [Install Docker Compose](https://docs.docker.com/compose/install/)
- **Telegram Bot Token:** Obtain a token by talking to [@BotFather](https://t.me/botfather) on Telegram.
- **Google Gemini API Key:** Get an API key from the [Google AI for Developers](https://ai.google.dev/) platform.

## Deployment

Follow these steps to get the bot up and running:

1.  **Clone the repository:**
    ```bash
    https://github.com/s24hira/NEET-notice-alert.git
    cd NEET-notice-alert
    ```

2.  **Create a `.env` file:**
    Create a file named `.env` in the root directory of the cloned repository and add your credentials:
    ```dotenv
    TELEGRAM_BOT_TOKEN=your_telegram_bot_token
    TELEGRAM_CHAT_ID=your_telegram_chat_id
    GEMINI_API_URL=your_gemini_api_url
    GEMINI_API_KEY=your_gemini_api_key
    SUPABASE_URL=your_supabase_url
    SUPABASE_KEY=your_supabase_anon_key
    SUPABASE_NOTICES_TABLE=notices
    SUPABASE_USERS_TABLE=users
    ```
    Replace with your actual tokens.

3.  **Deploy using Docker Compose:**
    From the root directory of the repository, run the following command:
    ```bash
    docker-compose up -d --build
    ```
    The `--build` flag ensures the Docker image is built before starting the containers. The `-d` flag runs the services in detached mode.

4.  **Verify Deployment:**
    Check the logs to ensure the bot is running without errors:
    ```bash
    docker-compose logs -f
    ```

## Bot Commands

Users can interact with the bot using the following commands in Telegram:

-   `/start` - Subscribe to receive NEET notice alerts.
-   `/status` - Check the current operational status of the bot.
-   `/help` - Display a help message with available commands.

## Data Storage

The bot stores necessary data in the following locations within the container, which are mapped to local volumes for persistence:

-   **Notice Data:** Information about processed notices is stored in `./data`.
-   **Temporary Files:** Temporary PDF images and other processing files are stored in `./pdf_images`.

## Maintenance

The bot includes built-in maintenance features:

-   **Monitoring Frequency:** Checks the NEET website at random intervals (typically between 5-8 minutes) to avoid predictable patterns.
-   **File Cleanup:** Automatically removes temporary PDF and image files after processing.
-   **Notice Tracking:** Maintains a record of detected notices to prevent sending duplicate alerts to users.

## Support

For any issues, questions, or feature requests, please open an issue on the [GitHub repository](https://github.com/s24hira/neet25-alert/issues).

## Contributing

Contributions are welcome! Please feel free to fork the repository, make improvements, and submit pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
