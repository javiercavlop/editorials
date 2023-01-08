function main(){
    let img = document.getElementById("profile_pic_img");
    let firstNameForm = document.getElementById("first_name_form");
    let firstName = document.getElementById("first_name");
    let lastNameForm = document.getElementById("last_name_form");
    let lastName = document.getElementById("last_name");
    let usernameForm = document.getElementById("username_form");
    let username = document.getElementById("username");
    let emailForm = document.getElementById("email_form");
    let email = document.getElementById("email");
    let profilePicForm = document.getElementById("profile_pic_form");
    let profilePic = document.getElementById("profile_pic");

    if(profilePic.value.trim()=="static/images/profile.png" || profilePic.value.trim()=="/static/images/profile.png"){
        profilePic.value = "";
    }

    profilePic.addEventListener("change", function(){
        let value = profilePic.value.trim()
        if(value!=""){
            img.src = value;
        }else{
            img.src = "/static/images/profile.png";
        }
        deleteErrors(profilePicForm);
    });

    checkBtn();

    firstName.addEventListener("change", function(){
        deleteErrors(firstNameForm);
    });

    lastName.addEventListener("change", function(){
        deleteErrors(lastNameForm);
    });

    username.addEventListener("change", function(){
        deleteErrors(usernameForm);
    });

    email.addEventListener("change", function(){
        deleteErrors(emailForm);
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
    let btn = document.getElementById("profile_btn");
    if(document.getElementsByClassName("class-error-form").length > 0){
        btn.disabled = true;
    } else{
        btn.disabled = false;
    }
}

document.addEventListener("DOMContentLoaded", main);