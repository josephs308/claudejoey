<script id="bk-js">
(function(){
  document.querySelectorAll('form.book').forEach(function(f){
    var days=f.querySelector('.bk-days'),mon=f.querySelector('.bk-month'),prev=f.querySelector('.bk-prev'),next=f.querySelector('.bk-next');
    var slots=f.querySelector('.bk-slots'),th=f.querySelector('.bk-times-h'),tz=f.querySelector('.bk-tz');
    var step=f.querySelector('.bk-step'),det=f.querySelector('.bk-details'),pick=f.querySelector('.bk-when');
    if(!days)return;
    var zone='';try{zone=Intl.DateTimeFormat().resolvedOptions().timeZone||''}catch(e){}
    tz.textContent='30-minute call. Times shown in your time zone'+(zone?' ('+zone.replace(/_/g,' ')+')':'')+'.';
    var today=new Date();today.setHours(0,0,0,0);
    var first=new Date(today);first.setDate(first.getDate()+1);
    var last=new Date(today);last.setDate(last.getDate()+45);
    function ok(d){var w=d.getDay();return d>=first&&d<=last&&w!==0&&w!==6;}
    var view=new Date(first.getFullYear(),first.getMonth(),1),sel=null;
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
      var label=fmt(t,{weekday:'long',month:'long',day:'numeric'})+' at '+t.toLocaleTimeString(undefined,{hour:'numeric',minute:'2-digit'});
      f.querySelector('[name="call_time"]').value=label+(zone?' ('+zone+')':'');
      f.querySelector('[name="call_iso"]').value=t.toISOString();
      f.querySelector('[name="timezone"]').value=zone;
      pick.textContent=label;step.hidden=true;det.hidden=false;
      var first=det.querySelector('input:not([type=hidden])');if(first)first.focus({preventScroll:true});
    }
    f.querySelector('.bk-change').addEventListener('click',function(){det.hidden=true;step.hidden=false;});
    prev.addEventListener('click',function(){view=new Date(view.getFullYear(),view.getMonth()-1,1);draw();});
    next.addEventListener('click',function(){view=new Date(view.getFullYear(),view.getMonth()+1,1);draw();});
    draw();
  });
})();
</script>
