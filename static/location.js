document.querySelector("form[name='myForm']").addEventListener("submit", function(){
    alert("here")
    if (navigator.geolocation && document.querySelector('input[name="current"]:checked')){
        alert("here2")
        navigator.geolocation.getCurrentPosition(function(position){
            alert("here3")
            var latitude = position.coords.latitude;
            var longitude = position.coords.longitude;
            document.querySelector("input[name='current']").value = latitude + "," + longitude
             $('form[name="myForm"]').submit();
        });
    }
});
