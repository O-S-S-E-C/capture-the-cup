# mytheme — Capture the Cup CTFd theme

Dark arena theme with a navy background, high contrast text, and cyan and red
accents pulled from the event logo.

Based on CTFd's stock `core` theme, with these additions layered on top:

- `static/custom/css/capture-the-cup.css` — tokenized design system and page styling
- `static/custom/js/capture-the-cup.js` — navbar event badge + card entrance animation
- `assets/img/logo1.png` — the event logo source, copied to `static/img/logo1.png` by Vite
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

This folder is meant to be bind-mounted into the running CTFd container at
`/opt/CTFd/CTFd/themes/mytheme` (see the cloud-init script / docker-compose
override). After deploying, select "mytheme" in
**Admin -> Config -> Theme**.
