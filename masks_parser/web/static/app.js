// Показывает имя выбранного файла, подсвечивает зону при перетаскивании
// и блокирует кнопку на время проверки. Без JS форма работает так же.
document.querySelectorAll("[data-drop]").forEach((drop) => {
  const input = drop.querySelector("input[type=file]");
  const label = drop.querySelector("[data-file]");
  const initial = label.textContent;

  const show = () => {
    const file = input.files[0];
    drop.classList.toggle("has-file", Boolean(file));
    label.textContent = file ? `✓ ${file.name} · ${(file.size / 1024).toFixed(0)} КБ` : initial;
  };

  input.addEventListener("change", show);
  ["dragenter", "dragover"].forEach((type) =>
    drop.addEventListener(type, (event) => {
      event.preventDefault();
      drop.classList.add("dragging");
    }),
  );
  ["dragleave", "drop"].forEach((type) => drop.addEventListener(type, () => drop.classList.remove("dragging")));
  drop.addEventListener("drop", (event) => {
    event.preventDefault();
    if (event.dataTransfer.files.length) {
      input.files = event.dataTransfer.files;
      show();
    }
  });
});

document.querySelectorAll("form[data-submit]").forEach((form) => {
  form.addEventListener("submit", () => {
    const button = form.querySelector("[data-busy]");
    button.disabled = true;
    button.textContent = button.dataset.busy;
  });
});
