
/*
Creates a banner right above the answer portion of the page and populates it with the content "hello". Styled with design.css
*/
var mainContent = document.getElementById("mainbar");
var parent = mainContent.parentNode;
var bannerWrapper = document.createElement("div");
var banner = document.createElement("div");
banner.id = "Crew";
bannerWrapper.id = "bannerWrapper";
bannerWrapper.textContent = "Crew: ";
bannerWrapper.appendChild(banner);
parent.insertBefore(bannerWrapper, mainContent);

var type = 2;
if(type === 1) {
  var tags = document.querySelectorAll(".question .post-tag");
  for(let tag of tags) {
    banner.appendChild(tag);
    getTimeIn(tag);
    getTimeOut(tag);
    trackClick(tag);
  }
} else if (type === 2) {
  var tags = document.querySelectorAll(".user-info");
  //Set used to prevent a single contributor from appearing multiple times in the design.
  var contributors = new Set();
  for(let tag of tags) {
    var tagChildren = tag.children;
    var avatar = false;
    for(let child of tagChildren) {
      if(child.classList.contains("user-gravatar32")) {
        //If there is only one child node that means that that user has no information to display, so only
        //display the avatars that have more than one child node.
        if(child.childNodes.length > 1) {
          //The middle child nodes
          var userURL = child.childNodes[1].href;
          if(!contributors.has(userURL)) {
            contributors.add(userURL);
            avatar = true;
          }
        }
      } else {
        child.classList.add("popup-hidden");
      }
    }
    // If the user has an avatar, display that user as part of the crew.
    if(avatar) {
      //Remove the default hovering behavior from Stack Overflow to avoid losing track of the user's mouse movements.
      tag.classList.remove("user-hover");
      getTimeIn(tag);
      getTimeOut(tag);
      trackClick(tag);
      banner.appendChild(tag);
    } else {
      tag.classList.add("hidden");
    }
  }
}

const DELAY = 1000;
var timeIn = null;
/*
This event listener keeps track of the mouse's movement, and if the mouse enters the parameter element's space, it records at what
time that happened.
*/

function getTimeIn(element) {
  element.addEventListener('mouseenter', function (e) {
    timeIn = new Date();
    for(let child of e.target.children) {
      child.classList.remove("popup-hidden");
    }
  });
}

/*
This event listener keeps track of the mouse's movement, and if the mouse exits the parameter element's space, it calculates the difference in time
and if the mouse had hovered long enough, makes a call to the API to record an impression.
*/
function getTimeOut(element) {
  element.addEventListener('mouseleave', function (e) {
    var timeOut = new Date();
    var totalTime = timeOut.getTime() - timeIn.getTime();
    for(let child of e.target.children) {
      if(!child.classList.contains("user-gravatar32")) {
        child.classList.add("popup-hidden");
      }
    }
    // get time returns the time in milliseconds.
    // check whether timeIn is null and whether the difference is greater than one second.
    if(timeIn && totalTime >= DELAY) {
      chrome.runtime.sendMessage({type: "stackoverflow:mouse", url: window.location.href, time: totalTime}, function(response){
        console.log(response.testType + " " + response.testURL + " " + response.testTime);
      });
    }
    timeIn = null;
  });
}

function trackClick(element) {
  element.addEventListener('click', function (e) {
    chrome.runtime.sendMessage({type: "stackoverflow:click", url: window.location.href}, function(response) {
      console.log(response.testType + " " + response.testURL);
    });
  });
}