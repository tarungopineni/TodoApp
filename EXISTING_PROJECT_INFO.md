# Existing Project Information

## 1. PROJECT OVERVIEW
- **Application Summary**: A FastAPI-based RESTful backend API and server-side Jinja2 template Web application for user and task (todo) management.
- **Main Purpose**: Allows users to register accounts, authenticate via JWT, and perform CRUD operations on their personal todo tasks. Includes role-based access control allowing administrator accounts to view and delete all tasks in the system.
- **Technologies / Frameworks Used**:
  - **Backend Framework**: FastAPI (v0.x built on Starlette and Pydantic)
  - **ORM & Database Tooling**: SQLAlchemy, Alembic (for database schema migrations)
  - **Database Systems**: PostgreSQL (primary production database connection defined), SQLite (used for local testing and present as local file DB)
  - **Authentication & Security**: Passlib (Bcrypt password hashing), PyJWT / python-jose (JWT token generation & decoding)
  - **Templating & Static Files**: Jinja2 (HTML templating), Starlette StaticFiles
  - **Testing**: Pytest, FastAPI `TestClient` (built on `httpx`)
  - **Frontend UI Libraries**: Bootstrap CSS & JS, jQuery (slim), Popper.js
- **Programming Languages**: Python 3, HTML5, JavaScript (ES6+), CSS3
- **Overall Architecture**: Monolithic FastAPI application structured using `APIRouter` modules (`auth`, `todos`, `admin`, `users`). Serves both JSON REST API endpoints and rendered Jinja2 HTML templates with static CSS/JS assets.

---

## 2. PROJECT STRUCTURE
### Important Folders
- **`routers/`**: Contains APIRouter endpoint definitions split by domain:
  - `admin.py`: Router for administrative tasks management.
  - `auth.py`: Router for authentication, user creation, and JWT token issuance.
  - `todos.py`: Router for user todo CRUD operations.
  - `users.py`: Router for user profile management.
- **`templates/`**: Contains Jinja2 HTML layout and page templates:
  - `layout.html`: Base template layout with CSS imports.
  - `home.html`: Homepage view template.
  - `login.html`: User login form template.
  - `register.html`: User registration form template.
- **`static/`**: Contains static assets served at `/static`:
  - `css/`: `base.css`, `bootstrap.css`
  - `js/`: `base.js` (client-side form event handlers and fetch calls), `bootstrap.js`, `jquery-slim.js`, `popper.js`
- **`test/`**: Pytest test suite directory containing unit and integration tests:
  - `utils.py`: Shared test configuration, SQLite test database engine, fixtures, dependency overrides, and `TestClient` setup.
  - `test_admin.py`: Test cases for `/admin` routes.
  - `test_auth.py`: Test cases for authentication and JWT functions.
  - `test_todos.py`: Test cases for `/todos` routes.
  - `test_users.py`: Test cases for `/user` profile routes.
  - `test_main.py`: Test case for application health check endpoint.
  - `test_example.py`: Sample unit tests and fixture demonstration.
  - `temp.py`: Scratch script initializing test SQLite engine.
- **`alembic/`**: Alembic migration directory containing environment configurations and migration scripts (`versions/60fc2a245572_create_phonenumber_column_for_users_.py`).

### Important Files
- `main.py`: Application entry point. Instantiates `FastAPI()`, builds database tables via `Base.metadata.create_all`, mounts `/static`, mounts Jinja2 templates, defines root routes (`/login-page`, `/register-page`, `/healthy`), and includes all routers.
- `database.py`: Establishes SQLAlchemy `engine`, `SessionLocal` maker, and `Base` declarative class.
- `models.py`: Defines SQLAlchemy ORM database models: `Users` and `Todos`.
- `alembic.ini`: Configuration file for Alembic database migrations.
- `todosapp.db`: Local SQLite database file present in the project root.

