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
  - Description: Register a new user in Firebase Auth and sync with local databases. Returns user data and valid tokens.
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
        "idToken": "string",
        "refreshToken": "string",
        "expiresIn": "string"
      }
    }
    ```

- **POST** `/api/v1/auth/login`
  - Description: Login user via Firebase and return profile + tokens.
  - Headers: None (Public)
  - Request Body:
    ```json
    {
      "email": "test@example.com",
      "password": "password123"
    }
    ```
  - Response:
    ```json
    {
      "success": true,
      "message": "Login successful",
      "data": {
        "user": { ...user_data... },
        "idToken": "string",
        "refreshToken": "string",
        "expiresIn": "string"
      }
    }
    ```

- **POST** `/api/v1/auth/refresh`
  - Description: Exchange a refresh token for a new ID token.
  - Headers: None (Public)
  - Request Body:
    ```json
    {
      "refresh_token": "string"
    }
    ```
  - Response:
    ```json
    {
      "success": true,
      "message": "Token refreshed successfully",
      "data": {
        "idToken": "string",
        "refreshToken": "string",
        "expiresIn": "string"
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

### Documents
- **POST** `/api/v1/documents/upload`
  - Description: Upload a resume or one/more certificate files (max 10MB each). Validates magic bytes (PDF, JPEG, PNG, DOCX, DOC). Stores in GridFS.
  - Headers: `Authorization: Bearer <firebase_id_token>` (Student only)
  - Request Body (Multipart/Form):
    - `type`: "resume" | "certificate"
    - `files`: List[UploadFile] (Use key 'files' or repeat key 'files' for multiple)
  - Response:
    ```json
    {
      "success": true,
      "message": "X file(s) processed successfully",
      "data": [
        {
          "document_id": "string",
          "type": "resume | certificate",
          "hash_sha256": "string",
          "status": "pending",
          "filename": "string"
        }
      ]
    }
    ```

- **GET** `/api/v1/documents/readiness`
  - Description: Checks if the student has met the 3/3 requirement (Resume, at least one Certificate, and GitHub URL) required to start analysis.
  - Headers: `Authorization: Bearer <firebase_id_token>` (Student only)
  - Response:
    ```json
    {
      "success": true,
      "message": "Readiness status retrieved",
      "data": {
        "has_resume": boolean,
        "has_certificate": boolean,
        "has_github": boolean,
        "is_ready": boolean,
        "missing": ["string"]
      }
    }
    ```

- **POST** `/api/v1/documents/github`
  - Description: Submit a GitHub profile URL for analysis.
  - Headers: `Authorization: Bearer <firebase_id_token>` (Student only)
  - Request Body:
    ```json
    {
      "github_url": "https://github.com/username"
    }
    ```
  - Response:
    ```json
    {
      "success": true,
      "message": "GitHub URL submitted successfully",
      "data": {
        "document_id": "string",
        "type": "github",
        "hash_sha256": "string",
        "status": "pending",
        "github_url": "string"
      }
    }
    ```

- **GET** `/api/v1/documents/my`
  - Description: List all uploaded documents and GitHub URL for the current student.
  - Headers: `Authorization: Bearer <firebase_id_token>` (Student only)
  - Response:
    ```json
    {
      "success": true,
      "message": "Documents retrieved successfully",
      "data": [
        {
          "document_id": "string",
          "type": "resume | certificate | github",
          "hash_sha256": "string",
          "status": "pending | analyzing | done | failed",
          "filename": "string (optional)",
          "github_url": "string (optional)"
        }
      ]
    }
    ```

---
