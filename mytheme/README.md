# mytheme — Capture the Cup CTFd theme

Based on CTFd's stock `core` theme, with two additions layered on top:

- `static/custom/css/capture-the-cup.css` — event color palette, card/button restyle
- `static/custom/js/capture-the-cup.js` — navbar event badge + card entrance animation

Both are linked directly in `templates/base.html` (search for "capture-the-cup"
to find the two added lines), so they load on every page without touching
CTFd's admin settings.

## Using the hero banner block

The CSS includes an optional `.ct-capture-hero` block (big event title banner).
It isn't wired into any template automatically. To use it, go to
**Admin -> Pages -> index** in CTFd and paste something like:

    <div class="ct-capture-hero">
      <h1>Capture the Cup</h1>
      <p>Welcome to the event.</p>
    </div>

## Optional: event logo/banner image

Drop a file named `capture-the-cup.png` into `static/custom/img/` if you want
the hero block's background photo to show. Safe to skip — the gradient still
renders fine without it.

## Deploying

This folder is meant to be bind-mounted into the running ctfd container at
`/opt/CTFd/CTFd/themes/mytheme` (see the cloud-init script / docker-compose
override). After deploying, select "mytheme" in
**Admin -> Config -> Theme**.
