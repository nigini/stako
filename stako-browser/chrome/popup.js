displayVisit();

// update popup display with latest visit
function displayVisit () {
  chrome.storage.local.get(['visitList'], function(result){
      var visitList = result.visitList;
      var visit = {};
      visit = visitList.pop();
      console.log(visit);
      visitList.push(visit);

      $('#url').text(visit.tabUrl);
      $('#timestamp').text(visit.timestamp);
  });
}
