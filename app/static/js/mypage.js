// アカウント管理ダイアログ
const dialog = document.getElementById("accountDialog");
const openButton = document.getElementById("openButton");
const closeButton = document.getElementById("closeButton");

openButton.addEventListener("click", () => {
  dialog.showModal();
});

closeButton.addEventListener("click", () => {
  dialog.close();
});

// 退会確認ダイアログ
const deleteDialog = document.getElementById("deleteDialog");
const openDeleteButton = document.getElementById("openDeleteButton");
const cancelDeleteButton = document.getElementById("cancelDeleteButton");

openDeleteButton.addEventListener("click", () => {
  // アカウント管理を閉じてから退会確認を表示
  dialog.close();
  deleteDialog.showModal();
});

cancelDeleteButton.addEventListener("click", () => {
  deleteDialog.close();
});
