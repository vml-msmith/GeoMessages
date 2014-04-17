var App = {
  "app_loaded": false,
  "testing_on_desktop": true,
  "init": function() {
    App.utilities.log("[init]");

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
    };

    function initPages() {
    };
  },
  "utilities": {
    "log": function(message) {
      console.log(message);
    }
  }
};
