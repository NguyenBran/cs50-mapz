$(document).ready(function(){
    document.querySelector("form[name='myForm']").addEventListener("submit", function(){
        if (navigator.geolocation && document.querySelector('input[name="current"]:checked')){
            navigator.geolocation.getCurrentPosition(function(position){
                var latitude = position.coords.latitude;
                var longitude = position.coords.longitude;
                document.querySelector("input[name='current']").value = latitude + "," + longitude
                 $('form[name="myForm"]').submit();
            });
        }
    });
});