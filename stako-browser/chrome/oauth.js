window.onload = function () {
    //chrome.storage.local.remove('STAKO_TOKEN');
    getValidToken(true).then( token => {
        if (!token) {
            setPopupAlert('WE COULD NOT LOG YOU IN! :(');
        } else {
            updatePopupData();
        }
    });
};

const STAKO_API_URL = 'https://stako.org/api/v1/';
const STAKO_AUTH_URL = STAKO_API_URL + 'auth/';
const STAKO_USER_URL = STAKO_API_URL + 'user/';

function getValidToken(reAuth=true) {
    return new Promise(function(resolve, reject) {
        chrome.storage.local.get({'STAKO_TOKEN': null}, function (data) {
            let token = data['STAKO_TOKEN'];
            if (token) {
                console.log('STAKO_TOKEN: ' + JSON.stringify(token));
                let utc_now = Math.floor(Date.now() / 1000);
                if (token.expiration && ((token.expiration-utc_now) > 10)) { // Token expires in 10s or more?
                    return resolve(token);
                } else {
                    console.log('STAKO_TOKEN EXPIRED!');
                }
            }
            if(reAuth) {
                return authenticateUser().then(success => {
                    if(success) {
                        return resolve(getValidToken(false));
                    }
                });
            }
            return resolve(null);
        });
    });
}
/*
 * Request CHROME_USER and validate it as a STAKO_USER.
 * If the authentication happens correctly, this method will also update the cached STAKO_USER.
 */
function authenticateUser() {
    return new Promise(function(resolve, reject) {
        chrome.identity.getAuthToken({interactive: true}, function (token) {
            if (chrome.runtime.lastError) {
                console.log('LOG IN FAIL: ' + chrome.runtime.lastError.message);
                return resolve(false);
            } else {
                chrome.identity.getProfileUserInfo(function (info) {
                    console.log('AUTHENTICATING: ' + info.email + ' - GOOGLE_ID: ' + info.id + ' - TOKEN: ' + token);
                    chrome.storage.local.set({email: info.email});
                    authStakoUser(info.email, info.id, token).then(stakoToken => {
                        if (stakoToken) {
                            chrome.storage.local.set({'STAKO_TOKEN': stakoToken});
                            updateStakoUser(stakoToken.uuid).then(user => {
                                return resolve(true);
                            })
                        } else {
                            console.log('FAIL TO RETRIEVE STAKO TOKEN!');
                            return resolve(false);
                        }
                    });
                });
            }
        });
    });
}

function authStakoUser(userEmail, googleID, oauthToken) {
    console.log('authenticating stako user: ' + userEmail);
    const auth_url = STAKO_AUTH_URL + `?email=${userEmail}&google_id=${googleID}&token=${oauthToken}`;
    const request = new Request(auth_url, {method: 'GET'});
    return fetch(request)
        .then(response => {
            if (response.status === 200) {
                return response.json()
                    .then( stakoToken => {
                        console.log('AUTH TOKEN: ' + JSON.stringify(stakoToken));
                        return stakoToken;
                    });
            } else if (response.status === 401) {
                return null;
            } else {
                response.text()
                    .then(text => {
                        throw Error('Could not authenticate stako user: HTTP_STATUS ' + response.status + ' + ' + text)
                    });
            }
        })
        .catch(error => {
            console.error(error);
        });
}

function updatePopupData() {
    chrome.storage.local.get({'email': null}, function (data) {
        if(data) document.getElementById('login').innerText = data['email'];
    });
    chrome.storage.local.get({'STAKO_USER': null}, function (data) {
        if (data) {
            let user = data['STAKO_USER'];
            console.log('CACHED USER: ' + JSON.stringify(user));
            document.getElementById('nickname').innerText = user.nickname;
            document.getElementById('motto').innerText = user.motto;
        }
    });
}

function setPopupAlert(alert) {
    console.log('ALERT: ' + alert.ALERT);
    document.getElementById('alert').innerText = alert.ALERT;
}

function updateStakoUser(uuid) {
    console.log('UPDATE USER: ' + uuid);
    const search_url = STAKO_USER_URL + uuid + '/';
    return getValidToken().then( token => {
        if(token) {
            let header = {'Authorization': `Bearer ${token.access_token}`}
            const request = new Request(search_url, {method: 'GET', headers: header});
            return fetch(request).then(response => {
                    console.debug(response);
                    if (response.status === 200) {
                        return response.json()
                            .then( stakoUser => {
                                console.log('FOUND USER: ' + JSON.stringify(stakoUser));
                                chrome.storage.local.set({'STAKO_USER': stakoUser});
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
                    return null;
                });
        } else {
            console.log('NO ACCESS TOKEN AVAILABLE!');
            return null;
        }
    });
}