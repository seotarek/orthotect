# JSON-LD Structured Data Templates

Production-grade, validated Schema.org templates in JSON-LD format with `@graph` support for interface engineering. Use customizable placeholders (`{{APP_NAME}}`, `{{WEBSITE_URL}}`, `{{PRICE}}`, `{{SUPPORT_URL}}`) when integrating into your application templates.

## 1. Unified SaaS Homepage (`@graph` Pattern)

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "{{WEBSITE_URL}}/#organization",
      "name": "{{APP_NAME}}",
      "url": "{{WEBSITE_URL}}/",
      "logo": {
        "@type": "ImageObject",
        "url": "{{WEBSITE_URL}}/logo.png",
        "width": 512,
        "height": 512
      },
      "sameAs": [
        "https://github.com/example/{{APP_NAME}}",
        "https://x.com/{{APP_NAME}}"
      ]
    },
    {
      "@type": "WebSite",
      "@id": "{{WEBSITE_URL}}/#website",
      "url": "{{WEBSITE_URL}}/",
      "name": "{{APP_NAME}} Interface Engineering",
      "publisher": {
        "@id": "{{WEBSITE_URL}}/#organization"
      },
      "potentialAction": {
        "@type": "SearchAction",
        "target": {
          "@type": "EntryPoint",
          "urlTemplate": "{{WEBSITE_URL}}/search?q={search_term_string}"
        },
        "query-input": "required name=search_term_string"
      }
    },
    {
      "@type": "SoftwareApplication",
      "@id": "{{WEBSITE_URL}}/#software",
      "name": "{{APP_NAME}}",
      "operatingSystem": "All",
      "applicationCategory": "DeveloperApplication",
      "description": "Deterministic interface engineering and runtime gate architecture for autonomous AI agents.",
      "offers": {
        "@type": "Offer",
        "price": "{{PRICE}}",
        "priceCurrency": "USD"
      },
      "aggregateRating": {
        "@type": "AggregateRating",
        "ratingValue": "4.9",
        "ratingCount": "120",
        "bestRating": "5"
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
      "name": "What is {{APP_NAME}}?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "{{APP_NAME}} is a deterministic interface engineering runtime that enforces WCAG accessibility, CSS logical properties, and finite state machine integrity."
      }
    },
    {
      "@type": "Question",
      "name": "How does {{APP_NAME}} handle customer support?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Support is available at {{SUPPORT_URL}} and via the community discussion forum."
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
      "item": "{{WEBSITE_URL}}/"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "Documentation",
      "item": "{{WEBSITE_URL}}/docs/"
    },
    {
      "@type": "ListItem",
      "position": 3,
      "name": "Skills",
      "item": "{{WEBSITE_URL}}/docs/skills/"
    }
  ]
}
</script>
```
