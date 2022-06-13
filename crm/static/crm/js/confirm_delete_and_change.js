function ok() {
    return confirm('Are you sure you want to delete this user??');
}

function mail(id) {
    var user = document.getElementById(id);
    var change_mail = user.querySelector("[name='change_mail']").value;
    var new_mail = prompt('Change email:', change_mail);
    var reg = /^([A-Za-z0-9_\-\.])+\@([A-Za-z0-9_\-\.])+\.([A-Za-z]{2,4})$/;
    if(reg.test(new_mail) == false) {
        alert('email is not correct');
        return false;
    } else {
        user.querySelector("[name='change_mail']").value = [new_mail, id];
    }
}