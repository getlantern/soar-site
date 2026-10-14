# soar.lantern.io

The website for [Soar](https://github.com/getlantern/soar), the DNS tunnel for networks that censor
everything except DNS: one static `index.html` with no build step, served by Cloudflare Pages.

Cloudflare Pages builds this repository straight from GitHub: every push to `main` deploys it, with
no build command and the repository root as the output directory. Pull requests get preview
deployments. `_headers` sets the response headers.

To preview locally, open `index.html` in a browser, or run `python3 -m http.server`.

The site moved here from `site/` in [getlantern/soar](https://github.com/getlantern/soar), with its
history.