### Component Connections
- `main.py` imports `engine` from `database.py` and `Base` from `models.py` to auto-create database tables on startup.
- `main.py` includes routers from `routers/` (`auth.py`, `todos.py`, `admin.py`, `users.py`).
- Routers import `SessionLocal` from `database.py` to provide a database session dependency (`get_db`).
- Routers import database models `Users` and `Todos` from `models.py`.
- Routers use `get_current_user` from `routers/auth.py` as a FastAPI dependency (`Depends`) to authenticate incoming requests via JWT tokens.
- Frontend HTML templates in `templates/` and JavaScript in `static/js/base.js` interact with backend endpoints (`/auth/token`, `/todos/todo`, etc.).

---

## 3. BACKEND
- **Framework**: FastAPI (Python)
- **Server Setup**: Standard ASGI application initialized as `app = FastAPI()` in `main.py`. (Executable via ASGI servers such as Uvicorn).
- **Main Application Entry Point**: `main.py`
- **Routes**:
  - `main.py`: GET `/login-page`, GET `/register-page`, GET `/healthy`, Static mount `/static`.
  - `routers/auth.py`: GET `/auth/login-page`, GET `/auth/register-page`, POST `/auth/create`, POST `/auth/token`.
  - `routers/todos.py`: GET `/todos/`, GET `/todos/todo/{todo_id}`, POST `/todos/todos`, PUT `/todos/todo/{todo_id}`, DELETE `/todos/todo/{todo_id}`.
  - `routers/admin.py`: GET `/admin/todo`, DELETE `/admin/todo/{todo_id}`.
  - `routers/users.py`: GET `/user/`, PUT `/user/password`, PUT `/user/add_phone/{phone}`.
- **Controllers / Services**: Business logic is written directly inside route handler functions in `routers/`. Key authentication helpers (`authenticate`, `create_access_token`, `get_current_user`) exist in `routers/auth.py`.
- **Middleware**: Built-in FastAPI dependency injection (`Depends`) used for DB session management (`get_db`) and authentication (`get_current_user`). No custom FastAPI middleware components registered.
- **Dependencies**:
  - `fastapi`
  - `sqlalchemy`
  - `pydantic`
  - `passlib` (with `bcrypt`)
  - `python-jose` / `jose` (with `jwt`)
  - `starlette`
  - `jinja2`
  - `pytest`
  - `alembic`

---

## 4. AUTHENTICATION
- **Registration**:
  - Handled via endpoint `POST /auth/create`.
  - Accepts JSON payload (`User_Request` model): `email`, `username`, `first_name`, `last_name`, `role`, `hashed_password` (raw password passed in request, hashed prior to DB persistence).
  - Hashes password using Bcrypt and stores a new `Users` record in the database.
- **Login**:
  - Handled via endpoint `POST /auth/token`.
  - Accepts form data adhering to `OAuth2PasswordRequestForm` (`username` and `password`).
  - Calls `authenticate()` helper function to verify user existence and validate password using `bcrypt_context.verify()`.
  - Returns a JSON token response (`{"access_token": "<token>", "token_type": "bearer"}`) on success. Raises `HTTPException(401, detail="Could not validate")` on failure.
- **Password Handling**:
  - Hashes passwords using `passlib.context.CryptContext(schemes=['bcrypt'], deprecated='auto')`.
  - Password update functionality implemented via `PUT /user/password`, requiring verification of the existing password before updating.
- **JWT / Token System**:
  - Token Algorithm: `HS256`.
  - Token Claims: `sub` (username), `id` (user ID), `role` (user role), `exp` (expiration timestamp).
  - Secret Key: Configured as a string constant (`SECRET_KEY`) inside `routers/auth.py`.
- **Token Expiration**:
  - Tokens expire after 20 minutes (`timedelta(minutes=20)`).
- **Protected Routes**:
  - Protected endpoints accept `user_dependency = Annotated[dict, Depends(get_current_user)]`.
  - `get_current_user` extracts Bearer token using `OAuth2PasswordBearer(tokenUrl='auth/token')`, decodes JWT, validates presence of `username` and `id`, and returns a dictionary: `{"username": username, "id": user_id, "user_role": user_role}`.
