'use strict';
/* Kessler & Associates — site behaviour. No dependencies. */

/* FAQ disclosure ------------------------------------------------------- */
document.addEventListener('click', function (e) {
  var q = e.target.closest('.faq-q');
  if (!q) return;
  var item = q.closest('.faq-item');
  var open = item.classList.toggle('is-open');
  q.setAttribute('aria-expanded', String(open));
});

/* Review rail --------------------------------------------------------- */
function railScroll(dir) {
  var rail = document.getElementById('reviewRail');
  if (!rail) return;
  var card = rail.querySelector('.review');
  var step = card ? card.getBoundingClientRect().width + 26 : 340;
  rail.scrollBy({ left: dir * step, behavior: 'smooth' });
}

/* Intake forms -------------------------------------------------------- */
function handleIntake(formId, okId) {
  var form = document.getElementById(formId);
  if (!form) return;
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    if (!form.reportValidity()) return;
    var ok = document.getElementById(okId);
    if (ok) {
      ok.classList.add('is-on');
      ok.textContent = 'Received. An attorney reviews this personally and calls within 60 minutes.';
    }
    form.querySelector('button[type="submit"]').disabled = true;
  });
}
handleIntake('intakeTop', 'intakeTopOk');
handleIntake('intakeMain', 'intakeMainOk');

/* Case screener ------------------------------------------------------- */
(function () {
  var panel = document.getElementById('screenerPanel');
  var toggle = document.getElementById('screenerToggle');
  if (!panel || !toggle) return;

  var log = document.getElementById('screenerLog');
  var opts = document.getElementById('screenerOpts');

  var script = [
    { ask: 'What kind of incident was it?',
      opts: ['Vehicle collision', 'Construction site', 'Medical care', 'Fall on property', 'A death in the family'] },
    { ask: 'When did it happen?',
      opts: ['Within the last week', 'Within the last year', 'One to three years ago', 'Longer than that'] },
    { ask: 'Have you been treated by a doctor for it?',
      opts: ['Yes, and still treating', 'Yes, treatment finished', 'Not yet'] },
    { ask: 'Has any insurer offered you money?',
      opts: ['No offer yet', 'An offer was made', 'I already signed something'] }
  ];
  var step = -1;

  function say(who, text) {
    var el = document.createElement('div');
    el.className = 'msg from-' + who;
    el.textContent = text;
    log.appendChild(el);
    log.scrollTop = log.scrollHeight;
  }

  function render() {
    opts.textContent = '';
    if (step >= script.length) {
      say('firm', 'That is enough for an attorney to give you a straight answer. Nothing here is legal advice — the call is where you get that, and it is free.');
      var call = document.createElement('a');
      call.className = 'btn btn--seal btn--block';
      call.href = 'tel:+12125550380';
      call.textContent = 'Call (212) 555-0380';
      var form = document.createElement('a');
      form.className = 'btn btn--line btn--block';
      form.href = 'authority-site.html#contact';
      form.textContent = 'Send it in writing instead';
      opts.appendChild(call);
      opts.appendChild(form);
      return;
    }
    say('firm', script[step].ask);
    script[step].opts.forEach(function (label) {
      var b = document.createElement('button');
      b.type = 'button';
      b.textContent = label;
      b.addEventListener('click', function () {
        say('you', label);
        step += 1;
        render();
      });
      opts.appendChild(b);
    });
  }

  function open() {
    panel.classList.add('is-on');
    panel.setAttribute('aria-hidden', 'false');
    toggle.setAttribute('aria-expanded', 'true');
    if (step === -1) {
      step = 0;
      say('firm', 'Four questions, then we tell you whether this is worth an attorney’s time. No name required.');
      render();
    }
  }
  function close() {
    panel.classList.remove('is-on');
    panel.setAttribute('aria-hidden', 'true');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.focus();
  }

  toggle.addEventListener('click', function () {
    panel.classList.contains('is-on') ? close() : open();
  });
  var x = document.getElementById('screenerClose');
  if (x) x.addEventListener('click', close);
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && panel.classList.contains('is-on')) close();
  });
})();
