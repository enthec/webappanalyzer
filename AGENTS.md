# Instructions for AI agents

This repository is a list of fingerprints (regular expressions and selectors) that identify web technologies. A wrong
fingerprint is worse than a missing one: it reports a technology on sites that don't use it. These rules apply to any
change made with an AI agent, and pull requests that break them are closed.

## Hard rules

1. **Nothing generic is accepted.** Every pattern must point to the technology itself: its own domain, its own named
   JS global, cookie, meta tag, header, attribute or class. A pattern that could appear on a site that doesn't use the
   technology is generic and the pull request will be rejected. Generic examples that were rejected:
   - generic HTML or classes: `id="coupon-code-form"`, `class="m-coupons"`
   - paths without the vendor's domain: `/v1/events$`, `/v1/g\.js\?w=`
   - short or common names: JS globals `n2g`, `_tip`, `trackingFunctions`, cookie `__psid`
   - another vendor's identifiers: `FS.clearUserCookie` belongs to FullStory, `ad-srv.net` belongs to NEORY, not belboon
   - content that any site may have: an email address `@gmail.com`
2. **Never guess.** Only add a pattern you have seen on a real site using the technology or in the vendor's own
   documentation, and link that source in the pull request. If you can't verify something, leave it out. Don't infer a
   domain, global or category from the technology name.
3. **Verify who owns every domain you use** (vendor documentation, WHOIS, the vendor's own site) and cite it in the pull
   request. A domain that sounds like the brand may belong to someone else.
4. **Don't duplicate.** Before adding a technology, search `src/technologies` for its name, domains, JS globals, cookies
   and meta values. If it already exists, extend that entry instead of creating a new one.
5. **`requires` and `implies` mean dependency, not co-occurrence.** Use them only when the technology can't work without
   the other one (a WordPress plugin requires `WordPress`, a WooCommerce extension requires `WooCommerce`, a Shopify-only
   app implies `Shopify`). Never add them because two technologies are often found on the same sites. A product that also
   works outside the platform has no dependency on it.
6. **Keep the diff small.** One technology per pull request. Edit only the entries you are adding or fixing, never
   copy or rewrite a whole file and never touch unrelated entries. Rebase on `main` instead of copying an old file.
7. **`python3 scripts/check.py` must pass** before opening the pull request.

## Field semantics

The full specification is in [README.md](README.md#specification). The fields that are most often misused:

| Field       | Matched against                                       | Use it for                                          |
|-------------|-------------------------------------------------------|-----------------------------------------------------|
| `scriptSrc` | URLs of `<script src>` files                          | the vendor's script URL, e.g. `cdn\\.vendor\\.com/` |
| `scripts`   | JavaScript code, not the URL it was loaded from       | code or strings that only the vendor's script has   |
| `js`        | JavaScript properties (name, optionally its value)    | the vendor's own global, e.g. `VendorSDK.version`   |
| `xhr`       | **hostnames** of XHR requests, never paths or queries | `(?:^\|\\.)api\\.vendor\\.com$`                     |
| `dom`       | CSS selectors                                         | elements or attributes only the vendor renders      |
| `text`      | plain text of the page                                | vendor credits such as `Powered by Vendor`          |
| `meta`      | `<meta name content>` values                          | `{"generator": "^Vendor"}`                          |
| `headers`   | HTTP response headers                                 | `{"X-Powered-By": "^Vendor"}`                       |
| `dns`       | DNS records                                           | the vendor's nameservers or TXT verification        |
| `html`      | **deprecated**, don't use it in new patterns          | use `dom`, `text` or `css`                          |

## Writing patterns

- Patterns are regular expressions inside JSON strings, so every backslash is written twice: `vendor\\.com`.
- Escape every dot of a domain (`vendor\\.com`, not `vendor.com`) and every `?` that starts a query string (`\\?id=`).
- Anchor domains so they don't match longer ones: `[/.]vendor\\.com/` in URLs, `(?:^|\\.)vendor\\.com$` in `xhr`.
- `/*` means "zero or more slashes", it is not a wildcard.
- Extra information goes after `\\;`: `\\;version:\\1` to capture a version, `\\;confidence:50` for a weak pattern.

## New technology checklist

- `cats`: ids from [src/categories.json](src/categories.json) that describe what the technology is. Platform categories
  (`WordPress plugins`, `Shopify apps`, ...) require the dependency described in rule 5.
- `website`: the vendor's homepage.
- `description`: one factual sentence about what the technology is, no marketing.
- `icon`: a real PNG, JPG or SVG in [src/images/icons](src/images/icons), under 100 KB, with no scripts in SVGs.
- The entry goes in the file named after its first letter (`_.json` for digits and symbols).
- Run `python3 scripts/fix_order.py` to sort and format the files, then `python3 scripts/check.py`.

## Pull request description

- The technology, its website and what it is.
- Ten or more URLs of sites that use it.
- For every pattern, where it was observed (site URL or vendor documentation).
- For every domain, the source that proves the vendor owns it.

## What the CI checks

`.github/workflows/validate.yml` runs every validator in `.github/workflows/scripts`. Besides the structure, schema,
order and format of the files, it rejects `xhr` patterns with paths, platform plugins without their dependency, fake or
oversized icons and SVGs with scripts. On pull requests, `pr_validator.py` also checks the changed entries: required
fields, short globals and cookies, globals or cookies already used by another technology, unescaped dots and queries,
deprecated fields, and pull requests that add, modify or delete too many entries. Warnings (patterns without a domain or
the brand name, domains or names shared with another technology) are reviewed by a maintainer.