- **User Identification**:
  - Users are identified by their database `id` (integer) extracted from JWT claims.
- **Authorization**:
  - **Admin Role Authorization**: Admin endpoints (`GET /admin/todo`, `DELETE /admin/todo/{todo_id}`) verify that `user_role == "admin"`. Otherwise, an HTTP 401 exception is raised.
  - **User Data Isolation**: Todo endpoints (`GET /todos/`, `GET /todos/todo/{todo_id}`, `PUT /todos/todo/{todo_id}`, `DELETE /todos/todo/{todo_id}`) explicitly filter database queries by `Todos.owner_id == user.get("id")`.
- **Logout**:
  - Backend does not maintain server-side token revocation or session blacklist.
  - Client-side helper function `logout()` in `static/js/base.js` clears browser cookies and redirects to `/auth/login-page`.

---

## 5. TODO / TASK FEATURES
- **Create Task**: Implemented (`POST /todos/todos`). Assigns `owner_id` from authenticated user ID.
- **Read / List Tasks**: Implemented (`GET /todos/`). Lists tasks belonging exclusively to authenticated user.
- **Read Single Task**: Implemented (`GET /todos/todo/{todo_id}`). Fetches single task owned by authenticated user.
- **Update Task**: Implemented (`PUT /todos/todo/{todo_id}`). Updates `title`, `description`, `priority`, and `complete` fields for user's task.
- **Delete Task**: Implemented (`DELETE /todos/todo/{todo_id}`). Deletes task owned by authenticated user.
- **Admin Read All Tasks**: Implemented (`GET /admin/todo`). Returns all tasks across all users for admin accounts.
- **Admin Delete Task**: Implemented (`DELETE /admin/todo/{todo_id}`). Deletes any task by ID for admin accounts.
- **Implemented Task Fields**:
  - `id`: Integer (Primary Key, Indexed)
  - `title`: String (Validated: minimum length 3)
  - `description`: String (Validated: minimum length 3, maximum length 20)
  - `priority`: Integer (Validated: greater than 0)
  - `complete`: Boolean (Default: `False`)
  - `owner_id`: Integer (Foreign Key to `users.id`)
- **Unimplemented Task Fields & Features**:
  - Date / Time fields (created_at, updated_at): **Not implemented**
  - Deadline / Due Date: **Not implemented**
  - Categories / Tags: **Not implemented**
  - Task Search / Filtering / Sorting / Pagination: **Not implemented**

---

## 6. API ENDPOINTS

### 1. Health Check
- **HTTP Method**: `GET`
- **URL/Path**: `/healthy`
- **Purpose**: System health status check.
- **Authentication Required**: No
- **Request Body**: None
- **Parameters**: None
- **Response**: `{"status": "healthy"}` (Status 200)

### 2. Login Page (Root)
- **HTTP Method**: `GET`
- **URL/Path**: `/login-page`
- **Purpose**: Renders Jinja2 template `home.html`.
- **Authentication Required**: No
- **Request Body**: None
- **Parameters**: None
- **Response**: HTML Page (Status 200)

### 3. Register Page (Root)
- **HTTP Method**: `GET`
- **URL/Path**: `/register-page`
- **Purpose**: Renders Jinja2 template `register.html`.
- **Authentication Required**: No
- **Request Body**: None
- **Parameters**: None
- **Response**: HTML Page (Status 200)

### 4. Auth Login Page
- **HTTP Method**: `GET`
- **URL/Path**: `/auth/login-page`
- **Purpose**: Renders Jinja2 template `login.html`.
- **Authentication Required**: No
- **Request Body**: None
- **Parameters**: None
- **Response**: HTML Page (Status 200)

### 5. Auth Register Page
- **HTTP Method**: `GET`
- **URL/Path**: `/auth/register-page`
- **Purpose**: Renders Jinja2 template `register.html`.
- **Authentication Required**: No
- **Request Body**: None
- **Parameters**: None
- **Response**: HTML Page (Status 200)

