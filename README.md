# FlexTravel Planner

A full-stack travel planner with a Django REST API backend and a React + Vite + Tailwind frontend.

## Project Structure

- `backend/` - Django + Django REST Framework API
- `frontend/` - React app built with Vite and styled with Tailwind CSS

## Backend Setup (Django + DRF)

1. Go to the backend directory:
   ```bash
   cd backend
   ```
2. (Optional but recommended) Create and activate a virtual environment.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run migrations:
   ```bash
   python manage.py migrate
   ```
5. Start the Django server:
   ```bash
   python manage.py runserver
   ```

The API endpoint is available at:

- `http://127.0.0.1:8000/api/itineraries/`

## Frontend Setup (React + Vite + Tailwind)

1. Open a new terminal and go to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the React development server:
   ```bash
   npm run dev
   ```

By default, Vite runs on `http://127.0.0.1:5173` and proxies `/api` requests to the Django backend.
