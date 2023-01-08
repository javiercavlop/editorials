"use strict"

function main_base(){
    let urlForm = document.getElementById("url_form");
    let url = document.getElementById("url");

    checkBtn();

    url.addEventListener("change", function(){
        deleteErrors(urlForm);
    });
}

function deleteErrors(form){
    if(form.classList.contains("class-error-form")){
        form.classList.remove("class-error-form");
        let nodes = [];

        for (let i = 0; i < form.children.length; i++) {
            let node = form.children[i];
            if(node.classList.contains("class-error-message")){
                nodes.push(node);
            }
        }

        for (let node of nodes){
            node.parentNode.removeChild(node)
        }
        checkBtn();
    }
}

function checkBtn(){
    let btn = document.getElementById("url-btn");
    if(document.getElementsByClassName("class-error-form").length > 0){
        btn.disabled = true;
    } else{
        btn.disabled = false;
    }
}

function deleteDB(url, books){
    if(confirm("¿Estás seguro de que quieres borrar la base de datos? Se perderá un total de " + books.toString() + " libros")==true){
        return window.location.href = url;
    }
};

function populateDB(url){
    if(confirm("¿Estás seguro de que quieres extraer libros ahora? Este proceso es muy costoso y puede llevar varias horas")==true){
        return window.location.href = url;
    }
};

document.addEventListener("DOMContentLoaded", main_base);