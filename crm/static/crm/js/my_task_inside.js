function delegateOn() {
    var dep = document.getElementsByName('department')[0];
    var pos = document.getElementsByName('position')[0];
    if (document.getElementById('notMyTask').click) {
        dep.disabled = '';
        pos.disabled = '';
    }
}

function delegateOff() {
    var dep = document.getElementsByName('department')[0];
    var pos = document.getElementsByName('position')[0];
    if (document.getElementById('myCheck').click) {
        dep.disabled = 'disabled';
        pos.disabled = 'disabled';
    }
}
