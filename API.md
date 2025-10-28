## 📚 API Documentation

**MED** provides a RESTful API built with Django REST Framework (DRF) for managing users' personal dictionaries. The API allows you to authenticate via tokens, create, view, update, and delete words belonging to authenticated users.

### 🔐 Authentication

All API requests must include an `Authorization` header with a valid Token:

```
Authorization: Token <your-api-token>
```

To obtain an API token:
1. Send a POST request to `/api/v1/token/` with your username and password.
2. Use the returned token in subsequent requests.

---

### 🧩 Endpoints

#### 1. Obtain API Token

- **URL**: `/api/v1/token/`
- **Method**: `POST`
- **Description**: Obtain an API token by providing username and password.
- **Request Body**:
  ```json
  {
    "username": "<username>",
    "password": "<password>"
  }
  ```
- **Response**:
  - **Success (200)**:
    ```json
    {
      "token": "<your-api-token>"
    }
    ```
  - **Error (400)**:
    ```json
    {
      "error": "Invalid credentials"
    }
    ```

#### 2. Check API Token

- **URL**: `/api/v1/token/`
- **Method**: `GET`
- **Description**: Checks if the provided token is valid.
- **Response**:
  - **Success (200)**:
    ```json
    {
      "status": "valid",
      "user": "<username>"
    }
    ```
  - **Error (401)**:
    ```json
    {
      "detail": "Authentication credentials were not provided."
    }
    ```

#### 3. Delete API Token (Logout)

- **URL**: `/api/v1/token/`
- **Method**: `DELETE`
- **Description**: Deletes the token that was used for authentication (logs out the user).
- **Response**:
  - **Success (204)**: Empty response.
  - **Error (400)**:
    ```json
    {
      "error": "No token found to delete."
    }
    ```

---

#### 4. List User Words

- **URL**: `/api/v1/words/`
- **Method**: `GET`
- **Description**: Retrieves a list of all words belonging to the authenticated user.
- **Response**:
  - **Success (200)**:
    ```json
    [
      {
        "id": 1,
        "word": "example",
        "translation": "приклад",
        "example": "This is an example sentence.",
        "word_type": "noun",
        "time_create": "2025-01-01T12:00:00Z",
        "time_update": "2025-01-01T12:00:00Z",
        "is_favourite": false
      }
    ]
    ```

#### 5. Add a New Word

- **URL**: `/api/v1/words/`
- **Method**: `POST`
- **Description**: Adds a new word for the authenticated user.
- **Request Body**:
  ```json
  {
    "word": "example",
    "translation": "приклад",
    "example": "This is an example sentence.",
    "word_type": "noun",
    "is_favourite": false
  }
  ```
- **Response**:
  - **Success (201)**:
    ```json
    {
      "id": 1,
      "word": "example",
      "translation": "приклад",
      "example": "This is an example sentence.",
      "word_type": "noun",
      "time_create": "2025-01-01T12:00:00Z",
      "time_update": "2025-01-01T12:00:00Z",
      "is_favourite": false
    }
    ```
  - **Error (400)**:
    ```json
    {
      "error": "<validation_error_message>"
    }
    ```

---

#### 6. Update a Word (Full Update)

- **URL**: `/api/v1/words/<id>/`
- **Method**: `PUT`
- **Description**: Fully updates a word by its ID.
- **Request Body**:
  ```json
  {
    "word": "updated",
    "translation": "оновлено",
    "example": "Updated example sentence.",
    "word_type": "verb",
    "is_favourite": true
  }
  ```
- **Response**:
  - **Success (200)**: Returns the updated word object.
  - **Error (400)**: Validation error message.

#### 7. Update a Word (Partial Update)

- **URL**: `/api/v1/words/<id>/`
- **Method**: `PATCH`
- **Description**: Partially updates a word (only specified fields).
- **Request Body** (example):
  ```json
  {
    "is_favourite": true
  }
  ```
- **Response**:
  - **Success (200)**: Updated word data.
  - **Error (404)**:
    ```json
    {
      "error": "Word not found or you do not have permission"
    }
    ```

#### 8. Delete a Word

- **URL**: `/api/v1/words/<id>/`
- **Method**: `DELETE`
- **Description**: Deletes a word belonging to the current user by ID.
- **Response**:
  - **Success (204)**: Empty response.
  - **Error (404)**:
    ```json
    {
      "error": "Word not found or you do not have permission"
    }
    ```

---

### 🧠 Example Usage

#### Obtain Token
```bash
curl -X POST -H "Content-Type: application/json" -d '{"username": "user", "password": "pass"}' http://localhost:8000/api/v1/token/
```

#### Check Token
```bash
curl -H "Authorization: Token <your-api-token>" http://localhost:8000/api/v1/token/
```

#### Add a Word
```bash
curl -X POST -H "Authorization: Token <your-api-token>" -H "Content-Type: application/json" -d '{"word": "sky", "translation": "небо"}' http://localhost:8000/api/v1/words/
```

#### Update a Word
```bash
curl -X PATCH -H "Authorization: Token <your-api-token>" -H "Content-Type: application/json" -d '{"is_favourite": true}' http://localhost:8000/api/v1/words/1/
```

#### Delete a Word
```bash
curl -X DELETE -H "Authorization: Token <your-api-token>" http://localhost:8000/api/v1/words/1/
```

---

## 🛠️ API Overview

- **Framework**: Django REST Framework (DRF)
- **Auth**: Token-based (DRF's `TokenAuthentication`)
- **Permissions**: Authenticated users only for all word operations
- **Models**: `Word` — stores user-specific vocabulary entries
- **Serializer**: `WordSerializer` — validates and serializes dictionary data
