$(function(){
    // when user opens popup, total will be displayed
    chrome.storage.sync.get(['total', 'limit'], function(budget){
        $('#total').text(budget.total);
        $('#limit').text(budget.limit);
    })

    //when user clicks on submit button "spendAmount"...
    $('#spendAmount').click(function(){
        //create Chrome storage, check if "total" already exists
        chrome.storage.sync.get(['total', 'limit'], function(budget){
            var newTotal = 0;
            if(budget.total){
                newTotal += parseInt(budget.total);
            }

            var amount = $('#amount').val();
            //add what the user has entered
            if(amount){
                newTotal += parseInt(amount);
            }

            //set total in Chrome storage
            chrome.storage.sync.set({'total': newTotal}, function(){
                if(amount && newTotal >= budget.limit){
                    var notifOptions = {
                        type: 'basic',
                        iconUrl: 'icon48.png',
                        title: 'Limit reached!',
                        message: "Uh oh! Looks like you've reached your limit!"
                    };
                    chrome.notifications.create('limitNotif', notifOptions);
                }
            });

            //update UI
            $('#total').text(newTotal);
            $('#amount').val('');
        });
    });
});
