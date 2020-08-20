// For this part to work, it must be run on a server.
// python3 -m http.server
// and then go to http://localhost:8000/popup.html
window.onload = function() {
    chrome.identity.getAuthToken({interactive: true}, function(token) {
        if(chrome.runtime.lastError)
          console.log(chrome.runtime.lastError);
        else
          console.log(token);
          gapi.load('auth2', function() {
            auth2 = gapi.auth2.init({
              client_id: '504661212570-gn5nc6mtccuj7hsjcn419vjfapbq4f9a.apps.googleusercontent.com',
              api_key: 'AIzaSyBqqou8EeYObgVw_X5f2JrYhvGyZM8gjxM',
              fetch_basic_profile: true,
              scopes: 'profile'
            });
            // Sign the user in, and then retrieve their profile
            auth2.signIn().then(function() {
              var profile = auth2.currentUser.get().getBasicProfile();
              console.log('ID: ' + profile.getId()); // Do not send to your backend! Use an ID token instead.
              console.log('Name: ' + profile.getName());
              console.log('Image URL: ' + profile.getImageUrl());
              console.log('Email: ' + profile.getEmail()); // This is null if the 'email' scope is not present.
              alert(profile.getId() + ": " + profile.getName());
            });
          });
          handleClientLoad();
    });
};

// Some code taken from https://github.com/google/google-api-javascript-client/blob/master/samples/authSample.html

// load the API client and auth2 library
function handleClientLoad() {
  gapi.load('client:auth2', initClient);
}

function initClient() {
  gapi.client.init({
    apiKey: 'AIzaSyBqqou8EeYObgVw_X5f2JrYhvGyZM8gjxM',
    clientId: '504661212570-gn5nc6mtccuj7hsjcn419vjfapbq4f9a.apps.googleusercontent.com',
    scope: 'profile'
  }).then(function() {
    gapi.auth2.getAuthInstance().signIn();
    makeApiCall();
  })
}

function makeApiCall() {
  gapi.client.people.people.get({
    // resourceName:
    // To get information about the authenticated user, specify people/me.
    // To get information about a google account, specify people/{account_id}.
    // To get information about a contact, specify the resource name that identifies the contact as returned by people.connections.list.
    'resourceName': 'people/me',
    'personFields.includeField': 'person.names,person.biographies,person.photos'
  }).then(function(response) {
    response.setHeader("Set-Cookie", "HttpOnly;Secure;SameSite=Strict");
    $('#nickname').text(response.result.names[0].givenName);
    $('#motto').text(response.result.biographies[0]);
    $('#profile_pic').image(response.result.photos[0]);
  })
}
