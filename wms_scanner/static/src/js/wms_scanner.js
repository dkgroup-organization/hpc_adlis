
document.addEventListener('keydown', FocusScan);

function FocusScan() {
    var scan = document.getElementById("scan"); 

    if (scan != document.activeElement) {
        scan.focus();
        }
    }

