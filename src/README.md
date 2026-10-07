# Mergington High School Activities API

A simple FastAPI application for viewing extracurricular activities. Teacher sign-in is required to register or unregister students.

## Features

- View all available extracurricular activities
- Teacher login and logout
- Teacher-only student registration and unregistration

## Getting Started

1. Install the dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Configure the teacher login and session signing secret in the environment. Do not commit these values to the repository:

   ```
   export TEACHER_USERNAME="teacher"
   export TEACHER_PASSWORD="<a strong, unique password>"
   export SESSION_SECRET="<a long, random secret>"
   ```

   `SESSION_SECRET` should be a cryptographically random value. The teacher session expires after eight hours.

3. Run the application:

   ```
   uvicorn app:app --app-dir src --reload
   ```

4. Open your browser and go to:
   - Activities page: http://localhost:8000/
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description |
| ------ | ----------------------------------------------------------------- | ----------- |
| GET    | `/activities`                                                     | Get all activities and current participants |
| GET    | `/auth/status`                                                    | Check whether the current browser has a teacher session |
| POST   | `/auth/login`                                                     | Sign in with the configured teacher username and password |
| POST   | `/auth/logout`                                                    | End the current teacher session |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Teacher-only student registration |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Teacher-only student unregistration |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All activity data is stored in memory, which means it resets when the server restarts. Teacher credentials are supplied through environment variables rather than stored in a checked-in file. The signed session cookie is HTTP-only and uses strict same-site settings; deploy over HTTPS.
