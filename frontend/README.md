# NeonSearch Frontend

This is the frontend application for the NeonSearch project, built with React. It provides the user interface for searching and displaying video content aggregated by the backend.

## Technologies

*   React
*   JavaScript
*   HTML
*   CSS (with Tailwind CSS)
*   Node.js / npm

## Getting Started

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

### Installation

1.  Navigate to the frontend directory:
    ```bash
    cd neonsearch/frontend
    ```
2.  Install Node.js dependencies:
    ```bash
    npm install
    ```

### Running the Development Server

```bash
npm start
```

This command runs the app in development mode. Open [http://localhost:3000](http://localhost:3000) to view it in your browser. The page will reload if you make changes to the code.

### Building for Production

```bash
npm run build
```

This builds the app for production to the `build` folder, optimizing it for performance.

## Project Structure

*   `public/`: Contains static assets like `index.html`.
*   `src/`: Contains the React application code.
    *   `components/ui/`: Reusable UI components.
    *   `hooks/`: Custom React hooks.
    *   `lib/`: Utility functions.
    *   `store/`: State management (e.g., videoStore.js).
*   `craco.config.js`, `tailwind.config.js`, etc.: Configuration files.

## Contributing

Please refer to the main project README for contribution guidelines.

## License

[Specify License Here, e.g., MIT License]
