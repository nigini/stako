var mainContent = document.getElementById("mainbar");
var parent = mainContent.parentNode;
var banner = document.createElement("div");
banner.textContent = "hello";
banner.id = "crew";
parent.insertBefore(banner, mainContent);
//console.log(parent);
//alert("Hello from your Chrome extension!")