### 6. Create User
- **HTTP Method**: `POST`
- **URL/Path**: `/auth/create`
- **Purpose**: Registers a new user account.
- **Authentication Required**: No
- **Request Body** (`User_Request` JSON):
  - `email`: string
  - `username`: string
  - `first_name`: string
  - `last_name`: string
  - `role`: string
  - `hashed_password`: string (raw password string)
- **Parameters**: None
- **Response**: `{"message": "User inserted!!"}` (Status 200)
- **Validation/Errors**: Pydantic model validation; hashes password with bcrypt.

### 7. Authenticate & Obtain Token
- **HTTP Method**: `POST`
- **URL/Path**: `/auth/token`
- **Purpose**: Authenticates credentials and returns JWT bearer token.
- **Authentication Required**: No
- **Request Body** (`OAuth2PasswordRequestForm` Form Data):
  - `username`: string
  - `password`: string
- **Parameters**: None
- **Response**: `{"access_token": "<token>", "token_type": "bearer"}` (Status 200)
- **Validation/Errors**: HTTP 401 `{"detail": "Could not validate"}` if authentication fails.

### 8. Read User Todos
- **HTTP Method**: `GET`
- **URL/Path**: `/todos/`
- **Purpose**: Fetches all todo items owned by authenticated user.
- **Authentication Required**: Yes (Bearer Token)
- **Request Body**: None
- **Parameters**: None
- **Response**: Array of Todo objects `[{"id": 1, "title": "...", "description": "...", "priority": 5, "complete": false, "owner_id": 1}]` (Status 200)
- **Validation/Errors**: HTTP 401 `{"detail": "Authentication failed!!"}` if token is invalid or user missing.

### 9. Read Single Todo
- **HTTP Method**: `GET`
- **URL/Path**: `/todos/todo/{todo_id}`
- **Purpose**: Fetches a single todo item by ID owned by authenticated user.
- **Authentication Required**: Yes (Bearer Token)
- **Request Body**: None
- **Parameters**: Path parameter `todo_id` (Integer, must be `gt=0`)
- **Response**: Single Todo object (Status 200)
- **Validation/Errors**: HTTP 401 if unauthenticated; HTTP 404 `{"detail": "Todo with that id is not found"}` if todo doesn't exist or is not owned by user.

### 10. Create Todo
- **HTTP Method**: `POST`
- **URL/Path**: `/todos/todos`
- **Purpose**: Creates a new todo item for authenticated user.
- **Authentication Required**: Yes (Bearer Token)
- **Request Body** (`TodoRequest` JSON):
  - `title`: string (min_length=3)
  - `description`: string (min_length=3, max_length=20)
  - `priority`: integer (gt=0)
  - `complete`: boolean
- **Parameters**: None
- **Response**: `{"message": "todo created"}` (Status 201 Created)
- **Validation/Errors**: HTTP 401 if unauthenticated; HTTP 422 if body fails validation.

### 11. Update Todo
- **HTTP Method**: `PUT`
- **URL/Path**: `/todos/todo/{todo_id}`
- **Purpose**: Updates an existing todo item owned by authenticated user.
- **Authentication Required**: Yes (Bearer Token)
- **Request Body** (`TodoRequest` JSON):
  - `title`: string (min_length=3)
  - `description`: string (min_length=3, max_length=20)
  - `priority`: integer (gt=0)
  - `complete`: boolean
- **Parameters**: Path parameter `todo_id` (Integer)
- **Response**: `{"message": "updated"}` (Status 204 No Content declared in decorator)
- **Validation/Errors**: HTTP 401 if unauthenticated; HTTP 404 `{"detail": "todo not found"}` if todo doesn't exist or user is not owner.

