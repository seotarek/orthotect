# Form Conversion Engineering & Friction Reduction

Form abandonment occurs when users encounter cognitive friction, unexpected validation errors, or ambiguous input requests. This reference provides concrete patterns for maximizing form completion rates while maintaining data integrity.

## 1. Field Minimization Principle
- **Streamlined Initial Conversion**: Require only essential inputs for initial signups (e.g. `Email` or `Name` and `Email`). Unnecessary fields increase cognitive friction and perceived effort.
- **Defer Non-Essential Data**: Collect secondary attributes such as job title, company size, phone number, and billing preferences progressively during onboarding after authentication succeeds.
- **Single-Column Baseline & Paired Inputs**: Default to a single vertical column for form fields to ensure a clear, predictable scanning path on mobile and desktop viewports. Form layouts can pair naturally related, short fields (such as `First Name` / `Last Name` or `City` / `ZIP`) on wide viewports as a testable layout hypothesis, provided tab order and ARIA labeling remain strictly sequential.

## 2. Progressive Disclosure for Complex Workflows
- **Multi-Step Chunking**: When a workflow requires more than 5 fields (e.g. checkout, onboarding, configuration), split into distinct logical steps.
- **Progress Telemetry**: Show a clear, accessible step indicator (`Step 1 of 3: Workspace Details`) with `aria-live="polite"` announcing step transitions.
- **State Preservation**: Persist entered data across steps in `sessionStorage` or local state so that back-navigation never wipes user input.

## 3. Inline Validation & Feedback Ergonomics
- **Validation Timing**: Validate on `blur` (when user leaves the field), never while actively typing unless checking password strength or character counts.
- **Positive Confirmation**: Display subtle green checkmarks or borders when requirements are satisfied, reducing cognitive anxiety.
- **Descriptive Error Messaging**:
  - *Bad*: "Invalid input."
  - *Good*: "Please enter a valid work email address (e.g., name@company.com)."
- **Accessible Linking**:
  ```html
  <label for="email-input" class="ot-form-label">Work Email</label>
  <input
    id="email-input"
    type="email"
    required
    aria-invalid="false"
    aria-describedby="email-error email-hint"
    class="ot-form-input"
  />
  <span id="email-hint" class="ot-form-hint">We'll send your confirmation link here.</span>
  <span id="email-error" class="ot-form-error" role="alert" hidden>Please enter a valid work email.</span>
  ```

## 4. FSM Submission Locks & Double-Submit Prevention
Double submissions cause duplicate billing charges, orphaned database records, and frustrated users. All submit buttons must be guarded by Finite State Machine states:
- `IDLE`: Submit button enabled (`Sign Up Now`).
- `SUBMITTING`: Submit button disabled, shows spinner and loading text (`Processing...`), `aria-busy="true"`.
- `SUCCESS`: Submit button shows success state (`Account Created`), redirects or unlocks dashboard.
- `ERROR`: Submit button re-enables with clear error banner and focused error field.

## 5. Touch & Mobile Ergonomics
- Set `inputmode` and `autocomplete` properly (`inputmode="email" autocomplete="email"`, `inputmode="numeric"` for verification codes).
- Provide a minimum hit area of 48px height for all input fields and checkboxes.
- Disable aggressive iOS auto-zoom by ensuring input font size is at least 16px (`1rem`).
