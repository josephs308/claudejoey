# Structured data (JSON-LD)

## Contents
1. The @graph pattern
2. Sitewide nodes
3. Types by page
4. Rules that keep markup valid
5. Examples
6. Testing

## 1. The @graph pattern

Put one `<script type="application/ld+json">` in the `<head>` of each page containing a single `@graph` array. Give each node an `@id` (a URL plus a fragment) and connect nodes by reference instead of nesting copies:

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {"@type": "Organization", "@id": "https://example.com/#org", "name": "Brand", "url": "https://example.com/", "logo": {"@type": "ImageObject", "@id": "https://example.com/#logo", "url": "https://example.com/assets/logo.png"}},
    {"@type": "WebSite", "@id": "https://example.com/#website", "url": "https://example.com/", "name": "Brand", "publisher": {"@id": "https://example.com/#org"}},
    {"@type": "WebPage", "@id": "https://example.com/services/seo/#webpage", "url": "https://example.com/services/seo/", "name": "…", "isPartOf": {"@id": "https://example.com/#website"}, "breadcrumb": {"@id": "https://example.com/services/seo/#breadcrumb"}, "about": {"@id": "https://example.com/#org"}}
  ]
}
```

Why: a graph lets Google and AI systems see that the org on every page is the same entity, and it's easy to generate from one function. Escape `</` as `<\/` when serializing so a string containing `</script>` can't break the page.

## 2. Sitewide nodes (on every page)

- **Organization** (or a more specific subtype: `LocalBusiness`, `LegalService`, `ProfessionalService`, `Store`, `OnlineStore`, `Corporation`): `name`, `url`, `logo`, `email`, `telephone`, `sameAs` (official social/profile URLs — LinkedIn, Facebook, Instagram, YouTube, Crunchbase, Wikipedia/Wikidata if they exist), `areaServed`, `address` only if it's a real public address.
- **WebSite**: `name`, `url`, `publisher` → org. Add `potentialAction` SearchAction only if the site really has search.
- **WebPage** (or `CollectionPage`, `AboutPage`, `ContactPage`, `FAQPage`-bearing page): `url`, `name`, `description`, `isPartOf` → website, `breadcrumb`, `inLanguage`, `dateModified`, `primaryImageOfPage`.

## 3. Types by page

| Page | Add |
|---|---|
| Homepage | Organization (full), WebSite, WebPage, FAQPage if it has visible FAQs |
| Service page | `Service` (`name`, `description`, `provider` → org, `areaServed`, `serviceType`), BreadcrumbList, FAQPage |
| Services / category hub | `CollectionPage` + `ItemList` of the child pages (`ListItem` with `position`, `url`, `name`), BreadcrumbList |
| Product page (ecommerce) | `Product` with `name`, `image`, `description`, `sku`, `brand`, `offers` (`Offer`: `price`, `priceCurrency`, `availability`, `url`, `priceValidUntil` optional, `shippingDetails` and `hasMerchantReturnPolicy` for merchant listings), `aggregateRating`/`review` only from real on-page reviews |
| Product category | `CollectionPage` + `ItemList`, BreadcrumbList |
| Blog post | `BlogPosting` (or `Article`/`NewsArticle`): `headline`, `description`, `image`, `datePublished`, `dateModified`, `author` (Person with `url`), `publisher` → org, `mainEntityOfPage` → webpage; BreadcrumbList; FAQPage if the post has visible FAQs |
| Blog index | `CollectionPage` (or `Blog`) + `ItemList` of posts |
| About | `AboutPage`; `Person` nodes for founders/team with `jobTitle`, `sameAs` |
| Contact | `ContactPage`; org `contactPoint` |
| Local location page | `LocalBusiness` subtype with real `address`, `geo`, `openingHoursSpecification`, `telephone` |
| Software / app | `SoftwareApplication` with `applicationCategory`, `operatingSystem`, `offers` |
| Events | `Event` with `startDate`, `location`, `offers` |
| Video | `VideoObject` with `name`, `thumbnailUrl`, `uploadDate`, `contentUrl`/`embedUrl` |

**Rich result reality check** (so you can set expectations honestly):
- FAQ rich results in Google are now limited to well-known government and health sites. Still use FAQPage markup — it's cheap, valid, and helps AI systems and Bing parse Q&A — but don't promise FAQ dropdowns in Google.
- HowTo rich results were removed. Don't bother.
- Breadcrumbs, Product/merchant listings, reviews on products, Article, Event, Video, Organization logo and sitelinks search are still meaningful.

## 4. Rules that keep markup valid

- **Markup must describe content visible on the page.** Every FAQ question/answer in JSON-LD must appear on the page with the same wording; prices and ratings in schema must match what's displayed. The audit script checks FAQ visibility.
- **Every `@id` reference must resolve** to a node in the same graph (or a well-known sitewide id you always emit). Dangling refs are flagged by the audit.
- **BreadcrumbList items must be real, indexable URLs**, in order, starting at the homepage. The last item can omit `item`.
- **No self-serving reviews**: an Organization/LocalBusiness can't carry review stars about itself from its own site.
- **Absolute URLs** everywhere in schema.
- **Dates in ISO 8601** (`2026-09-30`); `dateModified` ≥ `datePublished`.
- Don't mark up things that don't exist yet (a "coming soon" service with a price, fake ratings, an address you don't have).
- One Organization identity: same name, logo, URL and `sameAs` everywhere.

## 5. Examples

**Service page**
```json
{"@type":"Service","@id":"https://example.com/services/seo/#service","name":"SEO for Law Firms","serviceType":"Search engine optimization","description":"…","provider":{"@id":"https://example.com/#org"},"areaServed":{"@type":"Country","name":"United States"},"url":"https://example.com/services/seo/"}
```

**Breadcrumbs**
```json
{"@type":"BreadcrumbList","@id":"https://example.com/services/seo/#breadcrumb","itemListElement":[
 {"@type":"ListItem","position":1,"name":"Home","item":"https://example.com/"},
 {"@type":"ListItem","position":2,"name":"Services","item":"https://example.com/services/"},
 {"@type":"ListItem","position":3,"name":"SEO"}]}
```

**FAQ**
```json
{"@type":"FAQPage","@id":"https://example.com/services/seo/#faq","mainEntity":[
 {"@type":"Question","name":"How long does SEO take?","acceptedAnswer":{"@type":"Answer","text":"Most sites see movement in 3–6 months…"}}]}
```

**Product**
```json
{"@type":"Product","@id":"https://shop.example/products/trail-boot/#product","name":"Women's Trail Boot","image":["https://shop.example/img/trail-boot-1200.jpg"],"description":"…","sku":"TB-W-001","brand":{"@type":"Brand","name":"Trailco"},
 "offers":{"@type":"Offer","url":"https://shop.example/products/trail-boot/","priceCurrency":"USD","price":"129.00","availability":"https://schema.org/InStock","itemCondition":"https://schema.org/NewCondition"},
 "aggregateRating":{"@type":"AggregateRating","ratingValue":"4.7","reviewCount":"212"}}
```

## 6. Testing

- Google Rich Results Test: https://search.google.com/test/rich-results — test the homepage and one page of each template after changes.
- Schema.org validator: https://validator.schema.org — catches vocabulary errors the Google test ignores.
- Search Console → Enhancements shows errors across the whole site after Google recrawls.
