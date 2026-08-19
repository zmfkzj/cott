# page-build

## Purpose
Validate a page source and build its output path and deterministic HTML.

## Key points
- A slug must consist of nonempty lowercase-ASCII-letter-or-digit segments joined by single hyphens; return a slug error before an empty title. The successful path is `<slug>/index.html`.
- Render the title as `h1` and each nonempty body line as a `p` in input order, escaping `&`, angle brackets, and both quotation marks as HTML character references.
