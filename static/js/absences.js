const editModal = new bootstrap.Modal(
    document.getElementById("absenceEditModal"));
const editButtons = document.getElementsByClassName("btn-absence-edit");
const editForm = document.getElementById("absenceEditForm");

const deleteModal = new bootstrap.Modal(
    document.getElementById("absenceDeleteModal"));
const deleteButtons = document.getElementsByClassName("btn-absence-delete");
const deleteForm = document.getElementById("absenceDeleteForm");
const deleteConfirm = document.getElementById("absenceDeleteConfirm");


for (let button of editButtons) {
    button.addEventListener("click", (e) => {
        editModal.show()
        let absenceId = e.target.getAttribute("data-absence_id");
        editForm.setAttribute("action", `absence/edit/${absenceId}`);
    });
}

for (let button of deleteButtons) {
    button.addEventListener("click", (e) => {
        deleteModal.show()
        let absenceId = e.target.getAttribute("data-absence_id");
        deleteConfirm.href = `absence/delete/${absenceId}`;
    });
}