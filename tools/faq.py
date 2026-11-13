#!/usr/bin/env python3
"""The FAQ: one list that generates both the visible FAQ section and its
schema.org FAQPage markup in index.html, so the two can't drift apart.

Edit FAQ below, then run: python3 tools/faq.py
Answers are HTML (links allowed); the JSON-LD gets the same text with tags
stripped.
"""
import html
import json
import re
from pathlib import Path

SITE = "https://soar.lantern.io/"

FAQ = [
    ("What is Soar?",
     "Soar is an open-source DNS tunnel from <a href=\"https://lantern.io\">Lantern</a> "
     "for networks that censor everything except DNS. It carries TCP connections as DNS "
     "queries and answers through ordinary recursive resolvers (the ISP's, public ones, "
     "and in-country ones it discovers) to a server that is the authoritative name server "
     "for a zone delegated to it."),
    ("How does a DNS tunnel get past censorship?",
     "A censor can block an IP address, a TLS fingerprint or a whole protocol, but "
     "blocking the resolvers that every phone, bank and government site depends on is "
     "much harder. Soar's client seals data into the names it looks up under its zone, "
     "resolvers pass those queries on to Soar's server, and the server's answers carry "
     "data back. See <a href=\"#how\">how it works</a>."),
    ("How is Soar different from dnstt and VayDNS?",
     "dnstt and VayDNS are simple, but they use a single resolver and recover slowly "
     "from loss. Soar sends on every working resolver at once, weighted by how each one "
     "is performing, and drops a dead one without the user noticing. Retransmissions "
     "are re-cut to fit whichever resolver they go out on, and the server resends "
     "exactly what the client reports lost instead of waiting out a timer."),
    ("How is Soar different from slipstream and MasterDnsVPN?",
     "slipstream runs QUIC over DNS and copes with loss, but in Soar's benchmarks it "
     "can't connect when a resolver truncates answers, when some resolvers are dead, or "
     "when UDP is blocked, and its Rust implementation is archived. MasterDnsVPN and its "
     "forks, StormDNS and CottenDNS, handle resolvers well but share one static key "
     "among all clients, and on impaired networks can take tens of seconds to connect. Soar connected in 0.3 to 1.4 "
     "seconds in every benchmark network, and each session starts with its own key "
     "exchange."),
    ("How fast is Soar?",
     "In an emulator that puts eight tunnels behind the same impaired resolvers, Soar "
     "fetched 100&nbsp;KB at 476&nbsp;KB/s through clean resolvers, 124&nbsp;KB/s on a "
     "realistic mobile network and 130&nbsp;KB/s in a Russia-like network, and had the "
     "highest throughput in 7 of 9 networks. These are emulator results; field "
     "measurements from inside Iran, Russia and China come next. See the "
     "<a href=\"#benchmarks\">benchmarks</a>."),
    ("Does Soar work in Iran, Russia and China?",
     "It is built for how each one breaks DNS: AAAA answers where resolvers filter TXT "
     "and short names where they drop long ones, as in Iran; DNS over TCP port 53 with "
     "RFC&nbsp;7766 pipelining where UDP to public resolvers is intercepted, as in "
     "Russia; and authenticated answers, so forged ones are ignored, as in China. It "
     "bundles in-country resolver lists for all three. So far it has been measured in an "
     "emulator that reproduces each network, not yet in the field."),
    ("Can a censor read or forge Soar's traffic?",
     "Every session starts with an ephemeral X25519 key exchange that the server signs "
     "with its Ed25519 key, and each direction is sealed with ChaCha20-Poly1305 under its "
     "own key, so recorded traffic stays sealed even if the server's long-term key leaks "
     "later. A forged answer can't authenticate, so the client drops it and waits for the "
     "real one. Clients ship only the server's public key, so there's no shared secret to "
     "pull out of an app."),
    ("How do I run a Soar server?",
     "Delegate a zone, such as <code>t.example.com</code>, to your host with an NS "
     "record, generate a key pair with <code>soar-server keygen</code>, and run "
     "<code>soar-server</code> for that zone on port 53. Clients need the zone, the "
     "server's public key and some resolvers. By default the server dials only public "
     "addresses on ports 80 and 443. See <a href=\"#start\">Get started</a>."),
    ("Is there a Rust implementation?",
     "Yes. <a href=\"https://github.com/getlantern/soar-rs\">soar-rs</a> is a "
     "wire-compatible Rust client and server, still early work. Both implementations pass "
     "the same byte-exact test vectors from the spec, CI runs each language's client "
     "against the other's server, and the Go and Rust servers take the same flags and "
     "key files."),
    ("How does Lantern use Soar?",
     "Soar is the last-resort transport in <a href=\"https://kindling.lantern.io\">kindling</a>, "
     "Lantern's open-source library for getting an app's first requests through a "
     "censored network. Kindling dials it only when every faster transport, such as "
     "domain fronting, has failed. Any Go app can do the same with "
     "<code>kindling.WithDNSTunnel</code>."),
    ("Is Soar open source?",
     "Yes, under the Apache License 2.0. The reference implementation, in Go, and the "
     "protocol <a href=\"https://github.com/getlantern/soar/blob/main/SPEC.md\">spec</a> "
     "are at <a href=\"https://github.com/getlantern/soar\">github.com/getlantern/soar</a>. "
     "Its bundled Iran resolver and range lists come from KevinNet DNS, under the MIT "
     "license."),
    ("Is Soar ready for production?",
     "Not yet. Soar is pre-release: the protocol may still change and has no "
     "compatibility promise."),
    ("Who makes Soar?",
     "The <a href=\"https://lantern.io\">Lantern</a> team, who make Lantern, a free app "
     "for getting past internet censorship. You can "
     "<a href=\"https://lantern.io/download\">download Lantern</a> from lantern.io."),
    ("Why is it called Soar?",
     "Every DNS zone begins with an SOA record, its start of authority. Soar's server is "
     "the authority for its zone, where every query ends up, whichever resolver it passed "
     "through. Add an r and the authority soars over the wall."),
]


