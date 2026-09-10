(function () {
  'use strict';

  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('primary-nav');

  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      toggle.textContent = open ? 'Close' : 'Menu';
    });

    nav.addEventListener('click', function (e) {
      if (e.target.tagName === 'A' && window.innerWidth <= 820) {
        nav.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
        toggle.textContent = 'Menu';
      }
    });
  }

  /* Enquiry forms → Vercel API (/api/send-enquiry). Recipient Gmail stays server-side only. */
  var ENQUIRY_ENDPOINT = '/api/send-enquiry';
  var forms = document.querySelectorAll('form[data-enquiry]');

  Array.prototype.forEach.call(forms, function (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();

      var status = form.querySelector('.form-status');
      var btn = form.querySelector('button[type="submit"]');
      var get = function (n) {
        var el = form.elements[n];
        return el ? String(el.value).trim() : '';
      };

      var name = get('name');
      var phone = get('phone');

      if (!name || !phone) {
        if (status) {
          status.style.color = '#C0392B';
          status.textContent = 'Please add your name and phone number so we can call you back.';
        }
        return;
      }

      if (btn) {
        btn.disabled = true;
        btn.textContent = 'Sending…';
      }
      if (status) {
        status.style.color = '';
        status.textContent = 'Sending your enquiry…';
      }

      var payload = {
        name: name,
        phone: phone,
        city: get('city'),
        course: get('course'),
        education: get('education'),
        message: get('message'),
        page: document.title || location.pathname
      };
      var visitorEmail = get('email');
      if (visitorEmail) payload.email = visitorEmail;

      fetch(ENQUIRY_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(payload)
      })
        .then(function (res) {
          return res.json().then(function (json) {
            return { httpOk: res.ok, json: json };
          });
        })
        .then(function (result) {
          var json = result.json || {};
          if (result.httpOk && json.ok) {
            if (status) {
              status.style.color = '';
              status.textContent = 'Thanks, ' + name.split(' ')[0] + '. We received your enquiry and will call you back the same working day.';
            }
            form.reset();
          } else {
            if (status) {
              status.style.color = '#C0392B';
              status.textContent = json.error || 'Could not send. Please call or WhatsApp 77090 99599.';
            }
          }
        })
        .catch(function () {
          if (status) {
            status.style.color = '#C0392B';
            status.textContent = 'Could not send. Please call or WhatsApp 77090 99599.';
          }
        })
        .finally(function () {
          if (btn) {
            btn.disabled = false;
            btn.textContent = 'Send my enquiry';
          }
        });
    });
  });

  var counters = document.querySelectorAll('[data-count]');
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (counters.length && 'IntersectionObserver' in window && !reduced) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        var target = parseInt(el.getAttribute('data-count'), 10);
        var suffix = el.getAttribute('data-suffix') || '';
        var start = null;

        function tick(ts) {
          if (!start) start = ts;
          var p = Math.min((ts - start) / 1100, 1);
          var eased = 1 - Math.pow(1 - p, 3);
          el.textContent = Math.round(target * eased) + suffix;
          if (p < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
        io.unobserve(el);
      });
    }, { threshold: 0.4 });

    Array.prototype.forEach.call(counters, function (c) { io.observe(c); });
  } else {
    Array.prototype.forEach.call(counters, function (c) {
      c.textContent = c.getAttribute('data-count') + (c.getAttribute('data-suffix') || '');
    });
  }

  var y = document.querySelectorAll('[data-year]');
  Array.prototype.forEach.call(y, function (el) {
    el.textContent = new Date().getFullYear();
  });
})();
