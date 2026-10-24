# JSON-LD Structured Data Templates

Production-grade, validated Schema.org templates in JSON-LD format with `@graph` support for interface engineering.

## 1. Unified SaaS Homepage (`@graph` Pattern)

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://example.com/#organization",
      "name": "Orthotect",
      "url": "https://example.com/",
      "logo": {
        "@type": "ImageObject",
        "url": "https://example.com/logo.png",
        "width": 512,
        "height": 512
      },
      "sameAs": [
        "https://github.com/seotarek/orthotect",
        "https://twitter.com/orthotect"
      ]
    },
    {
      "@type": "WebSite",
      "@id": "https://example.com/#website",
      "url": "https://example.com/",
      "name": "Orthotect Interface Engineering",
      "publisher": {
        "@id": "https://example.com/#organization"
      },
      "potentialAction": {
        "@type": "SearchAction",
        "target": {
          "@type": "EntryPoint",
          "urlTemplate": "https://example.com/search?q={search_term_string}"
        },
        "query-input": "required name=search_term_string"
      }
    },
    {
      "@type": "SoftwareApplication",
      "@id": "https://example.com/#software",
      "name": "Orthotect CLI",
      "operatingSystem": "All",
      "applicationCategory": "DeveloperApplication",
      "description": "Deterministic interface engineering and runtime gate architecture for autonomous AI agents.",
      "offers": {
        "@type": "Offer",
        "price": "0",
        "priceCurrency": "USD"
      }
    }
  ]
}
</script>
```

## 2. FAQPage Schema

Use for documentation, product FAQ sections, or support pages.

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What is Orthotect?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Orthotect is a deterministic interface engineering runtime that enforces WCAG accessibility, CSS logical properties, and finite state machine integrity."
      }
    },
    {
      "@type": "Question",
      "name": "How does Orthotect prevent duplicate form submissions?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Orthotect enforces Finite State Machine (FSM) submit button contracts that transition into a disabled loading state upon form dispatch."
      }
    }
  ]
}
</script>
```

## 3. BreadcrumbList Schema

Use for nested documentation, e-commerce categories, or multi-level application views.

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Home",
      "item": "https://example.com/"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "Documentation",
      "item": "https://example.com/docs/"
    },
    {
      "@type": "ListItem",
      "position": 3,
      "name": "Skills",
      "item": "https://example.com/docs/skills/"
    }
  ]
}
</script>
```
