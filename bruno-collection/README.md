# VERIF-AI API Testing with Bruno

## 🔴 CRITICAL: Fixing the "422 Unprocessable Content" Error
The 422 error happens because of a specific setting in Bruno. 

### How to configure the "Body" tab correctly:
1.  Set body to **Multipart Form**.
2.  **Field 1 (type):**
    *   Key: `type`
    *   Value: `resume` (Type this manually)
    *   **Type:** Ensure the dropdown on the far right of this row says **Text**.
3.  **Field 2 (file):**
    *   Key: `file`
    *   Value: Click **Choose File** and pick `resume.pdf`.
    *   **Type:** Click the dropdown on the far right of this row and change it from "Text" to **File**.

**The error `Input should be a valid string` for the field `type` means you accidentally clicked "Choose File" on the `type` row instead of the `file` row.**

---

## Prerequisites
1. Install [Bruno](https://usebruno.com/)
2. Open Bruno and click **Open Collection**
3. Select the `bruno-collection/` folder in this repository.

## Step-by-Step Testing

### 1. Setup Environment
- Click the environment selector in the top right (default is "No Environment").
- Select **Create Environment** and name it `Local`.
- Add the following variables:
  - `baseUrl`: `http://localhost:8000`
  - `firebaseToken`: (Get this from the `/register` or `/login` response)

### 2. Authentication (Register/Login)
- Go to `auth/register.bru` or `auth/login.bru`.
- Run the request.
- Copy the `idToken` from the response (`data.idToken`).
- Update your `Local` environment's `firebaseToken` with this value.

### 3. Uploading Documents
- Go to `documents/upload-resume.bru`.
- Ensure the `file` field is set to **File** type and a file is selected.
- Ensure the `type` field is set to **Text** type with value `resume`.
- Click **Send**.

### 4. Submitting GitHub URL
- Go to `documents/submit-github.bru`.
- Ensure the `github_url` in the JSON body is correct.
- Click **Send**.

### 5. Verify Uploads
- Go to `documents/get-my-documents.bru`.
- Click **Send**.
- You should see a list of all your uploaded files and GitHub data.

## Common Issues
- **422 Unprocessable Entity:** Usually means the `file` or `type` field name is wrong in the body. Check that you used `type` and `file` as the keys.
- **401 Unauthorized:** Your `firebaseToken` has expired. Re-login and update the token.
- **403 Forbidden:** Ensure you have the `student` role.
