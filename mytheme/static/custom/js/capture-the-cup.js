/* Optional Capture the Cup enhancement script.
 * This is intentionally dependency-free and safe to remove if you only want CSS.
 */
(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    // Add a small event label to the navbar without changing CTFd navigation.
    var nav = document.querySelector('.navbar .navbar-brand, nav.navbar .navbar-brand');
    if (nav && !nav.querySelector('.ct-event-label')) {
      var label = document.createElement('span');
      label.className = 'ct-event-label';
      label.textContent = 'CAPTURE THE CUP';
      label.style.cssText = [
        'display:inline-block',
        'margin-left:.65rem',
        'padding:.18rem .5rem',
        'border:1px solid rgba(54,169,255,.55)',
        'border-radius:999px',
        'color:#36a9ff',
        'font-size:.62rem',
        'font-weight:800',
        'letter-spacing:.08em',
        'vertical-align:middle'
      ].join(';');
      nav.appendChild(label);
    }

    // Give challenge cards a subtle staggered entrance effect.
    var cards = document.querySelectorAll('.challenge-button, .list-group-item, .card');
    cards.forEach(function (card, index) {
      card.style.animation = 'ct-card-in .42s ease both';
      card.style.animationDelay = Math.min(index * 35, 350) + 'ms';
    });

    if (!document.getElementById('ct-card-animation')) {
      var style = document.createElement('style');
      style.id = 'ct-card-animation';
      style.textContent = '@keyframes ct-card-in{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}';
      document.head.appendChild(style);
    }
  });
})();
