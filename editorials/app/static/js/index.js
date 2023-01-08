"use strict"

function main(){

    // In-out card animation

    let productCard = document.getElementsByClassName("class-card");

    for (let product of productCard) {
        product.addEventListener("mouseover", function(){
            document.querySelectorAll(".selectbox").forEach(input => {
                input.style.opacity = "0";
                input.style.transition = "all 1s";
            })
        });
    
        product.addEventListener("mouseout", function(){
            document.querySelectorAll(".selectbox").forEach(input => {
                input.style.opacity = "1";
                input.style.transition = "all 1s";
            })
        });   
    }

    // Filters button

    let filtersButton = document.getElementById("filters-wrapper-menu-activation-button")
    let filtersBackground = document.getElementById("filters-background");
    let filtersWrapper = document.getElementById("filters-wrapper");
    let closeMenuButton = document.getElementById("filters-wrapper-menu-close-button");

    if(filtersButton != null){
        filtersButton.addEventListener("click", function(event){

            filtersBackground.classList.toggle("filters-background-active");
            filtersWrapper.classList.toggle("filters-active");
        });
    
        filtersBackground.addEventListener("click", function(event){
            filtersBackground.classList.toggle("filters-background-active");
            filtersWrapper.classList.toggle("filters-active");
        });
    
        closeMenuButton.addEventListener("click", function(event){
            filtersBackground.classList.toggle("filters-background-active");
            filtersWrapper.classList.toggle("filters-active");
        });
    }

    // Filters

    let urlSearchParams = new URLSearchParams(window.location.search);
    let oldParams = Object.fromEntries(urlSearchParams.entries());
    let newParams = {};

    let sortFiltersInputs = document.getElementsByClassName("sort-filter-input");

    for (let sortFilterInput of sortFiltersInputs) {
        sortFilterInput.addEventListener("click", function(event){

            for (let sortFilterInputToUncheck of sortFiltersInputs){

                if(sortFilterInput.name != sortFilterInputToUncheck.name){
                    sortFilterInputToUncheck.checked = false;   
                }
            }

            if(sortFilterInput.checked){
                newParams["order-by"] = sortFilterInput.value;
            }else{
                delete newParams["order-by"];
            }

        });   
    }

    let applyFiltersButton = document.getElementById("apply-filters-button");

    if(applyFiltersButton != null){
        applyFiltersButton.addEventListener("click", function(event){

            let newLocation = window.location.pathname + "?";
            let collectionFilter = document.querySelector("#collectionFilter").value;
            let categoryFilter = document.querySelector("#categoryFilter").value;
    
            for(let param in oldParams){
                if(!newParams[param]){
                    newParams[param] = oldParams[param];
                }
            }
    
            for(let param in newParams){
                newLocation += param + "=" + newParams[param] + "&";
            }

            if(collectionFilter != "Elige una colección..." && categoryFilter != "Elige una categoría..."){
                window.location.href = newLocation + "collection=" + collectionFilter + "&category=" + categoryFilter;
            }else if(collectionFilter != "Elige una colección..."){
                window.location.href = newLocation + "collection=" + collectionFilter;
            }else if(categoryFilter != "Elige una categoría..."){
                window.location.href = newLocation + "category=" + categoryFilter;
            }else{
                window.location.href = newLocation;
            }
    
        });
    }

    // Responsive titles

    let itemsTitles = document.getElementsByClassName("class-item-title");

    for (let itemTitle of itemsTitles) {

        itemTitle.addEventListener("scroll", scrollHandler);

        itemTitle.scroll({
            top: 1,
            behavior: 'smooth'
        });
    }

}

function scrollHandler(event){
    setInterval(function() {
        if(event.target.scrollTop >= event.target.scrollHeight-50 ){    
            event.target.scroll({
                top: 0,
                behavior: 'smooth'
            });
        }else{
            event.target.scroll({
                top: event.target.scrollTop + 1,
                behavior: 'smooth'
            });
        }
    }, 100);
    event.target.removeEventListener("scroll", scrollHandler);
}

function nextPage(minPages, maxPages){
    let min = parseInt(minPages);
    let max = parseInt(maxPages)-1;

    if(window.location.search){
        let urlSearchParams = new URLSearchParams(window.location.search);
        let oldParams = Object.fromEntries(urlSearchParams.entries());
        if (oldParams["page"]){
            delete oldParams["page"];
        }
        let page = new URLSearchParams(window.location.search).get('page')
        let newSearch = "?"
        if(page < max && page >= min){
            page++;
            for(let param in oldParams){
                newSearch += param + "=" + oldParams[param] + "&";
            }
            newSearch +=  "page=" + page;

            window.location.href = newSearch;
        }
    } else{
        min++;
        window.location.href = "?page=" + min;
    }
}

function previousPage(minPages, maxPages){
    let min = parseInt(minPages);
    let max = parseInt(maxPages)-1;

    if(window.location.search){
        let urlSearchParams = new URLSearchParams(window.location.search);
        let oldParams = Object.fromEntries(urlSearchParams.entries());
        if (oldParams["page"]){
            delete oldParams["page"];
        }
        let page = new URLSearchParams(window.location.search).get('page')
        let newSearch = "?"
        if(page <= max && page > min){
            page--;
            for(let param in oldParams){
                newSearch += param + "=" + oldParams[param] + "&";
            }
            newSearch +=  "page=" + page;

            window.location.href = newSearch;
        }
    }
}

function moveToPage(i, minPages, maxPages){

    let min = parseInt(minPages);
    let max = parseInt(maxPages)-1;
    let page = parseInt(i);

    if(window.location.search){
        let urlSearchParams = new URLSearchParams(window.location.search);
        let oldParams = Object.fromEntries(urlSearchParams.entries());

        if (oldParams["page"]){
            delete oldParams["page"];
        }

        let newSearch = "?"
        if(page <= max && page >= min){
            for(let param in oldParams){
                newSearch += param + "=" + oldParams[param] + "&";
            }
            newSearch +=  "page=" + page;

            window.location.href = newSearch;
        }
    }else{
        window.location.href = window.location.pathname + "?page=" + i;
    }

}


document.addEventListener("DOMContentLoaded", main);