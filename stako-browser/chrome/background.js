chrome.webNavigation.onCommitted.addListener(saveTabActivity, {url: [{hostSuffix: 'stackoverflow.com'}]});
chrome.storage.onChanged.addListener(getStakoUID);

function saveTabActivity(details) {
    // 0 indicates the navigation happens in the tab content window
    if (details.frameId === 0) {
        // create visit object containing tabUrl and timestamp
        var visit = {
            tabUrl: details.url,
            timestamp: details.timeStamp
        };
        // get visitlist if it exists, otherwise initialize to empty list
        chrome.storage.local.get({'STAKO_ACTIVITY': []}, function (item) {
            var newVisitList = item.visitList;
            if (newVisitList.indexOf(visit) === -1) {
                newVisitList.push(visit);
                console.log(visit);
            }
            chrome.storage.local.set({STAKO_ACTIVITY: newVisitList});
        })
    }
}