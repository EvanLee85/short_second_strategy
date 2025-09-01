// 选项卡（占位）
export function Tabs(items = []) {
  const wrap = document.createElement("div");
  const bar = document.createElement("div"); bar.style.marginBottom = "8px";
  const body = document.createElement("div");
  wrap.appendChild(bar); wrap.appendChild(body);

  function activate(idx) {
    body.innerHTML = "";
    const it = items[idx];
    items.forEach((x, i) => {
      btns[i].className = "btn " + (i === idx ? "brand" : "");
    });
    body.appendChild(typeof it.content === "function" ? it.content() : it.content);
  }

  const btns = items.map((it, i) => {
    const b = document.createElement("a");
    b.href = "javascript:void(0)";
    b.className = "btn";
    b.textContent = it.title || `Tab ${i+1}`;
    b.onclick = () => activate(i);
    bar.appendChild(b);
    return b;
  });

  if (items.length) activate(0);
  return wrap;
}
