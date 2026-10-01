<script id="bk-js">
(function(){
  document.querySelectorAll('form.book').forEach(function(f){
    var days=f.querySelector('.bk-days');if(!days)return;
    var mon=f.querySelector('.bk-month'),prev=f.querySelector('.bk-prev'),next=f.querySelector('.bk-next');
    var slots=f.querySelector('.bk-slots'),th=f.querySelector('.bk-times-h'),tz=f.querySelector('.bk-tz');
    var screens=[].slice.call(f.querySelectorAll('.bk-screen')),bar=f.querySelector('.bk-prog span'),err=f.querySelector('.bk-err');
    var cur=0,label='';
    function show(i,quiet){
      cur=i;if(err)err.hidden=true;screens.forEach(function(s,j){s.hidden=j!==i;s.setAttribute('aria-hidden',String(j!==i));if('inert' in s)s.inert=j!==i});f.classList.toggle('bk-at0',i===0);
      var a=screens[i];a.classList.remove('bk-anim');void a.offsetWidth;a.classList.add('bk-anim');
      if(bar)bar.style.width=Math.round(100*i/(screens.length-1))+'%';
      var s=screens[i],r=f.getBoundingClientRect();
      if(!quiet&&(r.top<0||r.top>innerHeight*.6))f.scrollIntoView({behavior:'smooth',block:'start'});
      var inp=s.querySelector('input:not([type=hidden]):not([type=radio])');if(inp&&!quiet)inp.focus({preventScroll:true});
    }
    var zone='';try{zone=Intl.DateTimeFormat().resolvedOptions().timeZone||''}catch(e){}
    tz.textContent='30-minute call. Times shown in your time zone'+(zone?' ('+zone.replace(/_/g,' ')+')':'')+'.';
    var today=new Date();today.setHours(0,0,0,0);
    var first=new Date(today);first.setDate(first.getDate()+1);
    var last=new Date(today);last.setDate(last.getDate()+45);
    /* Joe's hours, US Eastern time: 30-minute calls starting on these times */
    var HOURS={1:[[9,0],[13,0]],2:[[10,0],[11,30]],3:[[9,0],[13,0]],4:[[15,0],[19,0]],5:[[9,0],[13,0],[15,0],[19,0]]};
    var etf=null;try{etf=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',hourCycle:'h23',year:'numeric',month:'numeric',day:'numeric',hour:'numeric',minute:'numeric'})}catch(e){}
    function etOffset(ms){if(!etf)return -5*3600e3;var p={};etf.formatToParts(new Date(ms)).forEach(function(x){p[x.type]=+x.value});return Date.UTC(p.year,p.month-1,p.day,p.hour%24,p.minute)-ms;}
    function etTime(d,h,mi){var g=Date.UTC(d.getFullYear(),d.getMonth(),d.getDate(),h,mi);var t=g-etOffset(g);return new Date(g-etOffset(t));}
    function slotsFor(d){var r=HOURS[d.getDay()]||[],out=[],now=Date.now()+2*3600e3;
      for(var k=0;k<r.length;k+=2){for(var m=r[k][0]*60+r[k][1];m<=r[k+1][0]*60+r[k+1][1];m+=30){var t=etTime(d,Math.floor(m/60),m%60);if(+t>now&&isFree(t))out.push(t);}}
      return out;}
    /* live availability from Joe's Google Calendar (busy blocks only) */
    var busy=null,busyState='idle',API='/.netlify/functions/calendar';
    function isFree(t){if(!busy)return true;var a=+t,b=a+30*60e3;for(var i=0;i<busy.length;i++){if(busy[i][0]<b&&busy[i][1]>a)return false}return true;}
    function loadBusy(done){busyState='loading';
      fetch(API+'?from='+encodeURIComponent(first.toISOString())+'&to='+encodeURIComponent(new Date(+last+864e5).toISOString()))
        .then(function(r){if(!r.ok)throw new Error(r.status);return r.json()})
        .then(function(j){busy=j&&j.busy||[]})
        .catch(function(){busy=null})
        .then(function(){busyState='done';draw();if(sel)times();if(done)done();});}
    function ok(d){return d>=first&&d<=last&&slotsFor(d).length>0;}
    var view=new Date(first.getFullYear(),first.getMonth(),1),sel=null;
    (function(){var c=0,d=new Date(first);while(d.getMonth()===first.getMonth()){if(ok(d))c++;d.setDate(d.getDate()+1);}if(c<5)view=new Date(first.getFullYear(),first.getMonth()+1,1);})();
    function fmt(d,o){return d.toLocaleDateString(undefined,o)}
    function draw(){
      mon.textContent=fmt(view,{month:'long',year:'numeric'});
      prev.disabled=view<=new Date(first.getFullYear(),first.getMonth(),1);
      next.disabled=new Date(view.getFullYear(),view.getMonth()+1,1)>last;
      days.innerHTML='';var lead=(new Date(view.getFullYear(),view.getMonth(),1).getDay()+6)%7;
      for(var i=0;i<lead;i++)days.appendChild(document.createElement('span'));
      var n=new Date(view.getFullYear(),view.getMonth()+1,0).getDate();
      for(var dd=1;dd<=n;dd++){(function(d){
        var b=document.createElement('button');b.type='button';b.className='bk-day';b.textContent=d.getDate();
        if(+d===+today)b.classList.add('today');
        if(ok(d)){b.classList.add('on');b.setAttribute('aria-label',fmt(d,{weekday:'long',month:'long',day:'numeric'}));
          if(sel&&+d===+sel)b.classList.add('sel');
          b.addEventListener('click',function(){sel=d;draw();times();});}
        else{b.disabled=true;}
        days.appendChild(b);})(new Date(view.getFullYear(),view.getMonth(),dd));}
    }
    function times(){
      th.textContent=fmt(sel,{weekday:'long',month:'long',day:'numeric'});slots.innerHTML='';
      if(busyState==='loading'){var w=document.createElement('p');w.className='bk-empty';w.textContent='Checking availability\u2026';slots.appendChild(w);return;}
      var list=slotsFor(sel);if(!list.length){var e0=document.createElement('p');e0.className='bk-empty';e0.textContent='No open times left this day. Please pick another day.';slots.appendChild(e0);}
      list.forEach(function(t){
        var b=document.createElement('button');b.type='button';b.className='bk-slot';
        b.textContent=t.toLocaleTimeString(undefined,{hour:'numeric',minute:'2-digit'});
        b.addEventListener('click',function(){choose(t)});slots.appendChild(b);});
    }
    function choose(t){
      label=fmt(t,{weekday:'long',month:'long',day:'numeric'})+' at '+t.toLocaleTimeString(undefined,{hour:'numeric',minute:'2-digit'});
      f.querySelector('[name="call_time"]').value=label+(zone?' ('+zone+')':'');
      f.querySelector('[name="call_iso"]').value=t.toISOString();
      f.querySelector('[name="timezone"]').value=zone;
      f.querySelector('.bk-when').textContent=label;show(1);
    }
    function valid(s){var bad=[].slice.call(s.querySelectorAll('input[required]:not([type=radio])')).filter(function(i){return !i.checkValidity()});
      if(bad.length){bad[0].reportValidity();return false}return true;}
    var sending=false;
    function submit(){
      if(sending)return;sending=true;err.hidden=true;
      var fd=new FormData(f),ans={};
      ['monthly_budget','current_spend','attorneys','avg_case_value','practice_area'].forEach(function(k){if(fd.get(k))ans[k]=fd.get(k)});
      var data={start:fd.get('call_iso'),name:fd.get('name'),firm:fd.get('firm'),email:fd.get('email'),phone:fd.get('phone'),timezone:fd.get('timezone'),answers:ans,fax:fd.get('fax')};
      fetch(API,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)})
        .then(function(r){return r.json().catch(function(){return{}}).then(function(j){return{status:r.status,j:j}})},function(){return{status:0,j:{}}})
        .then(function(res){
          if(res.status===409){sending=false;taken();return;}
          var booked=res.status===200&&res.j&&res.j.ok;
          f.querySelector('[name="calendar_status"]').value=booked?'Added to Google Calendar, invite sent':'Not added to calendar ('+(res.j&&res.j.error||'no response')+'), confirm manually';
          sendForm(booked);});
    }
    function sendForm(booked){
      var body=new URLSearchParams(new FormData(f)).toString();
      fetch('/',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:body})
        .then(function(r){if(!r.ok&&!booked)throw new Error(r.status);
          f.querySelector('.bk-done-when').textContent=label+'.';
          var em=f.querySelector('[name="email"]').value,mail=f.querySelector('.bk-done-mail');
          mail.textContent='';mail.appendChild(document.createTextNode(booked?'We just sent a calendar invite to ':'We will email '));
          var b=document.createElement('b');b.className='bk-done-email';b.textContent=em;mail.appendChild(b);
          mail.appendChild(document.createTextNode(booked?'.':' to confirm your time.'));
          sending=false;show(screens.length-1);})
        .catch(function(){sending=false;screens.forEach(function(s){s.hidden=true;if('inert' in s)s.inert=true});err.hidden=false;});
    }
    function taken(){
      show(0);sel=null;slots.innerHTML='';
      loadBusy(function(){th.textContent='That time was just booked';slots.innerHTML='';var m=document.createElement('p');m.className='bk-empty';m.textContent='Someone grabbed that slot a moment ago. Please pick another time.';slots.appendChild(m);});
    }
    f.querySelector('.bk-retry').addEventListener('click',function(){err.hidden=true;screens[cur].hidden=false;if('inert' in screens[cur])screens[cur].inert=false;submit();});
    f.querySelector('.bk-err-back').addEventListener('click',function(){show(cur)});
    f.querySelector('.bk-change').addEventListener('click',function(){show(0)});
    f.querySelector('.bk-next-step').addEventListener('click',function(){if(valid(screens[1]))show(2)});
    f.querySelectorAll('.bk-back').forEach(function(b){b.addEventListener('click',function(){show(Math.max(0,cur-1))})});
    f.querySelectorAll('.bk-opt input').forEach(function(r){r.addEventListener('change',function(){
      var last=cur===screens.length-2;setTimeout(function(){last?submit():show(cur+1)},220);});});
    f.addEventListener('submit',function(ev){ev.preventDefault();if(cur===1&&valid(screens[1]))show(2);});
    prev.addEventListener('click',function(){view=new Date(view.getFullYear(),view.getMonth()-1,1);draw();});
    next.addEventListener('click',function(){view=new Date(view.getFullYear(),view.getMonth()+1,1);draw();});
    draw();show(0,true);
    var warm=function(){setTimeout(function(){if(busyState==='idle')loadBusy()},400)};
    if(document.readyState==='complete')warm();else addEventListener('load',warm);
    f.addEventListener('pointerdown',function(){if(busyState==='idle')loadBusy()},{once:true});
  });
})();
</script>
