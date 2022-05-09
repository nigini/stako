chrome.webNavigation.onCommitted.addListener(saveTabActivity, {url: [{hostSuffix: 'stackoverflow.com'}]});

const STAKO_ACTIVITY_URL = STAKO_API_URL + 'user/{}/activity/';

/*
This method listens for a message from design.js, which controls the content scripts of the page. When a mouse over or click message is sent,
the callback function grabs the type (mouse over), url, and time from the sent message and then creates a JSON object with that information
and saves it using the saveStakoActivity method.
*/
chrome.runtime.onMessage.addListener(
    function(request, sender, sendResponse) {
        if(request.type == "stackoverflow:mouse") {
            var mouseOver = {
                type: request.type,
                url: request.url,
                duration: request.time,
                element: request.ele,
                origin: request.origin
            };
            saveStakoActivity(mouseOver);
            sendResponse({testType: request.type, testURL: request.url, testTime: request.time, origin: request.origin});
        } else if(request.type == "stackoverflow:click") {
            var click = {
                type: request.type,
                url: request.url,
                element: request.ele,
                origin: request.origin
            };
            saveStakoActivity(click);
            sendResponse({testType: request.type, testURL: request.url, origin: request.origin});
        }
    }
);

function saveTabActivity(details) {
    // 0 indicates the navigation happens in the tab content window
    if (details.frameId === 0) {
        let visit = {
            type: 'stackoverflow:visit',
            url: details.url
        };
        saveStakoActivity(visit);
    }
}

function saveStakoActivity(activity_body) {
    chrome.storage.local.get({'STAKO_USER': null}, async function (user) {
        let uuid = user.STAKO_USER.uuid;
        if(uuid) {
            //Add the uuid to the type of activity.
            //activity_body["element"] = uuid;
            var token = await getValidToken(true);
            var key = token["access_token"];
            var auth_key = "Bearer " + key;
            const request = new Request(STAKO_ACTIVITY_URL.replace('{}', uuid),
                {method: 'POST', headers: {'Content-Type': 'application/json', 'Authorization': auth_key}, body: JSON.stringify(activity_body)});
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