# Contributing

WebAppAnalyzer is an [GPLv3 licensed](https://github.com/enthec/webappanalyzer/blob/master/LICENSE), open source project written in JavaScript. Anyone is welcome to contribute.

## Getting started

To get started, see the [README](https://github.com/enthec/webappanalyzer/blob/master/README.md).

## Adding a new technology

Wappalyzer uses [regular expressions](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Regular_Expressions) to fingerprint technologies. Refer to the [specification](https://github.com/enthec/webappanalyzer/blob/master/README.md#specification) for detail.

- Add a new block to [`src/technologies/*.json`](https://github.com/enthec/webappanalyzer/blob/master/src/technologies). The filename should match the first letter of the technology name (a-z). Use `_.json` if the first character is a number or symbol.

When creating a pull request, include ten or more links to websites that use the application.

## Adding a new category

Please [open an issue on GitHub](https://github.com/enthec/webappanalyzer/issues) first to discuss the need for a new category.

To add a category, edit [`src/categories.json`](/src/categories.json). You may use the English category name in all of them.

## Adding a new feature

Please [open an issue on GitHub](https://github.com/enthec/webappanalyzer/issues) first. New features and large changes are rarely accepted without prior discussion.
