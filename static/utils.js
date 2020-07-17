
var pathOptionTemplate = document.querySelector('#path_template');
var pathOptionSelector = document.querySelector('#path_options');

function showPrompt(path) {
    fetch(`/get_path_options?path=${path}`).then((response) => {
        response.json().then((data) => {
            var options_quantity = data.length;
            pathOptionSelector.innerHTML = "";

            if (!options_quantity) {
                return;
            }

            for (var i = 0; i < options_quantity; i++) {
                let templateClone = pathOptionTemplate.content.cloneNode(true);

                templateClone.querySelector("#path_option").value = `${data[i]}`;
                pathOptionSelector.appendChild(templateClone);
            }
        })
    })
}


function listenClickOnEnter(input, button) {
    input.addEventListener("keyup", event => {
        if (event.key !== "Enter") return;

        button.click();
        event.preventDefault();
    });
}