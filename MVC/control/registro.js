const form = document.querySelector("form");

formulario.addEventListener("submit", function (evento) {

   
    evento.preventDefault();

    
    const nombre = document.getElementById("nombre").value.trim();
    const correo = document.getElementById("correo").value.trim();
    const identificacion = document.getElementById("identificacion").value.trim();
    const password = document.getElementById("password").value.trim();


   
    if (nombre === "") {
        alert("Escribe tu nombre completo.");
        return;
    }


    
    if (correo === "") {
        alert("Escribe tu correo electrónico.");
        return;
    }


   
    if (identificacion === "") {
        alert("Escribe tu identificación.");
        return;
    }


    if (password === "") {
        alert("Crea una contraseña.");
        return;
    }


    alert("¡Cuenta creada correctamente!");

});