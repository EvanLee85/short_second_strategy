import { Card } from "../components/Card.js";
export default { route: "/404", title: "未找到", render() {
  const box=document.createElement("div");
  box.appendChild(Card({ title:"页面不存在", content:"请检查路径。" }));
  return box;
}};
