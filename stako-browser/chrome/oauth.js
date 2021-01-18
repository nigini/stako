window.onload = function () {
    chrome.identity.getAuthToken({interactive: true}, function (token) {
        if (chrome.runtime.lastError) {
            console.log('LOG IN FAIL: ' + chrome.runtime.lastError.message);
        } else {
            chrome.identity.getProfileUserInfo(function (info) {
                console.log('LOGGED IN AS ' + info.email);
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
        //TODO: When should this be updated? ADD some user.REFRESH?
        if (!user) {
            searchStakoUser(userEmail).then( foundUser => {
                if(!foundUser) {
                    document.getElementById('nickname').innerText = "USER NOT REGISTERED!";
                    document.getElementById('motto').innerText = "Sorry! Only pre-invited users allowed for now!";
                } else {
                    chrome.storage.local.set({STAKO_USER: foundUser});
                    user = foundUser;
                }
            });
        }
        if(user) {
            if(user.nickname) {
                document.getElementById('nickname').innerText = user.nickname;
            }
            if(user.motto) {
                document.getElementById('motto').innerText = user.motto;
            }
        }
    });
}

function searchStakoUser(userEmail) {
    console.log('searching stako user: ' + userEmail);
    const search_url = STAKO_USER_URL + '?key=email&value=' + userEmail;
    const request = new Request(search_url, {method: 'GET'});
    return fetch(request)
        .then(response => {
            console.debug(response);
            if (response.status === 200) {
                return response.json()
                    .then( stakoUser => {
                        console.log('found stako user: ' + JSON.stringify(stakoUser));
                        return stakoUser;
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
        .catch(error => {
            console.error(error);
        });
}