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

### Analysis
- **POST** `/api/v1/analysis/start`
  - Description: Start the multi-agent verification process. Returns a job ID and WebSocket URL.
  - Headers: `Authorization: Bearer <firebase_id_token>` (Student only)
  - Request Body:
    ```json
    {
      "student_uid": "string",
      "resume_document_id": "string",
      "cert_doc_ids": ["string"],
      "github_url": "string"
    }
    ```
  - Response (202 Accepted):
    ```json
    {
      "job_id": "string",
      "websocket_url": "string"
    }
    ```

- **WebSocket** `/api/v1/analysis/stream/{job_id}`
  - Description: Stream real-time research logs and progress tokens.
  - Query Params: `?token=<firebase_id_token>`
  - Message Format (JSON):
    ```json
    {
      "type": "thinking_token | research_step_start | research_step_complete | analysis_complete | error",
      "data": { ...event_data... }
    }
    ```

- **GET** `/api/v1/analysis/result/{student_uid}`
  - Description: Fetch the latest verification result for a student.
  - Headers: `Authorization: Bearer <firebase_id_token>` (Student or Recruiter)
  - Response:
    ```json
    {
      "success": true,
      "data": {
        "verification": {
          "student_uid": "string",
          "trust_score": float,
          "verdict": "AUTHENTIC | FLAGGED | SUSPICIOUS | FAKE",
          "resume_score": float,
          "cert_score": float,
          "github_score": float,
          "flags": [],
          "created_at": "ISO-8601"
        },
        "agent_results": [ ...list of 3 agent results... ]
      }
    }
    ```

---

### Profile
- **GET** `/api/v1/profile/me`
  - Description: Get the current user's profile. Creates a default profile if it doesn't exist.
  - Headers: `Authorization: Bearer <firebase_id_token>`
  - Response:
    ```json
    {
      "display_name": "string",
      "bio": "string",
      "skills": ["string"],
      "domain": "string",
      "location": "string",
      "is_public": boolean,
      "firebase_uid": "string",
      "trust_score": float,
      "verdict": "string",
      "verified_at": "ISO-8601",
      "created_at": "ISO-8601",
      "updated_at": "ISO-8601"
    }
    ```

- **PATCH** `/api/v1/profile/me`
  - Description: Update the current user's profile.
  - Headers: `Authorization: Bearer <firebase_id_token>`
  - Request Body:
    ```json
    {
      "display_name": "string",
      "bio": "string",
      "skills": ["string"],
      "domain": "string",
      "location": "string",
      "is_public": boolean
    }
    ```
  - Response: Updated Profile object.

- **GET** `/api/v1/profile/{uid}`
  - Description: Get a specific user's profile. Access restricted if profile is not public.
  - Headers: `Authorization: Bearer <firebase_id_token>`
  - Response: Profile object.

### Discovery
- **POST** `/api/v1/discover/search`
  - Description: Recruiters search for verified students using various filters.
  - Headers: `Authorization: Bearer <firebase_id_token>` (Recruiter only)
  - Request Body:
    ```json
    {
      "skills": ["string"],
      "min_trust_score": float,
      "domain": "string",
      "location": "string",
      "limit": int,
      "offset": int
    }
    ```
  - Response:
    ```json
    {
      "total": int,
      "results": [ ...ProfileResponse objects... ]
    }
    ```

- **POST** `/api/v1/discover/shortlist`
  - Description: Add a student to the recruiter's shortlist.
  - Headers: `Authorization: Bearer <firebase_id_token>` (Recruiter only)
  - Request Body:
    ```json
    {
      "student_uid": "string"
    }
    ```
  - Response:
    ```json
    {
      "success": true,
      "message": "Student shortlisted successfully"
    }
    ```

- **GET** `/api/v1/discover/shortlist`
  - Description: Get all shortlisted students for the recruiter.
  - Headers: `Authorization: Bearer <firebase_id_token>` (Recruiter only)
  - Response: List of Profile objects.

### Verification
- **GET** `/api/v1/verification/{verification_id}`
  - Description: Get full details of a specific verification run, including agent results and research logs.
  - Headers: `Authorization: Bearer <firebase_id_token>`
  - Response:
    ```json
    {
      "success": true,
      "data": {
        "verification": { ... },
        "agent_results": [ ... ],
        "research_logs": [ ... ]
      }
    }
    ```

---
**contracts/CONTRACT.md last updated:** Friday, 5 June 2026 (Phase 4 Discovery implemented)