### 12. Delete Todo
- **HTTP Method**: `DELETE`
- **URL/Path**: `/todos/todo/{todo_id}`
- **Purpose**: Deletes a todo item owned by authenticated user.
- **Authentication Required**: Yes (Bearer Token)
- **Request Body**: None
- **Parameters**: Path parameter `todo_id` (Integer)
- **Response**: Status 204 No Content
- **Validation/Errors**: HTTP 401 if unauthenticated; HTTP 404 `{"detail": "model not found!!"}` if todo doesn't exist or user is not owner.

### 13. Admin Read All Todos
- **HTTP Method**: `GET`
- **URL/Path**: `/admin/todo`
- **Purpose**: Fetches all todo items across all users in the system (Admin only).
- **Authentication Required**: Yes (Bearer Token with `user_role == "admin"`)
- **Request Body**: None
- **Parameters**: None
- **Response**: Array of all Todo objects (Status 200)
- **Validation/Errors**: HTTP 401 `{"detail": "Authentication failed"}` if unauthenticated or user role is not `admin`.

### 14. Admin Delete Todo
- **HTTP Method**: `DELETE`
- **URL/Path**: `/admin/todo/{todo_id}`
- **Purpose**: Deletes any todo item by ID (Admin only).
- **Authentication Required**: Yes (Bearer Token with `user_role == "admin"`)
- **Request Body**: None
- **Parameters**: Path parameter `todo_id` (Integer, must be `gt=0`)
- **Response**: Status 204 No Content
- **Validation/Errors**: HTTP 401 `{"detail": "Authentication failed"}` if not admin; HTTP 404 `{"detail": "could not found todo"}` if task not found.

### 15. Get User Information
- **HTTP Method**: `GET`
- **URL/Path**: `/user/`
- **Purpose**: Fetches profile information for the authenticated user.
- **Authentication Required**: Yes (Bearer Token)
- **Request Body**: None
- **Parameters**: None
- **Response**: User object details (Status 200)
- **Validation/Errors**: HTTP 401 `{"detail": "Authentication failed!!"}` if unauthenticated.

### 16. Change User Password
- **HTTP Method**: `PUT`
- **URL/Path**: `/user/password`
- **Purpose**: Changes password for the authenticated user.
- **Authentication Required**: Yes (Bearer Token)
- **Request Body** (`UserVerification` JSON):
  - `password`: string (current password)
  - `new_password`: string
- **Parameters**: None
- **Response**: `{"message": "Password changed successfully!!"}` (Status 204 No Content)
- **Validation/Errors**: HTTP 401 `{"detail": "Old password does not match!!"}` if current password verification fails or if unauthenticated.

### 17. Add / Update User Phone Number
- **HTTP Method**: `PUT`
- **URL/Path**: `/user/add_phone/{phone}`
- **Purpose**: Updates phone number for the authenticated user.
- **Authentication Required**: Yes (Bearer Token)
- **Request Body**: None
- **Parameters**: Path parameter `phone` (string)
- **Response**: Status 204 No Content
- **Validation/Errors**: HTTP 401 `{"detail": "Authentication failed!!"}` if unauthenticated.

---

## 7. DATABASE
- **Database Technology**:
  - Primary Database Connection configured in `database.py`: PostgreSQL via SQLAlchemy connection URL (`postgresql://postgres:******@localhost/TodoApplicationDatabase`).
  - Secondary / Test Database: SQLite (`sqlite:///./testdb.db` used in Pytest test suite, `todosapp.db` file present in root).
- **Migrations**: Managed via Alembic (`alembic/`). Migration file `60fc2a245572_create_phonenumber_column_for_users_.py` adds column `phonenumber` to table `users`.
- **Database Schema & Models (`models.py`)**:

### `users` Table (`Users` Model)
| Field Name | Type | Constraints / Attributes |
|---|---|---|
| `id` | Integer | Primary Key, Indexed (`index=True`) |
| `email` | String | Unique (`unique=True`) |
| `username` | String | Unique (`unique=True`) |
| `first_name` | String | Nullable |
| `last_name` | String | Nullable |
| `hashed_password` | String | Nullable |
| `is_active` | Boolean | Default `True` |
| `role` | String | Nullable |
| `phonenumber` | String | Nullable |

