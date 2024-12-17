const ACTION_MOUSE_ENTER = 1;
const ACTION_MOUSE_LEAVE = 2;
const ACTION_AUTO_CALL = 3;

const STATUS_DISABLE = 5;
const STATUS_EXTENDING = 6;
const STATUS_FINISHED = 7;

const ANIMATION_DURATION_MS = 400;

var menu_level = 0;
var gallery_offset = 0;


const GLB_SLIDE_SERVER_URL = 'http://jtc1246.github.io/cosmx-img-compressed'
const GLB_DATA_SERVER_URL = 'http://128.84.8.183/data'
const GLB_API_SERVER_URL = 'http://128.84.8.183/api'
const GLB_AI_CHAT_URL = '/chat'


function mouse_enter(func) {
    return function() {
        func(ACTION_MOUSE_ENTER, this);
    };
}

function mouse_leave(func) {
    return function() {
        func(ACTION_MOUSE_LEAVE, this);
    };
}

function ease_func(t) {
    return 1 - Math.pow(1 - t, 3);
}

function create_nav_item_function() {
    var level = 0;
    var status = STATUS_DISABLE;

    function update(action, button) {
        if (action == ACTION_MOUSE_ENTER) {
            status = STATUS_EXTENDING;
        }
        if (action == ACTION_MOUSE_LEAVE) {
            level = 0;
            status = STATUS_DISABLE;
            button.style.setProperty('--nav-hover-width', '0%');
            button.style.setProperty('--nav-hover-bg-transparency', '0');
            button.style.setProperty('--nav-hover-shadow', '0');
        }
        if (action == ACTION_AUTO_CALL) {
            if (status == STATUS_EXTENDING) {
                level += 5 / ANIMATION_DURATION_MS;
                if (level >= 1) {
                    status = STATUS_FINISHED;
                    level = 1;
                }
                button.style.setProperty('--nav-hover-width', ease_func(level) * 100 + '%');
                button.style.setProperty('--nav-hover-bg-transparency', ease_func(level) * 0.06);
                button.style.setProperty('--nav-hover-shadow', ease_func(level) * 0.4);
            }
            setTimeout(update, 5, ACTION_AUTO_CALL, button);
        }
    }
    return update;
}


window.addEventListener('DOMContentLoaded', function() {
    var nav_elements = document.querySelectorAll('#nav>a');
    // console.log(nav_elements.length);
    for (var i = 0; i < nav_elements.length; i++) {
        var func = create_nav_item_function();
        nav_elements[i].addEventListener('mouseenter', mouse_enter(func));
        nav_elements[i].addEventListener('mouseleave', mouse_leave(func));
        setTimeout(func, 5, ACTION_AUTO_CALL, nav_elements[i]);
    }
});

setTimeout(function() {
    try {
        valid_status = 1;
    } catch (e) {}
}, 50);

var _0xc83e2f94;