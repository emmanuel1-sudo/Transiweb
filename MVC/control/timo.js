
const botonTimo = document.getElementById("timo-boton");
const chatTimo = document.getElementById("timo-chat");
const cerrarTimo = document.getElementById("timo-cerrar");
const formularioTimo = document.getElementById("timo-formulario");
const entradaTimo = document.getElementById("timo-entrada");
const mensajesTimo = document.getElementById("timo-mensajes");

let ultimoTramite = "";

function abrirTimo() {
    chatTimo.hidden = false;
    botonTimo.setAttribute("aria-expanded", "true");
    entradaTimo.focus();
}

function cerrarChatTimo() {
    chatTimo.hidden = true;
    botonTimo.setAttribute("aria-expanded", "false");
    botonTimo.focus();
}

botonTimo.addEventListener("click", () => {
    if (chatTimo.hidden) {
        abrirTimo();
    } else {
        cerrarChatTimo();
    }
});

cerrarTimo.addEventListener("click", cerrarChatTimo);


function agregarMensaje(texto, tipo) {
    const mensaje = document.createElement("div");
    mensaje.classList.add("timo-mensaje", tipo);
    mensaje.textContent = texto;

    mensajesTimo.appendChild(mensaje);
    mensajesTimo.scrollTop = mensajesTimo.scrollHeight;
}


function responderTimo(pregunta) {
    const texto = pregunta.toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "");

    if (texto.includes("hola") || texto.includes("buenas")) {
        return "¡Hola! Soy Timo, tu asistente de Transiweb. ¿En qué puedo ayudarte?";
    }

    if (texto.includes("traspaso")) {
        return "¡Claro! El traspaso es el trámite mediante el cual se realiza el cambio de propietario de un vehículo. Generalmente se requiere documentación del comprador y vendedor, documentos del vehículo y cumplir los requisitos establecidos por el organismo de tránsito. ¿Quieres conocer más sobre este trámite?";
    }

    if (texto.includes("traslado")) {
        return "El traslado de cuenta permite cambiar el organismo de tránsito donde está registrado un vehículo. ¿Quieres conocer más sobre este procedimiento?";
    }

    if (texto.includes("matricula")) {
        return "La matrícula es el registro inicial de un vehículo ante un organismo de tránsito. ¿Quieres conocer los requisitos para realizarla?";
    }

    if (texto.includes("duplicado")) {
        return "El duplicado permite obtener una nueva copia de un documento del vehículo, por ejemplo, la licencia de tránsito. ¿Quieres saber más?";
    }

    if (texto.includes("radicado")) {
        return "El radicado permite registrar una solicitud o trámite ante el organismo de tránsito. ¿Quieres conocer cómo realizarlo?";
    }

    if (texto.includes("requisito") || texto.includes("documento")) {
        return "Los requisitos dependen del trámite que necesites. Dime si es un traspaso, traslado, matrícula o duplicado.";
    }

    if (texto.includes("licencia") || texto.includes("pase")) {
        return "La licencia de conducción es el documento que autoriza a una persona para conducir determinados vehículos. ¿Quieres información sobre este trámite?";
    }

    if (texto.includes("contacto") || texto.includes("ayuda")) {
        return "¡Estoy aquí para ayudarte! Puedes preguntarme sobre los trámites disponibles en Transiweb.";
    }

    if (texto.includes("gracias")) {
        return "¡Con mucho gusto! Aquí estaré para ayudarte.";
    }

    if (texto === "si" || texto === "sí" || texto === "claro") {
    if (ultimoTramite === "traspaso") {
        return "¡Claro! Para continuar con el traspaso, debes verificar los documentos del vehículo, comprador y vendedor, además de los requisitos exigidos por el organismo de tránsito. ¿Quieres que te explique los documentos que generalmente se solicitan?";
    }
}

    return "Quiero ayudarte. Por ahora puedo orientarte sobre traspasos, traslados, matrículas, duplicados, requisitos y navegación en Transiweb. ¿Qué necesitas consultar?";
}


function enviarMensaje(texto) {
    const pregunta = texto.trim();

    if (!pregunta) return;

    agregarMensaje(pregunta, "timo-usuario");
    entradaTimo.value = "";

    const respuesta = responderTimo(pregunta);
    agregarMensaje(respuesta, "timo-bot");
}

formularioTimo.addEventListener("submit", (evento) => {
    evento.preventDefault();
    enviarMensaje(entradaTimo.value);
});

document.querySelectorAll(".timo-sugerencias button").forEach((boton) => {
    boton.addEventListener("click", () => {
        enviarMensaje(boton.dataset.pregunta);
    });
});
