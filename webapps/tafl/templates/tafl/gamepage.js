var clicked = false;
var piece = null;
var dest = null;

function getCookie(c_name){
  if (document.cookie.length > 0)
  {
    c_start = document.cookie.indexOf(c_name + "=");
    if (c_start != -1)
    {
      c_start = c_start + c_name.length + 1;
      c_end = document.cookie.indexOf(";", c_start);
      if (c_end == -1) c_end = document.cookie.length;
      return unescape(document.cookie.substring(c_start,c_end));
    }
  }
  return "";
}

$(function () {
  $.ajaxSetup({
    headers: { "X-CSRFToken": getCookie("csrftoken") }
  });
});

$('#chatForm').on('submit', function (e) {
  e.preventDefault();
  $.ajax({
    type: 'post',
    url: "{% url 'sendMessage' %}",
    data: $("#chatForm").serialize(),
    error: function (html) {
      console.log(html);
    }
  });
  $("#inputUserPost").val("");
});

$('.board-cell').click(function(event) {
  if(clicked){  
    dest = $(this);
    $.ajax({
      type: 'POST',
      url: "{% url 'game' %}",
      data: {move: "[" + piece.parent().attr('data-id') + ", " + $(this).attr('data-id') + "]"},
      success: function (html) {
        //console.log(piece.parent().attr('data-id') + " => " + dest.attr('data-id'));
        if(html == "valid"){
          var temp = piece.detach();
          dest.append(temp);
        } else{
          console.log(html);
        }
      },
      error: function (html) {
        console.log(html);
      }
    });
    piece.parent().css('background-color', '');
    clicked = false;
  }
});

$('.tafl-piece').click(function(event) {
  {% if game.white_player == player%}
    var color = "white"
  {% else %}
    var color = "black"
  {% endif %}
  if($(this).hasClass(color)){
    event.stopPropagation();
    clicked = true;
    if(piece != null)
      piece.parent().css('background-color', '');
    piece = $(this);
    piece.parent().css('background-color', 'red');
  }
});

//========= FORMS/MOVES /\ ================

//=========  WEBSOCKETS \/ ================

{% if game.waiting_player %}
  jQuery(document).ready(function($) {
    $("#waitingModal").modal({backdrop: "static"});
  });
{% endif %}

jQuery(document).ready(function($) {
  size = ($("#board-container").width()-36)/9
  $(".board-cell").width(size);
  $(".board-cell").height(size);
  var elem = document.getElementById('chat_messages');
  elem.scrollTop = elem.scrollHeight;
  var ws4redis = WS4Redis({
    uri: '{{ WEBSOCKET_URI }}game_move?subscribe-user',
    receive_message: receiveMessage_move,
    heartbeat_msg: {{ WS4REDIS_HEARTBEAT }}
  });

  var ws4redis2 = WS4Redis({
    uri: '{{ WEBSOCKET_URI }}chat?subscribe-user',
    receive_message: receiveMessage_chat,
    heartbeat_msg: {{ WS4REDIS_HEARTBEAT }}
  });

  var ws4redis3 = WS4Redis({
    uri: '{{ WEBSOCKET_URI }}game_join?subscribe-user',
    receive_message: receiveMessage_join,
    heartbeat_msg: {{ WS4REDIS_HEARTBEAT }}
  });
});

function receiveMessage_move(msg) {
  //TODO: Neater
  msg = JSON.parse(msg)
  if(msg["capture"]){
    console.log("Capture " + msg['pos'][0] + ", " + msg['pos'][1]);
    src = $('[data-id="[' + msg['pos'][0] + ", " + msg['pos'][1] + ']"]').children(":first");
    src.detach();
  } else if (msg["win"]){
    window.location.replace("/tafl/");
  } 
  else{
    console.log("Moved")
    src = $('[data-id="[' + msg['move'][0][0] + ", " + msg['move'][0][1] + ']"]').children(":first");
    dst = $('[data-id="[' + msg['move'][1][0] + ", " + msg['move'][1][1] + ']"]');
    var temp = src.detach();
    dst.append(temp);
  }
}

function receiveMessage_chat(msg) {
  msg = JSON.parse(msg);
  $("#chat_messages").append(msg['name'] + ": " + msg['text'] + "<br>")
  var elem = document.getElementById('chat_messages');
  elem.scrollTop = elem.scrollHeight;
}

function receiveMessage_join(msg) {
  msg = JSON.parse(msg);
  $("#waitingModal").modal("hide");
  $("#opponent_title").html(msg);
}

$(window).resize(function() {
  size = ($("#board-container").width()-36)/9
  $(".board-cell").width(size);
  $(".board-cell").height(size);
});