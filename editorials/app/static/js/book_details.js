"use strict"

function main(){

    /* Load suggestions */

    let productId = window.location.pathname.split("/")[2];

    getSuggestions(productId).then(response => {
            
        let showcase = document.getElementsByTagName('showcase')[0];
        let current_url = window.location.href;
        let domain = current_url.split("/")[0] + "//" + current_url.split("/")[2];

        for(let suggestion of response.suggestions){
            
            let showcaseElement = document.createElement('div');
            showcaseElement.classList.add('showcase-element');

            let elementImg = document.createElement('img');
            elementImg.src = `${suggestion.cover}`;
            elementImg.alt = suggestion.title;
            showcaseElement.appendChild(elementImg);

            let elementLink = document.createElement('a');
            elementLink.href = domain + `/book/${suggestion.id}`;
            elementLink.innerHTML = "Ver libro";
            elementLink.classList.add('class-link');
            showcaseElement.appendChild(elementLink);

            showcase.appendChild(showcaseElement);

        }
    })

}

async function getSuggestions(product_id) {

    let current_url = window.location.href;
    let domain = current_url.split("/")[0] + "//" + current_url.split("/")[2];
    let url = domain + `/suggestions/${product_id}`;

    // Default options are marked with *
    const response = await fetch(url, {
        method: 'GET', // *GET, POST, PUT, DELETE, etc.
        mode: 'cors', // no-cors, *cors, same-origin
        cache: 'no-cache', // *default, no-cache, reload, force-cache, only-if-cached
        credentials: 'same-origin', // include, *same-origin, omit
        headers: {
            'Content-Type': 'application/json',
            "X-CSRFToken": getCookie('csrftoken'),

            // 'Content-Type': 'application/x-www-form-urlencoded',
        }, redirect: 'follow', // manual, *follow, error
        referrerPolicy: 'no-referrer', // no-referrer, *no-referrer-when-downgrade, origin, origin-when-cross-origin, same-origin, strict-origin, strict-origin-when-cross-origin, unsafe-url
    },);


    return response.json(); // parses JSON response into native JavaScript objects
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.addEventListener("DOMContentLoaded", main);