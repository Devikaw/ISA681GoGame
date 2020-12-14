$(document).ready(bind_events);

function bind_events() {
  var current_position;

  var $black_squares = $('tr:nth-child(odd) td:nth-child(even), tr:nth-child(even) td:nth-child(odd)');
  $black_squares.click(function () {
     if (current_position === undefined) {
      var pieces = pieces_on_board();
      $.post('/first_move/' + gamename,
        {
          x: $(this).data('x'),
          y: $(this).data('y'),
          pieces: pieces,
          pieces_count: pieces.length,
          last_move: GameConfig.last_move
        },
        function (data, status) {
          setTimeout(function () {
            $('body').html(data);
            bind_events();
          }, 300);
        }
      );
    } else {
      destination = {
        x: $(this).data('x'),
        y: $(this).data('y'),
        offset_left: $(this).offset().left,
        offset_top: $(this).offset().top
      }

      var translate_x = destination.offset_left - current_position.offset_left;
      var translate_y = destination.offset_top - current_position.offset_top;

      $selected_piece.css({
        transform: 'translate(' + translate_x + 'px, ' + translate_y + 'px)',
        transition: 'transform .3s'
      });

      var pieces = pieces_on_board();
      $.ajaxSetup({
                  beforeSend: function(xhr) {
                      xhr.setRequestHeader('X-CSRFToken', csrf_token);
                  }
      });

      $.post('/move',
        {
          cur_x: current_position.x,
          cur_y: current_position.y,
          dst_x: destination.x,
          dst_y: destination.y,
          pieces: pieces,
          pieces_count: pieces.length,
          board_size: $('tr').length,
          last_move: GameConfig.last_move
        },
        function (data, status) {
          setTimeout(function () {
            $('body').html(data);
            bind_events();
          }, 300);
        }
      );
    }
  });
}

function pieces_on_board() {
  var board_state = [];

  $('.board__piece').each(function () {
    var color;
    if ($(this).hasClass('board__piece--dark')) {
      color = 'DarkPiece';
    }
    if ($(this).hasClass('board__piece--light')) {
      color = 'LightPiece';
    }

    board_state.push({
      x: $(this).parent().data('x'),
      y: $(this).parent().data('y'),
      color: color
    });
  });

  return board_state;
}

function check_if_someone_won() {
  var num_of_light_pieces = $('.board__piece--light').length;
  var num_of_dark_pieces = $('.board__piece--dark').length;
  var pieces = pieces_on_board();

  if (num_of_light_pieces > num_of_dark_pieces) {
    alert('Light pieces won!')
  }

  if (num_of_dark_pieces === 0) {
    alert('Dark pieces won!')
  }
  $.post('/stop_game/' + gamename,
    {
      light_pieces: num_of_light_pieces,
      dark_pieces: num_of_dark_pieces
    },
    function (data, status) {
      setTimeout(function () {
        $('body').html(data);
        bind_events();
      }, 300);
    }
  );
}

function show_other_player_move() {
  var pieces = pieces_on_board();
  $.post('/update_board/' + gamename,
    function (data, status) {
      setTimeout(function () {
        $('body').html(data);
        bind_events();
      }, 300);
    }
  );
}
