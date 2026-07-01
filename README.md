# IncidentOps

IncidentOps is a modern, real-time Incident Management platform built with a robust Django backend and a sleek, dynamic React frontend. It provides teams with a centralized dashboard for declaring, managing, and resolving incidents, featuring role-based access control, real-time WebSocket updates, background task processing, and Explainable AI (XAI) for automated post-mortem insights.

## System Architecture

The project is containerized using Docker and consists of 5 main services:
- **Django Backend:** Handles API requests, business logic, WebSocket connections, and database interactions.
- **React Frontend:** A modern single-page application built with Vite and Tailwind CSS.
- **PostgreSQL:** Primary relational database for storing users, incidents, timelines, and post-mortems.
- **Redis:** Used as a message broker for Celery and a backing store for Django Channels (WebSockets).
- **Celery Worker:** Processes asynchronous background tasks like alert escalations and heavy data processing.

## Key Features & Phases

### 1. Infrastructure & Containerization
- Fully containerized development environment via `docker-compose.yml`.
- Unified configuration via `.env` file.
- Django served with Daphne (ASGI) to handle both standard HTTP endpoints and WebSocket traffic.
- Vite development server configured to proxy `/api` and `/ws` to the Django backend.

### 2. Authentication & RBAC
- Built on top of `django-allauth` and `djangorestframework-simplejwt`.
- Custom user model supporting role-based access control (Admin, Responder, Viewer).
- JWT authentication for the API and OAuth2 Single Sign-On (SSO) support for Google and GitHub.

### 3. Core Incidents & Real-Time Collaboration
- Strict incident lifecycle management (`DECLARED` → `ACKNOWLEDGED` → `INVESTIGATING` → `MITIGATING` → `RESOLVED`).
- Real-time incident updates broadcasted to clients via WebSockets using Django Channels.
- Complete timeline tracking and commenting system.
- Background escalation checks managed by Celery and Celery Beat.

### 4. Modern Frontend Dashboard
- Built with React, Zustand, and Tailwind CSS.
- Kanban-style incident board with live WebSocket updates.
- Deep integration of glassmorphism UI elements, micro-animations, and a sleek dark theme.
- Responsive design tailored for efficient incident tracking and navigation.

### 5. Explainable AI (XAI) Post-Mortems
- Integrated anomaly detection engine analyzing metrics like response times and error rates (uses Isolation Forest).
- Automated log parsing to identify error patterns, frequency spikes, and highlight crucial log entries.
- Generates human-readable insight cards explaining incidents with confidence scores and actionable recommendations.

## Project Structure

```text
/
├── docker-compose.yml         # Container orchestration
├── FirstApp/                  # Django Backend Project
│   ├── manage.py
│   ├── myproject/             # Main Django config (settings, urls, asgi, wsgi, celery)
│   ├── apps/
│   │   ├── authentication/    # Auth, Custom User, RBAC, OAuth flows
│   │   └── incidents/         # Incident models, API, consumers, signals, XAI engine
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile             # Backend Docker build instructions
│   └── .env                   # Environment configuration
└── frontend/
    └── my-project/            # React Frontend Project
        ├── src/
        │   ├── api/           # Axios HTTP client and API endpoints
        │   ├── components/    # Reusable UI components (Sidebar, Modal, Badges)
        │   ├── context/       # Auth state management
        │   ├── hooks/         # Custom React hooks (useWebSocket, useIncidents)
        │   ├── routes/        # Page views (Dashboard, Incident Details, Post-Mortems)
        │   └── utils/         # Utility functions
        ├── package.json       # Node dependencies
        ├── vite.config.js     # Vite configuration and proxy setup
        └── Dockerfile         # Frontend Docker build instructions
```

## How to Run

1. **Clone the Repository** and navigate to the project root.
2. **Setup Environment Variables:**
   - Copy `FirstApp/.env.example` to `FirstApp/.env`.
   - Update any necessary secrets (e.g., OAuth client IDs if using SSO).
3. **Start the Services:**
   Run the following command from the root directory (where `docker-compose.yml` is located):
   ```bash
   docker compose up --build
   ```
4. **Access the Application:**
   - **Frontend UI:** [http://localhost:3000](http://localhost:3000)
   - **Backend API:** [http://localhost:8000/api](http://localhost:8000/api)
   - **Django Admin:** [http://localhost:8000/admin](http://localhost:8000/admin)

## How It Works

- **Starting an Incident:** Responders can declare a new incident from the React dashboard. This calls the Django API, creating an `Incident` record in PostgreSQL.
- **Real-Time Feed:** When an incident is created or updated, Django model signals trigger a broadcast message to the `incidents_feed` WebSocket group. The React frontend, listening via a custom `useWebSocket` hook, instantly updates the Kanban board without requiring a page refresh.
- **Incident Lifecycle:** As responders work on the incident, they advance its status through predefined states. Each transition is validated by the backend and logged as an `IncidentUpdate` for the timeline.
- **Background Checks:** Celery beat periodically checks for unresolved, unacknowledged high-severity incidents, triggering escalations via Celery worker tasks if SLA thresholds are breached.
- **Post-Mortem Generation:** Once an incident is resolved, a user can generate a post-mortem. The backend's XAI module reconstructs the timeline, simulates/gathers system metrics and logs around the incident timeframe, runs anomaly detection (Isolation Forest/Z-Score), and compiles the findings into explainable insight cards and action items, saving the final report in the database for review.
