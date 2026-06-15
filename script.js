
  
  /* splash screen */
    window.addEventListener("load", function () {

      setTimeout(function () {

        const splash = document.getElementById("splash");
        splash.classList.add("hide");

        setTimeout(function () {
          splash.style.display = "none";
        }, 1000);

      }, 5200);   /* longer for movie intro */

    });
document.addEventListener("DOMContentLoaded", function () {

  /* =========================
  TOP BAR SLIDER
  ========================= */
  const items = document.querySelectorAll(".tb-item");
  const next = document.querySelector(".next");
  const prev = document.querySelector(".prev");

  if (items.length && next && prev) {

    let index = 0;

    function show(i){
      items.forEach(el => el.classList.remove("active"));
      items[i].classList.add("active");
    }

    function nextSlide(){
      index = (index + 1) % items.length;
      show(index);
    }

    function prevSlide(){
      index = (index - 1 + items.length) % items.length;
      show(index);
    }

    next.addEventListener("click", nextSlide);
    prev.addEventListener("click", prevSlide);

    setInterval(nextSlide, 4000);
  }

});
    /* MOBILE MENU */

    const mobileToggle =
      document.getElementById("mobileToggle");

    const mobileDrawer =
      document.getElementById("mobileDrawer");

   if(mobileToggle && mobileDrawer){

  mobileToggle.addEventListener("click", () => {

    mobileDrawer.classList.toggle("active");

  });

}

    /* MOBILE COLLECTION */

    const mobileCollectionBtn =
      document.getElementById("mobileCollectionBtn");

    const mobileDropdown =
      document.querySelector(".mobile-dropdown");

    mobileCollectionBtn.addEventListener("click", () => {

      mobileDropdown.classList.toggle("active");

    });
    const closeMenu =
      document.getElementById("closeMenu");

    closeMenu.addEventListener("click", () => {

      mobileDrawer.classList.remove("active");

    });

const revealImg = document.querySelector(".reveal-img");

const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if(entry.isIntersecting){
      entry.target.style.transitionDelay = "0.2s";
      entry.target.classList.add("show");
    }
  });
}, {
  threshold: 0.15
});

if(revealImg){
  observer.observe(revealImg);
}

/* =========================================
COUNTER ANIMATION
RESTART ON PAGE RELOAD + SCROLL
========================================= */

const counters = document.querySelectorAll(".count");

const counterSection =
  document.querySelector(".royal-counter-strip");

/* RESET COUNTERS ON LOAD */
window.addEventListener("load", () => {

  if(counters.length){

    counters.forEach(counter => {

      counter.innerText = "0";

    });

  }

});

/* COUNTER FUNCTION */
function startCounter(counter){

  const target =
    parseFloat(counter.dataset.count);

  let current = 0;

  const increment = target / 80;

  function updateCounter(){

    current += increment;

    if(current < target){

      if(target % 1 !== 0){

        counter.innerText =
          current.toFixed(1);

      }else{

        counter.innerText =
          Math.floor(current);

      }

      requestAnimationFrame(updateCounter);

    }else{

      counter.innerText = target;

    }

  }

  updateCounter();
}

/* INTERSECTION OBSERVER */
const counterObserver =
new IntersectionObserver((entries)=>{

  entries.forEach(entry=>{

    if(entry.isIntersecting){

      counters.forEach(counter=>{

        /* prevent repeating */
        if(!counter.classList.contains("counted")){

          counter.classList.add("counted");

          startCounter(counter);

        }

      });

    }

  });

},{
  threshold:0.45
});

/* OBSERVE SECTION */
if(counterSection){

  counterObserver.observe(counterSection);

}

const track = document.getElementById("heroTrack");
const dots = document.querySelectorAll(".hero-dots button");

let index = 0;
const total = 3;

// MOVE SLIDE
function go(i){
  track.style.transform = `translateX(-${i * 100}%)`;
  dots.forEach(d => d.classList.remove("active"));
  dots[i].classList.add("active");
  index = i;
}

// AUTO SLIDE
function next(){
  index = (index + 1) % total;
  go(index);
}

let auto = setInterval(next, 20000);

// DOT CLICK
dots.forEach((d,i)=>{
  d.addEventListener("click",()=>{
    go(i);
    clearInterval(auto);
    auto = setInterval(next, 5000);
  });
});

// SWIPE
let startX = 0;

track.addEventListener("touchstart",(e)=>{
  startX = e.touches[0].clientX;
});

track.addEventListener("touchend",(e)=>{
  let endX = e.changedTouches[0].clientX;

  if(startX > endX + 40){
    next();
  } else if(startX < endX - 40){
    index = (index - 1 + total) % total;
    go(index);
  }
});

/* =========================================
ABOUT SECTION REVEAL
========================================= */

const revealElements =
document.querySelectorAll(
  ".reveal-up, .reveal-left, .reveal-right"
);

const revealObserver =
new IntersectionObserver((entries)=>{

  entries.forEach(entry=>{

    if(entry.isIntersecting){

      entry.target.classList.add("active");

    }

  });

},{
  threshold:.15
});

revealElements.forEach(el=>{
  revealObserver.observe(el);
});







document.addEventListener(

"DOMContentLoaded",

()=>{

const slider=

document.querySelector(
".slider-track"
);

const images=

document.querySelectorAll(
".slider-track img"
);

let current=1;

function updateSlider(){

images.forEach(

(img,index)=>{

img.classList.remove(

"center",
"side"

);

if(index===current){

img.classList.add(
"center"
);

}else{

img.classList.add(
"side"
);

}

}

);

const imageWidth=

images[0]
.offsetWidth;

const gap=28;

const move=

(
current*
(imageWidth+gap)
)

-

(
slider.parentElement
.offsetWidth/2
)

+

(
imageWidth/2
);

slider.style.transform=

`translateX(-${move}px)`;

}

function autoSlide(){

current++;

if(

current>=
images.length

){

current=0;

}

updateSlider();

}

updateSlider();

setInterval(

autoSlide,

5000

);

});
