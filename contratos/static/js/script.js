function toggleSection(sectionId, buttonId) {
            let section = document.getElementById(sectionId);
            let button = document.getElementById(buttonId);
            
            if (section.style.display === "none") {
                section.style.display = "block";
                button.textContent = "Ocultar Detalle";
            } else {
                section.style.display = "none";
                button.textContent = "Ver Detalle";
            }
}

 document.addEventListener("DOMContentLoaded", function () {
    function clearForm() {
        console.log("🔄 Ejecutando clearForm()"); // Debug para verificar si la función se ejecuta

        // Restablecer el formulario
        let form = document.getElementById("searchForm");
        if (form) {
            form.reset();
        }

        // Ocultar la sección de resultados
        let resultContainer = document.querySelector(".result-container");
        if (resultContainer) {
            resultContainer.style.display = "none";
        }

        // Limpiar el valor de la caja de búsqueda
        let contratoInput = document.getElementById("id_contrato");
        if (contratoInput) {
            contratoInput.value = "";
        }

        // También limpiar los destinatarios seleccionados y mensajes de error
        let destinatarioSelect = document.getElementById("destinatarioSelect");
        if (destinatarioSelect) {
            destinatarioSelect.selectedIndex = 0;
        }

        let destinatarioInfo = document.getElementById("destinatarioInfo");
        if (destinatarioInfo) {
            destinatarioInfo.innerText = "";
        }

        let cargoInfo = document.getElementById("cargoInfo");
        if (cargoInfo) {
            cargoInfo.innerText = "";
        }

        let errorDestinatario = document.getElementById("errorDestinatario");
        if (errorDestinatario) {
            errorDestinatario.style.display = "none";
        }

        // Ocultar detalles de póliza y plurianual si estaban abiertos
        let polizaDetails = document.getElementById("polizaDetails");
        if (polizaDetails) {
            polizaDetails.style.display = "none";
        }

        let plurianualDetails = document.getElementById("plurianualDetails");
        if (plurianualDetails) {
            plurianualDetails.style.display = "none";
        }

        console.log("✅ Formulario y contenedores limpiados");
    }

    // Asignar la función al botón de "Limpiar"
    let clearButton = document.querySelector("button[onclick='clearForm()']");
    if (clearButton) {
        clearButton.addEventListener("click", clearForm);
    } else {
        console.warn("⚠️ Botón de limpiar no encontrado");
    }
});

		
function mostrarDestinatario() {
        let select = document.getElementById("destinatarioSelect");
        let nombreSeleccionado = select.value;
        let cargoSeleccionado = select.options[select.selectedIndex].getAttribute("data-cargo");
        let errorMensaje = document.getElementById("errorDestinatario");
        
        if (nombreSeleccionado) {
            document.getElementById("destinatarioInfo").innerText = "Destinatario seleccionado: " + nombreSeleccionado;
            document.getElementById("cargoInfo").innerText = "Cargo: " + cargoSeleccionado;
            errorMensaje.style.display = "none";  // Ocultar mensaje de error
            
        } else {
            document.getElementById("destinatarioInfo").innerText = "";
            document.getElementById("cargoInfo").innerText = "";
        }
}

function generarDocumento(tipo, contratoId) {
        let destinatario = document.getElementById("destinatarioSelect").value;
        let errorMensaje = document.getElementById("errorDestinatario");

        if (!destinatario) {
            //alert("Seleccione un destinatario.");
            errorMensaje.innerText = "⚠️ Seleccione un destinatario antes de generar el documento.";
            errorMensaje.style.display = "block";
            
            return;
        }
        
        // Codificar el nombre del destinatario para la URL
        let destinatarioEncoded = encodeURIComponent(destinatario.trim());

        let url = `/generar-documento/?contrato=${contratoId}&tipo=${tipo}&destinatario=${destinatario}`;

        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById("downloadLinks").innerHTML = `<p><a href="${data.doc_url}" download>Descargar Documento</a></p>`;
                    errorMensaje.style.display = "none"; // Ocultar error si se genera con éxito
                } else {
                    //alert("Error: " + data.error);
                    errorMensaje.innerText = "⚠️ Error en la petición: " + error;
                    errorMensaje.style.display = "block";
                }
            })
            .catch(error => console.error("Error en la petición:", error));
    }