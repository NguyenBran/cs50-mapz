$(document).ready(function(){
    document.getElementById("myForm").addEventListener("submit", function(event){
        event.preventDefault();
        if (navigator.geolocation && document.querySelector('input[name="current"]:checked')){
            navigator.geolocation.getCurrentPosition(function(position){
                var latitude = position.coords.latitude;
                var longitude = position.coords.longitude;
                document.getElementById("location").value = latitude + "," + longitude
                $('#myForm').submit();
            });
        }
    })
});