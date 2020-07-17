$(function(){
    //select input elemnt -- document.getElementByID
    $('#name').keyup(function(){
      //change text of h2 - value of input element
      $('#greet').text('Hello ' + $('#name').val());
    })
})
