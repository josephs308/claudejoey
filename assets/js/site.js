(function(){
  // Scroll reveals
  var targets=document.querySelectorAll('[data-reveal],.rule,.feature .img');
  if('IntersectionObserver' in window){
    var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);}});},{rootMargin:'0px 0px -8% 0px',threshold:.12});
    targets.forEach(function(t){io.observe(t);});
    // Safety net: reveal anything already scrolled past (fast scrolls, anchor jumps)
    var tick=false;
    window.addEventListener('scroll',function(){if(tick)return;tick=true;requestAnimationFrame(function(){tick=false;
      targets.forEach(function(t){if(!t.classList.contains('in')&&t.getBoundingClientRect().top<innerHeight){t.classList.add('in');io.unobserve(t);}});});},{passive:true});
  }else{targets.forEach(function(t){t.classList.add('in');});}

  // Links to the bottom form: put the cursor in the first field
  document.querySelectorAll('a[href="#contact-form"]:not([data-start]):not([data-chat-open])').forEach(function(a){
    a.addEventListener('click',function(){setTimeout(function(){var n=document.getElementById('c-name');if(n)n.focus({preventScroll:true});},500);});
  });

  // Mobile menu
  var mb=document.querySelector('.menu-btn'), menu=document.getElementById('menu');
  function setNav(o){document.body.classList.toggle('nav-open',o);mb.setAttribute('aria-expanded',o);mb.textContent=o?'Close':'Menu';}
  mb.addEventListener('click',function(){setNav(!document.body.classList.contains('nav-open'));});
  menu.addEventListener('click',function(e){if(e.target.tagName==='A')setNav(false);});

  // Forms (demo): validate, then show the demo notice
  document.querySelectorAll('form.lead-form').forEach(function(f){
    f.addEventListener('submit',function(e){
      e.preventDefault();
      if(!f.checkValidity()){f.reportValidity();return;}
      f.querySelector('.ok').style.display='block';
    });
  });

  // Guided chat (demo)
  var TREE={
    start:{q:"Hi, thanks for reaching out. What happened?",o:[["Car or truck crash","when"],["Motorcycle crash","when"],["Fall or dog bite","when"],["Hurt at work","when"],["Medical mistake","when"],["Lost a loved one","loss"],["Something else","when"]]},
    loss:{q:"I'm very sorry. When did your loved one pass away?",o:[["In the last month","where"],["1 to 12 months ago","where"],["1 to 3 years ago","where"],["Over 3 years ago","where"]]},
    when:{q:"I'm sorry you're dealing with this. When did it happen?",o:[["This week","where"],["In the last month","where"],["1 to 12 months ago","where"],["Over a year ago","where"]]},
    where:{q:"Where did it happen?",o:[["St. Louis area","form"],["Elsewhere in Missouri","form"],["Southern Illinois","form"],["Somewhere else","form"]]},
    form:{q:"Thank you. That's the kind of case Tyler handles. Leave your name and number and he'll call you back for a free consultation. There's no fee unless he wins.",form:true}
  };
  var btn=document.querySelector('.chat-btn'), box=document.getElementById('chat'), body=document.getElementById('chat-body'), started=false;
  function bub(t,me){var d=document.createElement('div');d.className='bub'+(me?' me':'');d.textContent=t;body.appendChild(d);body.scrollTop=body.scrollHeight;}
  function step(k){
    var n=TREE[k];bub(n.q);
    var w=document.createElement('div');
    if(n.form){
      w.className='chat-form';
      w.innerHTML='<div class="hf"><label for="ch-n">Name</label><input id="ch-n" autocomplete="name"></div><div class="hf"><label for="ch-p">Phone</label><input id="ch-p" type="tel" autocomplete="tel"></div><button class="btn" type="button">Request a call back</button>';
      w.querySelector('button').onclick=function(){
        var nm=w.querySelector('#ch-n').value.trim(), ph=w.querySelector('#ch-p').value.trim();
        if(!nm||!ph){(nm?w.querySelector('#ch-p'):w.querySelector('#ch-n')).focus();return;}
        w.remove();bub(nm+' · '+ph,true);
        bub("Thank you. Tyler will call you back. (Demo only: on the live site this goes straight to the firm with the full conversation.)");
      };
    }else{
      w.className='opts';
      n.o.forEach(function(o){var b=document.createElement('button');b.type='button';b.textContent=o[0];b.onclick=function(){w.remove();bub(o[0],true);setTimeout(function(){step(o[1]);},350);};w.appendChild(b);});
    }
    body.appendChild(w);body.scrollTop=body.scrollHeight;
  }
  function open(o){box.classList.toggle('open',o);btn.setAttribute('aria-expanded',o);if(o&&!started){started=true;step('start');}}
  btn.addEventListener('click',function(){open(!box.classList.contains('open'));});

  // Hero "What happened?" options start the chat with that answer already chosen
  function startWith(choice){
    body.innerHTML='';started=true;open(true);
    bub(TREE.start.q);
    var next='when';TREE.start.o.forEach(function(o){if(o[0]===choice)next=o[1];});
    setTimeout(function(){bub(choice,true);setTimeout(function(){step(next);},350);},300);
  }
  document.querySelectorAll('[data-start]').forEach(function(a){
    a.addEventListener('click',function(e){e.preventDefault();startWith(a.getAttribute('data-start'));});
  });
  document.querySelectorAll('[data-chat-open]').forEach(function(a){
    a.addEventListener('click',function(e){e.preventDefault();open(true);});
  });
  box.querySelector('.chat-x').addEventListener('click',function(){open(false);btn.focus();});
  document.addEventListener('keydown',function(e){if(e.key==='Escape'&&box.classList.contains('open')){open(false);btn.focus();}});
})();
