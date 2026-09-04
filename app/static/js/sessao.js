let ultimaAtividade = Date.now();

function registrarAtividade() {

    const agora = Date.now();

    // Evita mandar requisições centenas de vezes por segundo
    if (agora - ultimaAtividade < 30000) {
        return;
    }

    ultimaAtividade = agora;

    fetch("/registrar-atividade/", {
        method: "POST",
        credentials: "same-origin",
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
            "Content-Type": "application/json"
        }
    });
}


function getCookie(nome) {

    let cookies = document.cookie.split(";");

    for (let cookie of cookies) {

        cookie = cookie.trim();

        if (cookie.startsWith(nome + "=")) {
            return decodeURIComponent(
                cookie.substring(nome.length + 1)
            );
        }
    }

    return null;
}


document.addEventListener("click", registrarAtividade);
document.addEventListener("keydown", registrarAtividade);
document.addEventListener("scroll", registrarAtividade);
document.addEventListener("touchstart", registrarAtividade);


setInterval(function () {

    fetch("/verificar-sessao/", {
        method: "GET",
        credentials: "same-origin"
    })
    .then(function (response) {

        if (response.status === 401) {
            window.location.reload();
        }

    });

}, 50000);