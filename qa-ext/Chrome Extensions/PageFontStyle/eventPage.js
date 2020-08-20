// listen for messages during runtime
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse){
    if(request.todo == "showPageAction"){
      //retrieve all active tabs in the current window
      chrome.tabs.query({active: true, currentWindow: true}, function(tabs){
          //highlight the icon in the tab where the extension is loaded
          chrome.pageAction.show(tabs[0].id);
      });
    }
});
