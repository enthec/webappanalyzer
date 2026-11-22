# webappanalyzer

[![Validator Status](https://github.com/enthec/webappanalyzer/actions/workflows/validate.yml/badge.svg)](https://github.com/enthec/webappanalyzer/actions/workflows/validate.yml)
[![License](https://img.shields.io/github/license/enthec/webappanalyzer.svg)](https://opensource.org/license/gpl-3-0/)

> [!NOTE]
> This project is a continuation of the iconic [**Wappalyzer**](https://github.com/wappalyzer/wappalyzer) that went private in August 2023.
> 
> First and foremost, Enthec is committed not to set this repo private at any moment since this would be out of the scope of the company's business.
> 
> Our interest is to keep it growing, so it can be helpful to the community as it has been until now.
> 
> There are no changes to be expected in the library. We will update it with the same JSON structure currently in use so the user experience will not be modified.

## Specification

A long list of [regular expressions](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Regular_Expressions) is used to identify technologies on web pages. Wappalyzer inspects HTML code, as well as JavaScript variables, response headers and more.

Patterns (regular expressions) are kept in [`src/technologies/`](https://github.com/enthec/webappanalyzer/blob/master/src/technologies). The following is an example of an application fingerprint.

#### Example

```json5
{
  "Example": {
    "description": "A short description of the technology.",
    "cats": [
      1
    ],
    "cookies": {
      "cookie_name": "Example"
    },
    "dom": {
      "#example-id": {
        "exists": "",
        "attributes": {
          "class": "example-class"
        },
        "properties": {
          "example-property": ""
        },
        "text": "Example text content"
      }
    },
    "dns": {
      "MX": [
        "example\\.com"
      ]
    },
    "icon": "Example.svg",
    "cpe": "cpe:2.3:a:example:example:*:*:*:*:*:*:*:*",
    "js": {
      "Example.method": ""
    },
    "excludes": [
      "Example"
    ],
    "headers": {
      "X-Powered-By": "Example"
    },
    "text": [
      "\bexample\b"
    ],
    "css": [
      "\\.example-class"
    ],
    "robots": [
      "Disallow: /unique-path/"
    ],
    "implies": [
      "PHP\\;confidence:50"
    ],
    "requires": [
      "WordPress"
    ],
    "requiresCategory": [
      6
    ],
    "meta": {
      "generator": "(?:Example|Another Example)"
    },
    "probe": {
      "/path": ""
    },
    "scriptSrc": [
      "example-([0-9.]+)\\.js\\;confidence:50\\;version:\\1"
    ],
    "scripts": [
      "function webpackJsonpCallback\\(data\\) {"
    ],
    "url": [
      "example\\.com"
    ],
    "xhr": [
      "example\\.com"
    ],
    "oss": true,
    "saas": true,
    "pricing": [
      "mid",
      "freemium"
    ],
    "website": "https://example.com",
    "certIssuer": "Example",
  }
}
```

## JSON fields

Find the JSON schema at [`schema.json`](https://github.com/enthec/webappanalyzer/blob/main/schema.json).

## Required properties

---

| Field       | Type     | Description                      | Example                 | 
|-------------|----------|----------------------------------|-------------------------|
| **cats**    | `[]int`  | Category ids                     | `[1, 6]`                | 
| **website** | `string` | URL of the application's website | `"https://example.com"` | 

## Optional properties

---

### Base

| Field           | Type                | Description                                               | Example                                          | 
|-----------------|---------------------|-----------------------------------------------------------|--------------------------------------------------|
| **description** | `string`            | A short description of the technology                     | `"short description"`                            | 
| **icon**        | `string`            | Application icon filename                                 | `"Example.svg"`                                  | 
| **cpe**         | `string`            | Application v2.3 [CPE](https://nvd.nist.gov/products/cpe) | `"cpe:2.3:a:apache:http_server:*:*:*:*:*:*:*:*"` |  
| **saas**        | `boolean`           | Software As A Service                                     | `true`                                           | 
| **oss**         | `boolean`           | Open Source Software                                      | `true`                                           | 
| **pricing**     | [Pricing](#Pricing) | Cost indicator                                            | `["low", "freemium"]`                            | 

### Implies, requires and excludes

| Field                | Type       | Description                                                                               | Example         | 
|----------------------|------------|-------------------------------------------------------------------------------------------|-----------------|
| **implies**          | `[]string` | The presence of one application can imply the presence of another                         | `["PHP"]`       | 
| **requires**         | `[]string` | Similar to implies but detection only runs if the required technology has been identified | `["WordPress"]` | 
| **excludes**         | `[]string` | The presence of one application can exclude the presence of another                       | `["Apache"]`    | 
| **requiresCategory** | `[]int`    | Similar to requires, but with category ID                                                 | `[6]`           | 

### Patterns

| Field                    | Type                | Description                                                                                   | Regex | Example                                         | 
|--------------------------|---------------------|-----------------------------------------------------------------------------------------------|-------|-------------------------------------------------|
| **cookies**              | `{string:string}`   | Cookies                                                                                       | true  | `{"cookie_name": "Cookie value"}`               | 
| **dom**                  | [DOM](#DOM)         | [Query selectors](https://developer.mozilla.org/en-US/docs/Web/API/Document/querySelectorAll) | false | `["img[src*='example']"]`                       | 
| **dns**                  | `{string:[]string}` | DNS records                                                                                   | true  | `{"MX": ["example\\.com"]}`                     | 
| **js**                   | `{string:string}`   | JavaScript properties                                                                         | true  | `{"jQuery.fn.jquery": ""}`                      | 
| **headers**              | `{string:string}`   | HTTP response headers                                                                         | true  | `{"X-Powered-By": "^WordPress$"}`               | 
| **text**                 | `[]string`          | Matches plain text                                                                            | true  | `["\bexample\b"]`                               | 
| **css**                  | `[]string`          | CSS rules                                                                                     | true  | `["\\.example-class"]`                          | 
| **probe**                | `{string:string}`   | Request a URL to test for its existence or match text content                                 | false | `{"/path": "Example text"}`                     | 
| **robots**               | `[]string`          | Robots.txt contents                                                                           | false | `["Disallow: /unique-path/"]`                   | 
| **url**                  | `[]string`          | Full URL of the page                                                                          | true  | `["^https?//.+\\.wordpress\\.com"]`             | 
| **xhr**                  | `[]string`          | Hostnames of XHR requests                                                                     | true  | `["cdn\\.netlify\\.com"]`                       | 
| **meta**                 | `{string:string}`   | HTML meta tags                                                                                | true  | `{"generator": "^WordPress$"}`                  | 
| **scriptSrc**            | `[]string`          | URLs of JavaScript files                                                                      | true  | `["jquery\\.js"]`                               | 
| **scripts**              | `[]string`          | JavaScript source code                                                                        | true  | `["function webpackJsonpCallback\\(data\\) {"]` | 
| ~~**html**~~(deprecated) | `[]string`          | HTML source code                                                                              | true  | `["<a [^>]*href=\"index.html"]`                 | 
| **certIssuer**           | `string`            | SSL certificate issuer                                                                        | false | `"Let's Encrypt"`                               | 

## Patterns

---

Patterns are essentially JavaScript regular expressions written as strings, but with some additions.

### Quirks and pitfalls

- Because of the string format, the escape character itself must be escaped when using special characters such as the dot (`\\.`). Double quotes must be escaped only once (`\"`). Slashes do not need to be escaped (`/`).
- Flags are not supported. Regular expressions are treated as case-insensitive.
- Capture groups (`()`) are used for version detection. In other cases, use non-capturing groups (`(?:)`).
- Use start and end of string anchors (`^` and `$`) where possible for optimal performance.
- Short or generic patterns can cause applications to be identified incorrectly. Try to find unique strings to match.

### Tags

Tags (a non-standard syntax) can be appended to patterns (and implies and excludes, separated by `\\;`) to store additional information.


| Tag            | Description                                                                                                                                              | Example                                             | 
|----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------|
| **confidence** | Indicates a less reliable pattern that may cause false positives. The aim is to achieve a combined confidence of 100%. Defaults to 100% if not specified | `"js": {"Mage": "\\;confidence:50"}`                | 
| **version**    | Gets the version number from a pattern match using a special syntax                                                                                      | `"scriptSrc": "jquery-([0-9.]+)\.js\\;version:\\1"` | 


### Version syntax

Application version information can be obtained from a pattern using a capture group. A condition can be evaluated using the ternary operator (`?:`).


| Example   | Description                                                      | 
|-----------|------------------------------------------------------------------|
| `\\1`     | Returns the first match                                          | 
| `\\1?a:`  | Returns a if the first match contains a value, nothing otherwise | 
| `\\1?a:b` | Returns a if the first match contains a value, b otherwise       | 
| `\\1?:b`  | Returns nothing if the first match contains a value, b otherwise | 
| `foo\\1`  | Returns foo with the first match appended                        | 


## Types

### DOM

Dom data type can be either:

- `[]string`: list of [query selectors](https://developer.mozilla.org/en-US/docs/Web/API/Document/querySelectorAll)

- `JSON Object`: **key** is the [query selector](https://developer.mozilla.org/en-US/docs/Web/API/Document/querySelectorAll) & **value** is an object that requires the following structure:
  - value requirements:
    1. {"attributes": {string: `pattern`}}
       - `pattern` can be a regex
       - `pattern` is compatible with [tags](#Tags)
       - example: {"attributes": {"href": "pattern", "src": "pattern"}}
    2. {"properties": {string: `pattern`}}
       - `pattern` can be a regex
       - `pattern` is compatible with [tags](#Tags)
       - example: {"attributes": {"href": "pattern", "src": "pattern"}}
    3. {"text": `pattern`}
       - `pattern` can be a regex
       - `pattern` is compatible with [tags](#Tags)
    4. {"exists": ""}
       - `value` is an empty string
       - `empty string` is compatible with [tags](#Tags)

```json5
// example []string
{
  "dom": ["img[src*='example']", "form[action*='example.com/forms/']"]
}
```
```json5
// example JSON Object
{
  "dom": {
    "link[href*='fonts.g']": {
      "attributes": {
        "href": "fonts\\.(?:googleapis|google|gstatic)\\.com"
      },
      "properties": {
        "container": ""
      }, 
      "text": "GLPI\\s+version\\s+([\\d\\.]+)\\;version:\\1"
    },
    "style[data-href*='fonts.g']": {
      "attributes": {
        "data-href": "fonts\\.(?:googleapis|google|gstatic)\\.com"
      },
      "exists": "\\;confidence:50"
    }
  }
}
```

### Pricing

Cost indicator (based on a typical plan or average monthly price) and available pricing models. For paid products only.

**One of**:

- `low`: Less than US $100/mo
- `mid`: Between US \$100-\$1,000/mo
- `high`: More than US \$1,000/mo

**Plus any of**:

- `freemium`: Free plan available
- `onetime`: One-time payments accepted
- `recurring`: Subscriptions available
- `poa`: Price on asking
- `payg`: Pay as you go (e.g. commissions or usage-based fees)
