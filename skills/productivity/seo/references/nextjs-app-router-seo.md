# Next.js App Router SEO Implementation

Concrete patterns for implementing SEO in Next.js 14+ App Router projects.

## Sitemap (src/app/sitemap.ts)

Next.js auto-generates `/sitemap.xml` from this file:

```typescript
import { MetadataRoute } from "next";

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = "https://example.com";

  return [
    {
      url: baseUrl,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 1,
    },
    {
      url: `${baseUrl}/products`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.9,
    },
    // Dynamic pages
    {
      url: `${baseUrl}/products/item-slug`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.8,
    },
  ];
}
```

## Robots (src/app/robots.ts)

Auto-generates `/robots.txt`:

```typescript
import { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: ["/admin", "/api/"],
      },
    ],
    sitemap: "https://example.com/sitemap.xml",
  };
}
```

## Metadata in layout.tsx

```typescript
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: {
    default: "Site Title — Tagline",
    template: "%s | Site Title",  // For child pages
  },
  description: "Primary description for search results",
  keywords: ["keyword1", "keyword2", "long-tail keyword"],
  authors: [{ name: "Author Name" }],
  metadataBase: new URL("https://example.com"),
  alternates: {
    canonical: "/",
  },
  openGraph: {
    title: "OG Title",
    description: "OG Description",
    type: "website",
    locale: "id_ID",
    url: "https://example.com",
    siteName: "Site Name",
  },
  twitter: {
    card: "summary_large_image",
    title: "Twitter Title",
    description: "Twitter Description",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  verification: {
    google: "verification-code-from-search-console",
  },
};
```

## JSON-LD Structured Data in layout.tsx

```typescript
const jsonLd = {
  "@context": "https://schema.org",
  "@type": "Organization",
  name: "Organization Name",
  description: "Description",
  url: "https://example.com",
  address: {
    "@type": "PostalAddress",
    addressLocality: "City",
    addressRegion: "Province",
    addressCountry: "ID",
  },
};

// In the component:
<html lang="id">
  <head>
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
    />
  </head>
  ...
</html>
```

## Post-Deploy Steps

1. Register at https://search.google.com/search-console
2. Add property (URL prefix method)
3. Verify ownership (HTML tag or DNS)
4. Submit sitemap URL
5. Wait 3-7 days for initial indexing

## Timeline Expectations

- Initial indexing: 3-7 days after Search Console submission
- Ranking for low-competition branded keywords: 1-4 weeks
- Ranking for competitive generic keywords: months (requires backlinks + content)

## Key Pitfalls

- `metadataBase` is required for relative URLs in OG/canonical to resolve correctly
- Don't forget to block `/admin` and `/api/` in robots.txt
- JSON-LD must be in `<head>` or early in `<body>` for reliable parsing
- `verification.google` field: add AFTER getting the code from Search Console (leave commented until then)
- **Vercel deploy timing**: After pushing, wait ~2 minutes for Vercel to finish building before verifying with Google Search Console or testing sitemap.xml. Premature verification returns "meta tag not found" error; premature sitemap access returns 404. Tell the user to wait before clicking "Verify".
- **Google Search Console verification method**: For Vercel-hosted sites without custom domains, use "URL Prefix" property type + "HTML Tag" verification method (easiest — just add `verification.google` to metadata). Avoid "Domain" type which requires DNS access.
- **Sitemap "Cannot retrieve" status**: After submitting sitemap in Search Console, initial status often shows red "Cannot retrieve sitemap" — this is normal and resolves within 1-24 hours as Google retries. Don't panic or resubmit.
- **Request Indexing daily quota**: Google Search Console limits "Request Indexing" to ~10-20 URLs per day per property. If user hits "Quota Exceeded", tell them to try remaining URLs tomorrow. Priority order: homepage first, then key landing pages.
