// Circle overlay extension for Google Maps
// App Delegate Inc <http://appdelegateinc.com> 2010
// with modifications (updated to GMaps3 api) by Squiggled.co.uk
// This file adds a new CircleOverlay to GMaps3 to draw a circle on a map with stroke and fill
// Constructor
var CircleOverlay = function(latLng, radius, strokeColor, strokeWidth, strokeOpacity, fillColor, fillOpacity, numPoints, infoHtml, mouseover, mouseout, data) {

    // don't move forward without a lat/lng, blows shit up
    if (!latLng || !latLng.lat() || !latLng.lng()){
        console.log("WARN: CircleOverlay created with null latLng: " + latLng.lat() + ", " + latLng.lng());
        return;
    }

    this.latLng = latLng;
    this.radius = radius;
    this.strokeColor = strokeColor;
    this.strokeWidth = strokeWidth;
    this.strokeOpacity = strokeOpacity;
    this.fillColor = fillColor;
    this.fillOpacity = fillOpacity;
    this.strokeWeight = 1;
    this.infoHtml = infoHtml;
    this.data = data;
    this.mouseover = mouseover;
    this.mouseout = mouseout;
    this.info = null;
    

    // Set resolution of polygon
    if (typeof(numPoints) == 'undefined') {
        this.numPoints = 40
    } else {
        this.numPoints = numPoints;
    }
    
}

// Inherit from OverlayView
CircleOverlay.prototype = new google.maps.OverlayView();

// GMaps initialize callback
CircleOverlay.prototype.initialize = function(map) {
    this.map = map;
}

// Reset overlay
CircleOverlay.prototype.clear = function() {
    if (this.polygon != null && this.polygon.map != null) {
        this.polygon.setMap(null);
    }
}

// Calculate all the points of the circle and draw them
CircleOverlay.prototype.draw = function(force) {
    if (!this.latLng){
        return;
    }

    var d2r = Math.PI / 180;
    circleLatLngs = new Array();

    // Convert statute miles into degrees latitude
    var circleLat = this.radius * 0.014483;
    var circleLng = circleLat / Math.cos(this.latLng.lat() * d2r);


    // Create polygon points (extra point to close polygon)
    for (var i = 0; i < this.numPoints + 1; i++) {
        // Convert degrees to radians
        var theta = Math.PI * (i / (this.numPoints / 2));
        var vertexLat = this.latLng.lat() + (circleLat * Math.sin(theta));
        var vertexLng = this.latLng.lng() + (circleLng * Math.cos(theta));
        var vertextLatLng = new google.maps.LatLng(vertexLat, vertexLng);
        circleLatLngs.push(vertextLatLng);
    }

    this.clear();
    this.polygon = new google.maps.Polygon({
        paths: circleLatLngs,
        strokeColor: this.strokeColor,
        strokeWidth: this.strokeWidth,
        strokeOpacity: this.strokeOpacity,
        strokeWeight: this.strokeWidth,
        fillColor: this.fillColor,
        fillOpacity: this.fillOpacity
    });
    
    var polygon = this.polygon;
    polygon.overlay = this;
    polygon.mouseover = this.mouseover;
    polygon.mouseout = this.mouseout;
    polygon.data = this.data;
    
    var action = null;
    
    google.maps.event.addListener(polygon, 'mouseover', function() { 
        polygon.strokeOpacity = 1;

        /*action = setTimeout(function() {
            if (polygon.mouseover) {
                polygon.mouseover(polygon.data);
            }
            polygon.overlay.showInfo();
        }, 150);*/
    });
    
    google.maps.event.addListener(polygon, 'click', function() {
        if (polygon.overlay.href) {
            polygon.overlay.showInfo();
            // document.location = polygon.overlay.href;
        }
    });
    
    google.maps.event.addListener(polygon, 'mouseout', function(evt) { 
        /*
        polygon.strokeOpacity = .75;
                
        if (action) {
            clearTimeout(action);
        }

        if (polygon.overlay.info) {
            if (!polygon.overlay.info.sticky) {
                polygon.overlay.info.close();
                polygon.overlay.info = null;
            }
        }

        if (polygon.mouseout) {
            polygon.mouseout(polygon.data);
        }*/
    
    });
    
    this.polygon.setMap(this.map);
}

CircleOverlay.prototype.setMouseEvents = function(mouseover, mouseout) {
    google.maps.event.addListener(this.polygon, 'mouseover', mouseover);
    google.maps.event.addListener(this.polygon, 'mouseout', mouseout);
}

CircleOverlay.prototype.hideInfo = function() {
    if (this.info) {
        this.info.close();
        this.info = null;
    }
}

CircleOverlay.prototype.showInfo = function() {

    if (!this.latLng){
        return;
    }
    
    if (!this.info) {
        this.info = new InfoBubble({
            map: this.map,
            content: this.infoHtml,
            padding: 0,
            borderRadius: 4,
            arrowSize: 10,
            borderWidth: 1,
            borderColor: '#2c2c2c',
            backgroundColor: 'rgb(255,255,255)',
            disableAutoPan: false,
            hideCloseButton: false,
            arrowPosition: 30,
            shadowStyle:1,
            arrowStyle: 2,
            position: this.latLng,
            disableAnimation: true
        });
        
        var overlay = this;
        google.maps.event.addListener(this.info, "closeclick", function() { 
            overlay.info = null;
        });

        this.info.open();
    }
}

// Get the internal marker
CircleOverlay.prototype.polygon = function() {
    return this.polygon;
}

// Remove circle method
CircleOverlay.prototype.remove = function() {
    this.clear();
    this.polygon = null;
    this.map = null;
}

// Set radius of circle
CircleOverlay.prototype.setRadius = function(radius) {
    this.radius = radius;
}

// Set center of circle
CircleOverlay.prototype.setLatLng = function(latLng) {
    this.latLng = latLng;
}