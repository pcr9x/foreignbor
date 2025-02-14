# ForeignborGPT Setup Instructions

This guide will help you set up the backend and frontend for the ForeignborGPT project.

## Prerequisites

- Ensure you have [Node.js](https://nodejs.org/) and [npm](https://npmjs.com/) installed for the frontend.
- Ensure you have [Python 3.x](https://www.python.org/downloads/) and [pip](https://pip.pypa.io/en/stable/) installed for the backend.
- You should have `supabase` set up and configured for authentication.

---

## Backend Setup

1. Navigate to the `backend` folder:

    ```bash
    cd backend
    ```

2. Install the required Python dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Start the backend server using `uvicorn`:

    ```bash
    uvicorn api.main:app --reload
    ```

   The backend will be running at [http://localhost:8000](http://localhost:8000).

---

## Frontend Setup

1. Navigate to the `frontend` folder:

    ```bash
    cd frontend
    ```

2. Install the required npm dependencies:

    ```bash
    npm install
    ```

3. Start the frontend development server:

    ```bash
    npm run dev
    ```

   The frontend will be available at [http://localhost:3000](http://localhost:3000).

---

## Common Troubleshooting

- **Backend not running**: Ensure your virtual environment is activated, and all dependencies are installed.
- **Frontend not displaying correctly**: Verify that all npm dependencies are installed and no errors are showing in the terminal.
- **API errors**: Check the network tab in your browser's developer tools to verify if the frontend is correctly interacting with the backend.

---

## Notes

- The login and signup routes for authentication are handled by Supabase.
- Both the frontend and backend should be running concurrently for full functionality.

