const STAKO_API_URL = 'https://stako.org/api/v1/';
// const STAKO_API_URL = "http://127.0.0.1:5000/v1/";
const STAKO_AUTH_URL = STAKO_API_URL + 'auth/stako';
const STAKO_USER_URL = STAKO_API_URL + 'user/';

function clearCache() {
    chrome.storage.local.remove('STAKO_TOKEN');
    chrome.storage.local.remove('USER');
}

function authenticate() {
    return getValidToken(true).then(token =>{
       return token != null;
    });
}

function getValidToken(reAuth=true) {
    return new Promise(function(resolve, reject) {
        chrome.storage.local.get({'STAKO_TOKEN': null}, function (data) {
            let token = data['STAKO_TOKEN'];
            if (token) {
                let utc_now = Math.floor(Date.now() / 1000);
                if (token.expiration && ((token.expiration-utc_now) > 10)) { // Token expires in 10s or more?
                    return resolve(token);
                } else {
                    console.log('STAKO_TOKEN EXPIRED!');
                }
            }
            if(reAuth) {
                return authenticateUserStako().then(success => {
                    return resolve(getValidToken(false));
                });
            }
            return resolve(null);
        });
    });
}

/**
 * Implementation of authentication using the STAKO system instead of Google.
 */

function authenticateUserStako() {
    return new Promise(function(resolve, reject) {
        chrome.storage.local.get(['USER'], function(result) {
            result = result['USER'];
            if(!result || !result.username || !result.password) {
                return resolve(false);
            }
            if(result.username && result.password) {
                const auth_url = STAKO_AUTH_URL + `?email=${result.username}&pass_key=${result.password}`;
                authStakoUser(auth_url).then(stakoToken => {
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
            }
        });
    });
}
/*
 * Request CHROME_USER and validate it as a STAKO_USER.
 * If the authentication happens correctly, this method will also update the cached STAKO_USER.
 */
function authenticateGoogleUser() {
    return new Promise(function(resolve, reject) {
        chrome.identity.getAuthToken({interactive: true}, function (token) {
            if (chrome.runtime.lastError) {
                console.log('LOG IN FAIL: ' + chrome.runtime.lastError.message);
                return resolve(false);
            } else {
                chrome.identity.getProfileUserInfo(function (info) {
                    console.log('AUTHENTICATING: ' + info.email + ' - GOOGLE_ID: ' + info.id + ' - TOKEN: ' + token);
                    chrome.storage.local.set({email: info.email});
                    const auth_url = STAKO_AUTH_URL + `?email=${info.email}&google_id=${info.id}&token=${token}`;
                    authStakoUser(auth_url).then(stakoToken => {
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

function authStakoUser(auth_url) {
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
                                getSetup();
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

function getSetup() {
    var experimentType;
    chrome.storage.local.get({'STAKO_USER': null}, async function (user) {
      let uuid = user.STAKO_USER.uuid;
      if(uuid) {
          const search_url = STAKO_USER_URL + uuid + '/experiment/';
          var token = await getValidToken(true);
          var key = token["access_token"];
          var auth_key = "Bearer " + key;
          const request = new Request(search_url.replace('{}', uuid),
              {method: 'GET', headers: {'Content-Type': 'application/json', 'Authorization': auth_key}});
          experimentType = await fetch(request)
              .then(response => {
                  if(response.status === 200) {
                    return response.json();
                  } else {
                      console.log('COULD NOT SYNC: ' + JSON.stringify(response));
                  }
              });
            chrome.storage.local.set({'EXPERIMENT' : experimentType});
      } else {
          console.log('CANNOT SYNC ACTIVITY WITHOUT A USER_ID! TRY TO LOGIN AGAIN!');
      }
    });
    console.log(experimentType);
}