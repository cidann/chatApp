document.addEventListener('DOMContentLoaded',()=>{
    let backgroundCheckBox=document.querySelector('#backgroundCheckBox');
    if(backgroundCheckBox){
        backgroundCheckBox.onclick=()=>{
        let background=document.querySelector('#background')
        background.value='';
        background.disabled=!background.disabled;
        }
    }
    let passwordCheckBox=document.querySelector('#passwordCheckBox');
    if(passwordCheckBox){
        passwordCheckBox.onclick=()=>{
            let password=document.querySelector('#password')
            password.value='';
            password.disabled=!password.disabled;
        }
    }
})