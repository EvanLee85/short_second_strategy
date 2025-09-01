// 表单片段（占位，后续按页面需要补充）
export function FormRow({ label, input }) {
  const wrap = document.createElement("div");
  wrap.className = "form-row";
  const lab = document.createElement("label");
  lab.className = "label"; lab.textContent = label;
  wrap.appendChild(lab);
  wrap.appendChild(input);
  return wrap;
}
