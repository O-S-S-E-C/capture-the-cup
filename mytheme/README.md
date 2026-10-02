# mytheme — Capture the Cup CTFd theme

Dark broadcast-style theme with a navy/charcoal arena background, bright cyan,
red accents, and colors pulled from the event logo.

Based on CTFd's stock `core` theme, with these additions layered on top:

- `static/custom/css/capture-the-cup.css` — logo-inspired palette, dark surfaces, card/button/table restyle, hero styles
- `static/custom/js/capture-the-cup.js` — navbar event badge + card entrance animation
- `static/custom/img/capture-the-cup-logo.png` — the event logo
- `static/custom/hero-snippet.html` — ready-to-paste homepage hero HTML

The CSS/JS are linked directly in `templates/base.html` (search for
"capture-the-cup" to find the two added lines), so they load on every page
without touching CTFd's admin settings.

## Setting the homepage hero

Go to **Admin -> Pages -> index** in CTFd and paste the contents of
`static/custom/hero-snippet.html` into the page editor (switch it to raw
HTML / source mode first). It renders the logo, title, a welcome line, and a
button to the challenges page. Edit the text directly in that admin page
whenever you want to change the welcome message.

## Deploying

This folder is meant to be bind-mounted into the running ctfd container at
`/opt/CTFd/CTFd/themes/mytheme` (see the cloud-init script / docker-compose
override). After deploying, select "mytheme" in
**Admin -> Config -> Theme**.
