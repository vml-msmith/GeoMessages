var PGproxy = {
  "navigator": {
    "connection": function () {
      if (navigator.connection) {
        return navigator.connection;
      } else {
        console.log('navigator.connection');
        return {
          "type":"WIFI" // Avoids errors on Chrome
        };
      }
    },
    "notification": {
      "vibrate": function (a) {
        if (navigator.notification && navigator.notification.vibrate) {
          navigator.notification.vibrate(a);
        } else {
          console.log("navigator.notification.vibrate");
        }
      },
      "alert": function (a, b, c, d) {
        if (navigator.notification && navigator.notification.alert) {
          navigator.notification.alert(a, b, c, d);
        } else {
          console.log("navigator.notification.alert");
          alert(a);
        }
      }
    },
    "splashscreen": {
      "hide": function () {
        if (navigator.splashscreen) {
          navigator.splashscreen.hide();
        } else {
          console.log('navigator.splashscreen.hide');
        }
      }
    }
  }
};

var App = {
  "endpoint": "http://localhost:5000",
  "app_loaded": false,
  "testing_on_desktop": true,
  "access_token": null,
  "nearby": [],
  "nearby_last_update": null,
  "templates": {'row_template': '<li data-corners="false" data-shadow="false" data-iconshow="true" data-icon="arrow-r" data-iconpos="right" data-theme="c"><a href="#slide" data-rowid="#id">#type<h3>#title</h3><h4>#who #dist</h4><p>#date</p></a></li>',"test": "<div key='#key' class='row'><div class='type'>#type</div><div class='title'>#title</div><div class='distance'>#dist</div><div class='who'>#who</div><div class='date'>#date</div><div style='clear:both'></div></div>", 'slide_template': '<div class="hero">#hero</div><div class="note">#note</div>'},

  "createThumbnail": function(obj) {
    if (obj['thumbnail'] != null) {
      return '<img src="' + obj['thumbnail'] + '" />'
    }
    else {
      return '<img src="assets/imgs/writing.jpg" />'
    }
  },

  "createFriendsRowTemplate": function(row, key) {
    var thumbnail = App.createThumbnail(row);
    var custom_template = App.templates['row_template'];

    custom_template = custom_template.replace('#title', (row['title'] == null) ? '' : row['title']);
    custom_template = custom_template.replace('#dist', '<div class="distance">('+Math.round(row['distance'])+'m)</div>');
    custom_template = custom_template.replace('#who', row['author_name']);
    custom_template = custom_template.replace('#type', thumbnail);
    custom_template = custom_template.replace('#key', key);
    custom_template = custom_template.replace('#id', row['id']);
    d = new Date(row['date'] * 1000)
    custom_template = custom_template.replace('#date', d.getMonth() + '/' + d.getDate() + '/' + d.getFullYear());

    return custom_template;
  },

  "renderSlide": function(id) {
    App.utilities.log("[renderSlide]");

    $('#slide .content').empty();
    var slide = App.nearby[id];
    if (slide['photo'] != null) {
      var hero = '<img src="' + slide['photo'] + '" />'
    }
    else if (slide['video'] != null) {
      var hero = '<embed id="yt" src="http://www.youtube.com/v/'+slide['video']+'" width="300" height="199"></embed>';
    }
    else {
      var hero ='<img src="assets/imgs/writing.jpg" />';
    }
    var template = App.templates['slide_template'];

    $(template.replace('#note', slide['note']).replace('#hero', hero)).appendTo($('#slide .content'));

  },

  "renderNearbyList": function() {

    console.log("[renderNearbyList]")
    jQuery.mobile.loading('hide');
    jQuery('#nearby .rows').empty()

    if (App.nearby.length == 0) {
      jQuery('#nearby .emptyresults').show()
    }
    else {
      jQuery('#nearby .emptyresults').hide()
      var locations = App.nearby;
      for (var key in locations) {
        var row = locations[key];
        var custom_template = App.createFriendsRowTemplate(row, key)
        console.log(custom_template)
        var item = jQuery(custom_template);
        item.appendTo(jQuery('#nearby .rows'));
        item.trigger("create");
      }
      jQuery('#nearby .rows').listview().listview("refresh");
  }
  },


  "updateNearby": function(token) {
    if (App.nearby.length == 0) {
      jQuery.mobile.loading('show', { textVisilbe: false, text: "Searching...", theme:"b"  });
    }
    App.utilities.log("[updateNearby]");
    var d = new Date().getTime();
    if (App.nearby.length == 0 && (App.nearby_last_update == null || (App.nearby_last_update + 30000) < d)) {
      App.utilities.log("Do real update of nearby");
      App.nearby_last_update = d;
      navigator.geolocation.getCurrentPosition(
        function(position) { console.log("Position"); App.parsePosition(position); },
        function(error) { parseRest(null); alert('code: ' + error.message)});
    }
  },

  "parsePosition": function(position) {
    var url = App.endpoint + "/getMessages/" + App.access_token + "39.2128093367,-94.4940195736/500";

    if ( position != null) {
      var url = App.endpoint + "/getMessages/" + App.access_token + "/" + position.coords.latitude + "," + position.coords.longitude + "/500";
    }
    console.log(position);
    console.log(url);
    jQuery.getJSON(url,
                   function(data) {
                     console.log(data);
                     App.nearby = data.response;
                     App.renderNearbyList();
                   });
  },

  "doLogin": function(token) {
    var url = App.endpoint + "/getToken/facebook/" + token;
    App.utilities.log("[doLogin]")

    jQuery.mobile.loading('show', { textVisible: false  });

    jQuery.getJSON(url,
                   function(data) {
                     App.utilities.log(data);
                     if (data.status == 'success') {
                       App.access_token = data.response.token;

                       var options = {
                         success: function(responseText, statusText, xhr, $form) {
                           console.log(responseText); // What we want
                           console.log(statusText);
                           console.log(xhr);
                           console.log($form)
                         }
                       };

                       jQuery('#myForm').attr('action', App.endpoint + '/postMessage/' + App.access_token);
                       jQuery('#myForm').ajaxForm(options);
                       jQuery.mobile.changePage('#nearby');
                     }
                     else {
                       // give an error message.
                     }
                     jQuery.mobile.loading('hide');
                   });
  },

  "init": function() {
    App.utilities.log("[init]");
    App.utilities.log(document.URL);

    if (document.URL.indexOf("http://") === -1) {
      App.testing_on_desktop = false;
    }

    jQuery(document).ready(function () {
      App.utilities.log("jQuery finished loading");

      var deviceReadyDeferred = jQuery.Deferred();
      var jqmReadyDeferred = jQuery.Deferred();

      if (App.testing_on_desktop) {
        App.utilities.log("PhoneGap finished loading");
        _onDeviceReady();
        deviceReadyDeferred.resolve();
      } else {
        document.addEventListener("deviceReady", function () {
          App.utilities.log("PhoneGap finished loading");
          _onDeviceReady();
          deviceReadyDeferred.resolve();
        }, false);
      }

      jQuery(document).one("pageinit", function () {
        App.utilities.log("jQuery.Mobile finished loading");
        jqmReadyDeferred.resolve();
      });

      jQuery.when(deviceReadyDeferred, jqmReadyDeferred).then(function() {
        App.utilities.log("PhoneGap & jQuery.Mobile finished loading");
        initPages();
        App.utilities.log("App finished loading");
        App.app_loaded = true;
      });
    });

    function _onDeviceReady() {
      App.utilities.log("[onDeviceReady]");
      PGproxy.navigator.splashscreen.hide();
      if (App.testing_on_desktop == false) {
        FB.init({ appId: "1413269382263313", nativeInterface: CDV.FB, useCachedDialogs: false });
      }
    }

    function initPages() {
      App.utilities.log("[initPages]");

      var options = {
        success: function(responseText, statusText, xhr, $form) {
          console.log(responseText); // What we want
          console.log(statusText);
          console.log(xhr);
          console.log($form)
        }
      };
      jQuery('form').ajaxForm(options);
      jQuery(document).bind("pageinit", _initPages);

      if (App.testing_on_desktop == true) {
        App.access_token = 'f84133f3-9522-4011-b348-8c658e20837c';
        jQuery.mobile.changePage('#nearby');
      }
      function _initPages () {
        console.log(App)
        if (App.access_token == null) {
          jQuery.mobile.changePage('#login');
        }

        console.log("Test Init");
//        jQuery.mobile.changePage('#login');
      };
    };
  },
  "utilities": {
    "log": function(message) {
      console.log(message);
    }
  }
};
