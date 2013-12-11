$(document).ready(function(){

    $(".char_counter").each(function() {

        // see if there is a counter limit specified
        var limit = $(this).attr('limit');
        if (!limit) { limit = 160; }

        $(this).jqEasyCounter({'maxChars': limit,
                    'maxCharsWarning': limit,
                    'msgFontSize': '10px',
                    'msgTextAlign': 'right',
                    'msgAppendMethod': 'insertAfter'});
    });
});

$.fn.equalHeights = function(px) {
    $(this).each(function(){
	var currentTallest = 0;
	$(this).children().each(function(i){
	    if ($(this).height() > currentTallest) { currentTallest = $(this).height(); }
	});
	if (!px && Number.prototype.pxToEm) currentTallest = currentTallest.pxToEm(); //use ems unless px is specified
	// for ie6, set height since min-height isn't supported
	if ($.browser.msie && $.browser.version == 6.0) { $(this).children().css({'height': currentTallest}); }
	$(this).children().css({'min-height': currentTallest}); 
    });
    return this;
};

$.fn.centerVertically = function() {
    return this.each(function(i){
    var height = $(this).height();
    var parentHeight = $(this).parent().height();
    var marginTop = Math.ceil((parentHeight-height) / 2);

    $(this).css('padding-top', marginTop);
    });
};












