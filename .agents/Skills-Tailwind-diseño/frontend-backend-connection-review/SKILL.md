---
name: frontend-backend-connection-review
description: >
  Reviews frontend code changes for bugs and verifies that requests, responses,
  and routing stay consistent with the Django backend APIs. Use when the user
  mentions a "Frontend agent", frontend changes, API errors, or problems in the
  integration between the React/JS UI and the Django/PostgreSQL backend.
---

# Frontend–Backend Connection Review

This skill guides the agent to continuously review frontend changes (especially
those produced by a "Frontend agent") with a strong focus on integration with a
Django/PostgreSQL backend.

## When to Use This Skill

- When the user mentions:
  - "Frontend agent" or automated frontend code generation
  - Bugs in API calls, 4xx/5xx responses, or network errors
  - Issues where the UI does not reflect backend data correctly
  - CORS issues, CSRF problems, or authentication/authorization errors
- When reviewing diffs that touch:
  - API client utilities (e.g. `api.ts`, `fetchClient.ts`, `axios` wrappers)
  - Components or hooks that call REST endpoints or WebSockets
  - Forms or views that send data to the Django backend

## Review Goals

When using this skill, the agent should:

1. **Catch obvious frontend bugs**
   - Mis-typed variables or props
   - Incorrect use of React hooks or component state
   - Missing dependency arrays in `useEffect` that cause stale or looping calls
   - Unhandled promise rejections and missing `try/catch` around async calls

2. **Validate API contracts with the Django backend**
   - Ensure URL paths, HTTP methods, and query parameters match backend routes.
   - Check that request bodies follow the serializer/DRF schema
     (field names, nesting, types).
   - Verify expected response shapes (e.g. `results`, `count`, `next`) line up
     with backend views.

3. **Respect PostgreSQL and backend constraints**
   - Recognize that the backend is strict about types and max lengths.
   - Watch for user input that may exceed backend validation constraints.
   - Ensure client-side validation mirrors backend rules when possible.

4. **Verify error handling and UX**
   - Confirm that non-2xx responses are handled (not silently ignored).
   - Ensure error messages from the backend are surfaced to the user in a clear,
     non-technical way where appropriate.
   - Avoid exposing raw stack traces or sensitive technical details.

5. **Check authentication, CSRF, and security**
   - Confirm that auth headers or tokens are included where required.
   - For cookie-based auth, ensure CSRF tokens are sent correctly (for unsafe
     HTTP methods like POST/PUT/PATCH/DELETE).
   - Watch for obvious injection or XSS issues when rendering backend-provided
     HTML or user content.

## Step-by-Step Review Process

When this skill is active, follow this workflow for each relevant change:

1. **Identify affected endpoints**
   - Locate any `fetch`, `axios`, or similar calls.
   - Note the URL, HTTP method, headers, and payload shape.
   - If backend code is available, cross-check against Django `urls.py`,
     views, DRF viewsets, or serializers.

2. **Compare request/response contracts**
   - Check that required fields are always provided.
   - Confirm optional fields are handled gracefully if absent.
   - Ensure type conversions are correct (e.g. numbers vs strings, dates).

3. **Inspect state and rendering**
   - Verify that loading, success, and error states are all represented.
   - Check that components do not assume data is immediately available
     (handle `null`/`undefined` and empty lists safely).
   - Make sure re-renders are triggered when backend data changes.

4. **Review error handling**
   - Look for `.catch` blocks or `try/catch` around async/await.
   - Ensure user-visible feedback exists for common failure cases (network
     error, validation error, unauthorized, forbidden, not found).

5. **Summarize findings clearly**
   - Separate problems into:
     - **Critical**: Integration will break (wrong URL, missing field, etc.).
     - **Important**: Poor UX or fragile behavior under edge cases.
     - **Minor**: Style or non-breaking improvements.
   - When possible, reference specific files and lines and propose concrete
     code-level fixes.

## Examples of What to Flag

- Frontend calling `POST /api/customers/` but backend exposes
  `POST /api/clientes/`.
- Sending `customerId` as a string when backend expects an integer field.
- Ignoring a `409 Conflict` response where backend signals a duplicate record.
- Using `response.data.items` when backend returns `results`.
- Missing `await` before an async call, causing a race in state updates.

## Output Format

When reporting findings using this skill, structure feedback like this:

- **Critical**:
  - [Short description of the issue]
  - [Why it breaks the integration]
  - [Concrete fix suggestion]
- **Important**:
  - [Short description]
  - [Impact on robustness or UX]
- **Minor**:
  - [Short description]
  - [Optional improvement suggestion]

