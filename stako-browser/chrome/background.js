// Store url in chrome storage and filter by url host suffix
chrome.webNavigation.onCommitted.addListener(function(details) {
  // 0 indicates the navigation happens in the tab content window
  if (details.frameId === 0) {
      // create visit object containing tabUrl and timestamp
      var visit = {
        tabUrl: details.url,
        timestamp: details.timeStamp
      };

      // get visitlist if it exists, otherwise initialize to empty list
      chrome.storage.local.get({'visitList': []}, function(item) {
        var newVisitList = item.visitList;
        if (newVisitList.indexOf(visit) === -1) {
          newVisitList.push(visit);
        }
        //uncomment below to clear the visit list
        //newVisitList = [];
        console.log(newVisitList);
        chrome.storage.local.set({visitList: newVisitList});
      })
  }  //chrome.storage.local.clear();
}, {url: [{hostSuffix : 'stackoverflow.com'}]});
