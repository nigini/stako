$(function(){
    color = $('#fontColor').val();
    $('#fontColor').on("change paste keyup", function(){
        color = $(this).val();
    });
    $('#btnChange').click(function(){
        //send message to tab from where we clicked the button
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs){
            chrome.tabs.sendMessage(tabs[0].id, {todo: "changeColor", clickedColor: color})
        });
    });
});