### `todos` Table (`Todos` Model)
| Field Name | Type | Constraints / Attributes |
|---|---|---|
| `id` | Integer | Primary Key, Indexed (`index=True`) |
| `title` | String | Nullable |
| `description` | String | Nullable |
| `priority` | Integer | Nullable |
| `complete` | Boolean | Default `False` |
| `owner_id` | Integer | Foreign Key (`ForeignKey("users.id")`) |

- **Relationships**:
  - Foreign Key constraint `todos.owner_id` references `users.id`.
  - No SQLAlchemy explicit `relationship()` directive defined on models.
- **Indexes**:
  - `users.id` (primary key index)
  - `todos.id` (primary key index)
  - Unique constraint indexes on `users.email` and `users.username`.
- **Data Storage & Retrieval**: Handled via SQLAlchemy ORM sessions managed with dependency `get_db` yielding session instances.

---

## 8. EMAIL
Email functionality is not currently implemented.

---

## 9. BACKGROUND TASKS / SCHEDULING
No background tasks, scheduled jobs, cron jobs, task queues, deadline/reminder systems, or async workers are currently implemented in the codebase.

---

## 10. TESTING
- **Testing Framework**: Pytest (`pytest`)
- **HTTP Client**: FastAPI `TestClient` (built on `httpx` / Starlette)
- **Testing Folder Structure**: `test/` folder located in project root.
- **Existing Test Files**:
  - `test/utils.py`: Database override configuration creating an isolated SQLite database (`testdb.db`), `override_get_db`, `override_get_current_user`, Pytest fixtures (`test_todo`, `test_user`), and `TestClient` instance.
  - `test/test_admin.py`: Integration tests for `/admin/todo` (GET) and `/admin/todo/{todo_id}` (DELETE).
  - `test/test_auth.py`: Unit and integration tests for authentication helper functions (`authenticate`, `create_access_token`, `get_current_user`).
  - `test/test_todos.py`: Integration tests for `/todos` endpoints (GET, POST, PUT, DELETE, and 404 error cases).
  - `test/test_users.py`: Integration tests for `/user` endpoints (GET info, PUT password, PUT add phone).
  - `test/test_main.py`: Test for health check endpoint `/healthy`.
  - `test/test_example.py`: Sample standalone unit test cases and fixture examples.
  - `test/temp.py`: Utility script setting up test database engine.
- **Functionality Tested**: User authentication helpers, JWT decoding/validation, task CRUD operations, admin routes, user profile updates, health check.
- **Test Execution**: Executed via standard command line runner: `pytest`.

---

## 11. VALIDATION & ERROR HANDLING
- **Input Validation**: Handled via Pydantic schema models:
  - `User_Request`: Validates user creation input.
  - `TodoRequest`: Validates `title` (min_length=3), `description` (min_length=3, max_length=20), `priority` (gt=0), `complete` (boolean).
  - `UserVerification`: Validates password change input.
  - Path Parameter Validation: Uses `Path(gt=0)` on `todo_id`.
- **Schema Validation Errors**: Pydantic automatically returns HTTP 422 Unprocessable Entity for invalid JSON request bodies.
- **HTTP Error Handling**: Explicitly raised using FastAPI `HTTPException`:
  - `401 Unauthorized`: Raised for invalid login credentials, failed JWT decoding/validation, missing user claims, incorrect current password on password change, or missing admin role on admin routes.
  - `404 Not Found`: Raised when a todo item with the specified ID does not exist or does not belong to the requesting user.
- **Database Session Safety**: DB sessions are wrapped in `try ... finally` blocks within `get_db` dependencies to ensure connections are closed after processing requests.

---

