
/*
Creates a banner right above the answer portion of the page and populates it with the content "hello". Styled with design.css
*/
var mainContent = document.getElementById("mainbar");
var parent = mainContent.parentNode;
var banner = document.createElement("div");
banner.textContent = "Crew: ";
banner.id = "Crew";
//If they change the class name of is-selected it may no longer match the page though??
banner.classList.add("is-selected");
parent.insertBefore(banner, mainContent);

var type = 1;
if(type === 1) {
  var tags = document.querySelectorAll(".question .post-tag");
  for(let tag of tags) {
    banner.appendChild(tag);
    getTimeIn(tag);
    getTimeOut(tag);
    trackClick(tag);
  }
  console.log(tags);
} else if (type === 2) {
  var tags = document.querySelectorAll(".user-info.user-hover");
  for(let tag of tags) {
    var tagChildren = tag.children;
    for(let child of tagChildren) {

    }
    tag.removeChild();
    //banner.appendChild(tag);
  }
  console.log(tags);
}

const DELAY = 1000;
var timeIn = null;
/*
This event listener keeps track of the mouse's movement, and if it hovers over the "crew" div it sends a message to background.js with a JSON
object containing the type, url, and time of the interaction.
*/

/*
Old mouse over implementation.
banner.addEventListener('mousemove', function (e) {
  var element = e.target;
  if (element.id == 'Crew') {
    //alert("You moused over the div!");
    chrome.runtime.sendMessage({type: "mouse over", url: window.location.href, time: new Date()}, function(response){
      console.log(response.testURL + " " + response.testTime);
    });
  }
});
*/
function getTimeIn(element) {
  element.addEventListener('mouseenter', function (e) {
    timeIn = new Date();
  });
}

function getTimeOut(element) {
  element.addEventListener('mouseleave', function (e) {
    var timeOut = new Date();
    var totalTime = timeOut.getTime() - timeIn.getTime();
    // get time returns the time in milliseconds.
    // check whether timeIn is null and whether the difference is greater than one second.
    if(timeIn && totalTime >= DELAY) {
      chrome.runtime.sendMessage({type: "stackoverflow:mouse", url: window.location.href, time: totalTime}, function(response){
        console.log(response.testURL + " " + response.testTime);
      });
    }
    timeIn = null;
  });
}

function trackClick(element) {
  element.addEventListener('click', function (e) {
    chrome.runtime.sendMessage({type: "stackoverflow:click", url: window.location.href});
  });
}


//console.log(parent);
//alert("Hello from your Chrome extension!")