# VERIF-AI API Contract
> Auto-updated by agent after every endpoint change.
> Backend: tejasM17/verif-ai-backend
> Frontend: SharathKumar-M/verif-ai-frontend

## Base URLs
- Local: http://localhost:8000
- Production: https://verif-ai-backend.onrender.com

## Endpoints

### System
- **GET** `/health`
  - Description: Check API health and connectivity to external services.
  - Response:
    ```json
    {
      "status": "healthy",
      "mongodb": "connected",
      "firebase": "connected"
    }
    ```

- **GET** `/`
  - Description: Welcome message and link to Swagger UI.
  - Response:
    ```json
    {
      "message": "VERIF-AI API",
      "docs": "/docs",
      "version": "1.0.0"
    }
    ```

### Auth
- **POST** `/api/v1/auth/register`
  - Description: Register a new user in Firebase Auth and sync with local databases. Returns user data and a valid `idToken`.
  - Headers: None (Public)
  - Request Body:
    ```json
    {
      "email": "test@example.com",
      "password": "password123",
      "role": "student | recruiter",
      "display_name": "string (optional)"
    }
    ```
  - Response:
    ```json
    {
      "success": true,
      "message": "User registered and synced successfully",
      "data": {
        "user": {
          "id": "mongo_id",
          "firebase_uid": "string",
          "email": "string",
          "role": "string",
          "display_name": "string",
          "created_at": "ISO-8601"
        },
        "idToken": "valid_firebase_jwt"
      }
    }
    ```

- **POST** `/api/v1/auth/sync`
  - Description: Upsert user in MongoDB and Firestore after Firebase registration/login.
  - Headers: `Authorization: Bearer <firebase_id_token>`
  - Request Body:
    ```json
    {
      "firebase_uid": "string",
      "email": "string",
      "role": "student | recruiter",
      "display_name": "string (optional)"
    }
    ```
  - Response:
    ```json
    {
      "success": true,
      "message": "User created/updated successfully",
      "data": { ...user_data... }
    }
    ```

- **GET** `/api/v1/auth/me`
  - Description: Get current user profile from system.
  - Headers: `Authorization: Bearer <firebase_id_token>`
  - Response:
    ```json
    {
      "success": true,
      "data": { ...user_data... }
    }
    ```

- **PUT** `/api/v1/auth/role`
  - Description: Update user role in the system.
  - Headers: `Authorization: Bearer <firebase_id_token>`
  - Request Body:
    ```json
    { "role": "student | recruiter" }
    ```
  - Response:
    ```json
    {
      "success": true,
      "message": "Role updated successfully",
      "data": { ...user_data... }
    }
    ```

- **GET** `/api/v1/auth/health`
  - Description: Internal auth service health check.
  - Response:
    ```json
    {
      "success": true,
      "data": { "firebase": "ok", "mongodb": "ok" }
    }
    ```

---
