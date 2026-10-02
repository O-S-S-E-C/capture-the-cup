(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var nav = document.querySelector('.navbar .navbar-brand, nav.navbar .navbar-brand');
    if (nav && !nav.querySelector('.ct-event-label')) {
      var label = document.createElement('span');
      label.className = 'ct-event-label';
      label.textContent = 'CAPTURE THE CUP';
      nav.appendChild(label);
    }

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
