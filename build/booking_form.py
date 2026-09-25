"""Multi-step booking form markup. Imported by build.py."""

def render(e, practices, phone_tel, phone_display, email, booking_url=''):
    if booking_url:
        return ('<div class="form book rv"><h3>Book a strategy call</h3><p class="form-sub">Pick a time for a free 30-minute call.</p>'
                f'<iframe class="bk-embed" src="{e(booking_url)}" title="Book a strategy call with Vincere" loading="lazy"></iframe></div>')
    questions = [
        ('monthly_budget', 'What is your monthly marketing budget?', ['Under $2k', '$2k to $5k', '$5k to $10k', '$10k to $25k', '$25k to $50k', '$50k+']),
        ('current_spend', 'What do you spend on marketing each month right now?', ['Nothing yet', 'Under $2k', '$2k to $5k', '$5k to $10k', '$10k to $25k', '$25k to $50k', '$50k+']),
        ('attorneys', 'How many attorneys are at your firm?', ['Solo', '2 to 5', '6 to 15', '16 to 50', '50+']),
        ('avg_case_value', 'What is your average case value or fee?', ['Under $2.5k', '$2.5k to $10k', '$10k to $50k', '$50k+', 'Contingency']),
        ('practice_area', 'What is your primary practice area?', [lab for _, lab in practices] + ['Other']),
    ]
    n = len(questions)
    qs = ''
    for i, (name, q, opts) in enumerate(questions):
        o = ''.join(f'<label class="bk-opt"><input type="radio" name="{name}" value="{e(x)}" required><span>{e(x)}</span></label>' for x in opts)
        wide = ' bk-opts-wide' if len(opts) > 8 else ''
        qs += (f'<div class="bk-screen" data-s="q" hidden><p class="bk-qn">Question {i+1} of {n}</p><h4 class="bk-q">{e(q)}</h4>'
               f'<div class="bk-opts{wide}">{o}</div><button type="button" class="bk-back">&lsaquo; Back</button></div>\n')
    return f'''<form class="form book rv" name="vincere-booking" method="POST" action="/thanks.html" data-netlify="true" netlify-honeypot="fax" novalidate>
        <input type="hidden" name="form-name" value="vincere-booking">
        <input type="hidden" name="call_time"><input type="hidden" name="call_iso"><input type="hidden" name="timezone">
        <p class="hp"><label>Fax <input name="fax" tabindex="-1" autocomplete="off"></label></p>
        <div class="bk-prog" aria-hidden="true"><span></span></div>
        <div class="bk-screen" data-s="cal">
          <h3>Book a strategy call</h3>
          <p class="form-sub">Pick a time for a free 30-minute call. We will walk through your market and your numbers. No obligation.</p>
          <div class="bk-step">
            <div class="bk-cal">
              <div class="bk-head"><button type="button" class="bk-nav bk-prev" aria-label="Previous month">&lsaquo;</button><b class="bk-month" aria-live="polite"></b><button type="button" class="bk-nav bk-next" aria-label="Next month">&rsaquo;</button></div>
              <div class="bk-dow"><span>Mo</span><span>Tu</span><span>We</span><span>Th</span><span>Fr</span><span>Sa</span><span>Su</span></div>
              <div class="bk-days"></div>
            </div>
            <div class="bk-times"><p class="bk-times-h">Available times</p><div class="bk-slots"><p class="bk-empty"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>Pick a day to see open times.</p></div><p class="bk-tz"></p></div>
          </div>
        </div>
        <div class="bk-screen" data-s="info" hidden>
          <div class="bk-pick"><div><small>Your call</small><b class="bk-when"></b></div><button type="button" class="bk-change">Change</button></div>
          <h4 class="bk-q">Tell us who you are.</h4>
          <div class="f2">
            <div class="f"><label for="b-name">Full name</label><input id="b-name" name="name" required autocomplete="name"></div>
            <div class="f"><label for="b-firm">Firm name</label><input id="b-firm" name="firm" required autocomplete="organization"></div>
          </div>
          <div class="f2">
            <div class="f"><label for="b-email">Email</label><input id="b-email" name="email" type="email" required autocomplete="email"></div>
            <div class="f"><label for="b-phone">Phone</label><input id="b-phone" name="phone" type="tel" required autocomplete="tel"></div>
          </div>
          <button type="button" class="btn btn-orange btn-arr bk-next-step">Continue</button>
          <button type="button" class="bk-back">&lsaquo; Back</button>
        </div>
{qs}        <div class="bk-screen bk-done" data-s="done" hidden>
          <div class="bk-check" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg></div>
          <h3>Your meeting is booked.</h3>
          <p class="bk-done-when"></p>
          <p class="bk-done-mail">We just sent a calendar invite to <b class="bk-done-email"></b>.</p>
          <p class="form-fine">Need to change it? Call <a href="tel:{phone_tel}">{phone_display}</a> or reply to the invite.</p>
        </div>
        <div class="bk-err" role="alert" hidden><p>Something went wrong sending your booking. Please try again, or call <a href="tel:{phone_tel}">{phone_display}</a> and we will book it for you.</p><button type="button" class="btn btn-orange bk-retry">Try again</button><button type="button" class="bk-back bk-err-back">&lsaquo; Back</button></div>
        <noscript><p class="form-sub">Booking needs JavaScript. Call <a href="tel:{phone_tel}">{phone_display}</a> or email <a href="mailto:{email}">{email}</a> to book.</p></noscript>
      </form>'''
