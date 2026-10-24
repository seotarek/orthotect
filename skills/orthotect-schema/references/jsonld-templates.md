# JSON-LD Structured Data Templates

Production-grade, validated Schema.org templates in JSON-LD format with `@graph` support for interface engineering. Use customizable placeholders (`{{APP_NAME}}`, `{{WEBSITE_URL}}`, `{{PRICE}}`, `{{SUPPORT_URL}}`) when integrating into your application templates.

> **Google Search Central Compliance Note:**
> Every value declared in JSON-LD must visibly correspond to text rendered on the user-facing web page.
> **Never** invent synthetic `aggregateRating` scores (such as fake 4.9/5 counts) or phantom testimonials. Doing so violates Google Search Essentials and leads to manual rich-result actions. Include `aggregateRating` or `review` ONLY when real user ratings are published on the page.

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
      }
    },
    {
      "@type": "WebSite",
      "@id": "{{WEBSITE_URL}}/#website",
      "url": "{{WEBSITE_URL}}/",
      "name": "{{APP_NAME}}",
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
      "description": "Deterministic interface engineering and runtime gate architecture.",
      "offers": {
        "@type": "Offer",
        "price": "{{PRICE}}",
        "priceCurrency": "USD"
      }
    }
  ]
}
</script>
```

### Optional: Genuine Rating Extension
If (and only if) your application displays genuine, third-party verifiable user reviews or ratings on the page, append the `aggregateRating` block inside the `SoftwareApplication` entity:

```json
"aggregateRating": {
  "@type": "AggregateRating",
  "ratingValue": "{{RATING_VALUE}}",
  "reviewCount": "{{REVIEW_COUNT}}",
  "bestRating": "5",
  "worstRating": "1"
}
```

## 2. FAQPage Schema

Use for documentation, product FAQ sections, or support pages where question-answer pairs are visibly rendered.

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What platforms are supported by {{APP_NAME}}?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "{{APP_NAME}} runs in standard modern web browsers and runtime environments supporting Node.js and Python."
      }
    },
    {
      "@type": "Question",
      "name": "Where can I find documentation and technical support for {{APP_NAME}}?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Comprehensive technical documentation and support resources are accessible at {{SUPPORT_URL}}."
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
