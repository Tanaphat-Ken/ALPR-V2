# Authentication API Documentation

## Overview

Authentication system for ALPR V2 using JWT (JSON Web Tokens) with bcrypt password hashing.

## Endpoints

### 1. Register New User

**POST** `/api/v1/auth/register`

Create a new user account.

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "your-password"
}
```

**Response (201 Created):**

```json
{
  "user_id": 1,
  "email": "user@example.com",
  "message": "Registration successful"
}
```

**Errors:**

- `400 Bad Request`: Email already registered or invalid data
- `500 Internal Server Error`: Database error

---

### 2. Login

**POST** `/api/v1/auth/login`

Authenticate user and receive JWT access token.

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "your-password"
}
```

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": 1,
  "email": "user@example.com",
  "message": "Login successful"
}
```

**Errors:**

- `401 Unauthorized`: Incorrect email or password
- `403 Forbidden`: User account is deactivated

---

### 3. Get Current User Info

**GET** `/api/v1/auth/me`

Get information about the currently authenticated user.

**Headers:**

```
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "user_id": 1,
  "email": "user@example.com",
  "created_at": "2025-01-15T10:30:00",
  "updated_at": "2025-01-15T10:30:00"
}
```

**Errors:**

- `401 Unauthorized`: Invalid or expired token
- `403 Forbidden`: User account is deactivated
- `404 Not Found`: User not found

---

### 4. Logout

**POST** `/api/v1/auth/logout`

Logout current user (client-side token removal).

**Headers:**

```
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "message": "Logout successful",
  "user_id": 1
}
```

---

## Authentication Flow

### Registration Flow

1. User submits email and password
2. API validates email format and password length (min 6 chars)
3. API checks if email is already registered
4. Password is hashed using bcrypt
5. New user record created in database
6. API returns user info

### Login Flow

1. User submits email and password
2. API looks up user by email
3. API verifies password against hashed password
4. API checks if user is active
5. JWT token generated with user_id and email
6. Token expires in 7 days
7. API returns token and user info

### Protected Route Access

1. Client includes JWT token in Authorization header
2. API validates token signature and expiration
3. API extracts user_id from token
4. API verifies user still exists and is active
5. Request proceeds if validation passes

---

## Security Features

- **Password Hashing**: Bcrypt with automatic salt generation
- **JWT Tokens**: Signed with HS256 algorithm
- **Token Expiration**: 7 days default (configurable)
- **Email Validation**: Pydantic EmailStr validation
- **Password Requirements**: Minimum 6 characters
- **Active User Check**: Ensures user account is activated
- **CORS Protection**: Configured for localhost:3000

---

## Environment Variables

Add to `.env` file:

```env
SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
```

**Important:** Change the SECRET_KEY in production!

---

## Usage Examples

### Using curl

**Register:**

```bash
curl -X POST "http://localhost:8092/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"mypassword"}'
```

**Login:**

```bash
curl -X POST "http://localhost:8092/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"mypassword"}'
```

**Get User Info:**

```bash
curl -X GET "http://localhost:8092/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Using JavaScript (Fetch API)

**Register:**

```javascript
const response = await fetch("http://localhost:8092/api/v1/auth/register", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "test@example.com",
    password: "mypassword",
  }),
});
const data = await response.json();
```

**Login:**

```javascript
const response = await fetch("http://localhost:8092/api/v1/auth/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "test@example.com",
    password: "mypassword",
  }),
});
const { access_token } = await response.json();
localStorage.setItem("token", access_token);
```

**Protected Request:**

```javascript
const token = localStorage.getItem("token");
const response = await fetch("http://localhost:8092/api/v1/auth/me", {
  headers: { Authorization: `Bearer ${token}` },
});
const user = await response.json();
```

---

## Database Schema

**users table:**

```sql
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,  -- bcrypt hashed
    is_activate BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

## Testing

Start the API server:

```bash
cd alpr_general_api
python main.py
```

Visit Swagger UI documentation:

```
http://localhost:8092/docs
```

Test the endpoints interactively in the Swagger interface.

---

## Next Steps for Frontend Integration

1. Update `apiClient.ts` base URL if needed
2. Uncomment the API calls in `login.tsx` and `register.tsx`
3. Import and use the auth functions from `libs/auth.ts`
4. Store the JWT token in localStorage after login
5. Include token in Authorization header for protected requests
6. Clear token on logout

Example integration:

```typescript
// In login.tsx
import { login } from "@/libs/auth";

const response = await login({ email, password });
localStorage.setItem("token", response.access_token);
localStorage.setItem("userId", response.user_id.toString());
```
