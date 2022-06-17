function Go() {
    var complete = document.getElementsByName('complete')[0];
    if (document.getElementById('myCheck').checked) {
        console.log(complete)
        complete.disabled = '';
    } else {
        complete.disabled = 'disabled';
    }
}