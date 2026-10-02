# mytheme — Capture the Cup CTFd theme

Light theme (white/pale-blue background, dark text everywhere for contrast),
colors pulled from the event logo: red #E8384F, blue #2FA3F7. No navy.

Based on CTFd's stock `core` theme, with these additions layered on top:

- `static/custom/css/capture-the-cup.css` — palette, card/button/table restyle, hero styles
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

This folder is meant to be bind-mounted into the running ctfd container at
`/opt/CTFd/CTFd/themes/mytheme` (see the cloud-init script / docker-compose
override). After deploying, select "mytheme" in
**Admin -> Config -> Theme**.
