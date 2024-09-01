# Image Processing App

## Overview

This project is an image processing application using Flask and Celery. It processes images asynchronously and stores the results in an SQLite database. It also includes a webhook feature for notification upon completion.

## Setup

1. **Clone the Repository**

    ```bash
    git clone <repository-url>
    cd image-processing-app
    ```

2. **Install Dependencies**

    ```bash
    pip install -r requirements.txt
    ```

3. **Start Services**

    - **Start the Flask application**

      ```bash
      flask run
      ```

    - **Start the Celery worker**

      ```bash
      celery -A app.celery worker --loglevel=info
      ```

    - **Start the webhook server (optional, for testing)**

      ```bash
      python webhook_server.py
      ```

4. **Docker Setup**

   To build and run the Docker containers, use:

    ```bash
    docker-compose up --build
    ```

## API Endpoints

1. **Upload CSV File**

    - **Endpoint**: `/upload`
    - **Method**: POST
    - **Parameters**: `file` (CSV file)
    - **Response**: JSON with `request_id`

2. **Check Processing Status**

    - **Endpoint**: `/status/<request_id>`
    - **Method**: GET
    - **Response**: JSON with processing status and data

3. **Webhook**

    - The webhook endpoint is called after processing images. Set your own webhook URL in `app.py`.

## Notes

- Ensure Redis is running for Celery.
- Update the webhook URL in `app.py` as needed.
- For local testing, start the Flask app and Celery worker separately.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
