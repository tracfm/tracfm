/**
 * Created by .
 * User: eric
 * Date: 4/14/11
 * Time: 11:19 AM
 * To change this template use File | Settings | File Templates.
 */

// Google Maps
var mapLoaded = false;

if (!mapLoaded) {
    $.getScript('//maps.google.com/maps/api/js?sensor=false&key=AIzaSyDFLwxEdIzZb6xEWH9qAl7w_X_Hkz0rvNI&callback=mapLibraryReady');
}
// $.getScript('/static/js/maps.google.circleoverlay.js', function() {console.log("Circle overlay loaded.");});
// $.getScript('/static/js/maps.google.infobubble.js', function() {console.log("Infobubble overlay loaded.");});

// All default markers shown on the map
var markers = [];

// the current double-click marker
var clickMarker;


function mapLibraryReady() {

    mapLoaded = true;

    // It's up to whoever is embedding us to implement mapRead()
    mapReady();
}

function registerForClicks(map, id_lat, id_lng, callback) {
     google.maps.event.addListener(map, 'dblclick', function(event) {

         // clear our old marker
         if (clickMarker) {
             clickMarker.setMap(null);
         }

         if ($(id_lat).is(":visible")) {

             // set the current lat and lng
             if (event.latLng) {
                 if (id_lat && id_lng) {
                     $(id_lat).val(event.latLng.lat());
                     $(id_lng).val(event.latLng.lng());
                 }
             }

             // add our new marker to the map
             clickMarker = new google.maps.Marker({ position: event.latLng, map: map });

             if (callback) {
                 callback(clickMarker);
             }
         }
     });
}

function showMap(mapDivId, points) {

    if (!points) {
        points = []
    }

    // sort our points so we draw the largest ones first
    points.sort(function(a, b) { return b.count - a.count; });

    // default center point
    var center = new google.maps.LatLng(0.3103623222234959,32.57171667578132);

    var myOptions = {
        center: center,
        scrollwheel: false,
        disableDoubleClickZoom: true,
        mapTypeId: google.maps.MapTypeId.ROADMAP
    };

    var map = new google.maps.Map(document.getElementById(mapDivId), myOptions);

    // extend our map bounds to fit all points
    var bounds = new google.maps.LatLngBounds();
    var fitBounds = false;
    for (i in points) {
        var point = points[i];
        if (point.location) {
            bounds.extend(point.location);
            fitBounds = true;
        }
    }

    // if we have points, use those bounds
    if (fitBounds) {
        map.fitBounds(bounds);
    }
    // otherwise, just zoom out on our center point
    else {
        map.zoom = 13;
    }
    for (i in points) {
        var point = points[i];
        if (point.location) {
            var marker = addMarker(map, point.location, point.name, point.click);
        }
    }

    return map;
}

function addMarker(map, loc, name, click) {

    for (idx in markers) {
        if (markers[idx].position.equals(loc)) {
            markers[idx].setMap(null);
            markers.splice(idx, 1);
            break;
        }
    }

    if (clickMarker) {
        clickMarker.setMap(null);
    }

    var marker = new google.maps.Marker({
                    position: loc,
                    map: map,
                    title: unescape(name)
    });
    
    markers[markers.length] = marker;
    if (click) {
        google.maps.event.addListener(marker, 'click', click);
    }
}

function hideMarkers(clickerLocation) {
    for (idx in markers) {
        markers[idx].setMap(null);
    }

    if (clickerLocation) {
        // clear our old marker
         if (clickMarker) {
             clickMarker.setMap(null);
         }
        clickMarker = new google.maps.Marker({ position: clickerLocation, map: map });
        map.panTo(clickerLocation);
    }
}

function showMarkers() {
    for (idx in markers) {
        markers[idx].setMap(map);
    }
}
