document.addEventListener("DOMContentLoaded", () => {
  const editModal = document.getElementById("editModal");
  if (!editModal) return;
  editModal.addEventListener("show.bs.modal", (ev) => {
    const b = ev.relatedTarget;
    const id = b.getAttribute("data-id");
    editModal.querySelector("#edit-id").value = id;
    editModal.querySelector("#edit-username").value = b.getAttribute("data-username") || "";
    editModal.querySelector("#edit-email").value = b.getAttribute("data-email") || "";
    editModal.querySelector("#edit-role").value = b.getAttribute("data-role") || "worker";
    editModal.querySelector("#edit-name").value = b.getAttribute("data-name") || "";
    editModal.querySelector("#edit-phone").value = b.getAttribute("data-phone") || "";
    editModal.querySelector("#edit-active").checked = (b.getAttribute("data-active") === "1");
    editModal.querySelector("#edit-newpw").value = "";
    editModal.querySelector("form").action = `/admin/users/${id}/update`;
  });
});
