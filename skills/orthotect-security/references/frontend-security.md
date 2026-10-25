# Frontend Security & Client-Side Threat Defense Reference

Comprehensive architectural guide for securing browser runtimes, Single-Page Applications (React, Vue, Svelte), and static templates against modern client-side attacks.

---

## 1. Cross-Site Scripting (DOM XSS) (CWE-79)

### High-Risk Execution Sinks
Never bind untrusted input to:
- `element.innerHTML` or `element.outerHTML`
- `document.write()` or `document.writeln()`
- React `dangerouslySetInnerHTML={{ __html: ... }}`
- Vue `v-html="..."`
- `eval()`, `new Function()`, `setTimeout(string)`, `setInterval(string)`

### Safe Replacement Patterns
```javascript
// ✅ Best: Pure text assignment eliminates parser interpretation
element.textContent = userSuppliedName;

// ✅ When HTML formatting is required, enforce strict DOMPurify sanitization
import DOMPurify from 'dompurify';

const cleanHtml = DOMPurify.sanitize(userContent, {
  ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'ul', 'ol', 'li', 'code'],
  ALLOWED_ATTR: ['href', 'target', 'rel'],
  FORBID_TAGS: ['script', 'style', 'iframe', 'object', 'embed', 'svg', 'math']
});
element.innerHTML = cleanHtml;
```

---

## 2. Cross-Window Communication (PostMessage Security) (CWE-345)

### ❌ Dangerous: Wildcard Target Origin
```javascript
// Broadcasts sensitive data to ANY window, including malicious iframes
window.postMessage({ sessionToken: token }, '*');
```

### ✅ Secure: Exact Target Origin Verification
```javascript
// Sender specifies exact origin
const TARGET_ORIGIN = "https://trusted-service.example.com";
targetIframe.contentWindow.postMessage({ action: "SYNC_THEME", theme: "dark" }, TARGET_ORIGIN);

// Receiver validates event.origin before processing
window.addEventListener("message", (event) => {
  if (event.origin !== TARGET_ORIGIN) {
    console.warn("Blocked message from untrusted origin:", event.origin);
    return;
  }
  // Safe to process event.data
  handleMessage(event.data);
});
```

---

## 3. Prototype Pollution Guards (CWE-1321)

### ❌ Dangerous: Recursive Object Mutation
Copying user-supplied JSON properties into object prototypes allows attackers to alter application logic or trigger denial of service.

### ✅ Secure: Key Denylist & Clean Dictionaries
```javascript
// 1. Filter prototype keys during recursive deep clone/merge
function safeDeepAssign(target, source) {
  for (const key of Object.keys(source)) {
    if (key === '__proto__' || key === 'constructor' || key === 'prototype') {
      continue;
    }
    if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
      target[key] = safeDeepAssign(target[key] || {}, source[key]);
    } else {
      target[key] = source[key];
    }
  }
  return target;
}

// 2. Use prototype-less objects for lookup tables
const lookupTable = Object.create(null);
```

---

## 4. Reverse Tabnabbing & Open External Links (CWE-1022)

### ❌ Dangerous: Target Blank without Rel
```html
<a href="https://external-site.com" target="_blank">Partner Site</a>
```
*The external site gains access to `window.opener.location` and can silently redirect the user to a phishing page.*

### ✅ Secure: Strict Rel Attributes
```html
<a href="https://external-site.com" target="_blank" rel="noopener noreferrer">Partner Site</a>
```

---

## 5. Client-Side Token & State Isolation

| Storage Mechanism | Vulnerability to XSS | Recommended Usage |
|---|---|---|
| `localStorage` | **High:** Readable by any XSS script | Non-sensitive UI preferences (theme, language, layout state) |
| `sessionStorage` | **High:** Readable by any XSS script | Temporary tab UI state |
| `document.cookie` | **High:** If missing `HttpOnly` flag | Legacy non-sensitive state |
| `HttpOnly; Secure; SameSite=Lax` Cookies | **Immune to XSS script access** | **Authentication session tokens, refresh tokens, auth state** |

---

## 6. Content-Security-Policy (CSP) Directives

```http
Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-rAnd0m'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; frame-ancestors 'none'; object-src 'none'; base-uri 'self'; form-action 'self';
```
- `frame-ancestors 'none'`: Completely prevents Clickjacking by blocking the page from being framed.
- `object-src 'none'`: Disables dangerous plugins (Flash, Java).
- `base-uri 'self'`: Prevents `<base href="...">` hijacking.
