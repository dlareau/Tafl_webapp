var clicked = false;
var piece = null;
var dest = null;
{% if game.turn %}
  var turn = true;
{% else %}
  var turn = false;
{% endif %}

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
          turn = !turn;
          change_turn_ids();
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
    var color = "white";
  {% else %}
    var color = "black";
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

function change_turn_ids(){
  if (turn) {
    $(".white-id").show();
    $(".black-id").hide();
  } else {
    $(".black-id").show();
    $(".white-id").hide();
  }
}

{% if game.waiting_player %}
  jQuery(document).ready(function($) {
    $("#waitingModal").modal({backdrop: "static"});
  });
{% endif %}

jQuery(document).ready(function($) {
  // Various init tasks
  change_turn_ids();
  size = ($("#board-container").width()-36)/9
  $(".board-cell").width(size);
  $(".board-cell").height(size);
  var elem = document.getElementById('chat_messages');
  elem.scrollTop = elem.scrollHeight;

  // init websockets
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
    src = $('[data-id="[' + msg['pos'][0] + ", " + msg['pos'][1] + ']"]').children(":first");
    src.detach();
  } else if (msg["win"]){
    window.location.replace("/tafl/");
  } 
  else{
    turn = !turn;
    change_turn_ids();
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

$('#chat_disable').change(
  function(){
    if (this.checked) {
      $('#chat_messages').hide();
      $('#inputUserPost').attr("disabled", true);
      $('#ChatPostButton').attr("disabled", true);
      $("#inputUserPost").val("Disabled");
    } else {
      $('#chat_messages').show();
      $('#inputUserPost').removeAttr("disabled");
      $('#ChatPostButton').removeAttr("disabled");
      $("#inputUserPost").val("");
    }
  });

$(window).resize(function() {
  size = ($("#board-container").width()-36)/9;
  $(".board-cell").width(size);
  $(".board-cell").height(size);
});