<script id="bk-js">
(function(){
  document.querySelectorAll('form.book').forEach(function(f){
    var days=f.querySelector('.bk-days');if(!days)return;
    var mon=f.querySelector('.bk-month'),prev=f.querySelector('.bk-prev'),next=f.querySelector('.bk-next');
    var slots=f.querySelector('.bk-slots'),th=f.querySelector('.bk-times-h'),tz=f.querySelector('.bk-tz');
    var screens=[].slice.call(f.querySelectorAll('.bk-screen')),bar=f.querySelector('.bk-prog span'),err=f.querySelector('.bk-err');
    var cur=0,label='';
    function show(i,quiet){
      cur=i;screens.forEach(function(s,j){s.hidden=j!==i});f.classList.toggle('bk-at0',i===0);
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
    function ok(d){var w=d.getDay();return d>=first&&d<=last&&w!==0&&w!==6;}
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
      for(var m=9*60;m<=16*60+30;m+=30){(function(m){
        var t=new Date(sel);t.setHours(Math.floor(m/60),m%60,0,0);
        var b=document.createElement('button');b.type='button';b.className='bk-slot';
        b.textContent=t.toLocaleTimeString(undefined,{hour:'numeric',minute:'2-digit'});
        b.addEventListener('click',function(){choose(t)});slots.appendChild(b);})(m);}
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
    function submit(){
      err.hidden=true;
      var body=new URLSearchParams(new FormData(f)).toString();
      fetch('/',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:body})
        .then(function(r){if(!r.ok)throw new Error(r.status);
          f.querySelector('.bk-done-when').textContent=label+'.';
          f.querySelector('.bk-done-email').textContent=f.querySelector('[name="email"]').value;
          show(screens.length-1);})
        .catch(function(){err.hidden=false;});
    }
    f.querySelector('.bk-change').addEventListener('click',function(){show(0)});
    f.querySelector('.bk-next-step').addEventListener('click',function(){if(valid(screens[1]))show(2)});
    f.querySelectorAll('.bk-back').forEach(function(b){b.addEventListener('click',function(){show(Math.max(0,cur-1))})});
    f.querySelectorAll('.bk-opt input').forEach(function(r){r.addEventListener('change',function(){
      var last=cur===screens.length-2;setTimeout(function(){last?submit():show(cur+1)},220);});});
    f.addEventListener('submit',function(ev){ev.preventDefault();if(cur===1&&valid(screens[1]))show(2);});
    prev.addEventListener('click',function(){view=new Date(view.getFullYear(),view.getMonth()-1,1);draw();});
    next.addEventListener('click',function(){view=new Date(view.getFullYear(),view.getMonth()+1,1);draw();});
    draw();show(0,true);
  });
})();
</script>
