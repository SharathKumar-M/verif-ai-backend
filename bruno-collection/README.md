# VERIF-AI Auth Testing Guide (Bruno)

Follow these steps to verify the full authentication and role-based access control (RBAC) flow.

## Step 0: Configure Bruno Environment
1. Open Bruno.
2. Go to **Environments** (top right).
3. Select or create an environment (e.g., `Local`).
4. Add these variables:
   - `baseUrl`: `http://localhost:8000`
   - `firebaseApiKey`: `[PASTE_YOUR_WEB_API_KEY]` 
     *(Find this in Firebase Console > Project Settings > General > Web API Key)*
   - `firebaseToken`: (Leave empty)
   - `testUid`: (Leave empty)

## Step 1: Register or Login
Open the **Firebase-Auth** or **auth** folder.

1.  **Backend Register** (`POST /api/v1/auth/register`):
    - **Recommended for testing**.
    - Registers you in Firebase AND Syncs with MongoDB/Firestore in one click.
    - Sets your `role` in Firebase Custom Claims.
    - **Note**: Choose `student` or `recruiter` in the request body.

## Step 2: Role-Based Access Control (RBAC) Testing

### Testing "Recruiters Only" Restriction
1.  **Register as a Student**: Use `Backend Register` with `"role": "student"`.
2.  **Try Update Role**: Run `Update Role` in the `auth` folder.
    - **Expected Result**: `403 Forbidden` (Only recruiters can update roles).
3.  **Register as a Recruiter**: Use `Backend Register` with `"role": "recruiter"`.
4.  **Try Update Role**: Run `Update Role`.
    - **Expected Result**: `200 OK`.

### ⚠️ IMPORTANT: Token Refresh
Firebase Custom Claims (roles) are baked into the ID Token (JWT). If a role is updated:
1. The *old* token still has the *old* role.
2. The user must **Login again** in Bruno to get a fresh `firebaseToken` with the new role.
3. Our `Backend Register` endpoint sets the claim *before* returning the token, so it works immediately.

## Step 3: Verify & Update
1.  **Get Me**: Verifies the backend can read your profile using the token.
2.  **Auth Health**: Check if MongoDB and Firebase are connected.

## Troubleshooting
- **401 Unauthorized**: Token expired. Run **Login** or **Backend Register** again.
- **403 Forbidden**: Either your UID doesn't match the body, or you are a `student` trying to access a `recruiter` endpoint.
- **500 Internal Server Error**: Check the backend logs. (Commonly caused by invalid `FIREBASE_API_KEY` or `FIREBASE_CREDENTIALS_JSON`).
