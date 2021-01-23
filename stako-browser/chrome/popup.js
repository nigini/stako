window.addEventListener("load", init);

function init() {
  displayVisit();
  addButtonFunctionality();
  loadCarosel();
}

// update popup display with latest visit
function displayVisit () {
  chrome.storage.local.get(['visitList'], function(result){
      var visitList = result.visitList;
      var visit = {};
      //visit = visitList.pop();
      console.log(visit);
      //visitList.push(visit);

      $('#url').text(visit.tabUrl);
      $('#timestamp').text(visit.timestamp);
  });
}

//This function allows the nickname and motto to be editable.
function addButtonFunctionality() {
  var nickname = document.getElementById("nickname");
  var motto = document.getElementById("motto");
  nickname.contentEditable = true;
  motto.contentEditable = true;
}

function loadCarosel() {
  chrome.storage.local.get(['STAKO_USER'], function(result) {
    var userData = result["STAKO_USER"];
    console.log(userData);
    var nick = document.getElementById("nickname");
    var mot = document.getElementById("motto");
    var carosel = document.querySelector("#carouselContent > .carousel-inner");
    //var tags = userData.activity["weekly_summary"][0]["top_tags"];
    //This tags is for testing,use line 37 when getting the actual data from the API.
    var tags = [];
    tags.push({
      "tag_name": "Java",
      "pages_visits": 0
    });
    tags.push({
      "tag_name": "Python",
      "pages_visits": 0
    });
    tags.push({
      "tag_name": "Git",
      "pages_visits": 0
    });
    nick.textContent = userData.nickname;
    mot.textContent = userData.moto;
    for(let tag of tags) {
      var slide = document.createElement("div");
      var tagName = document.createElement("a");
      var pageVisits = document.createElement("p");
      tagName.textContent = tag.tag_name;
      tagName.href = "https://stackoverflow.com/tags/" + tag.tag_name;
      pageVisits.textContent = tag.pages_visits;
      slide.classList.add("carousel-item", "text-center", "p-4");
      if(tag === tags[0]) {
        slide.classList.add("active");
      }
      trackClick(tagName);
      var innerBlock = document.createElement("div");
      innerBlock.classList.add("weekly-container");
      innerBlock.appendChild(tagName);
      innerBlock.appendChild(pageVisits);
      slide.append(innerBlock);
      carosel.append(slide);
    //var info =  result["activity"].weekly_summary;
    //console.log(info);
    }
  });
  var test = {
    "nickname": "Ben",
    "uuid": "str(uuid.uuid4())",
    "moto": "Carpe Diem",
    "start_date": "int(datetime.timestamp(datetime.utcnow()))",
    "activity": {
      "weekly_summary": [
        {
          "year": 2021,
          "week": 0,
          "top_tags": [
            {
              "tag_name": "Java",
              "pages_visits": 0
            },
            {
              "tag_name": "Git",
              "pages_visits": 0
            },
            {
              "tag_name": "Bit arithmetic",
              "pages_visits": 0
            }
          ],
          "pages_visits": 0
        }
      ],
      "updated": "int(datetime.timestamp(datetime.utcnow()))"
    }
  }
  }

  function trackClick(element) {
    //Tracks whether one of the elements of interest has been clicked on.
    element.addEventListener('click', function (e) {
      console.log('hello');
      chrome.runtime.sendMessage({type: "stackoverflow:click", url: element.href}, function(response) {
        console.log(response.testType + " " + response.testURL);
      });
    });
  }
