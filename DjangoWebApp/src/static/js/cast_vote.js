
// When the user clicks on the button, open the modal
function open_modal(modal, modal_content, candidate_div, value) {
  modal.style.display = "block";
  candidate_modal = candidate_div.cloneNode(true)
  candidate_modal.id = "candidate_modal";

  let child_nodes = modal_content.childNodes;
  for (let child of child_nodes) {
      if ((child.id) == "confirm_btn") {
        child.value = value;
      }
      else if((child.id) == "candidate_div") {
        child.appendChild(candidate_modal)
      }
  }    
}

// When the user clicks on <span> (x), close the modal
function close_modal(modal, modal_content) {
  modal.style.display = "none";
  let child_nodes = modal_content.childNodes;
  for (let child of child_nodes) {
    if ((child.id) == "confirm_btn") {
        child.value=null;
    }
    else if ((child.id) == "candidate_div"){
        child.removeChild(child.firstChild);
    }
}
}
