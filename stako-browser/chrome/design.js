window.addEventListener("load", init);

//Testing whether the branches merged.

//Hard coded value which determines which design intervention is used.
var type = 2;

//Constant that determines how long the mouse should hover over an element before it is considered an interaction.
const DELAY = 1000;

//This variable keeps track of when a user first mouses over an element and is then used to calculate how long they left their mouse over that element.
var timeIn = null;

//Manifest file can't completely filter out all the pages we want to filter out, so added an extra regex here to check before editing the page.
const pageURLRegex = new RegExp('https://*.stackoverflow.com/questions/[0-9]+/*');

//"Main Method" which loads everything into the page after the page has finished loading.
function init() {
  let currURL = "" + window.location.href;
  if((currURL).match(pageURLRegex)){
    var banner = insertBanner();
    insertDesign(banner);
  }
}

/*
Creates a banner right above the answer portion of the page. Note that all styling for design.js is contained within design.css
*/
function insertBanner() {
  var mainContent = document.getElementById("mainbar");
  var parent = mainContent.parentNode;
  var bannerWrapper = document.createElement("div");
  var banner = document.createElement("div");
  banner.id = "Crew";
  bannerWrapper.id = "bannerWrapper";
  bannerWrapper.appendChild(banner);
  parent.insertBefore(bannerWrapper, mainContent);
  banner.classList.add("scrollmenu");
  var crewWord = document.createElement("p");
  crewWord.textContent = "Crew";
  banner.appendChild(crewWord);
  return banner;
}

//Depending on whether design one or two has been hardcoded, either populates the crew with the technology tags or the pictures of everyone who
//has contributed to the page.
function insertDesign(banner) {
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
    //Set used to prevent a single contributor from appearing multiple times in the crew.
    var contributors = new Set();
    for(let tag of tags) {
      var tagChildren = tag.children;
      var avatar = false;
      for(let child of tagChildren) {
        if(child.classList.contains("user-gravatar32")) {
          //If there is only one child node that means that that user has no information to display, so only
          //display the avatars that have more than one child node.
          if(child.childNodes.length > 1) {
            //Using the link to the user's profile page to identify whether that user has already been added to the crew or not.
            var userURL = child.childNodes[1].href;
            if(!contributors.has(userURL)) {
              contributors.add(userURL);
              avatar = true;
            }
          }
        } else {
          //Hide all other info that the user has except for their avatar picture.
          child.classList.add("popup-hidden");
        }
      }
      // If the user has an avatar, display that user as part of the crew.
      if(avatar) {
        //Remove the default hovering behavior from Stack Overflow to avoid losing track of the user's mouse movements.
        tag.classList.remove("user-hover");
        //These three methods add the event listeners which we use to keep track of the user's interactions with the page.
        getTimeIn(tag);
        getTimeOut(tag);
        trackClick(tag);
        banner.appendChild(tag);
      } else {
        tag.classList.add("hidden");
      }
    }
  }
}

/*
This event listener keeps track of the mouse's movement, and if the mouse enters the parameter element's space, it records at what
time that happened.
*/

function getTimeIn(element) {
  element.addEventListener('mouseenter', function (e) {
    timeIn = new Date();
    //Shows the hidden information associated with the avatar.
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
    //Hides all information except for the avatar.
    for(let child of e.target.children) {
      if(!child.classList.contains("user-gravatar32")) {
        child.classList.add("popup-hidden");
      }
    }
    // get time returns the time in milliseconds.
    // check whether timeIn is null and whether the difference is greater than one second.
    if(timeIn && totalTime >= DELAY) {
      //If the condition is met, record the event by sending a message to background.js
      chrome.runtime.sendMessage({type: "stackoverflow:mouse", url: window.location.href, time: totalTime}, function(response){
        console.log(response.testType + " " + response.testURL + " " + response.testTime);
      });
    }
    timeIn = null;
  });
}

function trackClick(element) {
  //Tracks whether one of the elements of interest has been clicked on.
  element.addEventListener('click', function (e) {
    chrome.runtime.sendMessage({type: "stackoverflow:click", url: window.location.href}, function(response) {
      console.log(response.testType + " " + response.testURL);
    });
  });
}