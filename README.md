# NeonSearch

NeonSearch is a project designed to search and aggregate video content from various online platforms. It consists of a Python-based backend that handles web scraping and API requests, and a React-based frontend for user interaction.

## Features

*   Aggregates video search results from multiple platforms (Eporner, Pornhub, Redtube, Wow.xxx, XNXX, Xvideos).
*   Provides a user interface for searching and viewing video content.
*   Modular driver architecture for easy extension to new platforms.

## Technologies

*   **Backend:** Python
*   **Frontend:** React, JavaScript, HTML, CSS (with Tailwind CSS)
*   **Web Scraping:** BeautifulSoup

## Installation

### Backend

1.  Navigate to the backend directory:
    ```bash
    cd neonsearch/backend
    ```
2.  Install Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: Ensure you have Python and pip installed in your Termux environment. You might need to run `pkg install python`)*

### Frontend

1.  Navigate to the frontend directory:
    ```bash
    cd neonsearch/frontend
    ```
2.  Install Node.js dependencies:
    ```bash
    npm install
    ```
    *(Note: Ensure you have Node.js and npm installed in your Termux environment. You might need to run `pkg install nodejs`)*

## Running the Project

### Backend Server

1.  Navigate to the backend directory:
    ```bash
    cd neonsearch/backend
    ```
2.  Run the server:
    ```bash
    python server.py
    ```
    *(The server will typically run on http://localhost:PORT, check server.py for details)*

### Frontend Development Server

1.  Navigate to the frontend directory:
    ```bash
    cd neonsearch/frontend
    ```
2.  Start the development server:
    ```bash
    npm start
    ```
    *(This will usually open the application in your browser at http://localhost:3000)*

## Backend Drivers

The backend includes modular drivers for various video platforms. Each driver is documented with docstrings explaining its functionality.

*   **AbstractModule:** Base class defining the driver interface.
*   **EpornerDriver:** Handles scraping from Eporner.
*   **PornhubDriver:** Handles scraping from Pornhub (videos and GIFs).
*   **RedtubeDriver:** Handles scraping from Redtube.
*   **WowXXXDriver:** Handles scraping from Wow.xxx.
*   **XnxxDriver:** Handles scraping from XNXX.
*   **XvideosDriver:** Handles scraping from Xvideos.

Unit tests have been added for these drivers in the `tests/` directory to ensure their reliability.

## Project Structure

*   `backend/`: Contains the Python backend code, including web scraping drivers.
*   `frontend/`: Contains the React frontend code.
*   `tests/`: Contains unit tests for the backend drivers.

## Future Improvements (TODOs)

*   Implement more robust error handling for each backend driver to gracefully handle website changes or blocks.
*   Add comprehensive documentation for the backend drivers (beyond docstrings).
*   Ensure consistent styling and theming across all frontend UI components.
*   Implement API rate limiting and error handling in the backend server.
*   Consider adding security measures to the backend API, such as input validation and authentication if applicable.
*   Review frontend dependencies in `package.json` for unnecessary packages and update existing ones.
*   Review backend dependencies in `requirements.txt` for unnecessary packages and update existing ones.
*   Add integration tests for the frontend-backend communication.
*   Consider adding a mechanism to detect and handle website structure changes that might break drivers.
*   Ensure all API keys and sensitive information are managed securely (e.g., using environment variables).

## Contributing

Contributions are welcome! Please refer to `CONTRIBUTING.md` (if it exists) or open an issue/pull request.

## License

[Specify License Here, e.g., MIT License]
