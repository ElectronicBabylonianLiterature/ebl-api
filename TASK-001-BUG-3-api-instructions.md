# TASK-001 — API Implementation Instructions for Non-Numeric Date Spellings & Year Metadata (BUG-3)

## Overview

Implement support for structured year metadata (`isReconstructed`, `isEmended`) and robust handling of non-numeric date spellings in the API, matching the frontend changes. This includes:

- Extending date DTOs and database schema to support new metadata fields.
- Ensuring all endpoints and parsing logic handle non-numeric wrappers and metadata.
- Adding/adjusting tests.
- Providing a migration for existing data if needed.

---

## 1. Data Model & DTO Changes

### 1.1. Extend Date DTOs

- **Fragmentarium**: Update the date field DTOs (e.g., `DateFieldDto`, `KingDateDtoField`) to include:
  - `isReconstructed: Optional[bool]`
  - `isEmended: Optional[bool]`
- **Corpus/Other modules**: If other modules use date DTOs, update them similarly.

### 1.2. Update Domain Models

- Update all domain models representing dates to include the new fields.
- Ensure that serialization (`to_dict`, `from_dict`, etc.) and validation logic support these fields.

---

## 2. Database Schema

### 2.1. MongoDB Schema

- **Fragments**: Update the schema for date fields in the `fragments` collection to allow `isReconstructed` and `isEmended` as optional boolean fields in each date object.
- **Other collections**: If other collections store date fields, update their schema similarly.

### 2.2. Migration

- **Legacy data**: No destructive changes; existing data with raw `<...>`, `!`, etc. in year fields should be preserved for now. Plan for a future cleanup after the new model is live.

---

## 3. API Endpoints

### 3.1. Accept and Return Metadata

- Update all endpoints that accept or return date fields (e.g., fragment create/update, corpus text endpoints) to:
  - Accept `isReconstructed` and `isEmended` in incoming payloads for year fields.
  - Return these fields in responses.

### 3.2. Parsing and Validation

- Update date parsing logic to:
  - Recognize and ignore wrappers like `<...>`, `[... ]`, `(...)`, `!`, `?` for numeric conversion, but preserve the original value for display.
  - For year fields: Prefer structured metadata (`isReconstructed`, `isEmended`) over inferring from raw symbols.
  - Allow free-text values for flexibility, but ensure robust handling of supported patterns (`n`, `x`, `n+`, `x+n`, `n-n`, `n/n`, `n[a-z]`).
  - Convert `n?`, `n!`, `(n)`, `[n]`, `<n>` to use structured metadata instead.

    | Pattern Example | Structured Metadata Set | String Value Change   |
    | --------------- | ----------------------- | --------------------- |
    | `n?`            | `isUncertain: true`     | Remove `?` from value |
    | `n!`            | `isEmended: true`       | Remove `!` from value |
    | `<n>`           | `isReconstructed: true` | Remove `<` and `>`    |
    | `(n)`           | `isUncertain: true`     | Remove `(` and `)`    |
    | `[n]`           | `isBroken: true`        | Remove `[` and `]`    |

    For each case, the API should:
    - Detect the wrapper or symbol in the string value.
    - Set the corresponding structured metadata field to `true`.
    - Store the cleaned numeric value (with wrapper/symbol removed) in the value field.
    - Prefer the structured metadata for all logic and conversion.

---

## 4. Tests

- Add/extend unit and integration tests to cover:
  - DTO serialization/deserialization with new fields.
  - End-to-end fragment create/update/read with new metadata.
  - Parsing of non-numeric date spellings and correct handling of wrappers.
  - Backward compatibility with legacy data (raw `<...>`, `!`, etc.).

---

## 5. Migration Steps (don't do this yet)

1. Implement DTO, model, and endpoint changes.
2. Write and test the migration script for the database.
3. Deploy code changes.
4. Run the migration script on the production database.
5. Confirm that all endpoints work with both legacy and new data.

---

## 6. Notes

- Do **not** remove or overwrite legacy raw values in this migration. Only add support for the new fields and ensure robust parsing.
- Plan a future cleanup migration to convert legacy raw values to structured metadata after frontend and backend are both live and stable.

---

**End of instructions.**
