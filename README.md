# soar.lantern.io

The website for [Soar](https://github.com/getlantern/soar), the DNS tunnel for networks that censor
everything except DNS: one static `index.html` with no build step, served by Cloudflare Pages.

Cloudflare Pages builds this repository straight from GitHub: every push to `main` deploys it, with
no build command and the repository root as the output directory. Pull requests get preview
deployments. `_headers` sets the response headers.

To preview locally, open `index.html` in a browser, or run `python3 -m http.server`.

The site moved here from `site/` in [getlantern/soar](https://github.com/getlantern/soar), with its
history.

## The FAQ and structured data

The FAQ lives in `tools/faq.py`, which writes both the visible FAQ section and the schema.org
`FAQPage` markup into `index.html`, so the two always say the same thing. To change a question or
answer, edit the list there and run `python3 tools/faq.py`. The same script writes the rest of the
JSON-LD graph (`Organization`, `WebSite`, `WebPage`, `SoftwareSourceCode`). Every answer should be
backed by this page or by the READMEs and spec in getlantern/soar and getlantern/soar-rs.

`og.png` is the 1200×630 link-preview image, a screenshot of `tools/og.html`. `robots.txt` and
`sitemap.xml` point crawlers at the one page, and `404.html` makes unknown paths return a real
404 instead of the home page.
