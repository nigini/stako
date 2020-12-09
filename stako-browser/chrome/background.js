chrome.webNavigation.onCommitted.addListener(saveTabActivity, {url: [{hostSuffix: 'stackoverflow.com'}]});

function saveTabActivity(details) {
    // 0 indicates the navigation happens in the tab content window
    if (details.frameId === 0) {
        let visit = {
            TYPE: 'stackoverflow:visit',
            URL: details.url
        };
        saveStakoActivity(visit);
    }
}

const STAKO_API_URL = 'https://stako.org/api/v1/';
const STAKO_ACTIVITY_URL = STAKO_API_URL + 'user/{}/activity/';

function saveStakoActivity(activity_body) {
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
                        addActivityToCache(activity_body);
                    }
                });
        } else {
            console.log('CANNOT SYNC ACTIVITY WITHOUT A USER_ID! TRY TO LOGIN AGAIN!');
            addActivityToCache(activity_body);
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