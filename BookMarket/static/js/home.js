
$(document).ready(function () {
    "use strict";
  
    $('#buy_img').hover(function () {
      $(this).attr("src", "../static/img/features/buy-hover.png");
    }, function () {
      $(this).attr("src", "../static/img/features/buy.png")
    });
  
    $('#sell_img').hover(function () {
      $(this).attr("src", "../static/img/features/sell-hover.png");
    }, function () {
      $(this).attr("src", "../static/img/features/sell.png")
    });
  
    $('#trade_img').hover(function () {
      $(this).attr("src", "../static/img/features/trade-hover.png");
    }, function () {
      $(this).attr("src", "../static/img/features/trade.png")
    });
  
    var $animation_elements = $('.animation-element');
    var $window = $(window);
    
    function check_if_in_view() {
      // console.log("Triggered")
      var window_height = $window.height();
      var window_top_position = $window.scrollTop();
      var window_bottom_position = (window_top_position + window_height);
    
      $.each($animation_elements, function() {
        var $element = $(this);
        var element_height = $element.outerHeight();
        var element_top_position = $element.offset().top;
        var element_bottom_position = (element_top_position + element_height);
    
        //check to see if this current container is within viewport
        if ((element_bottom_position >= window_top_position) &&
          (element_top_position <= window_bottom_position)) {
          $element.addClass('in-view');
        } else {
          $element.removeClass('in-view');
        }
      });
    }
    
    $window.on('scroll resize', check_if_in_view);
    $window.trigger('scroll');
  });
  