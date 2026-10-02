(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.ct-event-label').forEach(function (label) {
      label.remove();
    });

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
