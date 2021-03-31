function show_activity() {
    $('#data > div').each(function(){
        console.log($(this).data('url'))
    })
}