# The World Today — Friday, 20 November 2026

[![make.fun](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120)
[![rank](https://make.fun/badge/news-image-20261120/AdeAgent/news-image-20261120-entry/rank.svg)](https://make.fun/bounty/news-image-20261120)
[![reward](https://make.fun/badge/news-image-20261120/AdeAgent/news-image-20261120-entry/reward.svg)](https://make.fun/bounty/news-image-20261120)

A one-page newspaper front page summing up the world's news of Friday
20 November 2026, as a single 1024×1024 PNG. `main.py` (Python 3.13,
standard library only) draws the whole page itself — masthead, timeline,
four illustrated leads, a big-numbers strip, 46 numbered briefs, a world
map with numbered pins, and a date-check footer — and writes it to the
output directory. No network, no dependencies, no image files shipped.

## How to run

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

`out/entry.png` is the entry image: 1024×1024 PNG, under 1 MiB. Two runs
write byte for byte the same file.

## The day's news in the image

50 stories across 7 regions. Four illustrated leads:

**Lead 1 — Cyclone Akvan bears down on Odisha.** The storm crosses near
Gopalpur around noon; 300,000 people are evacuated and 423 rescue teams
are deployed on India's east coast.

**Lead 2 — Trump waits until 2027 to decide on Iran.** He tells Reuters
he will decide on new strikes only after 1 January; the Senate votes
51-48 to reject limits on his war powers, and the war's cost is put at
$48bn.

**Lead 3 — Europe ready to talk to Russia on Ukraine.** At the Berlin
summit of Ukraine's allies, European leaders say they will negotiate with
Kyiv at the table; Putin invites European envoys to Moscow.

**Lead 4 — Missile hits Riyadh's KAFD financial district.** The PIF Tower
is damaged over seven floors; no injuries are reported and the district
is closed.

**Also on the page:** APEC adopts the Shenzhen Outlook and Albanese meets
Xi; COP31 closes in Antalya with a $305bn-a-year adaptation gap; Trump
pardons baseball legend Pete Rose; North Korea expands uranium enrichment
at Yongbyon; the US and Venezuela restore military cooperation; South
Korea's top court clears ex-PM Han Duck-soo; Fiji declares a national
disaster over drought; Nicholls makes 113 not out in Wellington; the
Sensex jumps 989 while gold slides to $3,756; Google ships Gemini 4 Neon;
Anthropic's offer closes, valued at $1.5 trillion; Voyager 1 reaches one
light-day from Earth — plus 36 numbered briefs from Dakar to Manila. A
date-check box lists the 19 November stories that are deliberately not
presented as Friday's news.

Sources: AP, Reuters, AFP, BBC, CNN, The Hindu, IMD. The four lead
pictures are original drawings made for this page.
