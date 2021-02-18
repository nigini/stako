window.addEventListener("load", init);


var key = ['a6af8190add5594fa190bb4d897aa25e84d5bbd1e679473492050a587bef0d18'];

var value = ['4232fb2cf8cad31f4ba975804750335d260ba197ce2363024627842bbf585836', '428f154b3e18bfe54659e0ef96566193bbe64a8a4e837cf22cea9b992ce7f377', '0fcd568a5cb9bdb4677b69354b11ee415af8f784519cff3da49a26f84eaee7f2'];
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
   chrome.storage.local.get({'EXPERIMENT': null}, async function (experiment) {
    console.log(experiment);
    var banner = insertBanner(experiment['EXPERIMENT']['experiments']);
    insertDesign(banner);
  });
  }
}

/*
Creates a banner right above the answer portion of the page. Note that all styling for design.js is contained within design.css
*/
function insertBanner(experiments) {
  console.log(experiments);
  var test = key[0];
  type = experiments[test];
  if(!type) {
    type = value[getRandomInt(3)];
  }
  console.log(type);
  var mainContent = document.getElementById("mainbar");
  var parent = mainContent.parentNode;
  var bannerWrapper = document.createElement("div");
  var banner = document.createElement("div");
  var dismiss = document.createElement("button");
  dismiss.classList.add("dismiss");
  dismiss.textContent = "X";
  dismiss.addEventListener("click", dismissIntervention);
  trackDismiss(dismiss);
  banner.id = "Crew";
  bannerWrapper.id = "bannerWrapper";
  bannerWrapper.appendChild(dismiss);
  bannerWrapper.appendChild(banner);
  if(type === value[0] || type === value[1]) {
    parent.insertBefore(bannerWrapper, mainContent);
  }
  banner.classList.add("scrollmenu");
  var crewWord = document.createElement("p");
  crewWord.textContent = "Crew";
  banner.appendChild(crewWord);
  return banner;
}

//Closes the intervention and reverts the page back to its original state.
function dismissIntervention() {
  var tags = document.querySelectorAll(".popup-hidden");
  for(let element of tags) {
    element.classList.remove("popup-hidden");
  }
  var intervention = document.getElementById("bannerWrapper");
  intervention.classList.add("popup-hidden");
  var nameAndDateTags = document.querySelectorAll(".nameAndDate");
  for(let info of nameAndDateTags) {
    info.classList.add("popup-hidden");
  }
}

//Depending on whether design one or two has been hardcoded, either populates the crew with the technology tags or the pictures of everyone who
//has contributed to the page.
function insertDesign(banner) {
  if(type === value[0]) {
    var tags = document.querySelectorAll(".question .post-tag");
    for(let element of tags) {
      var tag = element.cloneNode(true);
      element.parentElement.classList.add("popup-hidden");
      element.parentElement.classList.remove("grid");
      banner.appendChild(tag);
      getTimeIn(tag);
      getTimeOut(tag);
      trackClick(tag);
    }
  } else if (type === value[1]) {
    var tags = document.querySelectorAll(".user-info");
    //Set used to prevent a single contributor from appearing multiple times in the crew.
    var contributors = new Set();
    for(let element of tags) {
      var tag = element.cloneNode(true);
      var image = element.querySelector(".user-gravatar32");
      var reputation = element.querySelector(".user-details .-flair");
      var name = element.querySelector(".user-details a");
      var date = element.querySelector(".user-action-time");
      //Removes gray background
      element.parentElement.classList.remove("owner");
      var nameAndDate = document.createElement("div");
      nameAndDate.classList.add("nameAndDate");
      if(name) {
        var copyName = document.createElement("div");
        copyName.textContent = name.textContent
        nameAndDate.appendChild(copyName);
        name.classList.add("popup-hidden");
      }
      if(date) {
        var copyDate = document.createElement("div");
        copyDate.textContent = date.textContent
        nameAndDate.appendChild(copyDate);
        date.classList.add("popup-hidden");
      }
      element.parentElement.appendChild(nameAndDate);
      if(image) {
        image.classList.add("popup-hidden");
      }
      if(reputation) {
        reputation.classList.remove("-flair");
        reputation.classList.add("popup-hidden");
      }
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
Helper utility function to generate a random integer.
*/
function getRandomInt(max) {
  return Math.floor(Math.random() * Math.floor(max));
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
      if(element.classList.contains("post-tag")) {
        var tag_link = "https://stackoverflow.com/" + element.href;
        chrome.runtime.sendMessage({extensiondId: "background.js", type: "stackoverflow:mouse", url: window.location.href, time: totalTime, ele: tag_link}, function(response){
          console.log(response.testType + " " + response.testURL + " " + response.testTime);
        });
      } else if(element.classList.contains("user-info")) {
        var tag_link = "https://stackoverflow.com/" + element.href;
        var linkElement = element.querySelector(".user-gravatar32 > a");
        var link = linkElement.href;
        var tag_link = "https://stackoverflow.com/" + link;
        chrome.runtime.sendMessage({extensiondId: "background.js", type: "stackoverflow:mouse", url: window.location.href, time: totalTime, ele: tag_link}, function(response){
          console.log(response.testType + " " + response.testURL + " " + response.testTime);
        });
      }
    }
    timeIn = null;
  });
}

function trackClick(element) {
  //Tracks whether one of the elements of interest has been clicked on.
  if(element.classList.contains("post-tag")){
    element.addEventListener('click', function (e) {
      var tag_link = "https://stackoverflow.com/" + element.href;
      chrome.runtime.sendMessage({extensiondId: "background.js", type: "stackoverflow:click", url: window.location.href, ele: tag_link}, function(response) {
        console.log(response.testType + " " + response.testURL);
      });
    });
  } else if(element.classList.contains("user-info")){
    var linkElement = element.querySelector(".user-gravatar32 > a");
    var link = linkElement.href;
    element.addEventListener('click', function (e) {
      var tag_link = "https://stackoverflow.com/" + link;
      chrome.runtime.sendMessage({extensiondId: "background.js", type: "stackoverflow:click", url: window.location.href, ele:tag_link}, function(response) {
        console.log(response.testType + " " + response.testURL);
      });
    });
  }
}

function trackDismiss(element) {
  //Tracks whether the dismiss button has been clicked on.
  element.addEventListener('click', function (e) {
    chrome.runtime.sendMessage({extensiondId: "background.js", type: "stackoverflow:click", url: window.location.href, ele:"Dismiss-Click"}, function(response) {
      console.log(response.testType + " " + response.testURL);
    });
  });
}