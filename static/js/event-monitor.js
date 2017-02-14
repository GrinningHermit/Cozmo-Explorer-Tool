init_websocket = function() {
    socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    socket.on('my_response', function (msg) {
        console.log(msg.data);
        let stamp = '';
        if(msg.time != undefined){
            stamp = '<li><span>' + msg.time + '</span>' + msg.data + '</li>'
        } else {
                stamp = '<li>' + msg.data + '</li>'
        }
        $('#event-content').prepend(stamp);
    });
};
