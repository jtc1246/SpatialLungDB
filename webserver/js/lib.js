window.addEventListener('DOMContentLoaded', function() {
    var dropdowns = document.getElementsByClassName('lib-dropdown');
    for (var i = 0; i < dropdowns.length; i++) {
        try {
            var this_button = dropdowns[i].getElementsByTagName('button')[0];
            this_button.classList.add('lib-ignore-buttons');
            var this_menu = dropdowns[i].querySelector('.lib-dropdown > div');
            this_menu.classList.add('lib-ignore-popup');
            this_button.addEventListener('click', function(this_menu) { return function(event){
                if(this_menu.classList.contains('lib-ignore-dropdown-show')){
                    this_menu.classList.remove('lib-ignore-dropdown-show');
                }
                else {
                    lib_close_all();
                    this_menu.classList.add('lib-ignore-dropdown-show');
                }
                // console.log('button');
                event.stopPropagation();
            }}(this_menu), {passive: true});
        } catch (e) {
            console.log(e);
        }
    }
});

function lib_close_all(){
    var all_elements = document.getElementsByClassName('lib-ignore-popup');
    for (var i = 0; i < all_elements.length; i++) {
        all_elements[i].classList.remove('lib-ignore-dropdown-show');
    }
}

window.addEventListener('click', function() {
    lib_close_all();
    // console.log('window');
});

function is_firefox() {
    return navigator.userAgent.toLowerCase().indexOf('firefox') > -1;
}

window.addEventListener('DOMContentLoaded', function() {
    if(is_firefox()){
        document.getElementsByTagName('html')[0].classList.add('lib-ignore-firefox');
    }
});
