/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */


var app = {
  // Application Constructor
  initialize: function() {
    this.bindEvents();
    this.user = null;
    this.slide = null;
    this.nearby = [];
    this.templates = {'row_template': "<div key='#key' class='row'><div class='type'>#type</div><div class='title'>#title</div><div class='distance'>#dist</div><div class='who'>#who</div><div class='date'>#date</div><div style='clear:both'></div></div>", 'slide_template': '<div class="back">&lt; Back</div><div class="hero">#hero</div><div class="note">#note</div>'};

  },

  createThumbnail: function(obj) {
    if (obj['thumbnail'] != null) {
      return '<img src="' + obj['thumbnail'] + '" width=50px height=50px/>'
    }
    else {
      return '?';
    }
  },

  createFriendsRowTemplate: function(row, key) {
    var thumbnail = this.createThumbnail(row);
    var custom_template = this.templates['row_template'];

    custom_template = custom_template.replace('#title', (row['title'] == null) ? '' : row['title']);
    custom_template = custom_template.replace('#dist', '(200m) ');
    custom_template = custom_template.replace('#who', row['author_name']);
    custom_template = custom_template.replace('#type', thumbnail);
    custom_template = custom_template.replace('#key', key);

    return custom_template;
  },

  renderSlide: function() {
    $('#slide').empty();
    var slide = this.currentSlide;

    if (slide['photo'] != null) {
      var hero = '<img src="' + slide['photo'] + '">'
    }
    else if (slide['video'] != null) {
      var hero = '<embed id="yt" src="http://www.youtube.com/v/'+slide['video']+'" width="300" height="199"></embed>';
    }
    else {
      var hero ='Meh';
    }
    var template = this.templates['slide_template'];

    $(template.replace('#note', slide['note']).replace('#hero', hero)).appendTo($('#slide'));

    $('.back').bind('click', function() {
      $('#slide').hide();
      $('#nearby').show();
    });
  },

  renderNearbyList: function() {
    // Clear out the current rows so we can draw new ones.
    $('#nearby .rows').empty();

    // Loop through this.nearby and create all the rows.
    var locations = this.nearby;
    for (var key in locations) {
      var row = locations[key];
      var custom_template = this.createFriendsRowTemplate(row, key)
      var item = $(custom_template);
      item.appendTo($('#nearby .rows'));
    }

    // Bind each row's "click" to show the slide.
    var me = this;
    $('#nearby .row').bind('click', function(e) {
      e.preventDefault();
      me.currentSlide = me.nearby[$(this).attr('key')];
      me.renderSlide();

      $('#nearby').hide();
      $('#slide').show();
    });
  },

  // Bind Event Listeners
  //
  // Bind any events that are required on startup. Common events are:
  // 'load', 'deviceready', 'offline', and 'online'.
  bindEvents: function() {
    document.addEventListener('deviceready', this.onDeviceReady, false);
  },

  // deviceready Event Handler
  //
  // The scope of 'this' is the event. In order to call the 'receivedEvent'
  // function, we must explicity call 'app.receivedEvent(...);'
  onDeviceReady: function() {
    app.receivedEvent('deviceready');
    update_list();
    if (this.user == null) {
      $('#login').hide();
      $('#page').show();
/*
      try {
        // Show the login page.
        FB.init({ appId: "appid", nativeInterface: CDV.FB, useCachedDialogs: false });
     //   document.getElementById('data').innerHTML = "";
      } catch (e) {
        alert(e);
      }
*/
    }
    else {
      $('#login').hide();
      $('#page').show();

      // Show the home page.
    }
  },
    // Update DOM on a Received Event
    receivedEvent: function(id) {
//      update_list();
/*
        var parentElement = document.getElementById(id);
        var listeningElement = parentElement.querySelector('.listening');
        var receivedElement = parentElement.querySelector('.received');
*/
//        listeningElement.setAttribute('style', 'display:none;');
      //      receivedElement.setAttribute('style', 'display:block;');

        console.log('Received Event: ' + id);
    }
};


			$(function() {
				var $menu = $('nav#menu'),
					$html = $('html, body');

				$menu.mmenu();
				$menu.find( 'li > a' ).on(
					'click',
					function()
					{
						var href = $(this).attr( 'href' );

						//	if the clicked link is linked to an anchor, scroll the page to that anchor
						if ( href.slice( 0, 1 ) == '#' )
						{
              $('.section').hide();
              $(href).show();
              console.log($('h1', $(href)));
              var title = $('h1',$(href)).clone();
              $('#section-title').empty();
              $('#section-title').append(title);
              if (href == '#nearby') {
                update_list();
              }
							$menu.one(
								'closed.mm',
								function()
								{
									setTimeout(
										function()
										{
										}, 0
									);
								}
							);
						}
					}
				);
			});


      var row_template = "<div key='#key' class='row'><div class='type'>#type</div><div class='title'>#title</div><div class='distance'>#dist</div><div class='who'>#who</div><div class='date'>#date</div><div style='clear:both'></div></div>";
      var slide_template = '<div class="back">&lt; Back</div><div class="hero">#hero</div><div class="note">#note</div>';
var locations = [];

var do_rest_stuff = function(position) {
  var url = "http://localhost:5000/getNearby/1/39.2128093367,-94.4940195736/100";

  if ( position != null) {
    var url = "http://localhost:5000/getNearby/1/"+position.coords.latitude+","+position.coords.longitude+"/100";
  }

  jQuery.getJSON(url,
                 function(data) {
                   app.nearby = data.results;
                   app.renderNearbyList();
                 });
}

var update_list = function() {
  navigator.geolocation.getCurrentPosition(do_rest_stuff, function(error) { do_rest_stuff(null); alert('code: ' + error.message)});
}


$(document).ready(function() {
  update_list();
});
