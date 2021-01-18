window.addEventListener("load", init);

function init() {
  displayVisit();
  addButtonFunctionality();
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
  var updateButton = document.getElementById("update-personals-button");
  updateButton.addEventListener('click', function() {
    window.alert("hello");
    //Make some sort of Api call here to save what the user has typed in.
  })
}
