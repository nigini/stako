
/*
Creates a banner right above the answer portion of the page and populates it with the content "hello". Styled with design.css
*/
var mainContent = document.getElementById("mainbar");
var parent = mainContent.parentNode;
var banner = document.createElement("div");
banner.textContent = "hello";
banner.id = "Crew";
parent.insertBefore(banner, mainContent);

/*
This event listener keeps track of the mouse's movement, and if it hovers over the "crew" div it sends a message to background.js with a JSON
object containing the type, url, and time of the interaction.
*/
document.addEventListener('mousemove', function (e) {
  var element = e.target;
  if (element.id == 'Crew') {
    //alert("You moused over the div!");
    chrome.runtime.sendMessage({type: "mouse over", url: window.location.href, time: new Date()}, function(response){
      console.log(response.testURL + " " + response.testTime);
    });
  }
});


//console.log(parent);
//alert("Hello from your Chrome extension!")