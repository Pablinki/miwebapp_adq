// Mejoras en script.js para UX y consistencia



document.addEventListener("DOMContentLoaded", () => {
    // Botones y elementos
    
    console.log("Script cargado...")
    
    const searchForm = document.getElementById("searchForm");
    const clearButton = document.querySelector("#searchForm button[type='button']");
    const resultContainer = document.querySelector(".result-container");
    const destinatarioSelect = document.getElementById("destinatarioSelect");
    const destinatarioInfo = document.getElementById("destinatarioInfo");
    const cargoInfo = document.getElementById("cargoInfo");

    // Limpia el formulario y los resultados
    window.clearForm = function () {
        if (searchForm) searchForm.reset();
        if (resultContainer) resultContainer.style.display = "none";
        if (destinatarioInfo) destinatarioInfo.innerText = "";
        if (cargoInfo) cargoInfo.innerText = "";
        const downloadLinks = document.getElementById("downloadLinks");
        if (downloadLinks) downloadLinks.innerHTML = "";
    };

    // Muestra el destinatario y su cargo
    window.mostrarDestinatario = function () {
        const selectedOption = destinatarioSelect.options[destinatarioSelect.selectedIndex];
        destinatarioInfo.textContent = "Destinatario seleccionado: " + selectedOption.value;
        cargoInfo.textContent = "Cargo: " + selectedOption.getAttribute("data-cargo");
        const errorMsg = document.getElementById("errorDestinatario");
        // Limpia el mensaje de error si había
        if (errorMsg) {
            errorMsg.style.display = "none";
            errorMsg.innerText = "";
        }
    };

    // Genera documento y muestra enlace de descarga
    window.generarDocumento = function (tipo, contratoId) {
        const destinatario = destinatarioSelect.value;
        //const destinatarioSelect = document.getElementById("destinatarioSelect");
        const errorMsg = document.getElementById("errorDestinatario");

        if (!destinatario) {
            if (errorMsg) {
            errorMsg.style.display = "block";
            errorMsg.innerText = "⚠️ Debe asignar un destinatario antes de generar el documento.";
        }
            return;
        }
        
        // Limpia el mensaje si ya seleccionó destinatario
        if (errorMsg) {
            errorMsg.style.display = "none";
            errorMsg.innerText = "";
        }

        const url = `/generar-documento/?contrato=${contratoId}&tipo=${tipo}&destinatario=${encodeURIComponent(destinatario)}`;

        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const downloadLinks = document.getElementById("downloadLinks");
                    const enlace = document.createElement("a");
                    enlace.href = data.doc_url;
                    enlace.textContent = "Descargar " + tipo;
                    enlace.target = "_blank";
                    downloadLinks.appendChild(enlace);
                } else {
                    alert("Error: " + data.error);
                }
            })
            .catch(error => console.error("Error en la petición:", error));
    };

    // Muestra u oculta secciones adicionales (plurianual, etc)
    window.toggleSection = function (sectionId, buttonId) {
        const section = document.getElementById(sectionId);
        const button = document.getElementById(buttonId);

        if (!section || !button) return;

        if (section.style.display === "none" || section.style.display === "") {
            section.style.display = "block";
            button.textContent = "Ocultar Detalle";
        } else {
            section.style.display = "none";
            button.textContent = "Ver Detalle";
        }
    };

    
    const contratoInput = document.getElementById("id_contrato");
    
    console.log("Cargado:", searchForm, contratoInput);
    
    // Define globalmente la función
    window.detallesContrato = function (contratoId) {
        if (!searchForm || !contratoInput) {
            console.error("Formulario o campo de contrato no encontrados.");
            return;
        }

        contratoInput.value = contratoId;
        searchForm.submit();
    };
    
    

});

