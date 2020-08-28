chrome.webNavigation.onCommitted.addListener(saveTabActivity, {url: [{hostSuffix: 'stackoverflow.com'}]});

function saveTabActivity(details) {
    // 0 indicates the navigation happens in the tab content window
    if (details.frameId === 0) {
        // create visit object containing tabUrl and timestamp
        var visit = {
            tabUrl: details.url,
            timestamp: details.timeStamp,
        };
        saveStakoActivity(visit);
    }
}

const STAKO_API_URL = 'https://stako.org/api/v1/';
const STAKO_ACTIVITY_URL = STAKO_API_URL + 'user/{}/activity/';

function saveStakoActivity(activity) {
    let activity_body = {URL: activity.tabUrl};
    chrome.storage.local.get({'STAKO_USER': null}, function (user) {
        let uuid = user.STAKO_USER.uuid;
        if(uuid) {
            const request = new Request(STAKO_ACTIVITY_URL.replace('{}', uuid),
                {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(activity_body)});
            fetch(request)
                .then(response => {
                    if (response.status === 200) {
                        console.log('SYNCED: ' + JSON.stringify(activity_body));
                    } else {
                        console.log('COULD NOT SYNC: ' + JSON.stringify(activity_body));
                        addActivityToCache(activity);
                    }
                });
        } else {
            console.log('CANNOT SYNC ACTIVITY WITHOUT A USER_ID! TRY TO LOGIN AGAIN!');
            addActivityToCache(activity);
        }
    });
}

function addActivityToCache(activity){
    chrome.storage.local.get({'STAKO_ACTIVITY_CACHE': []}, function (item) {
        var newVisitList = item.STAKO_ACTIVITY_CACHE;
        newVisitList.push(activity);
        console.log('CACHED: ' + JSON.stringify(activity));
        chrome.storage.local.set({STAKO_ACTIVITY: newVisitList});
    });
}