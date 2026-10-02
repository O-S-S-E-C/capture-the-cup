# Capture the Cup CTFd theme

An editable CTFd theme repository for the Capture the Cup event.

## Structure

- `templates/` — page HTML and layout overrides.
- `static/custom/css/capture-the-cup.css` — dark broadcast-style visual design.
- `static/custom/js/capture-the-cup.js` — optional navbar label and card entrance animation.
- `static/custom/img/` — place the event logo here later.
- `static/assets/` — reserved for CTFd's compiled theme assets.

## Deployment

Mount this folder into the CTFd container as:

```yaml
- /srv/theme-repo/mytheme:/opt/CTFd/CTFd/themes/mytheme:ro
```

Then select `mytheme` in **Admin → Config → Theme**.

The custom CSS and JavaScript are linked directly from `static/custom/`; they are intentionally not passed through CTFd's Vite manifest system. This prevents CTFd from changing them into incorrect paths such as `static/static/*.min.css`.

## Updating later

The Git repository is the source of truth. After pushing changes:

```bash
cd /srv/theme-repo/mytheme
sudo git pull --ff-only
cd /srv/ctfd
sudo docker compose restart ctfd
```

Template changes usually appear after restarting CTFd. If CSS or JavaScript is cached, use a hard refresh or add/change a query-string version to the links in `templates/base.html`.

## Adding the logo later

Place the logo at:

```text
static/custom/img/capture-the-cup-logo.png
```

You can then reference it in a CTFd page or template with:

```html
<img src="/themes/mytheme/static/custom/img/capture-the-cup-logo.png" alt="Capture the Cup">
```