def strip(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s)).replace(" ", " ")


def faq_html() -> str:
    items = []
    for q, a in FAQ:
        slug = re.sub(r"[^a-z0-9]+", "-", q.lower()).strip("-")
        items.append(
            f'      <div class="qa" id="{slug}">\n'
            f'        <h3>{html.escape(q)}</h3>\n'
            f'        <p>{a}</p>\n'
            f'      </div>'
        )
    return "\n".join(items)


def faq_jsonld() -> dict:
    return {
        "@type": "FAQPage",
        "@id": SITE + "#faq",
        "isPartOf": {"@id": SITE + "#webpage"},
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": strip(a)}}
            for q, a in FAQ
        ],
    }


def graph() -> dict:
    org = {
        "@type": "Organization",
        "@id": "https://lantern.io/#organization",
        "name": "Lantern",
        "legalName": "Brave New Software Project, Inc.",
        "url": "https://lantern.io",
        "sameAs": ["https://github.com/getlantern"],
    }
    return {
        "@context": "https://schema.org",
        "@graph": [
            org,
            {
                "@type": "WebSite",
                "@id": SITE + "#website",
                "url": SITE,
                "name": "Soar",
                "publisher": {"@id": org["@id"]},
                "inLanguage": "en",
            },
            {
                "@type": "WebPage",
                "@id": SITE + "#webpage",
                "url": SITE,
                "name": "Soar: a fast DNS tunnel for censored networks, from Lantern",
                "isPartOf": {"@id": SITE + "#website"},
                "about": {"@id": SITE + "#software"},
                "primaryImageOfPage": SITE + "og.png",
                "inLanguage": "en",
            },
            {
                "@type": "SoftwareSourceCode",
                "@id": SITE + "#software",
                "name": "Soar",
                "description": strip(FAQ[0][1]),
                "codeRepository": "https://github.com/getlantern/soar",
                "programmingLanguage": ["Go", "Rust"],
                "license": "https://www.apache.org/licenses/LICENSE-2.0",
                "url": SITE,
                "author": {"@id": org["@id"]},
                "keywords": "DNS tunnel, censorship circumvention, recursive resolvers, "
                            "dnstt, slipstream, Iran, Russia, China, kindling",
            },
            faq_jsonld(),
        ],
    }


def main() -> None:
    p = Path(__file__).resolve().parent.parent / "index.html"
    s = p.read_text()
    s = re.sub(r"(<!-- faq:start -->).*?(\n[ \t]*<!-- faq:end -->)",
               lambda m: m.group(1) + "\n" + faq_html() + m.group(2), s, flags=re.S)
    ld = json.dumps(graph(), ensure_ascii=False, indent=1)
    s = re.sub(r'(<script type="application/ld\+json">\n).*?(\n</script>)',
               lambda m: m.group(1) + ld + m.group(2), s, flags=re.S)
    p.write_text(s)


if __name__ == "__main__":
    main()
