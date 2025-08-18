const editModal = new bootstrap.Modal(document.getElementById("profileEditModal"));
const editButton = document.getElementById("profileEditSettings");
editForm = document.getElementById("profileEditForm");

editButton.addEventListener("click", (e) =>{
    editModal.show();
    let profileId = e.target.getAttribute("data-profile_id");
    editForm.setAttribute("action", `profile/edit/${profileId}`);
})
