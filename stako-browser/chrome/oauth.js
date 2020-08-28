window.onload = function () {
    chrome.identity.getAuthToken({interactive: true}, function (token) {
        if (chrome.runtime.lastError) {
            console.log(chrome.runtime.lastError);
        } else {
            console.log(token);
            chrome.identity.getProfileUserInfo(function (info) {
                console.log(info.email)
                chrome.storage.local.set({email: info.email});
                document.getElementById('login').innerText = info.email;
                matchStakoUser(info.email);
            });
        }
    });
};

const STAKO_API_URL = 'https://stako.org/api/v1/';
const STAKO_USER_URL = STAKO_API_URL + 'user/';

function matchStakoUser(userEmail) {
    let user;
    chrome.storage.local.get({'STAKO_USER': null}, function (items) {
        user = items['STAKO_USER'];
        //TODO: When should this be updated?
        if (!user) {
            user = searchStakoUser(userEmail);
            if(!user) {
                createStakoUser(userEmail);
            }
        }
        if(user) {
            document.getElementById('nickname').innerText = user.nickname;
            document.getElementById('motto').innerText = user.motto;
        }
    });
}

function searchStakoUser(userEmail) {
    console.log('searching stako user: ' + userEmail);
    const search_url = STAKO_USER_URL + '?key=email&value=' + userEmail;
    const request = new Request(search_url, {method: 'GET'});
    fetch(request)
        .then(response => {
            if (response.status === 200) {
                response.json()
                    .then( stakoUser => {
                        console.log('found stako user: ' + JSON.stringify(stakoUser));
                        chrome.storage.local.set({STAKO_USER: stakoUser});
                    });
            } else if (response.status === 404) {
                return null;
            } else {
                response.text()
                    .then(text => {
                        throw Error('Could not search for user: HTTP_STATUS ' + response.status + ' + ' + text)
                    });
            }
        })
        .then(response => {
            console.debug(response);
        })
        .catch(error => {
            console.error(error);
        });
}

function createStakoUser(userEmail) {
    console.log('creating stako user: ' + userEmail);
    const request = new Request(STAKO_USER_URL, {method: 'POST', headers: {'Content-Type': 'application/json'}});
    fetch(request)
        .then(response => {
            if (response.status === 200) {
                response.json()
                    .then( stakoUser => {
                        console.log('created stako user: ' + JSON.stringify(stakoUser));
                        stakoUser.email = userEmail;
                        return updateStakoUser(stakoUser);
                    });
            } else {
                response.text()
                    .then(text => {throw Error('Could not create new STAKO user: HTTP_STATUS ' + response.status + ' + ' + text)});
            }
        })
        .then(response => {
            console.debug(response);
        })
        .catch(error => {
            console.error(error);
        });
}

function updateStakoUser(user) {
    console.log('updating stako user: ' + JSON.stringify(user));
    const request_url = STAKO_USER_URL + user.uuid + '/';
    const request = new Request(request_url,
                            {method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(user)});
    fetch(request)
        .then(response => {
            if (response.status === 200) {
                chrome.storage.local.set({STAKO_USER: user});
                console.log('Saved local stako user: ' + user.uuid);
                return user;
            } else {
                throw new Error('Could not update STAKO user: ' + JSON.stringify(user));
            }
        })
        .then(response => {
            console.debug(response);
        }).catch(error => {
        console.error(error);
    });
}
