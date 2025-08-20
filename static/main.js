document.addEventListener("DOMContentLoaded", () => {
  const editModal = document.getElementById("editModal");
  if (!editModal) return;

  editModal.addEventListener("show.bs.modal", (ev) => {
    const btn = ev.relatedTarget;
    const id = btn.getAttribute("data-id");
    const username = btn.getAttribute("data-username");
    const email = btn.getAttribute("data-email");
    const role = btn.getAttribute("data-role");
    const name = btn.getAttribute("data-name");
    const phone = btn.getAttribute("data-phone");
    const active = btn.getAttribute("data-active") === "1";

    editModal.querySelector("#edit-id").value = id;
    editModal.querySelector("#edit-username").value = username || "";
    editModal.querySelector("#edit-email").value = email || "";
    editModal.querySelector("#edit-role").value = role || "worker";
    editModal.querySelector("#edit-name").value = name || "";
    editModal.querySelector("#edit-phone").value = phone || "";
    editModal.querySelector("#edit-active").checked = active;

    // 동적 action 세팅
    const form = editModal.querySelector("form");
    form.action = `/admin/users/${id}/update`;
    editModal.querySelector("#edit-newpw").value = "";
  });
});