## 12. SECURITY
- **Password Hashing**: Bcrypt hashing using `passlib.context.CryptContext`. Raw passwords are never stored in plain text.
- **JWT / Token Security**: Signed JWT access tokens using HMAC-SHA256 (`HS256`).
- **Authorization & Isolation**:
  - Role check (`user_role == "admin"`) enforced on admin endpoints.
  - User data isolation enforced on user todo endpoints (`owner_id == user.get("id")`).
- **Environment Variables & Secret Management**: Not implemented. Database connection string and JWT secret key are hardcoded directly within source files (`database.py`, `alembic.ini`, `routers/auth.py`).
- **CORS**: Not configured in `main.py` (no `CORSMiddleware`).

---

## 13. CONFIGURATION & ENVIRONMENT
- **Environment Variables Required**: None used or loaded in codebase.
- **Configuration Files**: `alembic.ini` (Alembic migration configuration).
- **Dependencies**: Listed in source code imports (`fastapi`, `sqlalchemy`, `pydantic`, `passlib`, `python-jose`, `jinja2`, `starlette`, `pytest`, `alembic`).
- **Backend Execution**: Runnable via ASGI server, e.g., `uvicorn TodoApp.main:app --reload`.
- **Database Requirements**: PostgreSQL instance listening at `localhost:5432` with database `TodoApplicationDatabase` and user `postgres`, or fallback SQLite database `todosapp.db`.

---

## 14. DEPLOYMENT
No Dockerfile, docker-compose.yml, CI/CD pipelines, container configuration, or production server deployment files currently exist in the codebase.

---

## 15. EXISTING FEATURES SUMMARY

### Authentication
- User Registration (`POST /auth/create`)
- Password Hashing via Bcrypt (`passlib`)
- User Login & Authentication (`POST /auth/token`)
- JWT Access Token generation (20 min expiration, `HS256` algorithm)
- Protected route authentication dependency (`get_current_user`)
- Role assignment (`role` field)
- Client-side cookie clearing for logout (`static/js/base.js`)

### Task Management
- Create task for authenticated user (`POST /todos/todos`)
- Read / list tasks owned by authenticated user (`GET /todos/`)
- Read single task by ID owned by user (`GET /todos/todo/{todo_id}`)
- Update task title, description, priority, and complete status (`PUT /todos/todo/{todo_id}`)
- Delete user task (`DELETE /todos/todo/{todo_id}`)
- Admin read all tasks across all users (`GET /admin/todo`)
- Admin delete any task by ID (`DELETE /admin/todo/{todo_id}`)
- Supported Task fields: `id`, `title`, `description`, `priority`, `complete`, `owner_id`

### Database
- PostgreSQL connection setup via SQLAlchemy ORM (`database.py`)
- SQLite database configuration for Pytest test suite (`test/utils.py`, `todosapp.db`)
- Alembic database migration system (`alembic.ini`, `alembic/`)
- Declarative ORM models for `Users` and `Todos` (`models.py`)
- Foreign key linking `todos.owner_id` to `users.id`

### API
- FastAPI RESTful JSON API
- Jinja2 HTML page templates (`/login-page`, `/register-page`, `/auth/login-page`, `/auth/register-page`)
- Static files hosting mounted at `/static` (`static/css/`, `static/js/`)
- System health check endpoint (`GET /healthy`)

### Testing
- Automated test suite using Pytest and FastAPI `TestClient`
- Isolated SQLite test database environment (`test/utils.py`)
- Unit and integration tests covering Auth, Todos, Admin, Users, and Health check endpoints

### Email
- None (Email functionality is not currently implemented)

### Scheduling / Background Jobs
- None (Background tasks and job scheduling are not currently implemented)

### Security
- Password hashing using Bcrypt
- JWT token authentication with claims (`sub`, `id`, `role`)
- Role-based authorization (`admin` role check on admin endpoints)
- User data isolation filtering by `owner_id` on todo CRUD queries

### Deployment
- None (Deployment configurations such as Dockerfile, docker-compose, or server deployment scripts are not currently implemented)
