
var map;
var markers = [];

var zoom = 0;

function createOverlayMap(points) {
    var latlng = new google.maps.LatLng(0.3103623222234959,32.57171667578132);

    var myOptions = {
        // center: latlng,
        // zoom: 13,
        scrollwheel: false,
        disableDoubleClickZoom: true,
        mapTypeId: google.maps.MapTypeId.ROADMAP
    };

    map = new google.maps.Map(document.getElementById("map_canvas"), myOptions);

    bounds = calculateBounds(map, points);
    updateMap(points);
}

function calculateBounds(map, points){
    var bounds = new google.maps.LatLngBounds();
    
    // extend our map bounds to fit all points
    var locs = 0;
    for (i in points) {
        var point = points[i];
        if (point.count > 0 && point.latlng) {
            bounds.extend(point.latlng);
            locs++;
        }
    }

    
    // if we have points, use those bounds
    if (locs <= 1){
        bounds.extend(new google.maps.LatLng(0.3103623222234959,32.57171667578132));
        map.fitBounds(bounds);
    }
    // many points, we can just fit within those bounds
    else if (locs){
        map.fitBounds(bounds);
    }
    // otherwise, just zoom out on our center point
    else {
        bounds = null;
    }

    return bounds;
}

function fireIfLastEvent(points){
    if (lastEvent.getTime() + 500 <= new Date().getTime()) {
        updateMap(points);
    }
}

function scheduleDelayedCallback(points){
    return function(){
	lastEvent = new Date();
	setTimeout(function(){ fireIfLastEvent(points) }, 500);
    }
}

function updateMap(points, force){

    var bounds = map.getBounds();
    if (bounds && (force || zoom != map.getZoom())) {

        // sort our points so we draw the largest ones first
        points = points.slice(0)
        points = points.sort(function(a, b) { return b.count - a.count; });

        // figure out our largest count
        var total = 0;
        var largestCount = 0;
        if (points.length > 0){
            largestCount = points[0].count;
            total += points[0].count;
        }

        // determine our map area to scale the circles accordingly
        var ne = bounds.getNorthEast();
        var sw = bounds.getSouthWest()
        var n = ne.lat();
        var e = ne.lng();
        var s = sw.lat();
        var w = sw.lng();

        var mapWidth = gcd(new google.maps.LatLng(n,w), new google.maps.LatLng(n,e));
        var mapHeight = gcd(new google.maps.LatLng(n,w), new google.maps.LatLng(s,w));
        var mapArea = mapWidth * mapHeight;

        // find the average distance
        var totalDistance = 0;
        var locationCount = 0;
        for (i in points) {
            if (points[i].latlng) {
                for (j in points) {
                    if (i != j) {
                        if (points[j].latlng) {
                            totalDistance += gcd(points[i].latlng, points[j].latlng)
                            locationCount++;
                        }
                    }
                }
            }
        }

        // largest circle is based on the average distnace of all points
        var avgDistance = (totalDistance / locationCount);

        // console.log("mapHeight    = " + mapHeight);
        // console.log("avg distance = " + avgDistance);
        var fullArea = mapHeight * .20; // avgDistance;
        if (Math.pow(avgDistance, 1.5) < mapHeight) {
            fullArea /= 2;
            // console.log("Reducing circle size due to avg distance");
        }

        // clear our current markers
        for (i in markers){
            markers[i].setMap(null);
        }
        markers = [];

        // console.log("Map zoom: " + map.zoom);
        for (i in points) {
            var point = points[i];
            if (point.latlng) {
                var area = fullArea * (point.count / largestCount);
                point.radius = Math.sqrt(area / 3.14);

                // console.log("Radius for " + point.count  + " = " + point.radius);
                var marker = addCircleMarker(map, point, total, point.html);
                markers[markers.length] = marker;
            }
        }

        zoom = map.getZoom();
    }

    google.maps.event.addListenerOnce(map, 'bounds_changed', scheduleDelayedCallback(points));
}

function addCircleMarker(map, point, total, html){
    var pct = Math.round((point.count / total) * 100);

    var mouseover = function(data) {
        clearMapInfo();
        updateCounts(data.name, data.name, data.count, data.color, pct, true);
    }

    var mouseout = function(data) {
        clearCounts();
    }

    var marker = new CircleOverlay(point.latlng, point.radius, point.color, 2, 1, point.color, .7, 40,
                                   "<div class='map_bubble'>" + html + "</div>",
                                   mouseover, mouseout, point);
    marker.name = point.name;

    if (point.href){
        marker.href = point.href;
    }

    marker.setMap(map);

    return marker;
}



function showMapInfo(name) {
    clearMapInfo(name);
    for (i in markers) {
        var marker = markers[i];
        if (marker && marker.data.name == name) {
            map.panTo(marker.latLng);
            marker.showInfo();
        }
    }
}

function clearMapInfo(name) {
    for (i in markers) {
        var marker = markers[i];
        if (marker.data.name != name) {
            marker.hideInfo();
        }
    }
}

function gcd(latlng1, latlng2) {
    var R = 6371; // earth radius in km
    var dLat = toRad(latlng2.lat()-latlng1.lat());
    var dLon = toRad(latlng2.lng()-latlng1.lng());

    var a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(toRad(latlng1.lat())) * Math.cos(toRad(latlng2.lat())) *
            Math.sin(dLon/2) * Math.sin(dLon/2);
    var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    var d = R * c;

    return d;
}

function toRad(deg) {
    return (deg * Math.PI / 180)
}
