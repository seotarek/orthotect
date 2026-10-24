# Injection Attack Vectors & Deterministic Mitigations

Detailed catalog of common full-stack injection vectors, covering legacy and contemporary paradigms.

---

## 1. Client-Side DOM XSS (CWE-79)

### Attack Vectors
- `element.innerHTML = location.hash`
- `element.outerHTML = userInput`
- `document.write(userInput)`
- `dangerouslySetInnerHTML={{ __html: unescapedHtml }}`
- `<a href="javascript:alert(1)">` (JavaScript URI injection)

### Deterministic Fix
Always escape dynamic values or pass through a hardened sanitizer:

```javascript
// Pure text nodes prevent HTML parsing
element.textContent = userInput;

// When HTML markup is required, sanitize using DOMPurify
import DOMPurify from 'dompurify';
element.innerHTML = DOMPurify.sanitize(userHtml, {
  ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p'],
  ALLOWED_ATTR: ['href', 'target']
});
```

---

## 2. Prototype Pollution (CWE-1321)

### Attack Vectors
Recursive object merging that copies properties from user-supplied JSON containing `__proto__` or `constructor.prototype`.

```javascript
// Dangerous recursive merge
function unsafeMerge(target, source) {
  for (const key in source) {
    if (typeof source[key] === 'object') {
      target[key] = unsafeMerge(target[key] || {}, source[key]);
    } else {
      target[key] = source[key];
    }
  }
  return target;
}
```

### Deterministic Fix
Sanitize forbidden keys before assignment:

```javascript
function safeMerge(target, source) {
  for (const key of Object.keys(source)) {
    if (key === '__proto__' || key === 'constructor' || key === 'prototype') {
      continue;
    }
    if (typeof source[key] === 'object' && source[key] !== null) {
      target[key] = safeMerge(target[key] || {}, source[key]);
    } else {
      target[key] = source[key];
    }
  }
  return target;
}
```

---

## 3. Server-Side Template Injection (SSTI) (CWE-1336)

### Attack Vectors
Passing user input into Jinja2 / Mako / Pug / EJS string rendering functions:

```python
# Dangerous
from flask import render_template_string
render_template_string(f"Hello {user_input}")
```

### Deterministic Fix
Pass dynamic variables exclusively via context dictionaries:

```python
# Secure
render_template_string("Hello {{ name }}", name=user_input)
```

---

## 4. NoSQL & Object Injection (CWE-943)

### Attack Vectors
Passing unvalidated request bodies containing MongoDB operators (`$gt`, `$ne`, `$where`):

```javascript
// Express query injection: req.body.password can be { "$ne": "" }
db.users.findOne({ username: req.body.username, password: req.body.password });
```

### Deterministic Fix
Type-check and validate all inputs:

```javascript
if (typeof req.body.password !== 'string') {
  return res.status(400).json({ error: "Invalid password type" });
}
```
